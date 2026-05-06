import streamlit as st
import requests
from PIL import Image
import io
import os
import boto3
import json
from pathlib import PurePosixPath

# Load Manifest
@st.cache_data # Cache to not reload every click
def load_manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "metadata.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {}

manifest = load_manifest()

# S3 Client
s3 = boto3.client(
    "s3",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_REGION"]
)

BUCKET = st.secrets["BUCKET_NAME"]
PREFIX = "converted_recurtion_data/dino_demo_sample"

def get_s3_images():
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].lower().endswith(('.png', '.jpg', '.jpeg'))]

if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 0

ITEMS_PER_PAGE = 10
selected_image_bytes = None

# Page config
st.set_page_config(page_title="Cell DINOv2 Classifier", page_icon="🔬", layout="centered")

# Settings
API_URL = st.secrets["API_URL"]

st.title("🔬 Cell siRNA Classifier")
st.markdown("""
Upload a cellular microscopy image to predict the **siRNA ID** using our 
DINOv2-based inference engine.
""")

# --- THE TOP SLOT FOR RESULTS---
# Container stays empty until a prediction is made.
results_container = st.container()

# --- s3 GALLERY LOGIC---
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

                current_filename = s3_filename # Store filename for manifest lookup

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


# --- PREDICTION LOGIC (Rendering to the TOP) ---
if selected_image_bytes is not None:
    with results_container:
        st.success("Analysis Target Selected")
        col_img, col_res = st.columns([1, 1]) 

        with col_img:
                st.image(st.session_state['preview_img'], caption="Selected for Analysis", use_container_width=True)
                
                # --- MANIFEST LOOKUP ---
                if current_filename in manifest:
                    file_info = manifest[current_filename]
                    st.info(f"**Sample Source:** {file_info.get('type', 'N/A').replace('_', ' ').title()}")
                    if file_info.get('note'):
                        st.caption(f"📝 {file_info['note']}")

        with col_res:
            with st.spinner("🔬 Talking to SageMaker... (First analysis may take few seconds while the model warms up)"):
                try:
                    # Send the binary data
                    headers = {"Content-Type": "image/jpeg"}
                    response = requests.post(API_URL, data=selected_image_bytes, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()

                        # Extract result - adjust keys based on your FastAPI response
                        predicted_id = str(result.get('prediction') or result.get('sirna_id'))
                        confidence = result.get('confidence', 0)

                        # --- GROUND TRUTH LOGIC ---
                        ground_truth = manifest.get(current_filename, {}).get("label")
                        if ground_truth:
                            is_match = str(predicted_id) == str(ground_truth)
                            if is_match:
                                st.balloons()
                                st.success("✅ VALIDATION PASSED: Prediction matches Ground Truth!")
                            else:
                                st.warning("❌ VALIDATION MISMATCH: Model guessed incorrectly.")
                        
                        # Layout for results
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Predicted siRNA ID", f"#{result.get('sirna_id')}")
                            if ground_truth:
                                st.markdown(f"**Actual ID:** `#{ground_truth}`")
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