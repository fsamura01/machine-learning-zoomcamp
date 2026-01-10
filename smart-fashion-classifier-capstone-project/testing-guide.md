# Testing Guide: Smart Fashion Classifier on Kubernetes

This guide outlines the steps to deploy and test the full application (Model, Gateway, and Frontend) on a local Kubernetes cluster (Minikube, Kind, or Docker Desktop).

## 1. Prerequisites (Verify Images)

Ensure your Docker images are built and available to your cluster.

```bash
docker build -t clothing-model:v1 -f image-model.dockerfile .
docker build -t fashion-gateway:v1 -f image-gateway.dockerfile .
docker build -t fashion-frontend:v1 -f image-frontend.dockerfile .
```

## 2. Deploy Services

Apply the configuration files in `kube-config/`. Order matters slightly (best to have services up for pods to find).

```bash
# Apply all configurations
kubectl apply -f kube-config/
```

Expected Output:

```text
deployment.apps/frontend created
service/frontend created
deployment.apps/gateway configured
service/gateway unchanged
deployment.apps/tf-serving-model unchanged
service/tf-serving-model unchanged
```

## 3. Verify Pods are Running

Wait until all pods show `Running` status and `1/1` ready.

```bash
kubectl get pods
```

## 4. Access the Frontend

### Method A: Port Forwarding (Recommended for Localhost)

Forward the local port 8080 to the Frontend service's port 80.

```bash
kubectl port-forward service/frontend 8080:80
```

### Method B: External IP (LoadBalancer)

If using Docker Desktop or Cloud EKS, check for an `EXTERNAL-IP`.

```bash
kubectl get service frontend
```

## 5. Test the Application

1. Open your browser to **[http://localhost:8080](http://localhost:8080)**.
2. **Using URL:**
   - Select "Image URL" tab.
   - User defaults or try: `https://raw.githubusercontent.com/fsamura01/machine-learning-zoomcamp/main/smart-fashion-classifier-capstone-project/10005.jpg`
   - Click **Classify Product**.
3. **Using Upload:**
   - Select "Upload Image" tab.
   - Upload a local `.jpg` file.
   - Click **Classify Product**.

## Debugging Common Issues

If it fails:

1. **Check Gateway Logs:**

   ```bash
   kubectl logs -l app=gateway
   ```

2. **Check Frontend Logs:**

   ```bash
   kubectl logs -l app=frontend
   ```

3. **Verify Connectivity:**
   Exec into frontend and try to reach gateway:

   ```bash
   kubectl exec -it <frontend-pod-name> -- curl http://gateway:80/health
   ```
