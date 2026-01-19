# Error Documentation

This document records the errors encountered during the development and deployment of the Smart Fashion Classifier, along with their root causes and solutions.

## 1. JSONDecodeError / NameError in Gateway

**Error Message:**
```text
Traceback (most recent call last):
  File "requests\models.py", line 976, in json
    return complexjson.loads(self.text, **kwargs)
...
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```
*Note: The actual error causing the JSON decode failure was a 500 Internal Server Error returned by the gateway, masking the underlying Python exception.*

**Underlying Cause:**
A `NameError` in `gateway.py`:
```python
if isinstance(img_input, str):  # NameError: name 'img_input' is not defined
```
The variable `img_input` was used but not defined. The function argument was named `img`.

**Solution:**
Refactor `gateway.py` to use the correct variable name:
```python
def preprocess_image(img):
    if isinstance(img, str):
        # ...
```

---

## 2. Gunicorn WORKER TIMEOUT (Kubernetes)

**Error Message:**
```text
[2026-01-10 18:19:09 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:11)
[2026-01-10 18:19:10 +0000] [11] [ERROR] Error handling request /predict
...
File "/app/gateway.py", line 92, in predict
    predict_response = prediction_service_stub.Predict(predict_request, timeout=80.0)
...
[2026-01-10 18:19:11 +0000] [1] [ERROR] Worker (pid:11) was sent SIGKILL! Perhaps out of memory?
```

**Cause:**
The Gunicorn web server has a default worker timeout of **30 seconds**. The gateway code was configured to wait up to **80 seconds** for the TensorFlow Serving model to respond (`timeout=80.0` in the gRPC call).
When the model took longer than 30 seconds to respond (common on cold starts or without GPU), Gunicorn killed the worker process before it could receive the gRPC response.

**Solution:**
Update `gateway-deployment.yaml` to override the default Gunicorn command and increase the timeout to exceed the gRPC timeout (e.g., 100 seconds).

```yaml
containers:
- name: gateway
  image: fashion-gateway:v1
  command:
    - "gunicorn"
    - "--bind=0.0.0.0:9696"
    - "--timeout=100"  # Increased from default 30s
    - "gateway:app"
```

---

## 3. RemoteDisconnected / Connection Aborted

**Error Message:**
```text
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**Underlying Cause:**
The server terminated the connection abruptly before sending any data back, often appearing as "Remote end closed connection without response". In this Kubernetes environment, this is typically due to:

1.  **OOM (Out of Memory) Crash:** The gateway container runs out of memory while processing the image (loading TensorFlow libraries or manipulating large arrays) and is instantly killed by Kubernetes (OOMKilled). The default limit was 256Mi, which is often insufficient for TensorFlow.
2.  **Gunicorn Timeout:** Similar to the WORKER TIMEOUT, but if the worker is killed immediately or during a critical phase, the socket may simply close.
3.  **Port Mismatch:** The gateway may be trying to send HTTP traffic to the gRPC port (8500) or vice-versa, causing the server to close the connection.

**Solution:**
1.  **Increase Memory Limits:** (Critical) Update `gateway-deployment.yaml` to give the gateway at least 1Gi of memory.
    ```yaml
    resources:
      limits:
        memory: "1Gi"
      requests:
        memory: "512Mi"
    ```
2.  **Increase Gunicorn Timeout:** Ensure timeout is set to 120s to allow for slow model inference.
3.  **Verify Ports:** Ensure `TF_SERVING_HOST` uses port 8500 for gRPC or 8501 for REST/HTTP.

---

---

## 4. Connection Refused (gRPC)

**Error Message:**
```text
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.UNAVAILABLE
    details = "failed to connect to all addresses; last error: UNKNOWN: ipv4:10.96.23.254:8500: Failed to connect to remote host: connect: Connection refused (111)"
```

**Cause:**
The **Gateway** cannot reach the **Model** on port 8500. This is almost always because the **Model container is crashing** (CrashLoopBackOff) or is not fully ready. 
In this project, the `clothing-model` (TensorFlow Serving with Xception) requires significant memory (~1GB) to load. The default Kubernetes deployment had a limit of `512Mi`, causing the container to be **OOMKilled** (Out of Memory) during startup.

**Solution:**
Increase the memory limit for the `tf-serving-model` deployment in `model-deployment.yaml`.

```yaml
containers:
- name: tf-serving-model
  image: clothing-model:v1
  resources:
    requests:
      memory: "512Mi"
    limits:
      memory: "2Gi"  # Increased from 512Mi
```

---

---

## 5. FAQs / Configuration Explanations

### Why use `http://gateway:80/predict`?

When connecting services within a Kubernetes cluster (e.g., Frontend to Gateway), we use the **Service Name** and **Service Port**, not the container IP or container port.

1.  **`gateway` (Hostname):** This matches the `metadata.name` defined in `gateway-service.yaml`. Kubernetes DNS resolves this name to the Service's internal IP.
2.  **`:80` (Service Port):** Defined in `gateway-service.yaml` under `spec.ports`. The Service listens on port 80 and forwards traffic to the container's target port (9696).
    ```yaml
    ports:
      - port: 80         # <-- Service Port (External door)
        targetPort: 9696 # <-- Container Port (Internal room)
    ```
3.  **`/predict`:** The specific endpoint route defined in the Flask application (`gateway.py`).


It breaks down into three parts based on your Kubernetes configuration:

http://gateway (The Hostname)
In Kubernetes, every Service gets a DNS name equal to its metadata.name.
In 
gateway-service.yaml
, you defined:
yaml
metadata:
  name: gateway
This allows any other pod in the same namespace (like your frontend) to reach it simply by using the name gateway.
:80 (The Service Port)
This comes from the ports section in 
gateway-service.yaml
:
yaml
ports:
  - port: 80         # <--- The door the Service opens to the world
    targetPort: 9696 # <--- The actual port your Flask app listens on
Even though your Flask app (Gunicorn) is running on port 9696 inside the container, the Service is acting as a "receptionist" on port 80. It takes traffic on port 80 and forwards it to port 9696 on the container.
Therefore, the frontend connects to the Service port (80), not the container port directly.
/predict (The Path)
This is the specific route defined in your 
gateway.py
 Flask application (@app.route("/predict", methods=["POST"])).
Summary: You are telling the frontend: "Go to the logical computer named gateway, knock on door 80 (which sends you to 9696 inside), and ask for the /predict function."

### What does `kubectl port-forward service/frontend 8080:80` do?

This command creates a tunnel from your local machine (laptop) to the Kubernetes cluster.

*   **`service/frontend`**: Tells Kubernetes you want to connect to the **Service** named "frontend".
*   **`8080` (Local Port)**: The port appearing on your laptop. You will open `localhost:8080` in your browser.
*   **`80` (Remote Port)**: The port inside the cluster that the Service is listening on (defined in `frontend-service.yaml`).

**Flow:**
`Your Browser (localhost:8080)` -> `Kubernetes Tunnel` -> `Service (Port 80)` -> `Container (Port 8501)`

**Summary**

`service/frontend: Targets the Kubernetes Service named "frontend"`.
`8080 (Local): The port on your laptop.`
`80 (Remote): The port the Service is listening on.`
This creates the tunnel: `Laptop (8080) -> Service (80) -> Container (8501)`
.

### Why is the Gateway service set to `type: LoadBalancer`?

We use `type: LoadBalancer` for the Gateway to allow **external access** (e.g., from your laptop's terminal using `test.py` or curl).

1.  **Dual Access:** It allows the Service to be reached both internally (by the Frontend) and externally (by you).
2.  **External IP:** In cloud environments (AWS/GCP), this provisions a real IP. In local clusters (Docker Desktop/Minikube), it often maps to `localhost`.
3.  **Flexibility:** This setup lets you debug the API directly without needing to go through the Frontend UI every time.

**Configuration Check:**
*   Is it okay? **Yes.**
*   Are `test.py` and `app.py` conflicting? **No.** `test.py` uses the external access (LoadBalancer), while `app.py` (running inside the cluster) uses the internal DNS name (`gateway`).

---

## 6. Useful Debugging Commands

Use these commands to diagnose issues in the Kubernetes cluster.

### Check Logs
View the logs of the running gateway or model pods to see Python errors or Gunicorn outputs.
```bash
# Get pod names
kubectl get pods

# View logs for a specific pod
kubectl logs <pod-name>

# View logs for a specific container in a pod (if multiple exist)
kubectl logs <pod-name> -c <container-name>

# Stream logs in real-time
kubectl logs -f <pod-name>
```

### Inspect Pod Status (OOMKilled, etc.)
Check if a pod crashed due to Out of Memory (OOM) or other system-level errors.
```bash
kubectl describe pod <pod-name>
```
*Look for "Last State: Terminated" and "Reason: OOMKilled" or "Exit Code: 137".*

### Enter the Container
Open a shell inside the running container to debug network connectivity or file issues.
```bash
kubectl exec -it <pod-name> -- /bin/bash
```

### Test Internal Connectivity
Once inside the gateway pod, try to reach the model service manually.
```bash
# Test REST endpoint (if using port 8501)
curl http://tf-serving-model.default.svc.cluster.local:8501/v1/models/clothing-model

# Test DNS resolution
nslookup tf-serving-model
```

### Port Forwarding
Access the service running inside the cluster directly from your local machine (localhost).
```bash
# Forward local port 9696 to the gateway pod's port 9696
kubectl port-forward <gateway-pod-name> 9696:9696
```

### Verify Services and Endpoints
Ensure the Service is correctly pointing to the Pods.
```bash
kubectl get services
kubectl get endpoints
```
