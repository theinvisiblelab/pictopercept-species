import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium WebDriver
chrome_path = "/Users/gaoxinkangrui/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
options = webdriver.ChromeOptions()
options.binary_location = chrome_path
driver = webdriver.Chrome(options=options)

# Store Images
image_folder = "downloaded_images"
os.makedirs(image_folder, exist_ok=True)

# Create CSV file to store information
csv_file = "image_metadata.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Image Name", "Keywords"])

start_url = "https://www.si.edu/spotlight/open-access-animals"


# Download images
def download_image(download_url, image_name):
    file_path = os.path.join(image_folder, f"{image_name}.jpg")
    try:
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image saved: {file_path}")
        else:
            print(f"Failed to download: {download_url}")
    except Exception as e:
        print(f"Error downloading image {image_name}: {e}")


# Extract information on detail page
def parse_detail_page(detail_url):
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "field-record-id")))

        # Extract Title
        title_element = driver.find_element(By.TAG_NAME, "h1")
        title = title_element.text.strip()

        # Extract Record ID
        record_id_element = driver.find_element(By.CLASS_NAME, "field-record-id")
        record_id = record_id_element.find_element(By.TAG_NAME, "dd").text.strip()

        # Extract Keywords
        try:
            keywords_element = driver.find_element(By.XPATH,
                                                   "//dl[contains(@class, 'field-freetextnotes') and ./dt[text()='Keywords']]")
            keywords = keywords_element.find_element(By.TAG_NAME, "dd").text.strip()
        except Exception as e:
            print(f"Keywords not found on page: {detail_url}. Setting keywords as empty.")
            keywords = ""

        if record_id.startswith("nzp_"):
            record_id = record_id.replace("nzp_", "")  # Remove the nzp_ prefix
            download_url = f"https://ids.si.edu/ids/download?id={record_id}.jpg"
            print(f"Downloading image from: {download_url}")
            download_image(download_url, record_id)

            # Save to CSV file
            with open(csv_file, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([title, record_id, keywords])
                print(f"Metadata saved: Title: {title}, Image Name: {record_id}, Keywords: {keywords}")
        else:
            print(f"No valid record ID found on page: {detail_url}")
    except Exception as e:
        print(f"Error parsing detail page {detail_url}: {e}")


# Load all images
def load_all_results(main_url):
    """
    Click 'Show More' button until all images are shown
    """
    driver.get(main_url)
    previously_loaded = 0
    retries = 0

    while True:
        try:
            # Wait for 'Show More' button and click
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "edan-loader__button"))
            )
            show_more_button.click()
            print("Clicked 'Show More' button. Loading more results...")
            time.sleep(2)

            # Get the number of currently loaded results
            results = driver.find_elements(By.CLASS_NAME, "edan-search-result")
            current_loaded = len(results)
            print(f"Currently loaded results: {current_loaded}")

            # Check for new results
            if current_loaded == previously_loaded:
                retries += 1
                if retries >= 3:
                    print("No new results loaded after multiple retries. Exiting...")
                    break
            else:
                retries = 0
                previously_loaded = current_loaded

        except Exception as e:
            print("No more 'Show More' buttons to click or an error occurred:", e)
            break

def scrape_all_results():
    """
    Process all links for detail pages
    """
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "edan-search-result")))
        results = driver.find_elements(By.CLASS_NAME, "edan-search-result")
        print(f"Total results found after loading all pages: {len(results)}")

        result_links = set()
        for result in results:
            try:
                link_element = result.find_element(By.CSS_SELECTOR, "a.inner")
                detail_url = link_element.get_attribute("href")
                result_links.add(detail_url)
            except Exception as e:
                print(f"Error getting result link: {e}")

        print(f"Unique detail pages to process: {len(result_links)}")

        # Extract information from all detail pages
        for detail_url in result_links:
            print(f"Processing detail page: {detail_url}")
            parse_detail_page(detail_url)

    except Exception as e:
        print("Error occurred while scraping all results:", e)



try:
    load_all_results(start_url)
    scrape_all_results()
finally:
    driver.quit()
