import json
import os
import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import logging
from pathlib import Path

def setup_logging(log_path=None):
    """Set up logging configuration."""
    if log_path is None:
        log_path = os.path.expanduser("~/freedom_script.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def initialize_webdriver(settings):
    """Initialize WebDriver based on configuration."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    if settings.get('browser_logging', False):
        options.add_argument("--enable-logging")
    else:
        options.add_argument("--log-level=3")  # Suppress console output
    
    driver_type = settings.get('driver_type', 'local')
    
    try:
        if driver_type == 'remote':
            # Use remote WebDriver (Selenium Grid)
            remote_url = settings.get('remote_url', 'http://localhost:4444/wd/hub')
            logger.info(f"Connecting to remote WebDriver at {remote_url}")
            driver = webdriver.Remote(
                command_executor=remote_url,
                options=options
            )
        else:
            # Use local ChromeDriver
            logger.info("Using local ChromeDriver")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except ImportError:
                logger.warning("webdriver_manager not installed, using system ChromeDriver")
                service = Service()
                
            driver = webdriver.Chrome(service=service, options=options)
            
        logger.info("WebDriver initialized successfully")
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise

def load_settings(settings_file=None):
    """Load settings from JSON file or create default if not exists."""
    default_settings = {
        "driver_type": "local",  # 'local' or 'remote'
        "remote_url": "http://localhost:4444/wd/hub",
        "browser_logging": False,
        "log_path": "~/freedom_script.log",
        "config_path": "~/freedom_config.json"
    }
    
    if settings_file is None:
        settings_file = os.path.expanduser("~/.freedom_settings.json")
    
    settings_path = Path(settings_file)
    
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            # Update with any missing default settings
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
    else:
        settings = default_settings
        # Save default settings
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        logger.info(f"Created default settings file at {settings_path}")
    
    # Expand any ~ in paths
    for key in ['log_path', 'config_path']:
        if key in settings:
            settings[key] = os.path.expanduser(settings[key])
            
    return settings

class FreedomSession:
    """Class to manage Freedom sessions."""
    
    def __init__(self, settings=None):
        """Initialize with settings."""
        if settings is None:
            settings = load_settings()
        self.settings = settings
        self.driver = None
        self.config_file_path = self.settings.get('config_path', os.path.expanduser("~/freedom_config.json"))
        self.config = self.load_configuration()
    
    def load_configuration(self):
        """Load configuration from a JSON file."""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as config_file:
                    config = json.load(config_file)
                logger.info(f"Loaded configuration from {self.config_file_path}")
                return config
            else:
                logger.info(f"No configuration file found at {self.config_file_path}. Starting with an empty configuration.")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error loading configuration file: {e}")
            return {}
    
    def save_configuration(self, config):
        """Save configuration to a JSON file."""
        with open(self.config_file_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logger.info(f"Configuration saved to {self.config_file_path}")
        
    def login(self, username, password):
        """Perform login on the Freedom website."""
        if self.driver is None:
            self.driver = initialize_webdriver(self.settings)
            
        logger.info("Opening website...")
        self.driver.get("https://freedom.to/")
        
        logger.info("Clicking Log In...")
        self.driver.find_element(By.LINK_TEXT, "Log In").click()
        
        logger.info("Entering credentials...")
        self.driver.find_element(By.ID, "session_email").clear()
        self.driver.find_element(By.ID, "session_email").send_keys(username)
        
        self.driver.find_element(By.ID, "session_password").clear()
        self.driver.find_element(By.ID, "session_password").send_keys(password)
        
        logger.info("Submitting login form...")
        self.driver.find_element(By.ID, "login-form").submit()
        
        # Confirm successful login
        try:
            blocklist_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'blocklist-checklist'))
            )
            logger.info("Login successful.")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def gather_selection(self, selection_type, container):
        """Gather and select items such as blocklists or devices."""
        logger.info(f"Gathering {selection_type}...")
        
        # Find all checkbox rows in the container
        checkbox_rows = container.find_elements(By.CLASS_NAME, "checkbox-row")
        logger.info(f"Found {len(checkbox_rows)} {selection_type} elements")
        
        # Extract labels and their text
        labels = []
        names = []
        
        for i, row in enumerate(checkbox_rows):
            try:
                label = row.find_element(By.TAG_NAME, "label")
                labels.append(label)
                
                # Get the text using JavaScript
                script = "return arguments[0].textContent.trim();"
                text = self.driver.execute_script(script, label)
                
                if text:
                    names.append(text)
                else:
                    # Fallback name with index
                    names.append(f"{selection_type.capitalize()} {i+1}")
                    
                logger.debug(f"{selection_type.capitalize()} {i+1}: '{text}'")
                
            except Exception as e:
                logger.error(f"Error processing {selection_type} {i+1}: {e}")
                names.append(f"{selection_type.capitalize()} {i+1}")
                labels.append(None)

        if not names:
            logger.error(f"No {selection_type} found.")
            return False, []

        print(f"Available {selection_type}:")
        for i, name in enumerate(names):
            print(f"{i + 1}: {name}")
        
        while True:
            selected_indices = input(f"Enter the numbers of the {selection_type} to select (comma-separated): ")
            selected_indices = [index.strip() for index in selected_indices.split(",") if index.strip().isdigit()]
            if selected_indices:
                selected_indices = [int(index) - 1 for index in selected_indices]
                # Filter out invalid indices
                valid_indices = [i for i in selected_indices if 0 <= i < len(names)]
                if len(valid_indices) != len(selected_indices):
                    logger.warning("Some selected indices were out of range and will be ignored")
                    selected_indices = valid_indices
                
                selected_names = [names[i] for i in selected_indices]
                self.config[selection_type] = selected_names
                logger.info(f"Selected {selection_type}: {', '.join(selected_names)}")
                break
            else:
                print(f"Please select at least one {selection_type}.")

        # Click the selected labels
        for index in selected_indices:
            try:
                if labels[index]:
                    # Find the checkbox input within the label and click it
                    checkbox = labels[index].find_element(By.TAG_NAME, "input")
                    if not checkbox.is_selected():
                        checkbox.click()
                        logger.info(f"Clicked on {selection_type}: {names[index]}")
                    else:
                        logger.info(f"{names[index]} was already selected")
            except Exception as e:
                logger.error(f"Error clicking on {names[index]}: {e}")
                
        return True, selected_names
    
    def set_duration(self, total_minutes):
        """Set the duration for the blocking session."""
        if total_minutes <= 0:
            logger.error("Duration must be a positive number of minutes.")
            return False

        hours = total_minutes // 60
        minutes = total_minutes % 60

        logger.info(f"Setting session duration: {hours} hours and {minutes} minutes.")

        hours_input = self.driver.find_element(By.ID, "duration-hours")
        minutes_input = self.driver.find_element(By.ID, "duration-minutes")
        
        hours_input.clear()
        hours_input.send_keys(str(hours))
        
        minutes_input.clear()
        minutes_input.send_keys(str(minutes))
        return True
    
    def configure(self):
        """Run the configuration setup process."""
        try:
            # Blocklist selection
            blocklist_div = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'blocklist-checklist'))
            )
            blocklist_success, _ = self.gather_selection('blocklists', blocklist_div)
            if not blocklist_success:
                return False
            
            # Device selection
            try:
                logger.info("Locating device checklist...")
                device_div = blocklist_div.find_element(By.XPATH, "following-sibling::div[@class='checklist']")
                device_success, _ = self.gather_selection('devices', device_div)
                if not device_success:
                    return False
            except Exception as e:
                logger.error(f"An error occurred while locating devices: {e}")
                return False
            
            # Set duration
            while True:
                try:
                    total_minutes = int(input("Enter the total number of minutes to block: "))
                    if total_minutes > 0:
                        break
                    else:
                        print("Please enter a positive number of minutes.")
                except ValueError:
                    print("Please enter a valid number.")

            self.config['duration'] = total_minutes
            self.save_configuration(self.config)

            # Ask if the user wants to start the session now
            start_now = input("Configuration complete. Would you like to start the session now? (yes/no): ").strip().lower()
            if start_now == "yes":
                logger.info("Starting the session...")
                self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
                logger.info("Session has been successfully started.")
                return True
            else:
                logger.info("Configuration saved. You can start the session later using the saved configuration.")
                return True
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return False
    
    def start_session(self):
        """Start a session with existing configuration."""
        try:
            if not self.config:
                logger.error("No configuration found. Please run --reconfigure first.")
                return False
                
            # Select blocklists
            blocklist_div = self.driver.find_element(By.CLASS_NAME, 'blocklist-checklist')
            for label in blocklist_div.find_elements(By.TAG_NAME, 'label'):
                script = "return arguments[0].textContent.trim();"
                text = self.driver.execute_script(script, label)
                if text in self.config['blocklists']:
                    checkbox = label.find_element(By.TAG_NAME, "input")
                    if not checkbox.is_selected():
                        checkbox.click()
                        logger.info(f"Selected blocklist: {text}")

            # Select devices
            try:
                logger.info("Locating device checklist...")
                device_div = blocklist_div.find_element(By.XPATH, "following-sibling::div[@class='checklist']")
                for label in device_div.find_elements(By.TAG_NAME, "label"):
                    script = "return arguments[0].textContent.trim();"
                    text = self.driver.execute_script(script, label)
                    if text in self.config['devices']:
                        checkbox = label.find_element(By.TAG_NAME, "input")
                        if not checkbox.is_selected():
                            checkbox.click()
                            logger.info(f"Selected device: {text}")
            except Exception as e:
                logger.error(f"An error occurred during device selection: {e}")
                return False

            # Set the duration
            if not self.set_duration(self.config['duration']):
                return False

            # Submit the form
            logger.info("Submitting the session setup form...")
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            logger.info("Session has been successfully started.")
            return True
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return False
    
    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Freedom Blocking Script")
    parser.add_argument('--reconfigure', action='store_true', help="Reconfigure blocklists, devices, and duration.")
    parser.add_argument('--adjust-time', type=int, help="Adjust the duration of the block (in minutes) while keeping the other settings.")
    parser.add_argument('--settings', type=str, help="Path to settings file. Creates default if not exists.")
    args = parser.parse_args()
    
    # Load settings first
    settings = load_settings(args.settings)
    
    # Setup logging
    global logger
    logger = setup_logging(settings.get('log_path'))
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials
    username = os.getenv('FREEDOM_USERNAME')
    password = os.getenv('FREEDOM_PASSWORD')
    
    if not username or not password:
        logger.error("Freedom credentials not found. Please set FREEDOM_USERNAME and FREEDOM_PASSWORD in .env file.")
        return 1
    
    # Initialize Freedom session
    freedom = FreedomSession(settings)
    
    try:
        # Login to Freedom
        if not freedom.login(username, password):
            logger.error("Login failed. Please check your credentials.")
            return 1
        
        # Handle adjust time
        if args.adjust_time:
            freedom.config['duration'] = args.adjust_time
            freedom.save_configuration(freedom.config)
            logger.info(f"Duration adjusted to {args.adjust_time} minutes")
        
        # Run the requested operation
        if args.reconfigure:
            logger.info("Running configuration setup...")
            if not freedom.configure():
                logger.error("Configuration setup failed.")
                return 1
        else:
            logger.info("Starting session with saved configuration...")
            if not freedom.start_session():
                logger.error("Failed to start session.")
                return 1
        
        return 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        freedom.close()


if __name__ == "__main__":
    sys.exit(main())