from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
from datetime import datetime
import os
from dotenv import load_dotenv
import logger

from driver_setup import close_promo_bar

load_dotenv()
logger = logger.setup_json_logger()




def wait_for_pagination(driver, timeout:int=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".paginator"))
        )
        logger.info("Pagination loaded (auctions likely loaded).")
    except TimeoutException:
        logger.error("Pagination not found. Proceeding anyway...")


def extract_auction_urls(driver, max_pages:int, timeout:int=60*5):
    """
    Scrapes auction URLs from carsandbids.com/past-auctions/.
    
    Args:
        driver: Selenium WebDriver instance.
        max_pages (int): Max number of pages to scrape. If None, scrape all.
        timeout (int): Timeout for WebDriverWait.
    Returns:
        list: All scraped auction URLs.
    """
    driver.get('https://carsandbids.com/past-auctions/')
    close_promo_bar(driver)


    auction_urls = []
    current_page = 1

    while True:
        logger.info(f"Scraping page {current_page}...")

        try:
            # wait for auctions to load
            WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".auction-item")
            ))

            # extract urls from  current page
            auction_links = driver.find_elements(By.CSS_SELECTOR, ".auction-item .auction-title a[href]")
            auction_urls.extend([link.get_attribute("href") for link in auction_links])
            logger.info(f"Added {len(auction_links)} URLs (Total: {len(auction_urls)})")


        except TimeoutException:
            logger.info("No auctions found on page.")
            break
        except Exception as e:
            logger.error(f"Error scraping auction urls: {e}")
            break

        # check if it has scraped max_pages
        if max_pages and current_page >= max_pages:
            logger.info(f"Reached max pages ({max_pages}). Stopping.")
            break

        # else go to the next page
        try:
            next_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.arrow.next button"))
            )
            next_button.click()
            current_page += 1
            time.sleep(10)
        except TimeoutException:
            logger.warning("No more pages (or pagination button not clickable).")
            break
        except NoSuchElementException:
            logger.error("'Next' button not found.")
            break
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            break


    return auction_urls        
    