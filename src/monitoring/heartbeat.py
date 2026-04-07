import urllib.request
import os

def lambda_handler(event, context):
    url = os.environ['STREAMLIT_URL']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:

        req = urllib.request.Request(url, headers=headers)
        # Poking the app to reset the 24h sleep timer
        with urllib.request.urlopen(req, timeout=25) as response:
            status = response.getcode()
            print(f"Heartbeat successful: {url} returned {status}")
            return {"status": "online", "code": status}
    except Exception as e:
        print(f"Heartbeat failed for {url}: {str(e)}")
        return {"status": "offline", "error": str(e)}