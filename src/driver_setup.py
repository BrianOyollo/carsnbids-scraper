from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from fake_useragent import UserAgent
import time


from logger import setup_json_logger
logger = setup_json_logger()
ua = UserAgent()


def setup_driver():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={ua}")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
        )
    return driver


def close_promo_bar(driver, timeout=10):
    try:
        # Wait for the close button to be present AND clickable
        close_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".promo-bar.new-seller .rb.close.dismiss"))
        )
        close_button.click()
        logger.info("Promo bar closed successfully.")
    except TimeoutException:
        logger.warning("Promo bar close button not found or not clickable within timeout.")
    except Exception as e:
        logger.error(f"Error closing promo bar: {e}")


def driver_teardown(driver):
    logger.info("Closing webdriver")
    driver.quit()