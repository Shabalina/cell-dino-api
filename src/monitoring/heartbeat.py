import urllib.request
import os

def lambda_handler(event, context):
    url = os.environ['STREAMLIT_URL']
    try:
        # Poking the app to reset the 24h sleep timer
        with urllib.request.urlopen(url, timeout=25) as response:
            status = response.getcode()
            print(f"Heartbeat successful: {url} returned {status}")
            return {"status": "online", "code": status}
    except Exception as e:
        print(f"Heartbeat failed for {url}: {str(e)}")
        return {"status": "offline", "error": str(e)}