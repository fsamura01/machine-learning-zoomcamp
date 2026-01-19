import os
import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
# Replace with your EKS LoadBalancer URL or keep as localhost for local testing
DEFAULT_GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:9696/predict")
print(f"DEBUG: DEFAULT_GATEWAY_URL is {DEFAULT_GATEWAY_URL}")

GATEWAY_URL = st.sidebar.text_input("Gateway API URL", DEFAULT_GATEWAY_URL)

st.set_page_config(page_title="Smart Fashion Classifier", layout="centered")

st.title("👗 Smart Fashion Classifier")
st.markdown("""
Upload a fashion product image (or provide a URL) to see its category predicted by our 
**Xception-based Deep Learning Model**.
""")

# --- INPUT SECTION ---
tabs = st.tabs(["Upload Image", "Image URL"])

image_to_show = None
image_url_to_send = None

with tabs[0]:
    uploaded_file = st.file_uploader("Choose a fashion image...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image_to_show = Image.open(uploaded_file)
        # This image will be sent to the gateway when the button is pressed


with tabs[1]:
    url_input = st.text_input("Paste image URL here:")
    if url_input:
        image_url_to_send = url_input
        try:
            response = requests.get(image_url_to_send)
            image_to_show = Image.open(BytesIO(response.content))
        except:
            st.error("Could not load image from URL.")

# --- PREDICTION SECTION ---
if image_to_show:
    st.image(image_to_show, caption="Input Image", use_container_width=True)

    if st.button("Classify Product"):
        if not image_url_to_send and not uploaded_file:
            st.error("Please provide a URL or upload an image.")
        else:
            with st.spinner("Analyzing style..."):
                try:
                    # Send request to the Gateway Service
                    if uploaded_file:
                        # Reset file pointer to beginning just in case
                        uploaded_file.seek(0)
                        files = {"file": uploaded_file}
                        # We don't send json if we send files usually, or depends on implementation.
                        # requests.post handles multipart automatically with files=
                        response = requests.post(GATEWAY_URL, files=files)
                    else:
                        payload = {"url": image_url_to_send}
                        response = requests.post(GATEWAY_URL, json=payload)
                        
                    response.raise_for_status()
                    
                    predictions = response.json()
                    
                    # Process and Display Results
                    df = pd.DataFrame(list(predictions.items()), columns=['Category', 'Confidence'])
                    df = df.sort_values(by='Confidence', ascending=False)
                    
                    st.success(f"Top Prediction: **{df.iloc[0]['Category']}**")
                    
                    # Display Chart
                    st.bar_chart(df.set_index('Category'))
                    
                except Exception as e:
                    st.error(f"Error connecting to Gateway: {e}")

# --- FOOTER ---
st.divider()
st.caption("Powered by TensorFlow Serving, Flask Gateway, and AWS EKS.")