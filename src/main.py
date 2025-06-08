import os
import pandas
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from logger import setup_json_logger
import driver_setup
import scrape_auction_urls
import scrape_auction
import utils


load_dotenv()
logger = setup_json_logger()
today = datetime.now().date()

max_pages = os.getenv('MAX_PAGES_TO_SCRAPE')
db_path = os.getenv('SQLITE_DB_PATH')
raw_auctions_bucket = os.getenv("RAW_AUCTIONS_BUCKET")

def run_scraper():

    # setup driver
    logger.info(f"====== Setting up Webdriver ======")
    driver = driver_setup.setup_driver()

    # setup db connection
    logger.info("====== Setting up db connection ======")
    conn, cursor = utils.db_connection(db_path)

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
    print(f"new urls:{new_urls}")

    # insert new urls into db
    logger.info("====== Updating urls table ====== ")
    inserted_rows = utils.insert_urls(cursor,new_urls)
    print(f"inserted rows: {inserted_rows}")


    # scrape auction details
    logger.info('====== Scraping auction_details ======')
    auctions_data = []
    for url in new_urls:
        start_time = time.time()
        auction_data = scrape_auction.scrape_auction_data(driver,url)
        logger.info(f"Auction scraping completed in {(time.time() - start_time)} seconds")
        auctions_data.append(auction_data)

    print(auctions_data)

    # upload auctions to s3
    uploaded = utils.upload_to_s3(auctions_data, raw_auctions_bucket)

    if uploaded:
        # committ & close db connection
        logger.info('Auctions successfully uploaded to s3. Committing DB changes')
        conn.commit()
        cursor.close()
        conn.close()
    else:
        logger.warning("Upload failed. New urls will not be saved in the db")

    # close webdriver
    driver_setup.driver_teardown(driver)

run_scraper()