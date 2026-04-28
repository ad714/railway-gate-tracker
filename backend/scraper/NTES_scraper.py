import os
import logging
import asyncio
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ntes_scraper.log'),
        logging.StreamHandler()
    ]
)

# Selenium Functions
def initialize_browser():
    """Initialize and return a Chrome browser instance with proper error handling"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1200,800")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-webgl")
        options.add_argument("--log-level=3")
        print("Initializing Chrome browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        return None

def check_for_captcha(driver):
    """Check if a CAPTCHA is present on the page and pause for manual resolution."""
    try:
        captcha_indicators = [
            (By.XPATH, "//*[contains(text(), 'I am not a robot')]"),
            (By.XPATH, "//*[contains(text(), 'Verify you are not a bot')]"),
            (By.ID, "captcha"),
            (By.CLASS_NAME, "captcha")
        ]

        for by, value in captcha_indicators:
            try:
                captcha_element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((by, value))
                )
                if captcha_element:
                    print("\n⚠️ CAPTCHA DETECTED ⚠️")
                    print("Please solve the CAPTCHA in the browser window.")
                    print("The script will wait for 30 seconds before checking again.")
                    logging.warning("CAPTCHA detected! Pausing for manual intervention...")

                    time.sleep(30)
                    try:
                        driver.find_element(by, value)
                        print("CAPTCHA not resolved within 30 seconds. Please solve it and restart the script.")
                        logging.error("CAPTCHA not resolved within 30 seconds.")
                        return False
                    except:
                        print("CAPTCHA resolved. Resuming...")
                        logging.info("CAPTCHA resolved! Resuming scraping.")
                        return True
            except:
                continue
        return False
    except Exception as e:
        logging.error(f"Error checking for CAPTCHA: {e}")
        return False

def wait_for_element(driver, by, value, description, timeout=5, retries=2):
    """Wait for an element to be present and return it, with retries."""
    attempt = 0
    while attempt < retries:
        try:
            print(f"\nWaiting for {description} (using {by}='{value}') [Attempt {attempt + 1}/{retries}]")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            print(f"{description} found successfully!")
            return element
        except Exception as e:
            print(f"Failed to find {description}: {e}")
            print(f"Current URL: {driver.current_url}")
            driver.save_screenshot(f"debug_screenshot_{description.lower().replace(' ', '_')}_attempt_{attempt + 1}.png")
            print(f"Screenshot saved as debug_screenshot_{description.lower().replace(' ', '_')}_attempt_{attempt + 1}.png")
            attempt += 1
            if attempt < retries:
                print("Retrying after a short delay...")
                time.sleep(2)  # Short delay before retrying
    return None

def extract_time(text):
    """Extract and clean time from a string using regex."""
    try:
        match = re.search(r'\b\d{2}:\d{2}\b', text.strip())
        if match:
            return match.group(0)
        else:
            return None
    except Exception as e:
        logging.error(f"Error extracting time: {e}")
        return None

def extract_train_identifier(text):
    """Extract the train number and route from the train info string (e.g., '12201 | KCVL GARIBRATH (LTT-TVCN)')."""
    try:
        # Split on '|' to separate train number and name/route
        parts = text.split("|")
        if len(parts) < 2:
            logging.warning(f"Could not split train info: {text}")
            return None, None

        # Extract train number (before the '|')
        train_no = parts[0].strip()
        match = re.search(r'\b\d{5}\b', train_no)
        if not match:
            logging.warning(f"Could not extract 5-digit train number from: {train_no}")
            return None, None
        train_number = match.group(0)

        # Extract route from the name/route part (after the '|')
        name_route = parts[1].strip()
        route_match = re.search(r'\(([^)]+)\)', name_route)
        if not route_match:
            logging.warning(f"Could not extract route from: {name_route}")
            return train_number, None
        route = route_match.group(1)  # e.g., "LTT-TVCN"

        return train_number, route
    except Exception as e:
        logging.error(f"Error extracting train identifier: {e}")
        return None, None

def calculate_delay(departure_time_str, expected_time_str):
    """Calculate the delay between departure and expected time."""
    try:
        departure_time_clean = extract_time(departure_time_str)
        expected_time_clean = extract_time(expected_time_str)
        if not (departure_time_clean and expected_time_clean):
            return "0 minutes"

        departure_time = datetime.strptime(departure_time_clean, "%H:%M")
        expected_time = datetime.strptime(expected_time_clean, "%H:%M")
        delta = expected_time - departure_time
        minutes = delta.total_seconds() // 60
        return f"{int(minutes)} minutes"
    except Exception as e:
        logging.error(f"Error calculating delay: {e}")
        return "0 minutes"

def calculate_arriving_in(arrival_time_str, current_time):
    """Calculate the time remaining until arrival."""
    if arrival_time_str == "Unknown":
        return "Unknown"
    try:
        arrival_time_clean = extract_time(arrival_time_str)
        if not arrival_time_clean:
            return "Unknown"

        now = datetime.combine(datetime.today(), current_time)
        arrival_time = datetime.strptime(arrival_time_clean, "%H:%M")
        arrival_datetime = datetime.combine(datetime.today(), arrival_time.time())
        if arrival_datetime < now:
            arrival_datetime += timedelta(days=1)
        delta = arrival_datetime - now
        minutes = delta.total_seconds() // 60
        return f"{int(minutes)} minutes"
    except Exception as e:
        logging.error(f"Error calculating arrivingIn: {e}")
        return "Unknown"

def determine_direction_status(arrival_time_str, departure_time_str, current_time):
    """Determine if the train is Approaching, At Station, or Departing."""
    if arrival_time_str == "Unknown" or departure_time_str == "Unknown":
        return "Unknown"
    try:
        arrival_time_clean = extract_time(arrival_time_str)
        departure_time_clean = extract_time(departure_time_str)
        if not (arrival_time_clean and departure_time_clean):
            return "Unknown"

        now = datetime.combine(datetime.today(), current_time)
        arrival_time = datetime.strptime(arrival_time_clean, "%H:%M")
        departure_time = datetime.strptime(departure_time_clean, "%H:%M")
        arrival_datetime = datetime.combine(datetime.today(), arrival_time.time())
        departure_datetime = datetime.combine(datetime.today(), departure_time.time())

        if arrival_datetime < now:
            arrival_datetime += timedelta(days=1)
            departure_datetime += timedelta(days=1)

        if now < arrival_datetime:
            return "Approaching"
        elif arrival_datetime <= now <= departure_datetime:
            return "At Station"
        else:
            return "Departing"
    except Exception as e:
        logging.error(f"Error determining direction status: {e}")
        return "Unknown"

def is_within_one_hour(time_str, current_time):
    """Check if the given time is within the next 1 hour from the current time."""
    if time_str == "Unknown":
        return False
    try:
        time_clean = extract_time(time_str)
        if not time_clean:
            return False

        now = datetime.combine(datetime.today(), current_time)
        event_time = datetime.strptime(time_clean, "%H:%M")
        event_datetime = datetime.combine(datetime.today(), event_time.time())
        if event_datetime < now:
            event_datetime += timedelta(days=1)

        delta = event_datetime - now
        minutes = delta.total_seconds() // 60
        return 0 <= minutes <= 60  # Within the next 60 minutes
    except Exception as e:
        logging.error(f"Error checking if time is within one hour: {e}")
        return False

def estimate_gate_passage_time(train, j1_code, j2_code):
    """Estimate the time a train passes the gate based on departure times from J1 and J2."""
    try:
        j1_departure = extract_time(train["schedule"]["departure"]) if train["metadata"]["queriedStation"] == j1_code else None
        j2_departure = extract_time(train["schedule"]["departure"]) if train["metadata"]["queriedStation"] == j2_code else None

        if not (j1_departure and j2_departure):
            return "Unknown"

        j1_time = datetime.strptime(j1_departure, "%H:%M")
        j2_time = datetime.strptime(j2_departure, "%H:%M")

        # Determine direction
        if train["direction"]["from"] == j1_code and train["direction"]["to"] == j2_code:
            # J1 to J2 direction
            travel_time = (j2_time - j1_time).total_seconds() / 60  # in minutes
            # Assume the gate is roughly halfway (simplified)
            gate_pass_time = j1_time + timedelta(minutes=travel_time * 0.5)
        else:
            # J2 to J1 direction
            travel_time = (j1_time - j2_time).total_seconds() / 60  # in minutes
            gate_pass_time = j2_time + timedelta(minutes=travel_time * 0.5)

        return gate_pass_time.strftime("%H:%M")
    except Exception as e:
        logging.error(f"Error estimating gate passage time for train {train['trainNumber']}: {e}")
        return "Unknown"

async def get_live_trains(driver, station_name):
    """Scrape live train data for a single station from Indian Railways using an existing browser instance"""
    try:
        # Navigate to the NTES website if not already there
        if "mntes" not in driver.current_url:
            print("\nSTEP 1: Opening NTES website...")
            driver.get("https://enquiry.indianrail.gov.in/mntes/")
            wait_for_element(driver, By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'live station')]", "Live Station button")
            check_for_captcha(driver)

        # Navigate to Live Station page
        print("\nSTEP 2: Navigating to Live Station page")
        live_station_btn = wait_for_element(
            driver,
            By.XPATH,
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'live station')]",
            "Live Station button"
        )

        if live_station_btn:
            live_station_btn.click()
            time.sleep(2)  # Short delay to ensure the page loads
        else:
            print("Trying direct URL access...")
            driver.get("https://enquiry.indianrail.gov.in/mntes/liveStation")
            time.sleep(2)  # Short delay to ensure the page loads

        check_for_captcha(driver)  # Check for CAPTCHA after navigation

        # Wait for the station input field with retries
        station_input_field = wait_for_element(driver, By.ID, "jFromStationInput", "Station input field")
        if not station_input_field:
            raise Exception("Station input field not found after retries")

        # Enter station name
        print("\nSTEP 3: Entering station name")
        station_input = wait_for_element(driver, By.ID, "jFromStationInput", "Station input")
        if not station_input:
            raise Exception("Station input field not found")

        station_input.clear()
        station_input.send_keys(station_name)
        WebDriverWait(driver, 2).until(
            lambda d: station_input.get_attribute("value") == station_name
        )

        # Set time window to 2 hours (smallest available option)
        print("\nSTEP 4: Setting time window to 2 hours")
        time_radio = wait_for_element(driver, By.XPATH, "//input[@name='nHr' and @value='2']", "2-hour radio button")
        if not time_radio:
            raise Exception("2-hour radio button not found")

        driver.execute_script("arguments[0].scrollIntoView(true);", time_radio)
        driver.execute_script("arguments[0].click();", time_radio)
        WebDriverWait(driver, 2).until(
            EC.element_to_be_selected(time_radio)
        )

        # Submit form
        print("\nSTEP 5: Submitting form")
        submit_btn = wait_for_element(driver, By.XPATH, "//input[@value='Get Trains']", "Submit button")
        if not submit_btn:
            raise Exception("Submit button not found")

        submit_btn.click()
        wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Results table")
        check_for_captcha(driver)

        # Extract data
        print("\nSTEP 6: Extracting train data")
        table = wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Results table")
        if not table:
            raise Exception("Results table not found")

        trains = []
        rows = table.find_elements(By.XPATH, ".//tbody/tr[position()>1]")
        print(f"Found {len(rows)} trains")

        current_time = datetime.now().time()
        last_updated = datetime.now().isoformat() + "Z"

        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 5:  # Expect 5 columns: Sr., Train No./Name, Arrival, Departure, Platform
                    # Extract train number and route from the second column
                    train_text = cols[1].text
                    train_no, route = extract_train_identifier(train_text)
                    if not train_no or not route:
                        logging.warning(f"Skipping train due to missing train number or route: {train_text}")
                        continue

                    # Extract train name (between train number and route)
                    name_match = re.search(r'\|\s*(.*?)\s*\(', train_text)
                    train_name = name_match.group(1).strip() if name_match else ""

                    # Extract origin and destination from route
                    route_parts = route.split("-")
                    origin = route_parts[0] if route_parts else ""
                    destination = route_parts[1] if len(route_parts) > 1 else ""

                    # Extract arrival and departure times
                    arrival_text = cols[2].text.strip()
                    departure_text = cols[3].text.strip()

                    arrival_time_str = extract_time(arrival_text) or "Unknown"
                    departure_time_str = extract_time(departure_text) or "Unknown"

                    if departure_time_str.lower() in ["source", "destination"]:
                        logging.info(f"Skipping train {train_no} as it is at the source/destination: {departure_time_str}")
                        continue

                    if not departure_time_str or departure_time_str == "Unknown":
                        logging.warning(f"Skipping train {train_no} due to invalid departure time: {departure_time_str}")
                        continue

                    # Filter trains: only include those arriving or departing within the next 1 hour
                    within_one_hour = False
                    if arrival_time_str != "Unknown":
                        within_one_hour = is_within_one_hour(arrival_time_str, current_time)
                    if not within_one_hour:  # If arrival time is Unknown or not within 1 hour, check departure time
                        within_one_hour = is_within_one_hour(departure_time_str, current_time)

                    if not within_one_hour:
                        logging.info(f"Skipping train {train_no} as it is not within the next 1 hour: Arrival {arrival_time_str}, Departure {departure_time_str}")
                        continue

                    # Extract status and expected times
                    arrival_lines = arrival_text.split("\n")
                    departure_lines = departure_text.split("\n")
                    arrival_status = arrival_lines[1] if len(arrival_lines) > 1 else "Unknown"
                    departure_status = departure_lines[1] if len(departure_lines) > 1 else "Unknown"
                    expected_arrival = arrival_lines[2] if len(arrival_lines) > 2 else arrival_time_str
                    expected_departure = departure_lines[2] if len(departure_lines) > 2 else departure_time_str

                    delay = calculate_delay(departure_time_str, expected_departure)
                    if departure_status == "On Time":
                        delay = "0 minutes"

                    arriving_in = calculate_arriving_in(arrival_time_str, current_time)
                    direction_status = determine_direction_status(arrival_time_str, departure_time_str, current_time)

                    # Extract platform
                    platform_text = cols[4].text.strip()
                    platform_lines = platform_text.split("\n")
                    platform = platform_lines[0] if platform_lines else "Unknown"

                    train_data = {
                        "trainNumber": train_no,
                        "trainName": train_name,
                        "route": {
                            "origin": origin,
                            "destination": destination,
                            "fullRoute": route  # Store the full route (e.g., "LTT-TVCN") for matching
                        },
                        "schedule": {
                            "arrival": arrival_time_str,
                            "departure": departure_time_str,
                            "arrivalStatus": arrival_status,
                            "departureStatus": departure_status,
                            "delay": delay,
                            "arrivingIn": arriving_in
                        },
                        "platform": platform,
                        "direction": {
                            "from": "",
                            "to": "",
                            "status": direction_status
                        },
                        "metadata": {
                            "queriedStation": station_name,
                            "lastUpdated": last_updated
                        }
                    }
                    logging.info(f"Train {train_no} included: Route {route}, Arrival {arrival_time_str}, Departure {departure_time_str}")
                    trains.append(train_data)
            except Exception as e:
                logging.error(f"Error processing row: {e}")

        print(f"After filtering, {len(trains)} trains are within the next 1 hour.")
        return trains

    except Exception as e:
        print(f"\nError during scraping: {e}")
        return []

# async def get_train_running_status(driver, train_number):
#     """Scrape the live running status of a train from NTES."""
#     try:
#         # Navigate to the NTES website if not already there
#         if "mntes" not in driver.current_url:
#             print("\nSTEP 1: Opening NTES website for train running status...")
#             driver.get("https://enquiry.indianrail.gov.in/mntes/")
#             wait_for_element(driver, By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'train running status')]", "Train Running Status button")
#             check_for_captcha(driver)
#
#         # Navigate to Train Running Status page
#         print("\nSTEP 2: Navigating to Train Running Status page")
#         running_status_btn = wait_for_element(
#             driver,
#             By.XPATH,
#             "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'train running status')]",
#             "Train Running Status button"
#         )
#
#         if running_status_btn:
#             running_status_btn.click()
#             time.sleep(2)  # Short delay to ensure the page loads
#         else:
#             print("Trying direct URL access...")
#             driver.get("https://enquiry.indianrail.gov.in/mntes/trainRunningStatus")
#             time.sleep(2)
#
#         check_for_captcha(driver)
#
#         # Enter train number
#         print("\nSTEP 3: Entering train number")
#         train_input = wait_for_element(driver, By.ID, "trainNoInput", "Train number input")
#         if not train_input:
#             raise Exception("Train number input field not found")
#
#         train_input.clear()
#         train_input.send_keys(train_number)
#         WebDriverWait(driver, 2).until(
#             lambda d: train_input.get_attribute("value") == train_number
#         )
#
#         # Submit form
#         print("\nSTEP 4: Submitting form")
#         submit_btn = wait_for_element(driver, By.XPATH, "//input[@value='Get Status']", "Submit button")
#         if not submit_btn:
#             raise Exception("Submit button not found")
#
#         submit_btn.click()
#         wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Status table")
#         check_for_captcha(driver)
#
#         # Extract status data
#         print("\nSTEP 5: Extracting train running status")
#         table = wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Status table")
#         if not table:
#             raise Exception("Status table not found")
#
#         status_data = {
#             "lastStation": None,
#             "lastStationDeparture": "Unknown",
#             "nextStation": None,
#             "nextStationETA": "Unknown",
#             "status": "Unknown"
#         }
#
#         rows = table.find_elements(By.XPATH, ".//tbody/tr")
#         for row in rows:
#             try:
#                 cols = row.find_elements(By.TAG_NAME, "td")
#                 if len(cols) >= 5:
#                     station_code = cols[1].text.strip()
#                     if "(" in station_code and ")" in station_code:
#                         station_code = station_code[station_code.find("(")+1:station_code.find(")")]
#                     actual_arrival = cols[2].text.strip()
#                     actual_departure = cols[3].text.strip()
#                     eta = cols[4].text.strip()
#
#                     # Check if this is the last station the train departed from
#                     if actual_departure and actual_departure != "-" and actual_departure != "Not Departed":
#                         departure_time = extract_time(actual_departure)
#                         if departure_time:
#                             status_data["lastStation"] = station_code
#                             status_data["lastStationDeparture"] = departure_time
#                             # The next station will be the one after this in the table
#                             next_row = row.find_element(By.XPATH, "following-sibling::tr")
#                             if next_row:
#                                 next_cols = next_row.find_elements(By.TAG_NAME, "td")
#                                 if len(next_cols) >= 5:
#                                     next_station_code = next_cols[1].text.strip()
#                                     if "(" in next_station_code and ")" in next_station_code:
#                                         next_station_code = next_station_code[next_station_code.find("(")+1:next_station_code.find(")")]
#                                     next_eta = next_cols[4].text.strip()
#                                     eta_time = extract_time(next_eta)
#                                     status_data["nextStation"] = next_station_code
#                                     status_data["nextStationETA"] = eta_time if eta_time else "Unknown"
#                                     status_data["status"] = "Departed"
#                                     break
#             except Exception as e:
#                 logging.error(f"Error processing train status row: {e}")
#
#         logging.info(f"Train {train_number} status: {status_data}")
#         return status_data
#
#     except Exception as e:
#         logging.error(f"Error fetching train running status for {train_number}: {e}")
#         return {
#             "lastStation": None,
#             "lastStationDeparture": "Unknown",
#             "nextStation": None,
#             "nextStationETA": "Unknown",
#             "status": "Unknown"
#         }

async def determine_gate_status(trains, gate_data, driver, j1_code, j2_code):
    """Determine if the gate is closed or open based on train movements using departure times."""
    o1_code = gate_data["adjacent_stations"]["after"]["code"]  # Station after J1 (e.g., KPY)
    o2_code = gate_data["adjacent_stations"]["before"]["code"] # Station before J2 (e.g., MQO)
    n_code = gate_data["nearest_station"]["code"]              # Nearest station to gate (e.g., STKT)

    current_time = datetime.now()
    current_time_str = current_time.strftime("%H:%M")
    current_datetime = datetime.combine(datetime.today(), current_time.time())

    gate_status = "Open"
    affecting_train = None

    for train in trains:
        train_number = train["trainNumber"]
        direction_from = train["direction"]["from"]
        direction_to = train["direction"]["to"]

        # Use departure times from J1 and J2 to estimate train position
        j1_departure = extract_time(train["schedule"]["departure"]) if train["metadata"]["queriedStation"] == j1_code else None
        j2_departure = extract_time(train["schedule"]["departure"]) if train["metadata"]["queriedStation"] == j2_code else None

        if not (j1_departure and j2_departure):
            logging.warning(f"Cannot determine gate status for train {train_number}: Missing departure times")
            continue

        try:
            j1_departure_time = datetime.strptime(j1_departure, "%H:%M")
            j2_departure_time = datetime.strptime(j2_departure, "%H:%M")
            j1_departure_dt = datetime.combine(datetime.today(), j1_departure_time.time())
            j2_departure_dt = datetime.combine(datetime.today(), j2_departure_time.time())

            # Adjust for trains crossing midnight
            if j1_departure_dt > current_datetime:
                j1_departure_dt -= timedelta(days=1)
            if j2_departure_dt > current_datetime:
                j2_departure_dt -= timedelta(days=1)
            if j1_departure_dt > j2_departure_dt:
                j2_departure_dt += timedelta(days=1)

            # Determine if the train is affecting the gate
            if direction_from == j1_code and direction_to == j2_code:
                # Train is moving from J1 to J2
                if j1_departure_dt <= current_datetime <= j2_departure_dt:
                    # Train has departed J1 and has not yet reached J2
                    gate_status = "Closed"
                    affecting_train = train
                    logging.info(f"Gate closed: Train {train_number} is between J1 ({j1_departure}) and J2 ({j2_departure})")
                    break
                elif current_datetime < j1_departure_dt and (j1_departure_dt - current_datetime).total_seconds() / 60 <= 15:
                    # Train is approaching J1 within 15 minutes
                    gate_status = "Closed"
                    affecting_train = train
                    logging.info(f"Gate closed: Train {train_number} is approaching J1 at {j1_departure}")
                    break
            elif direction_from == j2_code and direction_to == j1_code:
                # Train is moving from J2 to J1
                if j2_departure_dt <= current_datetime <= j1_departure_dt:
                    # Train has departed J2 and has not yet reached J1
                    gate_status = "Closed"
                    affecting_train = train
                    logging.info(f"Gate closed: Train {train_number} is between J2 ({j2_departure}) and J1 ({j1_departure})")
                    break
                elif current_datetime < j2_departure_dt and (j2_departure_dt - current_datetime).total_seconds() / 60 <= 15:
                    # Train is approaching J2 within 15 minutes
                    gate_status = "Closed"
                    affecting_train = train
                    logging.info(f"Gate closed: Train {train_number} is approaching J2 at {j2_departure}")
                    break

        except Exception as e:
            logging.error(f"Error determining gate status for train {train_number}: {e}")
            continue

    return gate_status, affecting_train

async def fetch_live_train_data(station_data, mode="junction_individual"):
    """Fetch live train data by querying J1 and J2 using a single browser instance and determine gate status."""
    logging.info(f"Fetching live train data in mode: {mode}")
    driver = initialize_browser()
    if driver is None:
        print("Cannot proceed without browser instance")
        return [{"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"} for gate in station_data.get("gates", [])]

    try:
        results = []
        gates = station_data.get("gates", [])

        for gate in gates:
            j1 = gate.get("junctions", {}).get("before")
            j2 = gate.get("junctions", {}).get("after")
            route = gate.get("route", "")

            if not (j1 and j2 and route):
                logging.warning(f"Skipping gate {gate.get('gate_id')} due to missing junctions or route")
                results.append({"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"})
                continue

            j1_code = j1.get("code", j1.get("name", ""))
            j2_code = j2.get("code", j2.get("name", ""))

            # Note: All routes are bidirectional
            logging.info(f"Gate {gate.get('gate_id')} route '{route}' is bidirectional: includes {j1_code} to {j2_code} and {j2_code} to {j1_code}")

            # Query J1 (for trains stopping at J1)
            logging.info(f"Scraping live trains for J1: {j1_code}")
            j1_trains = await get_live_trains(driver, j1_code)
            logging.info(f"J1 ({j1_code}) trains: {[train['trainNumber'] for train in j1_trains]}")

            # Query J2 (for trains stopping at J2)
            logging.info(f"Scraping live trains for J2: {j2_code}")
            j2_trains = await get_live_trains(driver, j2_code)
            logging.info(f"J2 ({j2_code}) trains: {[train['trainNumber'] for train in j2_trains]}")

            # Match trains that appear in both J1 and J2 results (indicating they travel between the junctions)
            filtered_trains = []
            j1_train_dict = {train["route"]["fullRoute"]: train for train in j1_trains}
            j2_train_dict = {train["route"]["fullRoute"]: train for train in j2_trains}

            for route in j1_train_dict.keys():
                if route in j2_train_dict:
                    j1_train = j1_train_dict[route]
                    j2_train = j2_train_dict[route]
                    train_no = j1_train["trainNumber"]
                    # Determine direction based on departure times
                    j1_departure = extract_time(j1_train["schedule"]["departure"])
                    j2_departure = extract_time(j2_train["schedule"]["departure"])
                    if j1_departure and j2_departure:
                        j1_time = datetime.strptime(j1_departure, "%H:%M")
                        j2_time = datetime.strptime(j2_departure, "%H:%M")
                        if j1_time < j2_time:
                            # Train is going from J1 to J2
                            j1_train["direction"]["from"] = j1_code
                            j1_train["direction"]["to"] = j2_code
                            logging.info(f"Train {train_no} (Route {route}) travels from {j1_code} to {j2_code}: J1 Departure {j1_departure}, J2 Departure {j2_departure}")
                            filtered_trains.append(j1_train)
                        else:
                            # Train is going from J2 to J1
                            j2_train["direction"]["from"] = j2_code
                            j2_train["direction"]["to"] = j1_code
                            logging.info(f"Train {train_no} (Route {route}) travels from {j2_code} to {j1_code}: J1 Departure {j1_departure}, J2 Departure {j2_departure}")
                            filtered_trains.append(j2_train)
                    else:
                        logging.info(f"Train {train_no} (Route {route}) found in both J1 and J2 but cannot determine direction: J1 Departure {j1_departure}, J2 Departure {j2_departure}")

            # Deduplicate trains based on route
            unique_trains = {}
            for train in filtered_trains:
                route = train["route"]["fullRoute"]
                if route not in unique_trains:
                    unique_trains[route] = train
                else:
                    existing = unique_trains[route]
                    existing_departure = datetime.strptime(extract_time(existing["schedule"]["departure"]), "%H:%M").time()
                    new_departure = datetime.strptime(extract_time(train["schedule"]["departure"]), "%H:%M").time()
                    if new_departure > existing_departure:
                        unique_trains[route] = train

            # Sort trains by departure time
            live_trains = sorted(unique_trains.values(), key=lambda x: datetime.strptime(extract_time(x["schedule"]["departure"]), "%H:%M").time())

            # Determine gate status
            gate_status, affecting_train = await determine_gate_status(live_trains, gate, driver, j1_code, j2_code)
            logging.info(f"Gate {gate.get('gate_id')} status: {gate_status}")
            if affecting_train:
                logging.info(f"Affecting train: {affecting_train['trainNumber']} ({affecting_train['trainName']})")

            # Format the final output as requested
            print("\nFINAL RESULTS\n")
            print(f"GATE: {gate.get('gate_id')}, ({gate.get('position', {}).get('latitude', 'Unknown')}, {gate.get('position', {}).get('longitude', 'Unknown')})")
            
            # Nearest station
            nearest_station = gate.get("nearest_station", {})
            print(f"NEAREST STATION: {nearest_station.get('name', 'Unknown')} - {nearest_station.get('code', 'Unknown')}, ({nearest_station.get('position', {}).get('latitude', 'Unknown')}, {nearest_station.get('position', {}).get('longitude', 'Unknown')})")
            
            # Adjacent stations
            o1 = gate.get("adjacent_stations", {}).get("after", {})
            o2 = gate.get("adjacent_stations", {}).get("before", {})
            print(f"NEAREST STATION: {o1.get('name', 'Unknown')} - {o1.get('code', 'Unknown')}, ({o1.get('position', {}).get('latitude', 'Unknown')}, {o1.get('position', {}).get('longitude', 'Unknown')})")
            print(f"NEAREST STATION: {o2.get('name', 'Unknown')} - {o2.get('code', 'Unknown')}, ({o2.get('position', {}).get('latitude', 'Unknown')}, {o2.get('position', {}).get('longitude', 'Unknown')})")

            # Trains found, sorted by gate passage time
            print("TRAIN FOUND(in recency order):")
            if live_trains:
                # Estimate gate passage time for each train
                trains_with_passage = []
                for train in live_trains:
                    passage_time = estimate_gate_passage_time(train, j1_code, j2_code)
                    trains_with_passage.append((train, passage_time))

                # Sort by passage time
                trains_with_passage.sort(key=lambda x: datetime.strptime(x[1], "%H:%M") if x[1] != "Unknown" else datetime.max)

                # Print each train
                for train, passage_time in trains_with_passage:
                    route = f"{train['route']['origin']}-{train['route']['destination']}"
                    print(f"{train['trainNumber']}, {route}, {passage_time}")
                    print("." * 80)
            else:
                print("No trains found within the time window.")
                print("." * 80)

            print(f"\nGATE STATUS: {gate_status}")
            if affecting_train:
                print(f"AFFECTING TRAIN: {affecting_train['trainNumber']} ({affecting_train['trainName']})")

            # Also include the result in the return value for programmatic use
            results.append({
                "gate_id": gate.get("gate_id"),
                "live_trains": live_trains,
                "gate_status": gate_status,
                "affecting_train": affecting_train
            })

        return results

    except Exception as e:
        logging.error(f"Error in fetch_live_train_data: {e}")
        return [{"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"} for gate in station_data.get("gates", [])]

    finally:
        if driver:
            print("\nScript complete. Closing browser.")
            driver.quit()

# Example usage (you can uncomment and modify this to test the script)
# if __name__ == "__main__":
#     station_data = {
#         "gates": [
#             {
#                 "gate_id": 1,
#                 "position": {"latitude": 9.03449155, "longitude": 76.5951049},
#                 "route": "Kollam to Kayamkulam",
#                 "nearest_station": {
#                     "code": "STKT",
#                     "name": "Sasthankotta",
#                     "position": {"latitude": 9.0364612, "longitude": 76.6239423}
#                 },
#                 "adjacent_stations": {
#                     "after": {
#                         "code": "KPY",
#                         "name": "Karunagapalli",
#                         "position": {"latitude": 9.0597934, "longitude": 76.5355902}
#                     },
#                     "before": {
#                         "code": "MQO",
#                         "name": "Munroturuttu (halt)",
#                         "position": {"latitude": 8.9946666, "longitude": 76.61152129999999}
#                     }
#                 },
#                 "junctions": {
#                     "before": {
#                         "code": "QLN",
#                         "name": "Kollam Jn",
#                         "position": {"latitude": 8.8932118, "longitude": 76.6141396}
#                     },
#                     "after": {
#                         "code": "KYJ",
#                         "name": "Kayamkulam Jn",
#                         "position": {"latitude": 9.1748422, "longitude": 76.5013352}
#                     }
#                 }
#             }
#         ]
#     }
#     asyncio.run(fetch_live_train_data(station_data, mode="between_junctions"))