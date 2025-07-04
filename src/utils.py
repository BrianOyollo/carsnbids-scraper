import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import sqlite3
import csv
import json
import boto3
import argparse

from logger import setup_json_logger

load_dotenv()
logger = setup_json_logger()

sqlite_db_path = os.getenv('SQLITE_DB_PATH')


def db_connection(db_path:str=None):
    if not db_path:
        db_path = 'carsnbids.db'

    logger.info("Connecting to db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info("DB connection successfull")
        return conn, cursor
    except sqlite3.Error as e1:
        logger.error(f'Error connecting to db: {e1}',exc_info=True)
    except Exception as e2:
        logger.error(f"Error: {e2}",exc_info=True)

    

def insert_urls(cursor, urls: list):
    """
    Inserts new auction URLs into the SQLite database.

    Each URL contains an auction ID, which is extracted and used as the primary key.
    If a URL with the same auction ID already exists, it is ignored (ON CONFLICT DO NOTHING).

    Args:
        cursor (sqlite3.Cursor): An active SQLite cursor object.
        urls (list): A list of full auction URLs (strings).

    Returns:
        int: The number of rows successfully inserted into the database.
    """
    urls_data = []

    for url in urls:
        # Extract the auction ID from the URL (second last part of the path)
        auction_id = url.split("/")[-2]
        urls_data.append({'auction_id': auction_id, 'url': url})

    # Perform a batch insert using named parameters; ignore duplicates
    cursor.executemany(
        "INSERT INTO urls(auction_id, url) VALUES(:auction_id, :url) ON CONFLICT(auction_id) DO NOTHING",
        urls_data
    )
    inserted = cursor.rowcount
    return inserted  # Number of rows successfully inserted


def filter_urls(cursor, urls:list)->list:
    """
    Filters out URLs that already exist in the database.

    Args:
        cursor (sqlite3.Cursor): Database cursor.
        urls (list): List of URLs to check.

    Returns:
        list: URLs not found in the database (new URLs).
    """
    logger.info('Extracting new urls')
    auctions = {}
    for url in urls:
        try:
            auction_id = url.split("/")[-2]
            auctions[auction_id]=url
        except Exception as e:
            logger.error(f"Error processing url ({url}): {e}", exc_info=True)
            continue
    
    if not auctions:
        logger.info('No new urls found')
        return []
    
    
    auction_ids = list(auctions.keys()) # generate list of auction ids
    placeholders = ",".join('?' for _ in auction_ids) # generate placeholders
    query = f"""
        SELECT auction_id
        FROM urls
        WHERE auction_id in ({placeholders});
    """
    cursor.execute(query, auction_ids)
    existing_urls = cursor.fetchall()
    existing_ids = {row[0] for row in existing_urls}
    new_urls = [auctions[id] for id in auction_ids if id not in existing_ids]

    return new_urls



def upload_to_s3(s3_client, auction_data:list, bucket):
    """
    Uploads auction data to an S3 bucket as a JSON file.

    Args:
        auction_data (list): List of auction dictionaries to upload.
        bucket (str): Name of the target S3 bucket.

    The file will be named using the format: 'auctions_<prev_date>.json',
    where <prev_date> is the previous day's date in YYYY-MM-DD format.
    """

    prev_date = datetime.now().date() - timedelta(days=1)
    key = f"auctions_{prev_date}.json"

    json_data = json.dumps(auction_data, indent=3)
    try:
        logger.info('Uploading auctions to s3')
        s3_client.put_object(Bucket=bucket,Key=key, Body=json_data)
        return True
    except Exception as e:
        logger.error(f"Error uploading auctions to s3 bucket: {e}", exc_info=True)


def export_db_urls_to_csv(conn=None, cursor=None, file_path:str='auction_urls.csv'):
    """Exports all auction URLs from SQLite database to a CSV file.
    
    Retrieves URLs and their scrape timestamps from the database, then writes them
    to a CSV file with columns: ['url', 'scraped_at'].

    Args:
        file_path (str, optional): Output CSV file path. Defaults to 'auction_urls.csv'.
        conn (Optional[sqlite3.Connection]): Existing database connection. If None, creates a new one.
        cursor (Optional[sqlite3.Cursor]): Existing database cursor. If None, creates a new one.

    
    Returns:
        None: Output is written to the specified CSV file.
    
    Raises:
        Exception: Propagates any database or file I/O errors with full stack trace.
    
    Notes:
        - Overwrites existing file
        - Only closes connections it creates (won't close passed-in connections)
    """

    close_conn = False
    close_cursor = False

    try:
        logger.info("Exporting auction urls to csv file")

        if conn is None and cursor is None:
            conn,cursor = db_connection(sqlite_db_path)
            close_conn = True
            close_cursor = True
        
        logger.info("Querying db for urls")
        query = "SELECT url,scraped_at FROM urls"
        results = cursor.execute(query).fetchall()

        logger.info("Exporting urls to csv file")
        with open(f"{file_path}", "w") as file:
            csvwriter = csv.writer(file)
            csvwriter.writerow(['url','scraped_at'])
            csvwriter.writerows(results)

        logger.info(f"Auctions urls successfully exported to {os.path.abspath(file_path)}")
        print(f"Auctions urls successfully exported to {os.path.abspath(file_path)}")
    except Exception as e:
        logger.error(f"Error exporting auction urls to csv file: {e}", exc_info=True)
        raise
    finally:
        if close_cursor and cursor:
            cursor.close()
        if close_conn and conn:
            conn.close()

def import_urls_from_csv(conn=None, cursor=None, file_path:str='urls.csv'):

    close_conn = False
    close_cursor = False

    try:
        logger.info("Importing auction urls into db")

        urls = []

        # read csv file 
        logger.info(f'Reading csv file at {os.path.abspath(file_path)}')
        with open(file_path, "r") as file:
            csv_reader = csv.reader(file)
            next(csv_reader)

            for row in csv_reader:
                urls.append(row[0])

        # connect to db
        if conn is None and cursor is None:
            conn,cursor = db_connection(sqlite_db_path)
            close_conn = True
            close_cursor = True

        # insert urls
        logger.info("Inserting auctions urls into db")
        inserted = insert_urls(cursor, urls)
        conn.commit()

        logger.info(f"{inserted} urls inserted into db")
        print(f"{inserted} urls inserted into db")
    
    except Exception as e:
        logger.info(f"Error importing urls into db: {e}", exc_info=True)
        print(f'Error importing urls.{e}')

    finally:
        if close_cursor and cursor:
            cursor.close()
        if close_conn and conn:
            conn.close()


def start_instance(ec2_client, instance_id:str):
    """
    Start ec2 instance

    Args:
        instance_id (str): _description_
    """
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
    except Exception as e:
        logger.warning(f"Error starting ec2 instance: {e}", exc_info=True)


def stop_instance(ec2_client, instance_id:str):
    """
    Stop ec2 instance

    Args:
        instance_id (str): _description_
    """
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
    except Exception as e:
        logger.warning(f"Error terminating ec2 instance: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarsnBids Scraper Utilities")
    subparsers = parser.add_subparsers(dest='action', required=True, help="What action you want to do")

    # export action
    export_parser = subparsers.add_parser('export_urls', help="Export auction urls from DB to csv file")
    export_parser.add_argument("--file", type=str, default='auction_urls.csv', help="CSV file path to export to")

    # import parser
    import_parser = subparsers.add_parser('import_urls', help='Import auction urls from CSV to DB')
    import_parser.add_argument("--file", type=str, default='auction_urls.csv', help="CSV file path to import from")

    args = parser.parse_args()

    if args.action == 'export_urls':
        export_db_urls_to_csv(file_path=args.file)
    elif args.action == 'import_urls':
        import_urls_from_csv(file_path=args.file)

