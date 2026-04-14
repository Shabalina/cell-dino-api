import requests
import os

def lambda_handler(event, context):
    url = os.environ['STREAMLIT_URL']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    INFRA_FINGERPRINTS = [
        '<div id="root"></div>',
        'window.analytics',
        'streamlitstatus.com'
    ]
    
    try:
        response = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        response.raise_for_status()
        
        # Check if the infra markers exist
        has_infra = all(marker in response.text for marker in INFRA_FINGERPRINTS)
        
        if has_infra:
            print("Success: Streamlit infrastructure detected.")
            return {"status": "online", "verified_by": "infra_check"}
        else:
            # If these aren't there, we might be on a 404 or a 'deep sleep' redirect
            print("Warning: Page loaded but Streamlit root was not found.")
            return {"status": "partial", "message": "Shell not detected"}
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return {"status": "offline", "error": str(e)}