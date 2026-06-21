import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

def initialize_browser():
    """Initialize and return a Chrome browser instance with proper error handling"""
    try:
        # Set Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1200,800")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Install and initialize ChromeDriver
        print("Initializing Chrome browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        return None

def manual_element_check(driver, by, value, description):
    """Manual verification helper function with improved error handling"""
    if driver is None:
        print("Browser not initialized!")
        return None
        
    try:
        print(f"\nPlease verify: Looking for {description} (using {by}='{value}')")
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((by, value)))
        print("Element found successfully!")
        return element
    except Exception as e:
        print(f"Failed to find element: {e}")
        print(f"Current URL: {driver.current_url}")
        return None

def get_live_trains(station_name):
    """Scrape live train data from Indian Railways with robust error handling"""
    driver = initialize_browser()
    if driver is None:
        print("Cannot proceed without browser instance")
        return pd.DataFrame()

    try:
        # Step 1: Open NTES website
        print("\nSTEP 1: Opening NTES website...")
        driver.get("https://enquiry.indianrail.gov.in/mntes/")
        time.sleep(3)
        
        # Step 2: Navigate to Live Station page
        print("\nSTEP 2: Navigating to Live Station page")
        live_station_btn = manual_element_check(
            driver, 
            By.XPATH, 
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'live station')]",
            "Live Station button"
        )
        
        if live_station_btn:
            live_station_btn.click()
        else:
            print("Trying direct URL access...")
            driver.get("https://enquiry.indianrail.gov.in/mntes/liveStation")
        
        time.sleep(3)

        # Step 3: Enter station name
        print("\nSTEP 3: Entering station name")
        station_input = manual_element_check(driver, By.ID, "jFromStationInput", "Station input")
        if not station_input:
            raise Exception("Station input field not found")
            
        station_input.clear()
        station_input.send_keys(station_name)
        time.sleep(1)

        # Step 4: Setting time window
        print("\nSTEP 4: Setting time window")
        time_radio = manual_element_check(driver, By.XPATH, "//input[@name='nHr' and @value='2']", "2-hour radio")
        if time_radio:
            try:
                # Scroll to the element before clicking
                driver.execute_script("arguments[0].scrollIntoView(true);", time_radio)
                time.sleep(1)  # Allow time for scrolling

                # Use JavaScript to click the element
                driver.execute_script("arguments[0].click();", time_radio)
                print("Time window set successfully.")
            except Exception as e:
                print(f"Error clicking time window: {e}")
        else:
            raise Exception("2-hour radio button not found")

        # Step 5: Submit form
        print("\nSTEP 5: Submitting form")
        submit_btn = manual_element_check(driver, By.XPATH, "//input[@value='Get Trains']", "Submit button")
        if not submit_btn:
            raise Exception("Submit button not found")
            
        submit_btn.click()
        time.sleep(3)

        # Step 6: Extract data
        print("\nSTEP 6: Extracting train data")
        try:
            # Wait for the results table to appear
            table = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'w3-table')]"))
            )
            print("Results table found successfully!")
        except Exception as e:
            driver.save_screenshot("debug_screenshot.png")
            print("Screenshot saved as debug_screenshot.png")
            raise Exception(f"Results table not found: {e}")

        trains = []
        rows = table.find_elements(By.XPATH, ".//tbody/tr[position()>1]")
        print(f"Found {len(rows)} trains")

        current_time = datetime.now().time()  # Get the current time

        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 4:
                    train_text = cols[0].text.split("|")
                    departure_time_str = cols[2].text.strip().split("\n")[0]  # Clean the time string

                    # Debug the raw departure time
                    print(f"Raw departure time: '{departure_time_str}'")

                    # Parse the departure time
                    try:
                        departure_time = datetime.strptime(departure_time_str, "%H:%M").time()
                    except ValueError as e:
                        print(f"Skipping train due to invalid departure time: '{departure_time_str}' (Error: {e})")
                        continue

                    # Filter out trains that have already departed
                    if departure_time < current_time:
                        print(f"Skipping train {train_text[0].strip()} as it has already departed.")
                        continue

                    trains.append({
                        "Train No": train_text[0].strip(),
                        "Train Name": train_text[1].strip() if len(train_text) > 1 else "",
                        "Arrival": cols[1].text.strip(),
                        "Departure": departure_time_str,
                        "Platform": cols[3].text.strip() if len(cols) > 3 else "N/A"
                    })
            except Exception as e:
                print(f"Error processing row: {e}")

        return pd.DataFrame(trains)

    except Exception as e:
        print(f"\nError during scraping: {e}")
        return pd.DataFrame()
    
    finally:
        if driver:
            print("\nScript complete. Closing browser.")
            driver.quit()

if __name__ == "__main__":
    print("Indian Railways Live Train Scraper")
    print("---------------------------------")
    station = input("Enter station name/code (e.g. 'Delhi' or 'NDLS'): ").strip()
    
    if not station:
        print("Error: Station name cannot be empty")
    else:
        df = get_live_trains(station)
        if not df.empty:
            print("\nSuccessfully extracted train data:")
            print(df.to_string(index=False))
            
            csv_file = f"live_trains_{station}.csv"
            df.to_csv(csv_file, index=False)
            print(f"\nData saved to {csv_file}")
        else:
            print("\nFailed to extract train data. Check browser for issues.")