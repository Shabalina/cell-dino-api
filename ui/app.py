import streamlit as st
import requests
from PIL import Image
import io
import os
import boto3
from pathlib import PurePosixPath

# S3 Client
s3 = boto3.client(
    "s3",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)

BUCKET = st.secrets["BUCKET_NAME"]
PREFIX = "converted_recurtion_data/test_dino_sample"

def get_s3_images():
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].lower().endswith(('.png', '.jpg', '.jpeg'))]

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

ITEMS_PER_PAGE = 10
selected_image_bytes = None

# --- PAGE CONFIG ---
st.set_page_config(page_title="Cell DINOv2 Classifier", page_icon="🔬", layout="centered")

# --- SETTINGS ---
# In production, move this to st.secrets["API_URL"]
# API_URL = "https://h3ct11p3ya.execute-api.us-east-1.amazonaws.com/prod/predict"
API_URL = st.secrets["API_URL"]

st.title("🔬 Cell siRNA Classifier")
st.markdown("""
Upload a cellular microscopy image to predict the **siRNA ID** using our 
DINOv2-based inference engine.
""")

# --- 1. THE TOP SLOT FOR RESULTS---
# Container stays empty until a prediction is made.
results_container = st.container()

# --- 2. s3 GALLERY LOGIC---
st.subheader("S3 Test Sample Gallery")
image_keys = get_s3_images()

if image_keys:
    # Calculate total pages
    n_images = len(image_keys)
    n_pages = (n_images // ITEMS_PER_PAGE) + (1 if n_images % ITEMS_PER_PAGE > 0 else 0)

    # Slice the list for the current page
    start_idx = st.session_state['page_number'] * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_batch = image_keys[start_idx:end_idx]

    # --- RENDER GALLERY ---
    cols = st.columns(5)
    for idx, key in enumerate(current_batch):
        # Generate a temporary URL that lasts for 1 hour
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': BUCKET, 'Key': key},
                                        ExpiresIn=3600)
        
        with cols[idx % 5]:
            st.image(url, use_container_width=True)
            s3_filename = PurePosixPath(key).name
            # if st.button("Predict", key=key):
            if st.button(f"Analyze {s3_filename}", key=f"btn_{s3_filename}", use_container_width=True):
                # Get the raw bytes from S3
                image_obj = s3.get_object(Bucket=BUCKET, Key=key)
                selected_image_bytes = image_obj['Body'].read()

                # Convert bytes to a PIL Image object and store image in session state
                st.session_state['preview_img'] = Image.open(io.BytesIO(selected_image_bytes))
                # st.rerun() # Ensure the top results block updates immediately


    # --- PAGINATION CONTROLS ---
    st.write(f"Showing page {st.session_state['page_number'] + 1} of {n_pages}")
    col_prev, col_spacer, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.button("⬅️ Previous") and st.session_state['page_number'] > 0:
            st.session_state['page_number'] -= 1
            st.rerun()

    with col_next:
        if st.button("Next ➡️") and st.session_state['page_number'] < n_pages - 1:
            st.session_state['page_number'] += 1
            st.rerun()

# --- 2 GALLERY LOGIC ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_FOLDER = os.path.join(SCRIPT_DIR, "demo_images")


# --- PREDICTION LOGIC (Rendering to the TOP) ---
if selected_image_bytes is not None:
    with results_container:
        st.success("Analysis Target Selected")
        col_img, col_res = st.columns([1, 1]) 

        with col_img:
                st.image(st.session_state['preview_img'], caption="Selected for Analysis", use_container_width=True)

        with col_res:
            with st.spinner("Talking to SageMaker..."):
                try:
                    # Send the binary data
                    headers = {"Content-Type": "image/jpeg"}
                    response = requests.post(API_URL, data=selected_image_bytes, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("Analysis Complete!")
                        
                        # Layout for results
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Predicted siRNA ID", f"#{result.get('sirna_id')}")
                        with col2:
                            confidence = result.get('confidence', 0)
                            st.metric("Confidence Score", f"{confidence:.2%}")
                            
                        # Visual confidence bar
                        st.progress(confidence)
                        
                    else:
                        st.error(f"API Error ({response.status_code}): {response.text}")
                        
                except Exception as e:
                    st.exception(f"Connection Error: {e}")

st.divider()
st.caption("Built with Streamlit • Powered by AWS SageMaker & DINOv2")