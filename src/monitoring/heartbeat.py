import requests
import os

def lambda_handler(event, context):
    url = os.environ['STREAMLIT_URL']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # requests.get handles 303 redirects and session cookies much better than urllib
        response = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        status = response.status_code
        
        print(f"Heartbeat successful: {url} returned {status}")
        return {"status": "online", "code": status}
            
    except Exception as e:
        print(f"Heartbeat failed for {url}: {str(e)}")
        return {"status": "offline", "error": str(e)}