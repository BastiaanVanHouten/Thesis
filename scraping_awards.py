from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Set up ChromeOptions
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=C:/Users/Bas van Houten/AppData/Local/Google/Chrome/User Data/Profile 4")

# Set up ChromeDriverManager to automatically download and manage the ChromeDriver executable
driver = WebDriver(service=Service(ChromeDriverManager().install()), options=chrome_options)

# List of movie identifiers
movie_identifiers = ['tt3564472', 'tt1462764', 'tt15671028', 'tt14230388']

# Navigate to each movie page
for identifier in movie_identifiers:
    movie_url = f"https://pro.imdb.com/title/{identifier}/"
    driver.get(movie_url)
    
    try:
        # Find and extract the awards information
        awards_element = driver.find_element(By.CLASS_NAME, 'awards_summary_text')
        awards = awards_element.text.strip()
    
        # Print the awards information
        print(f"Awards for movie {identifier}: {awards}")
    
    except NoSuchElementException:
        print(f"No awards information found for movie {identifier}")
    
    # Add any additional scraping or interactions for each movie page here
    # ...
    
# Close the browser session
driver.quit()
