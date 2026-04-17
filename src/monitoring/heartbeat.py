import os
import time
import brotli
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def lambda_handler(event, context):
    # Paths
    br_path = '/opt/nodejs/node_modules/@sparticuz/chromium/bin/chromium.br'
    output_path = '/tmp/chromium'
    # 1. Decompress the binary if it's not already in /tmp
    if not os.path.exists(output_path):
        print("Decompressing Chromium binary to /tmp...")
        with open(br_path, 'rb') as f:
            compressed_data = f.read()
        
        decompressed_data = brotli.decompress(compressed_data)
        
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        
        # Give it execute permissions
        os.chmod(output_path, 0o755)
        print("Decompression complete.")

    # 2. Setup Selenium
    options = Options()
    options.binary_location = output_path  # point to the NEW file in /tmp
    
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")

    # Path to the driver provided by the layer
    service = Service("/opt/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        url = os.environ['STREAMLIT_URL']
        print(f"🔍 Analysing application state for: {url}")
        driver.get(url)
        
        # 1. Wait for Title Change (Checking if already awake)
        is_awake = False
        for i in range(30):
            if driver.title != "Streamlit" and driver.title != "":
                is_awake = True
                break
            time.sleep(1)
            if i % 10 == 0:
                print(f"⏳ Waiting for hydration... (Iteration {i})")

        if is_awake:
            print(f"SUCCESS: App is already AWAKE. Title: '{driver.title}'")
        else:
            print("Initialising recovery: Title is still default. Checking for Sleep Overlay...")
            
            # 2. Check for the Wakeup Button
            source = driver.page_source
            if "wakeup-button" in source or "Zzzz" in source:
                print("App is confirmed SLEEPING. Attempting to wake...")
                try:
                    button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid^="wakeup-button"]')
                    button.click()
                    print("Wake-up signal sent successfully (Button clicked).")
                    time.sleep(5) # Brief wait for the container to start booting
                except Exception as e:
                    print(f"Failed to click wake-up button: {e}")
            else:
                print("No known sleep markers found. App state is unknown.")
    except Exception as e:
        print(f"An error occurred during the check: {e}")
    finally:
        print("Cleaning up resources and closing driver.")
        driver.quit()