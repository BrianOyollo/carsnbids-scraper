from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
from datetime import datetime
import os
import json

from driver_setup import close_promo_bar
from logger import setup_json_logger

logger = setup_json_logger()



def scrape_auction_data(driver, url:str, timeout:int = 60) -> dict:
    """
    Scrapes detailed information from a single auction page.
    
    Args:
        url: URL of the auction page
        driver: Selenium WebDriver instance
        timeout: Maximum wait time for elements
        
    Returns:
        Dictionary containing all scraped auction details
    """
    driver.get(url)
    close_promo_bar(driver)

    auction_data = {
        'auction_url': url,
        'auction_title': None,
        'auction_subtitle': None,
        'auction_stats':{
            'reserve_status': None,
            'auction_status': None,
            'highest_bid_value': None,
            'buyer_username': None,
            'seller_username': None,
            'bid_count': None,
            'view_count': None,
            'watcher_count': None,
            'auction_date': None,
            'bids':[]
            
        },
        'auction_quick_facts': {
            'Make': None,
            'Model': None,
            'Mileage': None,
            'VIN': None,
            'Title Status': None,
            'Location': None,
            'Seller': None,
            'Engine': None,
            'Drivetrain': None,
            'Transmission': None,
            'Body Style': None,
            'Exterior Color': None,
            'Interior Color': None,
            'Seller Type': None
        },
        'dougs_take': None,
        'auction_highlights': {
            'description': None,
            'bullet_points': []
        },
        'known_flaws': [],
        'service_history': {
            'description': None,
            'items': []
        },
        'included_items': [],
        'ownership_history': None,
        'seller_notes': [],
        'auction_videos': []
    }

    try:
        # Wait for main content to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".auction-title"))
        )
        # Extract title
        title_element = driver.find_element(By.CSS_SELECTOR, ".auction-title h1")
        auction_data['auction_title'] = title_element.text.strip()
        
        # Extract subtitle
        subtitle_element = driver.find_element(By.CSS_SELECTOR, ".d-md-flex.justify-content-between.flex-wrap h2")
        auction_data['auction_subtitle'] = subtitle_element.text.strip()
        
        # Extract reserve status
        reserve_element = driver.find_element(By.CSS_SELECTOR, "#auction-jump h3 span")
        auction_data['auction_stats']['reserve_status'] = 'Reserve' if 'Reserve' in reserve_element.text else 'No Reserve'
        
        # Extract auction status and final bid
        status_container = driver.find_element(By.CSS_SELECTOR, ".current-bid.ended")
        
        if 'cancelled' in status_container.get_attribute("class"):
            auction_data['auction_stats']['auction_status'] = 'Canceled'
        else:
            status_header = status_container.find_element(By.CSS_SELECTOR, "h4").text
            if 'Sold to' in status_header:
                auction_data['auction_stats']['auction_status'] = 'Sold'
                auction_data['auction_stats']['buyer_username'] = status_container.find_element(By.CSS_SELECTOR, ".username .user").text
            elif 'Reserve not met' in status_header:
                auction_data['auction_stats']['auction_status'] = 'Reserve Not Met'
            
            # Extract final bid amount
            bid_value = status_container.find_element(By.CSS_SELECTOR, ".bid-value").text
            auction_data['auction_stats']['highest_bid_value'] = bid_value.replace('$', '').strip()

        # Extract statistics from the stats ul
        stats_section = driver.find_element(By.CSS_SELECTOR, "ul.stats")
        
        # Seller information
        seller_element = stats_section.find_element(By.CSS_SELECTOR, "li.seller .user")
        auction_data['auction_stats']['seller_username'] = seller_element.text.strip()
        
        # Other stats
        stats_items = stats_section.find_elements(By.CSS_SELECTOR, "li:not(.seller)")
        for item in stats_items:
            label = item.find_element(By.CSS_SELECTOR, ".th").text.strip()
            value = item.find_element(By.CSS_SELECTOR, ".td").text.strip()
            
            if label == "Ended":
                auction_data['auction_stats']['auction_date'] = value
            elif label == "Bids":
                auction_data['auction_stats']['bid_count'] = int(value.replace(',', ''))
            elif label == "Views":
                auction_data['auction_stats']['view_count'] = int(value.replace(',', ''))
            elif label == "Watching":
                auction_data['auction_stats']['watcher_count'] = int(value.replace(',', ''))

        # Process auction quick facts
        # Wait for quick facts section to load
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".quick-facts"))
            )
            # Extract quick facts
            quick_facts = driver.find_element(By.CSS_SELECTOR, ".quick-facts")
            
            # Process first definition list
            first_dl = quick_facts.find_elements(By.CSS_SELECTOR, "dl")[0]
            items = first_dl.find_elements(By.CSS_SELECTOR, "dt")
            for item in items:
                label = item.text.strip().lower().replace(" ", "_")
                dd = item.find_element(By.XPATH, "./following-sibling::dd[1]")
                
                if label == "make":
                    auction_data['auction_quick_facts']['Make'] = dd.find_element(By.CSS_SELECTOR, "a").text.strip()
                elif label == "model":
                    auction_data['auction_quick_facts']['Model'] = dd.find_element(By.CSS_SELECTOR, "a").text.strip()
                elif label == "mileage":
                    auction_data['auction_quick_facts']['Mileage'] = dd.text.strip()
                elif label == "vin":
                    auction_data['auction_quick_facts']['VIN'] = dd.text.strip()
                elif label == "title_status":
                    auction_data['auction_quick_facts']['Title Status'] = dd.text.strip()
                elif label == "location":
                    auction_data['auction_quick_facts']['Location'] = dd.text.strip()
                elif label == "seller":
                    auction_data['auction_quick_facts']['Seller'] = dd.find_element(By.CSS_SELECTOR, ".user").text.strip()

            # Process second definition list
            second_dl = quick_facts.find_elements(By.CSS_SELECTOR, "dl")[1]
            items = second_dl.find_elements(By.CSS_SELECTOR, "dt")
            for item in items:
                label = item.text.strip().lower().replace(" ", "_")
                dd = item.find_element(By.XPATH, "./following-sibling::dd[1]")
                
                if label == "engine":
                    auction_data['auction_quick_facts']['Engine'] = dd.text.strip()
                elif label == "drivetrain":
                    auction_data['auction_quick_facts']['Drivetrain'] = dd.text.strip()
                elif label == "transmission":
                    auction_data['auction_quick_facts']['Transmission'] = dd.text.strip()
                elif label == "body_style":
                    auction_data['auction_quick_facts']['Body Style'] = dd.text.strip()
                elif label == "exterior_color":
                    auction_data['auction_quick_facts']['Exterior Color'] = dd.text.strip()
                elif label == "interior_color":
                    auction_data['auction_quick_facts']['Interior Color'] = dd.text.strip()
                elif label == "seller_type":
                    auction_data['auction_quick_facts']['Seller Type'] = dd.text.strip()

        except NoSuchElementException:
            logger.warning('Auction quick facts not found')
        except Exception as e:
            logger.Warning(e)

        # Extract Doug's Take
        try:
            dougs_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.dougs-take")
            auction_data['dougs_take'] = dougs_section.find_element(
                By.CSS_SELECTOR, ".detail-body p").text.strip()
        except NoSuchElementException:
            print("Doug's take not found")
        except Exception as e:
            logger.Warning(e)

        # Extract Highlights
        try:
            highlights_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-highlights")
            highlights_body = highlights_section.find_element(By.CSS_SELECTOR, ".detail-body")
            
            # Get description paragraph
            try:
                auction_data['auction_highlights']['description'] = highlights_body.find_element(
                    By.CSS_SELECTOR, "p").text.strip()
            except NoSuchElementException:
                logger.warning('Auction hightlights not found')
            except Exception as e:
                logger.warning(f'Error: {e}')
                
            
            # Get bullet points
            bullet_points = highlights_body.find_elements(By.CSS_SELECTOR, "ul li")
            auction_data['auction_highlights']['bullet_points'] = [
                point.text.strip() for point in bullet_points
                if point.text.strip()
            ]

        except NoSuchElementException:
            logger.warning('Auction highlights not found')
        except Exception as e:
            logger.Warning(e)

        # Extract Known Flaws
        try:
            flaws_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-known_flaws")
            flaws_items = flaws_section.find_elements(By.CSS_SELECTOR, ".detail-body li")
            auction_data['known_flaws'] = [item.text.strip() for item in flaws_items]
        except NoSuchElementException:
            logger.warning('Known flaws not found')
        except Exception as e:
            logger.Warning(e)


        # Extract Service History
        try:
            service_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-recent_service_history")
            auction_data['service_history']['description'] = service_section.find_element(
                By.CSS_SELECTOR, ".detail-body p").text.strip()
            service_items = service_section.find_elements(By.CSS_SELECTOR, ".detail-body li")
            auction_data['service_history']['items'] = [item.text.strip() for item in service_items]
        except NoSuchElementException:
            logger.warning('Service History not found')
        except Exception as e:
            logger.Warning(e)

         # Extract Included Items
        try:
            items_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-other_items")
            included_items = items_section.find_elements(By.CSS_SELECTOR, ".detail-body li")
            auction_data['included_items'] = [item.text.strip() for item in included_items]
        except NoSuchElementException:
            logger.warning("Included items not found")
        except Exception as e:
            logger.Warning(e)

        # Extract Ownership History
        try:
            history_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-ownership_history")
            auction_data['ownership_history'] = history_section.find_element(
                By.CSS_SELECTOR, ".detail-body p").text.strip()
        except NoSuchElementException:
            logger.warning('Ownership history not found')
        except Exception as e:
            logger.Warning(e)

        # Extract Seller Notes
        try:
            notes_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-seller_notes")
            notes_items = notes_section.find_elements(By.CSS_SELECTOR, ".detail-body li")
            auction_data['seller_notes'] = [item.text.strip() for item in notes_items]
        except NoSuchElementException:
            logger.warning('Seller notes not found')
        except Exception as e:
            logger.Warning(e)
        
        # Extract Video Links
        try:
            videos_section = driver.find_element(By.CSS_SELECTOR, ".detail-section.detail-videos")
            video_previews = videos_section.find_elements(By.CSS_SELECTOR, ".video-embed img.video-preview")
            auction_data['auction_videos'] = [
                img.get_attribute("src").split('/vi/')[1].split('/')[0] 
                for img in video_previews 
                if 'ytimg.com' in img.get_attribute("src")
            ]
        except NoSuchElementException:
            logger.warning('Auction videos not found')
        except Exception as e:
            logger.Warning(e)

        # bids
        try:
            # Wait for main content and click Bid History button
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".comments"))
            )
            
            # Click Bid History filter button
            try:
                bid_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-filter='4'][data-ga='bids']"))
                )
                driver.execute_script("arguments[0].click();", bid_button)
                time.sleep(2)  # Allow bids to load
            except Exception as e:
                logger.warning(f"Couldn't click bid history button: {str(e)}")
                return auction_data
            except Exception as e:
                logger.Warning(e)

            # Extract bid history
            bids = []
            bid_items = driver.find_elements(By.CSS_SELECTOR, ".thread li.bid")
            for bid in bid_items:
                try:
                    bid = bid.find_element(By.CSS_SELECTOR, ".bid-value").text.replace('$', '').replace(',', '')
                    bids.append(bid)
                    # bid_data = {
                    #     # 'bidder': bid.find_element(By.CSS_SELECTOR, ".user").text.strip(),
                        
                    #     # 'time': bid.find_element(By.CSS_SELECTOR, ".time").get_attribute("data-full"),
                    #     # 'is_verified': bool(bid.find_elements(By.CSS_SELECTOR, ".verified")),
                    #     # 'reputation': bid.find_element(By.CSS_SELECTOR, ".rep").text.replace('Reputation Icon', '').strip()
                    # }
                   
                except Exception as e:
                    logger.warning(f"Error parsing bid: {str(e)}")
                    continue
            auction_data['auction_stats']['bids']=bids

        except Exception as e:
            logger.warning(f"Error scraping bid history: {str(e)}")

    except TimeoutException:
        logger.warning(f"Timeout while scraping {url}")
    except Exception as e:
        logger.warning(f"Error scraping {url}: {str(e)}")
    
    return auction_data
