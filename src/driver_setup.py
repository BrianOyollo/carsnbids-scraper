from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time



def setup_driver():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/87.0.4280.88 Safari/537.36")

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
        print("Promo bar closed successfully.")
    except TimeoutException:
        print("Promo bar close button not found or not clickable within timeout.")
    except Exception as e:
        print(f"Error closing promo bar: {e}")


def driver_teardown(driver):
    driver.quit()