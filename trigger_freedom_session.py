import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from the .env file
load_dotenv()

# Get username and password from environment variables
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# Set up the Chrome WebDriver with headless option using webdriver-manager
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (no UI)
options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration, recommended for headless mode
options.add_argument("--window-size=1920x1080")  # Set window size to avoid element visibility issues
options.add_argument("--no-sandbox")  # Required if running as root user (not generally recommended)
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems in Docker

# Correctly instantiate the WebDriver using the Service class
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.implicitly_wait(30)

try:
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

    print("Interacting with page elements...")
    driver.find_element(By.XPATH, "//div[@id='content']/div/div/div/div/div[2]/div[2]/div[3]/div/div[5]/label/span/input").click()
    driver.find_element(By.XPATH, "//div[@id='content']/div/div/div/div/div[2]/div[2]/div[3]/div[2]/div[2]/label/span/input").click()
    driver.find_element(By.XPATH, "//div[@id='content']/div/div/div/div/div[2]/div[2]/div[3]/div[2]/div[3]/label/span/input").click()
    driver.find_element(By.XPATH, "//div[@id='content']/div/div/div/div/div[2]/div[2]/div[3]/div[2]/div[4]/label/span/input").click()
    driver.find_element(By.XPATH, "//div[@id='content']/div/div/div/div/div[2]/div[2]/div[3]/div[2]/div[5]/label/span/input").click()
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

except NoSuchElementException as e:
    print(f"Element not found: {e}")
    driver.get_screenshot_as_file("error_screenshot.png")
except ElementNotInteractableException as e:
    print(f"Element not interactable: {e}")
    driver.get_screenshot_as_file("error_screenshot.png")
except NoAlertPresentException as e:
    print(f"No alert present: {e}")
    driver.get_screenshot_as_file("error_screenshot.png")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    driver.get_screenshot_as_file("error_screenshot.png")
finally:
    # Close the browser window
    driver.quit()
