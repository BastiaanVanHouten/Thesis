import requests
from bs4 import BeautifulSoup

# Example: Navigate to a webpage
url = "https://pro.imdb.com/title/tt3564472"

# Send a GET request to the URL
response = requests.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Find all <a> tags within <li> tags
name_tags = soup.find_all("li")
names = []

# Extract the names from the <a> tags
for name_tag in name_tags:
    a_tag = name_tag.find("a")
    if a_tag:
        name = a_tag.get_text(strip=True)
        names.append(name)

# Print all the extracted names
for name in names:
    print(name)

# Close the response
response.close()



### tried working on the popularitymeter
import requests
from bs4 import BeautifulSoup
import time

# Start URL
url = "https://pro.imdb.com/title/tt3564472"

# Create a session for making requests
session = requests.Session()

# Send a GET request to the start URL
response = session.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Create a list to store the popularity data
popularity_data = []

# Scrape the initial month's popularity score and date range
score_element = soup.select_one("span.week_high")
date_range_element = soup.select_one("span.a-color-secondary.week_range")

# Check if the elements exist before accessing their text
if score_element and date_range_element:
    score = score_element.text
    date_range = date_range_element.text

    # Add the data to the list
    popularity_data.append({"Score": score, "Date Range": date_range})

# Navigate to previous months and scrape their popularity data
for _ in range(10):  # Replace 10 with the desired number of months to scrape
    # Simulate waiting for page to load
    time.sleep(2)

    # Automate navigation to the previous month
    # Code here to interact with the website's controls or graph to navigate

    # Send a GET request to the updated URL
    response = session.get(url)

    # Update the BeautifulSoup object with the new content
    soup = BeautifulSoup(response.content, "html.parser")

    # Scrape the popularity score and date range for the current month
    score_element = soup.select_one("span.week_high")
    date_range_element = soup.select_one("span.a-color-secondary.week_range")

    # Check if the elements exist before accessing their text
    if score_element and date_range_element:
        score = score_element.text
        date_range = date_range_element.text

        # Add the data to the list
        popularity_data.append({"Score": score, "Date Range": date_range})

    # Close the response
    response.close()

# Print the collected popularity data
for data in popularity_data:
    print(data)


### second try ### 

import requests
from bs4 import BeautifulSoup

# Example: Navigate to a webpage
url = "https://pro.imdb.com/title/tt3564472"

# Send a GET request to the URL
response = requests.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Find the div element containing the popularity data
div_element = soup.find("div", class_="a-column a-span4 week_high_wrap")

if div_element:
    # Find the span element with class "week_high" inside the div element
    span_element = div_element.find("span", class_="week_high")
    
    if span_element:
        # Extract the popularity score
        popularity_score = span_element.get_text(strip=True)
        print("Popularity score:", popularity_score)
    else:
        print("Popularity score not found.")
else:
    print("Popularity data not found.")

# Close the response
response.close()