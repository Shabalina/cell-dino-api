import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def run_heartbeat():
    # Setup Chrome Options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = os.environ.get('STREAMLIT_URL')
        print(f"Checking app state: {url}")
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
        print(f"Error during heartbeat: {e}")
    finally:
        driver.quit()
        print("Session closed.")

if __name__ == "__main__":
    run_heartbeat()