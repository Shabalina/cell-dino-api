import streamlit as st
import requests
from PIL import Image
import io
import os


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

# --- 2 GALLERY LOGIC ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_FOLDER = os.path.join(SCRIPT_DIR, "demo_images")


selected_image_bytes = None

if os.path.exists(DEMO_FOLDER):
    files = [f for f in os.listdir(DEMO_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        st.warning(f"No images found in: {DEMO_FOLDER}")
    else:
        st.subheader("Select a Demo Image")


    # Create a grid of columns
    cols = st.columns(6)

    for idx, file_name in enumerate(files):
        img_path = os.path.join(DEMO_FOLDER, file_name)
        img = Image.open(img_path)
        
        with cols[idx % 6]:
            st.image(img, use_container_width=True)
            # When button is clicked, we store the bytes in a variable
            if st.button(f"Analyze {file_name}", key=f"btn_{file_name}", use_container_width=True):
                with open(img_path, "rb") as f:
                    selected_image_bytes = f.read()
                # Store original image for display later
                st.session_state['preview_img'] = img

else:
    st.error(f"Folder not found: {DEMO_FOLDER}")


st.divider()

# --- UPLOADER LOGIC (Alternative) ---
uploaded_file = st.file_uploader("...or upload your own image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    selected_image_bytes = uploaded_file.getvalue()
    st.session_state['preview_img'] = Image.open(uploaded_file)


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