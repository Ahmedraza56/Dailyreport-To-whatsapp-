import schedule
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

# Load environment variables from .env file
load_dotenv()


# Get credentials from environment variables
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Configure logging
logging.basicConfig(level=logging.INFO, filename='daily_report.log', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def capture_screenshot(report_url, file_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    chrome_options.binary_location = "/usr/lib/chromium/chromium"

    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)  

    driver.get(report_url)
    
    wait = WebDriverWait(driver, 20)  # Increase wait time
    try:
        time.sleep(5)  # Wait for the page to fully load
        
        # Set the zoom level to 80%
        driver.execute_script("document.body.style.zoom='80%'")
        
        driver.save_screenshot(file_name)
        logging.info(f"Screenshot saved at: {file_name}")
    except Exception as e:
        logging.error(f"An error occurred while capturing screenshot: {e}")
    finally:
        driver.quit()

def upload_image_to_imgbb(image_path, api_key):
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": api_key},
            files={"image": image_file}
        )
    response_data = response.json()
    if response_data['status'] == 200:
        link = response_data['data']['url']
        logging.info(f"Image uploaded to: {link}")
        return link
    else:
        logging.error(f"An error occurred while uploading the image: {response_data}")
        return None

def send_whatsapp_message_twilio(image_path, phone_number, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone_number}',
            media_url=image_path
        )
        logging.info(f"Message sent with SID: {msg.sid}")
    except TwilioRestException as e:
        logging.error(f"An error occurred while sending the message: {e}")

def job():
    report_url = 'YOUR_WEBSITE_LINK'
    screenshot_path = 'report_screenshot.png'
    phone_numbers = ['+12345678', '+112131314']  # Add your numbers here
   
    message = 'Here is the daily report screenshot.'
    
    capture_screenshot(report_url, screenshot_path)
    
    image_link = upload_image_to_imgbb(screenshot_path, IMGBB_API_KEY)
    if image_link:
        for phone_number in phone_numbers:
            send_whatsapp_message_twilio(image_link, phone_number, message)
    
    # Additional processing
    logging.info("Message sent successfully to all recipients.")


schedule.every().day.at("21:00").do(job)

logging.info("Scheduler started, waiting for the scheduled time...")

while True:
    schedule.run_pending()
    time.sleep(60)  # wait one minute before checking again













