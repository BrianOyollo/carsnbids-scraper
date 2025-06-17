import os
import pandas as pd
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from logger import setup_json_logger
import boto3
import driver_setup
import scrape_auction_urls
import scrape_auction
import utils
import notify



load_dotenv()
logger = setup_json_logger()
today = datetime.now().date()

max_pages = os.getenv('MAX_PAGES_TO_SCRAPE')
db_path = os.getenv('SQLITE_DB_PATH')
raw_auctions_bucket = os.getenv("RAW_AUCTIONS_BUCKET")
ec2_instance_id = os.getenv('EC2_INSTANCE_ID')

ntfy_topic = os.getenv('NTFY_TOPIC')


def run_scraper():
    """
    Orchestrates the entire scraping pipeline:
        - Sets up the Selenium WebDriver
        - Connects to the database
        - Scrapes auction listing URLs
        - Filters out already known URLs
        - Scrapes auction details for the new URLs
        - Inserts new URLs into the database
        - Uploads auction data to S3
        - Commits DB changes only if upload is successful
        - Closes all resources cleanly
        - Sends notification to phone using ntfy (https://ntfy.sh/)
    """
    ntfy_message = ''
    conn = None
    cursor = None
    driver = None

    try:
        # setup driver
        logger.info(f"====== Setting up Webdriver ======")
        driver = driver_setup.setup_driver()

        # setup db connection
        logger.info("====== Setting up db connection ======")
        conn, cursor = utils.db_connection(db_path)

        # aws connections
        s3_client = boto3.client("s3")
        ec2_client = boto3.client("ec2")


        # scrape daily urls
        logger.info('====== Scraping daily urls ===== ')
        page_count = 1
        if max_pages:
            page_count = int(max_pages)
        start_time = time.time()
        daily_urls = scrape_auction_urls.extract_auction_urls(driver, page_count)
        logger.info(f"URLs scraping completed in {(time.time() - start_time)} seconds")


        # filter out url
        logger.info("====== Filtering out urls ====== ")
        new_urls = utils.filter_urls(cursor, daily_urls)

        if not new_urls:
            logger.info("No new auctions found. Shutting down instance.")
            ntfy_message = "No new auctions today. Instance will shut down."
            notify.send_notification(ntfy_topic, ntfy_message)

            utils.stop_instance(ec2_client, ec2_instance_id)
            
            return


        # scrape auction details
        logger.info('====== Scraping auction_details ======')
        auctions_data = []
        successful_urls = []
        for url in new_urls:
            try:
                logger.info(f'Scraping url: {url}')
                start_time = time.time()
                auction_data = scrape_auction.scrape_auction_data(driver,url)
                logger.info(f"Auction scraping completed in {(time.time() - start_time)} seconds")
                auctions_data.append(auction_data)
                successful_urls.append(url)
            except Exception as e:
                logger.warning(f'Error scraping {url}', exc_info=True)

        # insert new urls into db
        logger.info("====== Updating urls table ====== ")
        inserted_rows = utils.insert_urls(cursor,successful_urls)

        # upload auctions to s3
        uploaded = utils.upload_to_s3(s3_client, auctions_data, raw_auctions_bucket)

        if uploaded:
            # committ & close db connection
            logger.info('Auctions successfully uploaded to s3. Committing DB changes')
            conn.commit()

            logger.info(f"Scraped urls: {len(daily_urls)}")
            logger.info(f"New urls: {len(new_urls)}")
            logger.info(f"Successfully scraped urls: {len(new_urls)}")
            logger.info(f"URLs inserted into db: {inserted_rows}")

            # ntfy msg
            ntfy_message = f"""
                Daily auctions scraping completed.\n
                Scraped urls: {len(daily_urls)}.\n
                New urls: {len(new_urls)}.\n
                Successfully scraped urls: {len(new_urls)}.\n
                URLs inserted into db: {inserted_rows}.\n
            """
        else:
            logger.warning("Upload failed. New urls will not be saved in the db", exc_info=True)
            ntfy_message = f"Upload to s3 failed"

    except Exception as e:
        logger.error(f"Error in scraping pipeline: {e}", exc_info=True)
        ntfy_message = f"Error in pipeline. \n {e}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        if driver:
            driver_setup.driver_teardown(driver)

        # send notification
        notify.send_notification(ntfy_topic,ntfy_message)


run_scraper()