from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium import webdriver
from bs4 import BeautifulSoup

# Set up ChromeOptions
chrome_options = Options()

# Set up ChromeDriverManager to automatically download and manage the ChromeDriver executable
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Example: Navigate to a webpage
driver.get("https://pro.imdb.com/title/tt3564472")

# Find the login button and click on it
login_button = driver.find_element(By.XPATH, '//span[@data-action="log_event" and contains(text(), "Log In")]')
login_button.click()

# Find the login button and click on it
login_button = driver.find_element(By.XPATH, '//div[@class="a-section a-spacing-none a-spacing-top-none a-padding-none login_url"]/a')
login_button.click()

# Find the email input field and fill in your email
email_input = driver.find_element(By.ID, 'ap_email')
email_input.send_keys('b.a.vanhouten@tilburguniversity.edu')

# Find the password input field and fill in your password
password_input = driver.find_element(By.ID, 'ap_password')
password_input.send_keys('Djojo123')

# Find the submit button and click on it
submit_button = driver.find_element(By.XPATH, '//button[contains(@class, "button-text signin-button-text")]')
submit_button.click()

# Wait for the login page to load
time.sleep(2)  # Adjust the wait time as needed