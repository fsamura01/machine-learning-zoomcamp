# Testing Guide: Smart Fashion Classifier on Kubernetes

This guide outlines the steps to deploy and test the full application (Model, Gateway, and Frontend) on a local Kubernetes cluster (Minikube, Kind, or Docker Desktop).

## 1. Prerequisites (Verify Images)

Ensure your Docker images are built and available to your cluster.

```bash
docker build -t clothing-model:v1 -f image-model.dockerfile .
docker build -t fashion-gateway:v1 -f image-gateway.dockerfile .
docker build -t fashion-frontend:v1 -f image-frontend.dockerfile .
```

### Using Kind (Kubernetes in Docker)?
If you are using **Kind**, you must load the images into the cluster so they are available to your pods.

**1. Load Local Images**
```bash
kind load docker-image clothing-model:v1 fashion-gateway:v1 fashion-frontend:v1
```
*Note: You can target a specific cluster with `--name cluster-name`.*

**2. Image Pull Policy**
Ensure your deployment YAML files set `imagePullPolicy: IfNotPresent` or `Never`. If set to `Always`, Kubernetes will try (and fail) to pull from Docker Hub.

**3. Alternative: Image Archives**
If you have a `.tar` archive:
```bash
kind load image-archive /path/to/image.tar
```

**4. Verify Loaded Images**
To check what images are on a node:
```bash
docker exec -it <kind-node-name> crictl images
```bash
docker exec -it <kind-node-name> crictl images
```

**5. Cluster Inspection Commands**
Useful commands to check the status of your nodes and the underlying Docker containers running the cluster.

*   **List Node Names:**
    ```bash
    kubectl get nodes -o name
    ```
    *Purpose:* Returns just the names of the nodes (e.g., `node/kind-control-plane`). Useful for scripting or getting the exact name for `docker exec`.

*   **Detailed Node info:**
    ```bash
    kubectl get nodes -o wide
    ```
    *Purpose:* Shows detailed information including Internal-IP, External-IP, OS Image, Kernel-Version, and Container Runtime. Use this to verify network configs.

*   **Find Kind Containers (Docker):**
    ```bash
    docker ps --filter "label=io.x-k8s.kind.cluster"
    ```
    *Purpose:* Lists only the Docker containers that are acting as Kubernetes nodes for your Kind cluster. Use this to find the Container ID if you need to inspect the "node" itself from the outside.

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
