import json
import os
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get username and password from environment variables
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# Get directory where script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration file path, can be set via environment variable or defaults to 'config.json'
config_file_path = os.path.join(script_dir, 'config.json')

# Argument parser setup
parser = argparse.ArgumentParser(description="Freedom Blocking Script")
parser.add_argument('--reconfigure', action='store_true', help="Reconfigure blocklists, devices, and duration.")
parser.add_argument('--adjust-time', type=int, help="Adjust the duration of the block (in minutes) while keeping the other settings.")
args = parser.parse_args()

# Set up the Chrome WebDriver with headless option using webdriver-manager
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (no UI)
options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration, recommended for headless mode
options.add_argument("--window-size=1920x1080")  # Set window size to avoid element visibility issues
options.add_argument("--no-sandbox")  # Required if running as root user (not generally recommended)
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems in Docker
options.add_argument("--log-level=3")  # Suppress console output (3 = FATAL)

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
print(service.path)
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(10)

# Utility Functions
def save_configuration(config):
    """Save configuration to a JSON file."""
    with open(config_file_path, 'w') as config_file:
        json.dump(config, config_file)
    print(f"Configuration saved to {config_file_path}")

def load_configuration():
    """Load configuration from a JSON file."""
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
    print(f"Loaded configuration from {config_file_path}:")
    print(json.dumps(config, indent=4))
    return config

def login_to_freedom(driver):
    """Perform login on the Freedom website."""
    print("Opening website...")
    driver.get("https://freedom.to/")
    
    print("Clicking Log In...")
    driver.find_element(By.LINK_TEXT, "Log In").click()
    
    print("Entering email...")
    driver.find_element(By.ID, "session_email").clear()
    driver.find_element(By.ID, "session_email").send_keys(username)
    
    print("Entering password...")
    driver.find_element(By.ID, "session_password").clear()
    driver.find_element(By.ID, "session_password").send_keys(password)
    
    print("Submitting login form...")
    driver.find_element(By.ID, "login-form").submit()
    
    # Add a test to confirm successful login by checking the blocklist div
    try:
        # Wait for the blocklist div to appear as a sign of successful login
        blocklist_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'blocklist-checklist'))
        )
        print("Login successful.")
        return True
    except Exception as e:
        print(f"Login failed: {e}")

        # Optionally, check for an error message on the login page
        try:
            error_message = driver.find_element(By.CLASS_NAME, "error-message-class").text  # Replace with actual class or ID if applicable
            print(f"Error message displayed: {error_message}")
        except:
            print("No specific error message found.")
        
        return False

def gather_selection(driver, config, selection_type, container):
    """Gather and select items such as blocklists or devices."""
    print(f"Gathering {selection_type}...")
    labels = container.find_elements(By.TAG_NAME, 'label')
    names = [label.text for label in labels]

    if not names:
        print(f"No {selection_type} found.")
        driver.quit()
        exit(1)

    print(f"Available {selection_type}:")
    for i, name in enumerate(names):
        print(f"{i + 1}: {name}")
    
    while True:
        selected_indices = input(f"Enter the numbers of the {selection_type} to select (comma-separated): ")
        selected_indices = [index.strip() for index in selected_indices.split(",") if index.strip().isdigit()]
        if selected_indices:
            selected_indices = [int(index) - 1 for index in selected_indices]
            config[selection_type] = [names[i] for i in selected_indices]
            break
        else:
            print(f"Please select at least one {selection_type}.")

    for index in selected_indices:
        labels[index].click()

def set_duration(driver, total_minutes):
    """Set the duration for the blocking session."""
    if total_minutes <= 0:
        print("Duration must be a positive number of minutes.")
        driver.quit()
        exit(1)

    hours = total_minutes // 60
    minutes = total_minutes % 60

    print(f"Setting session duration: {hours} hours and {minutes} minutes.")

    hours_input = driver.find_element(By.ID, "duration-hours")
    minutes_input = driver.find_element(By.ID, "duration-minutes")
    
    hours_input.clear()
    hours_input.send_keys(str(hours))
    
    minutes_input.clear()
    minutes_input.send_keys(str(minutes))
        

def run_configuration_setup(driver, config):
    """Run the configuration setup process."""
    
    # Blocklist selection
    blocklist_div = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'blocklist-checklist'))
    )
    gather_selection(driver, config, 'blocklists', blocklist_div)
    
    # Device selection (assuming it's the next sibling of blocklist-checklist)
    try:
        print("Locating device checklist...")
        device_div = blocklist_div.find_element(By.XPATH, "following-sibling::div[@class='checklist']")
        gather_selection(driver, config, 'devices', device_div)
    except Exception as e:
        print(f"An error occurred while locating devices: {e}")
        driver.quit()
        exit(1)
    
    # Set and save duration
    if args.adjust_time:
        total_minutes = args.adjust_time
    else:
        while True:
            try:
                total_minutes = int(input("Enter the total number of minutes to block: "))
                if total_minutes > 0:
                    break
                else:
                    print("Please enter a positive number of minutes.")
            except ValueError:
                print("Please enter a valid number.")

    config['duration'] = total_minutes

    save_configuration(config)

    # Ask if the user wants to start the session now
    start_now = input("Configuration complete. Would you like to start the session now? (yes/no): ").strip().lower()
    if start_now == "yes":
        print("Starting the session...")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        print("Session has been successfully started.")
        driver.quit()
        exit(0)
    else:
        print("Configuration saved. You can start the session later using the saved configuration.")
        driver.quit()
        exit(0)

# Main Execution Logic

if os.path.exists(config_file_path):
    try:
        config = load_configuration()
    except json.JSONDecodeError as e:
        print(f"Error loading configuration file: {e}")
        config = {}
else:
    config = {}
    print(f"No configuration file found at {config_file_path}. Starting with an empty configuration.")

try:
    if login_to_freedom(driver):
        print("Proceeding with selecting blocklists and devices...")

        # Check for existing configuration
        if os.path.exists(config_file_path) and not args.reconfigure and not args.adjust_time:

            print(f"Using configuration from {config_file_path}:")
            print(json.dumps(config, indent=4))

            # Select blocklists
            blocklist_div = driver.find_element(By.CLASS_NAME, 'blocklist-checklist')
            for label in blocklist_div.find_elements(By.TAG_NAME, 'label'):
                if label.text in config['blocklists']:
                    label.click()

            # Select devices
            try:
                print("Locating device checklist for final execution...")
                device_div = blocklist_div.find_element(By.XPATH, "following-sibling::div[@class='checklist']")
                for label in device_div.find_elements(By.TAG_NAME, "label"):
                    if label.text in config['devices']:
                        label.click()
            except Exception as e:
                print(f"An error occurred during device selection: {e}")
                driver.quit()
                exit(1)

            # Set the duration
            set_duration(driver, config['duration'])

            # Submit the form if not already started
            print("Submitting the session setup form...")
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            print("Session has been successfully started.")
        
        else:
            run_configuration_setup(driver, config)
    else:
        print("Terminating script due to failed login.")
        driver.quit()
        exit(1)

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
