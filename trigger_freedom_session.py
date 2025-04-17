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
import time # For cookie handling delays
from datetime import datetime # For screenshot timestamp

# --- Determine the script's directory & Default Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LOG_FILENAME = "freedom_script.log"
DEFAULT_CONFIG_FILENAME = ".freedom_config.json" # Hidden file convention
DEFAULT_SETTINGS_FILENAME = ".freedom_settings.json" # Hidden file convention
LOGS_DIR_NAME = "logs"
# ---

# Initialize a basic logger FIRST for use during setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
basic_logger = logging.getLogger("freedom_basic")
basic_logger.info(f"Script directory determined as: {SCRIPT_DIR}")

# --- Path Resolution Helper ---
def resolve_path(path_str, base_dir, ensure_parent_exists=False):
    """Expands '~', resolves path relative to base_dir if not absolute,
       and optionally ensures parent directory exists."""
    if not path_str:
        return None
    path = Path(os.path.expanduser(str(path_str)))
    if not path.is_absolute():
        path = base_dir / path
    resolved_path = path.resolve()

    if ensure_parent_exists:
        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            basic_logger.error(f"Could not create directory {resolved_path.parent}: {e}")
            # Allow function to return path, calling code should handle failure if needed

    return resolved_path

# --- Logging Setup ---
def setup_logging(log_path_setting=None):
    """Set up logging configuration, defaulting to script directory's logs sub-directory."""
    if log_path_setting:
        log_path = resolve_path(log_path_setting, SCRIPT_DIR, ensure_parent_exists=True)
    else:
        # Default log file path is now in logs sub-directory
        log_path = resolve_path(LOGS_DIR_NAME + "/" + DEFAULT_LOG_FILENAME, SCRIPT_DIR, ensure_parent_exists=True)

    if not log_path:
        print("ERROR: Could not determine or create log path. Logging disabled.", file=sys.stderr)
        logging.basicConfig(level=logging.CRITICAL, handlers=[logging.NullHandler()])
        return logging.getLogger(__name__) # Return a non-functional logger

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Added %(name)s
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout) # Keep console output
        ],
        force=True # Overwrite basicConfig potentially called implicitly
    )
    logger = logging.getLogger(__name__) # Get logger for this module
    logger.info(f"Logging configured. Log file: {log_path}")
    return logger

# --- Settings Loading ---
def load_settings(settings_arg=None):
    """Load settings, defaulting paths relative to script directory."""
    # Defaults use simple filenames, resolved later relative to SCRIPT_DIR
    default_settings = {
        "driver_type": "local",
        "remote_url": "http://localhost:4444/wd/hub",
        "chrome_binary_path": "",
        "browser_logging": False,
        "log_path": LOGS_DIR_NAME + "/" + DEFAULT_LOG_FILENAME, # Default to logs subdir
        "config_path": DEFAULT_CONFIG_FILENAME
    }

    # Determine the target settings file path
    if settings_arg:
        # Resolve argument relative to CWD if not absolute
        settings_path = resolve_path(settings_arg, Path.cwd())
        basic_logger.info(f"Using settings file specified via argument: {settings_path}")
    else:
        # Default settings file path relative to the script directory
        settings_path = SCRIPT_DIR / DEFAULT_SETTINGS_FILENAME
        basic_logger.info(f"No settings file specified, using default: {settings_path}")

    settings = {}
    if settings_path and settings_path.exists(): # Check if path resolved and exists
        basic_logger.info(f"Loading settings from: {settings_path}")
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            basic_logger.info("Settings loaded successfully.")
        except json.JSONDecodeError as e:
            basic_logger.error(f"Error reading JSON from {settings_path}: {e}. Using default settings.")
            settings = default_settings # Fallback to defaults
        except OSError as read_e:
             basic_logger.error(f"Could not read settings file {settings_path}: {read_e}. Using default settings.")
             settings = default_settings # Fallback

    else:
        basic_logger.info(f"Settings file not found or path invalid. Using default settings.")
        settings = default_settings
        # Save default settings to the determined default path if possible
        default_save_path = SCRIPT_DIR / DEFAULT_SETTINGS_FILENAME
        try:
            default_save_path.parent.mkdir(parents=True, exist_ok=True) # Ensure script dir exists
            with open(default_save_path, 'w') as f:
                json.dump(settings, f, indent=4)
            basic_logger.info(f"Created default settings file at {default_save_path}")
        except OSError as e:
            basic_logger.error(f"Could not create default settings file at {default_save_path}: {e}")

    # --- Ensure all paths in settings are absolute relative to SCRIPT_DIR ---
    final_settings = default_settings.copy() # Start with defaults
    final_settings.update(settings)          # Override with loaded settings

    paths_to_resolve = ['log_path', 'config_path', 'chrome_binary_path']
    for key in paths_to_resolve:
        path_value = final_settings.get(key)
        if path_value:
            # Ensure log/config parent dirs exist when resolving
            needs_parent = key in ['log_path', 'config_path']
            resolved = resolve_path(path_value, SCRIPT_DIR, ensure_parent_exists=needs_parent)
            if resolved:
                basic_logger.info(f"Resolved path for '{key}': '{path_value}' -> '{resolved}'")
                final_settings[key] = str(resolved) # Store as string
            else:
                 basic_logger.warning(f"Could not resolve path for key '{key}' with value '{path_value}'.")
                 final_settings[key] = str(path_value) # Keep original
        else:
            final_settings[key] = "" # Keep empty

    return final_settings


# --- WebDriver Initialization (Original Logic) ---
def initialize_webdriver(settings):
    """Initialize WebDriver based on configuration."""
    logger = logging.getLogger(__name__) # Get configured logger
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    chrome_binary = settings.get('chrome_binary_path')
    if chrome_binary:
        logger.info(f"Using custom Chrome binary path: {chrome_binary}")
        options.binary_location = str(chrome_binary) # Use resolved path

    if settings.get('browser_logging', False):
        options.add_argument("--enable-logging")
    else:
        options.add_argument("--log-level=3")

    driver_type = settings.get('driver_type', 'local')

    try:
        if driver_type == 'remote':
            remote_url = settings.get('remote_url', 'http://localhost:4444/wd/hub')
            logger.info(f"Connecting to remote WebDriver at {remote_url}")
            driver = webdriver.Remote(command_executor=remote_url, options=options)
        else:
            logger.info("Using local ChromeDriver")
            try:
                driver = webdriver.Chrome(options=options)
                logger.info("Used Selenium's built-in driver manager")
            except Exception as local_error:
                logger.warning(f"Selenium's built-in manager failed: {local_error}")
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Used webdriver-manager fallback")
                except Exception as wdm_error:
                    logger.warning(f"webdriver-manager failed: {wdm_error}")
                    try:
                        service = Service()
                        driver = webdriver.Chrome(service=service, options=options)
                        logger.info("Used system ChromeDriver")
                    except Exception as path_error:
                        logger.error(f"All local ChromeDriver attempts failed. Final error: {path_error}")
                        raise

        logger.info("WebDriver initialized successfully")
        driver.implicitly_wait(10) # Keep implicit wait from original
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise


# --- Freedom Session Class ---
class FreedomSession:
    """Class to manage Freedom sessions."""

    def __init__(self, settings=None):
        """Initialize with settings."""
        # Use basic_logger until full logger is confirmed available
        current_logger = logging.getLogger(__name__) if logging.getLogger(__name__).hasHandlers() else basic_logger

        if settings is None:
            current_logger.warning("FreedomSession initialized without pre-loaded settings. Loading defaults.")
            settings = load_settings()
        self.settings = settings
        self.driver = None

        # Get the resolved, absolute path for the config file from settings
        self.config_file_path = self.settings.get('config_path')
        
        # Use resolved, absolute path from settings
        self.config = self.load_configuration() # Load config using the path

    def load_configuration(self):
        """Load configuration from the absolute JSON file path."""
        logger = logging.getLogger(__name__)
        if not self.config_file_path:
             logger.error("Configuration file path is not set in settings.")
             return {}

        config_path_obj = Path(self.config_file_path)
        try:
            if config_path_obj.exists():
                with open(config_path_obj, 'r') as config_file:
                    config = json.load(config_file)
                logger.info(f"Loaded configuration from {config_path_obj}")
                return config
            else:
                logger.info(f"No configuration file found at {config_path_obj}. Starting with an empty configuration.")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error reading JSON from configuration file {config_path_obj}: {e}")
            return {}
        except OSError as e:
             logger.error(f"Error accessing configuration file {config_path_obj}: {e}")
             return {}

    def save_configuration(self, config):
        """Save configuration to the absolute JSON file path."""
        logger = logging.getLogger(__name__)
        if not self.config_file_path:
             logger.error("Cannot save configuration, file path is not set.")
             return

        config_path_obj = Path(self.config_file_path)
        try:
            # Parent directory should exist due to resolve_path in load_settings
            with open(config_path_obj, 'w') as config_file:
                json.dump(config, config_file, indent=4)
            logger.info(f"Configuration saved to {config_path_obj}")
        except OSError as e:
             logger.error(f"Could not save configuration file to {config_path_obj}: {e}")
        except TypeError as e:
            logger.error(f"Error serializing configuration to JSON: {e}")


    # --- Original Selenium Interaction Methods ---
    def login(self, username, password):
        """Perform login on the Freedom website using original logic."""
        logger = logging.getLogger(__name__) # Get configured logger
        # Driver initialization now happens *before* login is called in main()
        if not self.driver:
             logger.error("Login called but WebDriver is not initialized.")
             # Attempt to initialize as fallback - might be better to fail in main
             self.driver = initialize_webdriver(self.settings)
             if not self.driver: return False

        logger.info("Opening website...")
        self.driver.get("https://freedom.to/")

        try: # Wrap core login steps
            logger.info("Clicking Log In...")
            # Allow potential NoSuchElementException etc. if page structure changes
            self.driver.find_element(By.LINK_TEXT, "Log In").click()
            time.sleep(1) # Small pause after click, might help login form appear

            logger.info("Entering credentials...")
            # Add waits for fields to be present before interacting
            email_field = WebDriverWait(self.driver, 10).until(
                 EC.presence_of_element_located((By.ID, "session_email"))
            )
            email_field.clear()
            email_field.send_keys(username)

            password_field = WebDriverWait(self.driver, 10).until(
                 EC.presence_of_element_located((By.ID, "session_password"))
            )
            password_field.clear()
            password_field.send_keys(password)

            logger.info("Submitting login form...")
            self.driver.find_element(By.ID, "login-form").submit() # Original submit action

            # Confirm successful login using the original check
            logger.info("Waiting for dashboard check element...")
            WebDriverWait(self.driver, 10).until(
                 EC.presence_of_element_located((By.CLASS_NAME, 'blocklist-checklist'))
            )
            logger.info("Login successful (original check passed).")

            return True
            

        except Exception as e:
            # Broader exception handling for timeouts, element not found etc.
            logger.error(f"Login process failed: {e}", exc_info=True) # Log traceback
            # --- Screenshot on error ---
            try:
                logs_dir = resolve_path(LOGS_DIR_NAME, SCRIPT_DIR, ensure_parent_exists=True)
                if logs_dir and self.driver:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = logs_dir / f"login_error_{timestamp}.png"
                    self.driver.save_screenshot(str(screenshot_path))
                    logger.info(f"Screenshot saved to {screenshot_path}")
                elif not self.driver:
                     logger.warning("WebDriver not available for screenshot.")
            except Exception as screen_err:
                logger.error(f"Failed to save screenshot: {screen_err}")
            # --- End Screenshot ---
            return False

    def gather_selection(self, selection_type, container):
        """Gather and select items such as blocklists or devices."""
        logger = logging.getLogger(__name__)
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
        logger = logging.getLogger(__name__)
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
        logger = logging.getLogger(__name__)
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
        logger = logging.getLogger(__name__)
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
        logger = logging.getLogger(__name__)
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


# --- Main Execution Block ---
def main():
    """Main function to parse arguments and run the script."""
    pre_logger = logging.getLogger("freedom_pre") # Basic logger for early messages

    parser = argparse.ArgumentParser(
        description="Automate Freedom.to session start or configuration.",
        epilog=f"Default files are stored relative to script directory: {SCRIPT_DIR}"
    )
    parser.add_argument('--reconfigure', action='store_true', help="Reconfigure blocklists, devices, and duration.")
    parser.add_argument('--adjust-time', type=int, help="Adjust the duration of the block (in minutes) while keeping the other settings.")
    parser.add_argument('--settings', type=str, help="Path to settings file. Creates default if not exists.")
    args = parser.parse_args()

    # --- Setup ---
    settings = load_settings(args.settings)
    logger = setup_logging(settings.get('log_path')) # Assign configured logger

    if load_dotenv(): logger.info(".env file loaded.")
    else: logger.info("No .env file found or not loaded.")

    logger.info("Retrieving credentials...")
    username = os.getenv('FREEDOM_USERNAME')
    password = os.getenv('FREEDOM_PASSWORD')
    if not username or not password:
        logger.critical("Credentials not found in environment/.env file.")
        return 1
    logger.info("Credentials retrieved successfully.") # Added success log

    # --- Initialize Session ---
    freedom = None
    exit_code = 1

    try:
        logger.info("Initializing Freedom session object...")
        freedom = FreedomSession(settings) # Initializes config etc.

        logger.info("Initializing WebDriver...")
        freedom.driver = initialize_webdriver(freedom.settings) # Init WebDriver
        if not freedom.driver:
            logger.critical("Failed to initialize WebDriver.")
            return 1

        # --- Perform Form Login Directly ---
        logger.info("Attempting form login...")
        login_successful = freedom.login(username, password) # Call original login
        # --- End Form Login ---

        if not login_successful:
            logger.error("Login failed. Cannot proceed.")
            # Screenshot happens inside login() on failure
            return 1 # Exit if login failed

        # --- Perform Action (Reconfigure or Start Session) ---
        if args.reconfigure:
            logger.info("Starting reconfiguration process...")
            # Use freedom.configure() which returns True/False
            if freedom.configure():
                 exit_code = 0
            else:
                 logger.error("Reconfiguration process failed.")
                 exit_code = 1 # Ensure error code if configure fails
        else:
            # Default action: Start session (potentially adjusting time)
            if args.adjust_time:
                 if args.adjust_time > 0:
                      logger.info(f"Adjusting session duration to {args.adjust_time} minutes.")
                      freedom.config['duration'] = args.adjust_time
                      # Optional: Save adjusted time back to config file?
                      # freedom.save_configuration(freedom.config)
                 else:
                      logger.error("Invalid --adjust-time value. Must be positive.")
                      return 1 # Exit

            logger.info("Attempting to start session...")
            # Use freedom.start_session() which returns True/False
            if freedom.start_session():
                 exit_code = 0
            else:
                 logger.error("Failed to start session.")
                 exit_code = 1 # Ensure error code if start fails

    except Exception as e:
        # Log critical errors happening outside specific method calls
        logger.critical(f"An unexpected critical error occurred in main: {e}", exc_info=True)
        exit_code = 1
        # Final screenshot attempt
        if freedom and freedom.driver:
             try:
                  logs_dir = resolve_path(LOGS_DIR_NAME, SCRIPT_DIR, ensure_parent_exists=True)
                  if logs_dir:
                       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                       final_error_path = logs_dir / f"final_error_{timestamp}.png"
                       freedom.driver.save_screenshot(str(final_error_path))
                       logger.info(f"Final error screenshot saved to {final_error_path}")
             except Exception as screen_err: logger.error(f"Failed to save final error screenshot: {screen_err}")
    finally:
        logger.info("Initiating cleanup...")
        if freedom: freedom.close()
        else: logger.info("FreedomSession object not created/valid, no browser to close.")
        logger.info(f"Script finished with exit code {exit_code}.")

    return exit_code



if __name__ == "__main__":
    sys.exit(main())