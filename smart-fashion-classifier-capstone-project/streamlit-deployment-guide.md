# Streamlit Cloud Deployment Guide

This guide explains how to deploy the **Frontend** component of the Smart Fashion Classifier to [Streamlit Cloud](https://streamlit.io/cloud).

> [!IMPORTANT]
> **Architecture Constraint:** Streamlit Cloud only hosts the Python frontend (`app.py`). It **cannot** host the Dockerized Gateway or TensorFlow Model directly.
>
> For the frontend on Streamlit Cloud to work, your Backend (Gateway) must be accessible via a **Public URL**. 
>
> **Options for Backend:**
> 1.  **Public Cloud:** Deploy Gateway+Model to AWS EKS, Google Cloud Run, or DigitalOcean Kubernetes.
> 2.  **Local Tunnel:** Run Kind locally and expose the Gateway using **ngrok** (e.g., `ngrok http 9696`).

## 1. Prepare the Repository

Streamlit Cloud pulls code directly from GitHub.

1.  **Ensure `requirements.txt` exists**:
    The `streamlit-frontend/` directory must contain a `requirements.txt` file with these dependencies:
    ```text
    streamlit
    requests
    pandas
    Pillow
    protobuf
    ```
    *(I have created this file for you).*

2.  **Push to GitHub**:
    Ensure your latest code (including the new `requirements.txt`) is committed and pushed to your GitHub repository.

## 2. Deploy to Streamlit Cloud

1.  Log in to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  **Repository:** Select your `smart-fashion-classifier-capstone-project` repo.
4.  **Branch:** `main` (or your working branch).
5.  **Main file path:** `streamlit-frontend/app.py`
    *   *Note: You must specify the subdirectory path.*
6.  Click **"Deploy!"**.

## 3. Configure the Gateway Connection

By default, the app tries to connect to `http://gateway:9696` (internal Kubernetes DNS), which will **fail** on Streamlit Cloud. You need to point it to your public backend.

1.  On your Streamlit App dashboard, click the **Settings** (three dots) -> **Settings**.
2.  Go to **"Secrets"**.
3.  Add your public Gateway URL:

    ```toml
    # If using ngrok
    GATEWAY_URL = "https://<your-ngrok-id>.ngrok-free.app/predict"
    
    # If using AWS LoadBalancer
    # GATEWAY_URL = "http://<external-ip-or-dns>/predict"
    ```
4.  Save. The app will restart.

## 4. Testing with ngrok (Local Backend)

If you don't have a cloud cluster, use `ngrok` to make your local Kind cluster accessible to Streamlit Cloud.

1.  **Port Forward Gateway locally:**
    ```bash
    kubectl port-forward service/gateway 9696:80
    ```
2.  **Start ngrok:**
    ```bash
    ngrok http 9696
    ```
3.  **Copy the HTTPS URL** (e.g., `https://a1b2c3d4.ngrok-free.app`).
4.  **Update Streamlit Secrets** with this new URL.
