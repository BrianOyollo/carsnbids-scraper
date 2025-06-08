import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import sqlite3
import csv

from logger import setup_json_logger

load_dotenv()
logger = setup_json_logger()

uls_file_path = os.getenv('URLS_FILE_PATH')
filter_duration = os.getenv('URLS_FILTER_DURATION')
db_path = os.getenv('SQLITE_DB_PATH')

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
        logger.error(f'Error connecting to db: {e1}')
    except Exception as e2:
        logger.error(f"Error: {e2}")

    

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

    return cursor.rowcount  # Number of rows successfully inserted


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
            logger.error(f"Error processing url ({url}): {e}")
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
    logger.info(f"{len(new_urls)} new urls found")

    return new_urls
        

    
