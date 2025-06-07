from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
from datetime import datetime
import os


from driver_setup import close_promo_bar


def wait_for_pagination(driver, timeout:int=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".paginator"))
        )
        print("✅ Pagination loaded (auctions likely loaded).")
    except TimeoutException:
        print("⚠️ Pagination not found. Proceeding anyway...")


def extract_auction_urls(driver, max_pages:int=None, timeout:int=60*5):
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
        print(f"Scraping page {current_page}...")

        try:
            # wait for auctions to load
            WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".auction-item")
            ))

            # extract urls from  current page
            auction_links = driver.find_elements(By.CSS_SELECTOR, ".auction-item .auction-title a[href]")
            auction_urls.extend([link.get_attribute("href") for link in auction_links])
            print(f"✅ Added {len(auction_links)} URLs (Total: {len(auction_urls)})")


        except TimeoutException:
            print("❌ No auctions found on page.")
            break
        except Exception as e:
            print("❌ Error scraping auction urls.")
            print(e)
            break

        # check if it has scraped max_pages
        if max_pages and current_page >= max_pages:
            print(f"Reached max pages ({max_pages}). Stopping.")
            break

        # else go to the next page
        try:
            next_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.arrow.next button"))
            )
            next_button.click()
            current_page += 1
            time.sleep(5)
        except TimeoutException:
            print("⚠️ No more pages (or pagination button not clickable).")
            break
        except NoSuchElementException:
            print("⚠️ 'Next' button not found.")
            break
        except Exception as e:
            print(f"❌ Error navigating to next page: {e}")
            break


    return auction_urls        



def save_auction_urls_locally(auction_urls, filename="auction_urls.txt"):
    """
    Saves auction URLs to a local file, skipping duplicates.
    
    Args:
        auction_urls (list): List of URLs to save.
        filename (str): File to store URLs (one per line).
    """
    try:
        # Read existing URLs (if file exists)
        try:
            with open(filename, 'r') as f:
                existing_urls = set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            pass

        # Append only new URLs
        new_urls =[url for url in auction_urls if url not in existing_urls]
        
        if new_urls:
            with open(filename, 'a') as f:  # 'a' mode = append without overwriting
                for url in new_urls:
                    f.write(url + '\n')
            print(f"✅ Added {len(new_urls)} new URLs to {filename}")
        else:
            print("⏩ No new URLs to add.")

    except Exception as e:
        print(f"❌ Error saving URLs: {e}")


def save_auction_urls_to_csv(auction_urls, filename="auction_urls.csv"):
    """
    Saves auction URLs to CSV with scraping date.
    Only adds new URLs that don't already exist in the file.
    
    Args:
        auction_urls (list): List of URLs to save
        filename (str): CSV file path (default: auction_urls.csv)
    """
    try:
        # Get current date in ISO format (YYYY-MM-DD)
        scrape_date = datetime.now().date().isoformat()
        
        # Read existing URLs if file exists
        existing_urls = set()
        if os.path.exists(filename):
            with open(filename, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header if exists
                existing_urls = {row[0] for row in reader if row}  # Extract URLs from first column
        
        # Prepare new entries
        new_entries = []
        for url in auction_urls:
            if url not in existing_urls:
                new_entries.append([url, scrape_date])
        
        # Write to CSV (append mode)
        file_exists = os.path.exists(filename)
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(["url", "scrape_date"])
            
            # Add new entries
            writer.writerows(new_entries)
        
        print(f"✅ Added {len(new_entries)} new URLs to {filename}")
        
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
    
    