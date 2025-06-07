import os
import pandas
from datetime import datetime, timedelta

from logger import setup_json_logger
import driver_setup
import scrape_auction_urls

logger = setup_json_logger()

today = datetime.now().date()

def run_scraper():

    # setup driver
    logger.info(f"Setting up driver")
    driver = driver_setup.setup_driver()

    # scrape daily urls
    logger.info('Scraping daily urls')
    daily_urls = scrape_auction_urls.extract_auction_urls(driver, 2)

    # filter out urls
    
    

run_scraper()