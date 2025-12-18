# **This error indicates that your gRPC client is trying to connect to `localhost:8500` (or `[::1]:8500` in IPv6), but **no server is listening on that port**.**

## Quick Diagnostics

First, check if anything is running on port 8500:

```bash
# Windows
netstat -ano | findstr :8500

# Linux/Mac
lsof -i :8500
# or
netstat -tuln | grep 8500
```

## Common Solutions

### 1. **Start the gRPC Server**

Make sure your gRPC server is actually running before the client tries to connect:

```python
# Start your server first
python your_grpc_server.py
```

Then run your client in a separate terminal.

### 2. **Check the Server Address**

Verify the server is listening on the correct address:

```python
# Server should be configured like:
server.add_insecure_port('[::]:8500')  # Listen on all interfaces
# or
server.add_insecure_port('0.0.0.0:8500')  # IPv4
```

### 3. **Update Client Connection String**

If connecting to a remote server or Docker container, update your client:

```python
# Instead of:
channel = grpc.insecure_channel('localhost:8500')

# Try:
channel = grpc.insecure_channel('0.0.0.0:8500')
# or for Docker:
channel = grpc.insecure_channel('host.docker.internal:8500')
# or use the actual IP/hostname
```

### 4. **Add Connection Timeout & Retry**

Make your client more robust:

```python
import grpc
from grpc import StatusCode

# Add timeout and wait for ready
channel = grpc.insecure_channel(
    'localhost:8500',
    options=[
        ('grpc.max_receive_message_length', 50 * 1024 * 1024),
    ]
)

# Wait for the channel to be ready
try:
    grpc.channel_ready_future(channel).result(timeout=10)
    print("Connected successfully!")
except grpc.FutureTimeoutError:
    print("Failed to connect within 10 seconds")
```

### 5. **Docker/Kubernetes Context**

If running in containers:

**Docker Compose:**

```yaml
services:
  grpc-server:
    ports:
      - "8500:8500"
  grpc-client:
    depends_on:
      - grpc-server
    environment:
      - GRPC_SERVER=grpc-server:8500  # Use service name
```

**Kubernetes:**

```python
# Use the service name
channel = grpc.insecure_channel('tf-serving-service:8500')
```

### 6. **Check Firewall/Port Availability**

```bash
# Windows - allow port through firewall
netsh advfirewall firewall add rule name="gRPC" dir=in action=allow protocol=TCP localport=8500

# Linux
sudo ufw allow 8500/tcp
```

## What's Your Context?

To give you a more specific solution, let me know:

- Are you running TensorFlow Serving, a custom gRPC service, or something else?
- Are you using Docker/Kubernetes?
- Is the server running on the same machine or remotely?

**Most likely:** You just need to start your gRPC server before running the client
----

Good! The server **is running** on port 8500 (PID 18588 and 8856). The issue is that your client is trying to connect via **IPv6** (`[::1]:8500`), but there might be a connection issue.

## Solutions

### 1. **Force IPv4 Connection (Recommended)**

Change your client to explicitly use IPv4:

```python
# Instead of:
channel = grpc.insecure_channel('localhost:8500')

# Use:
channel = grpc.insecure_channel('127.0.0.1:8500')
```

Or add DNS resolution options:

```python
channel = grpc.insecure_channel(
    'localhost:8500',
    options=[
        ('grpc.dns_enable_srv_queries', 0),
        ('grpc.enable_http_proxy', 0),
    ]
)
```

### 2. **Disable IPv6 for gRPC (Environment Variable)**

Set this before running your Python script:

```bash
# Windows Command Prompt
set GRPC_DNS_RESOLVER=native
python your_script.py

# Windows PowerShell
$env:GRPC_DNS_RESOLVER="native"
python your_script.py

# Linux/Mac
export GRPC_DNS_RESOLVER=native
python your_script.py
```

### 3. **Add Connection Options**

Try with explicit connection parameters:

```python
import grpc

channel = grpc.insecure_channel(
    '127.0.0.1:8500',
    options=[
        ('grpc.max_send_message_length', 50 * 1024 * 1024),
        ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.keepalive_time_ms', 10000),
    ]
)

# Test the connection
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected successfully!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### 4. **Check if Multiple Servers are Conflicting**

You have two PIDs listening (18588 and 8856). One might be blocking the other:

```bash
# Check what's running
tasklist | findstr "18588 8856"

# Kill one if needed (run as administrator)
taskkill /PID 8856 /F
```

### 5. **Restart the Server with IPv4 Only**

If you control the server, make it listen on IPv4 explicitly:

```python
# In your gRPC server code:
server.add_insecure_port('0.0.0.0:8500')  # IPv4 only
# Instead of:
# server.add_insecure_port('[::]:8500')  # IPv6
```

## Quick Test

Try this to confirm IPv4 works:

```python
import grpc

# Test IPv4
channel = grpc.insecure_channel('127.0.0.1:8500')
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ IPv4 connection works!")
except:
    print("✗ IPv4 connection failed")

# Test IPv6
channel = grpc.insecure_channel('[::1]:8500')
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ IPv6 connection works!")
except:
    print("✗ IPv6 connection failed")
```

**Most likely solution:** Change `localhost:8500` to `127.0.0.1:8500` in your client code. This forces IPv4 and should resolve the issue immediately
----

Now the error shows it's trying IPv4 (`127.0.0.1:8500`) but the connection is still being **refused**. This suggests you're running the client from a **different environment** than where the server is running.

## Diagnosis

Based on the traceback showing `/usr/local/lib/python3.11/dist-packages/`, you're running this in a **Linux environment** (likely Docker container or Jupyter notebook), but your `netstat` output was from **Windows**.

### Are you in one of these scenarios?

1. **Running client in Docker, server on Windows host**
2. **Running client in WSL2, server on Windows**
3. **Running client in Jupyter/Colab, server locally**

## Solutions by Scenario

### If Client is in Docker Container

```python
# Use host.docker.internal to reach Windows host
channel = grpc.insecure_channel('host.docker.internal:8500')
```

Or get your Windows IP and use that:

```bash
# On Windows, find your IP
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)
```

```python
# Use your actual IP
channel = grpc.insecure_channel('192.168.1.100:8500')
```

### If Client is in WSL2

```python
# Get Windows host IP from WSL2
# In WSL2, run: cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
# Then use that IP:
channel = grpc.insecure_channel('<WINDOWS_IP>:8500')
```

Or use this Python helper:

```python
import subprocess
import grpc

# Get Windows host IP from WSL2
result = subprocess.run(
    ["sh", "-c", "cat /etc/resolv.conf | grep nameserver | awk '{print $2}'"],
    capture_output=True,
    text=True
)
windows_ip = result.stdout.strip()
print(f"Connecting to Windows host at: {windows_ip}:8500")

channel = grpc.insecure_channel(f'{windows_ip}:8500')
```

### If in Kubernetes/Docker Compose

Make sure your client can reach the server service:

```python
# Use the service name instead of localhost
channel = grpc.insecure_channel('tf-serving:8500')
# or whatever your service is named
```

### Server Configuration Check

Make sure your Windows server is listening on **all interfaces**, not just localhost:

```python
# Server code should have:
server.add_insecure_port('0.0.0.0:8500')  # Listen on all interfaces
# NOT just:
# server.add_insecure_port('127.0.0.1:8500')  # Only localhost
```

Then restart your server.

### Quick Test - Find Your Setup

Run this in your client environment:

```python
import platform
import socket

print("System:", platform.system())
print("Hostname:", socket.gethostname())

# Try to resolve localhost
try:
    print("Localhost resolves to:", socket.gethostbyname('localhost'))
except Exception as e:
    print("Error resolving localhost:", e)

# Check if we're in Docker
import os
if os.path.exists('/.dockerenv'):
    print("Running inside Docker container")
```

**Tell me the output and I'll give you the exact solution for your setup!**

Most likely you need to use `host.docker.internal:8500` or your Windows machine's actual IP address instead of `127.0.0.1:8500`
----

Ah! Both client and server are in Docker. The issue is that **`127.0.0.1` refers to the container itself**, not the server container.

## Solution: Use Docker Service Name

You need to connect using the **server's Docker service/container name**, not `localhost` or `127.0.0.1`.

### Option 1: Docker Compose (Recommended)

If using `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tf-serving:  # or whatever your server is named
    image: tensorflow/serving
    ports:
      - "8500:8500"
      - "8501:8501"
    # ... other config

  client:
    image: your-client-image
    depends_on:
      - tf-serving
    environment:
      - TF_SERVING_HOST=tf-serving  # Use service name
```

**In your Python client:**

```python
# Use the service name from docker-compose
channel = grpc.insecure_channel('tf-serving:8500')
```

### Option 2: Docker Network (Manual)

If running containers manually:

```bash
# Create a network
docker network create ml-network

# Run server
docker run -d \
  --name tf-serving \
  --network ml-network \
  -p 8500:8500 \
  tensorflow/serving

# Run client
docker run -it \
  --name client \
  --network ml-network \
  your-client-image
```

**In your Python client:**

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

### Option 3: Find Server Container Name

If you don't know the service name:

```bash
# List all running containers
docker ps

# Look for your gRPC server container name
# Use that name in your client
```

**Example:**

```bash
$ docker ps
CONTAINER ID   IMAGE                  NAMES
abc123...      tensorflow/serving     my-tf-serving
def456...      jupyter/notebook       my-client
```

```python
# Use the container name
channel = grpc.insecure_channel('my-tf-serving:8500')
```

### Option 4: Use Host Network Mode (Not Recommended)

```bash
# Run both containers with --network host
docker run --network host tensorflow/serving
docker run --network host your-client-image
```

```python
# Now localhost works
channel = grpc.insecure_channel('localhost:8500')
```

## Quick Fix for Existing Setup

**Most common fix:** Update your connection string to use the server container name:

```python
import grpc
import os

# Get server hostname from environment or use default
server_host = os.getenv('TF_SERVING_HOST', 'tf-serving')  # Change 'tf-serving' to your actual container name
server_port = '8500'

channel = grpc.insecure_channel(f'{server_host}:{server_port}')

# Verify connection
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print(f"✓ Connected to {server_host}:{server_port}")
except Exception as e:
    print(f"✗ Failed to connect: {e}")
```

## Debugging Steps

1. **Find your server container name:**

```bash
docker ps | grep 8500
```

1. **Check if containers are on same network:**

```bash
docker network inspect bridge
# or
docker network inspect <your-network-name>
```

1. **Test connectivity from client container:**

```bash
# Enter your client container
docker exec -it <client-container-name> bash

# Try to ping server (if ping is installed)
ping tf-serving

# Or test port connectivity
nc -zv tf-serving 8500
# or
telnet tf-serving 8500
```

**What's the name of your server container?** Once you tell me, I can give you the exact connection string to use
---

Perfect! Now I can see the issue clearly:

- **Server container**: `gallant_brahmagupta` (TensorFlow Serving)
- **Client container**: `romantic_roentgen` (Jupyter notebook)

These containers are **not on the same Docker network by default**, so they can't communicate with each other.

## Solution 1: Create Network and Reconnect (Recommended)

```bash
# 1. Create a network
docker network create ml-network

# 2. Connect both containers to the network
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen

# 3. Verify both are connected
docker network inspect ml-network
```

**Then in your Jupyter notebook:**

```python
import grpc
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Use the server container name
channel = grpc.insecure_channel('gallant_brahmagupta:8500')
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Test connection
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected successfully!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

## Solution 2: Use Host Network from Client

Since the server is already exposing port 8500 on your host (Windows), you can access it via the **host's IP**:

```python
import grpc
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Use host.docker.internal or your machine's IP
channel = grpc.insecure_channel('host.docker.internal:8500')
# OR if host.docker.internal doesn't work:
# channel = grpc.insecure_channel('172.17.0.1:8500')  # Docker bridge default gateway

prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
```

## Solution 3: Recreate with Docker Compose (Best Long-term)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tf-serving:
    image: tensorflow/serving:2.7.0
    container_name: tf-serving
    ports:
      - "8500:8500"
      - "8501:8501"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=your_model
    command:
      - "--model_base_path=/models/your_model"
      - "--rest_api_port=8501"

  jupyter:
    image: tensorflow/tensorflow:latest-jupyter
    container_name: jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/tf/notebooks
    depends_on:
      - tf-serving
    environment:
      - TF_SERVING_HOST=tf-serving

networks:
  default:
    name: ml-network
```

Then:

```bash
docker-compose up -d
```

**In your notebook:**

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

## Quick Test Now (Solution 2 - Fastest)

Try this in your Jupyter notebook right now:

```python
import grpc

# Try these in order:
endpoints = [
    'host.docker.internal:8500',
    '172.17.0.1:8500',
    'gateway.docker.internal:8500',
]

for endpoint in endpoints:
    try:
        channel = grpc.insecure_channel(endpoint)
        grpc.channel_ready_future(channel).result(timeout=2)
        print(f"✓ SUCCESS: Use '{endpoint}'")
        break
    except Exception as e:
        print(f"✗ Failed: {endpoint}")
```

**Once you find the working endpoint, use it for your predictions:**

```python
# Use the working endpoint from above
channel = grpc.insecure_channel('host.docker.internal:8500')
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Your prediction code
predict_response = prediction_service_stub.Predict(predict_request, timeout=20.0)
```

Try **Solution 2** (the quick test) first - it should work immediately without stopping your containers
----

Got it! Since you're using official images, the quickest solution is **Solution 1** (connect to existing network) or **Solution 2** (use host gateway).

## Fastest Fix - Try This Now in Your Jupyter Notebook

```python
import grpc
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Connect via Docker host gateway
channel = grpc.insecure_channel('172.17.0.1:8500')
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Test it
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected successfully to TF Serving!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

`172.17.0.1` is the **default Docker bridge gateway** that allows containers to reach the host's exposed ports.

## If That Doesn't Work

### Option A: Connect Containers to Same Network (No Restart Needed)

Run these commands on your **Windows host**:

```bash
# Create network
docker network create ml-network

# Connect both containers
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen

# Verify
docker network inspect ml-network | findstr "Name"
```

**Then in Jupyter:**

```python
channel = grpc.insecure_channel('gallant_brahmagupta:8500')
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
```

### Option B: Find the Server's IP on Bridge Network

```bash
# Get the server container's IP
docker inspect gallant_brahmagupta | findstr "IPAddress"
```

You'll see something like `"IPAddress": "172.17.0.2"`.

**Use that IP in Jupyter:**

```python
channel = grpc.insecure_channel('172.17.0.2:8500')  # Use the IP you found
```

## Complete Working Example

Once connected, your prediction code should be:

```python
import grpc
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Connect to TF Serving
channel = grpc.insecure_channel('172.17.0.1:8500')  # or the IP that works
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Create request
request = predict_pb2.PredictRequest()
request.model_spec.name = 'your_model_name'
request.model_spec.signature_name = 'serving_default'

# Add your input data
request.inputs['input_name'].CopyFrom(
    tf.make_tensor_proto(your_data, shape=your_shape)
)

# Make prediction
response = stub.Predict(request, timeout=20.0)
print("Prediction successful!")
print(response)
```

**Try `172.17.0.1:8500` first** - that's the most common solution for your setup
----

Great question! This is a fundamental Docker networking concept.

## Why `localhost:8500` Doesn't Work

When you're **inside a Docker container**, `localhost` (or `127.0.0.1`) refers to **that container itself**, not your Windows host machine.

```
┌─────────────────────────────────────────┐
│ Windows Host Machine                    │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Client Container             │      │
│  │ (romantic_roentgen)          │      │
│  │                              │      │
│  │ localhost:8500 ──► ❌        │      │
│  │ (looks inside THIS container)│      │
│  └──────────────────────────────┘      │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Server Container             │      │
│  │ (gallant_brahmagupta)        │      │
│  │                              │      │
│  │ Port 8500 is HERE! ✓         │      │
│  └──────────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

## Why `172.17.0.1:8500` Works

`172.17.0.1` is the **Docker bridge network gateway** - it's the IP address that lets containers communicate with the host machine.

```
┌─────────────────────────────────────────┐
│ Windows Host Machine                    │
│ (also accessible as 172.17.0.1)         │
│                                         │
│  Port 8500 mapped to server container   │
│         ▲                               │
│         │                               │
│  ┌──────┴───────────────────────┐      │
│  │ Client Container             │      │
│  │                              │      │
│  │ 172.17.0.1:8500 ──► ✓        │      │
│  │ (goes to host, then mapped   │      │
│  │  to server container)        │      │
│  └──────────────────────────────┘      │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Server Container             │      │
│  │ Port 8500 ✓                  │      │
│  └──────────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

## The Flow with `172.17.0.1:8500`

1. Client container sends request to `172.17.0.1:8500` (Docker bridge gateway)
2. Request reaches Windows host machine
3. Host sees port 8500 is mapped: `0.0.0.0:8500` → `gallant_brahmagupta:8500`
4. Request forwarded to server container
5. Server responds back through the same path

## Alternative Solutions

### 1. **Container Name** (if on same network)

```python
channel = grpc.insecure_channel('gallant_brahmagupta:8500')
```

Direct container-to-container communication - **fastest and best practice**.

### 2. **Host Gateway** (what you're using now)

```python
channel = grpc.insecure_channel('172.17.0.1:8500')
```

Goes through the host - **works but adds a hop**.

### 3. **Server's Container IP** (fragile)

```python
channel = grpc.insecure_channel('172.17.0.2:8500')  # example
```

Direct to container IP - **works but IP can change on restart**.

## Best Practice

Connect them to the same network so you can use container names:

```bash
docker network create ml-network
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen
```

Then use:

```python
channel = grpc.insecure_channel('gallant_brahmagupta:8500')
```

This is:

- ✅ Clearer (readable container name)
- ✅ Faster (direct container communication)
- ✅ More reliable (survives container restarts)
- ✅ Docker best practice

**TL;DR:** `localhost` in a container = that container. `172.17.0.1` = the host machine where your port mapping lives
----

This error means the containers **are not on the same Docker network**, so they can't resolve each other's names via DNS.

## Fix: Connect Them to the Same Network

Run these commands on your **Windows host**:

```bash
# 1. Create a network
docker network create ml-network

# 2. Connect both containers to it
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen

# 3. Verify they're connected
docker network inspect ml-network
```

You should see both container names in the output.

**Now in your Jupyter notebook:**

```python
import grpc
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Now this will work!
channel = grpc.insecure_channel('gallant_brahmagupta:8500')
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Test connection
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected using container name!")
except Exception as e:
    print(f"✗ Failed: {e}")
```

## Why This Happens

By default, Docker containers are on the `bridge` network, but containers on the default bridge network **cannot resolve each other by name**. They need to be on a **user-defined network** for DNS resolution to work.

```
Default bridge network:
❌ Container names don't resolve
✅ Can use IPs like 172.17.0.1

User-defined network (ml-network):
✅ Container names resolve automatically
✅ Better isolation
✅ Docker best practice
```

## Verify It Worked

After connecting them to the network, test from your Jupyter container:

```python
import socket

try:
    ip = socket.gethostbyname('gallant_brahmagupta')
    print(f"✓ gallant_brahmagupta resolves to: {ip}")
except:
    print("✗ Still can't resolve name - network not connected properly")
```

## Summary

- **Current working solution:** `172.17.0.1:8500` (uses host gateway)
- **Better solution:** Connect to same network, then use `gallant_brahmagupta:8500` (direct container communication)

The network connection commands don't require restarting your containers, so you can do this right now without losing your Jupyter session

---

I've created a comprehensive guide that structures all the errors you encountered and their solutions in a clear, easy-to-follow format. The guide includes:

## Key Sections

1. **Initial Setup** - Proper commands for starting both containers on different platforms
2. **Common Errors & Solutions** - All 5 major errors you faced with detailed explanations
3. **Best Practices** - Docker Compose setup and connection priorities
4. **Complete Working Example** - Full end-to-end code
5. **Troubleshooting Checklist** - Step-by-step debugging process

## Highlights

- ✅ Clear visual diagrams showing why `localhost` doesn't work
- ✅ Platform-specific commands (Windows CMD/PowerShell, Git Bash, Linux/Mac)
- ✅ Explanation of Docker networking concepts
- ✅ Complete working code examples
- ✅ Quick reference tables

The guide emphasizes that the **root cause** of most connection issues is understanding that `localhost` inside a container refers to that container itself, not the host or other containers. The best solution is using Docker Compose with user-defined networks for proper DNS resolution.

You can save this guide and reference it for future Docker projects
----

You're on Windows, so `grep` doesn't work in Command Prompt. Here are the Windows equivalents:

## Check TensorFlow Serving Logs (Windows)

**Command Prompt:**

```bash
docker logs gallant_brahmagupta | findstr "Exporting HTTP/REST API"
```

**PowerShell:**

```powershell
docker logs gallant_brahmagupta | Select-String "Exporting HTTP/REST API"
```

Or just view all logs:

```bash
docker logs gallant_brahmagupta
```

Look for lines like:

```
[evhttp_server.cc : 245] NET_LOG: Entering the event loop ...
[evhttp_server.cc : 250] NET_LOG: Exporting HTTP/REST API at:localhost:8501 ...
```

---

## Test Connectivity Between Containers

For the ping command, you're getting an error because **the containers aren't on the same network yet**.

First, let's check if ping is even available in the Jupyter container:

```bash
docker exec romantic_roentgen which ping
```

If ping isn't available, try these alternatives:

### Option 1: Check Network Connection

```bash
# See what networks each container is on
docker inspect romantic_roentgen | findstr NetworkMode
docker inspect gallant_brahmagupta | findstr NetworkMode
```

### Option 2: Connect Them to Same Network (Fix the DNS issue)

```bash
# Create network
docker network create ml-network

# Connect both containers
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen

# Verify
docker network inspect ml-network
```

### Option 3: Test Connection with Python

From your Jupyter notebook, run:

```python
import socket

# Test if we can resolve the server container name
try:
    ip = socket.gethostbyname('gallant_brahmagupta')
    print(f"✓ gallant_brahmagupta resolves to: {ip}")
except socket.gaierror:
    print("✗ Cannot resolve 'gallant_brahmagupta' - containers not on same network")
    print("   Using 172.17.0.1:8500 instead")

# Test gRPC connection
import grpc

endpoints = [
    ('gallant_brahmagupta:8500', 'Container name'),
    ('172.17.0.1:8500', 'Docker bridge gateway'),
]

for endpoint, description in endpoints:
    try:
        channel = grpc.insecure_channel(endpoint)
        grpc.channel_ready_future(channel).result(timeout=2)
        print(f"✓ SUCCESS: {description} ({endpoint}) works!")
        break
    except Exception as e:
        print(f"✗ FAILED: {description} ({endpoint})")
```

---

## Quick Summary

**For Windows users:**

- Replace `grep` with `findstr` (CMD) or `Select-String` (PowerShell)
- Replace `ping` tests with Python socket tests in Jupyter

**Current status:**

- Your containers CAN communicate via `172.17.0.1:8500` ✅
- They CANNOT use container names yet because they're not on the same network ❌

**To fix:**
Run these commands to enable container name resolution:

```bash
docker network create ml-network
docker network connect ml-network gallant_brahmagupta
docker network connect ml-network romantic_roentgen
```

Then you can use `gallant_brahmagupta:8500` in your code
----

Perfect! Let me teach you how to read this network inspection output and identify if containers are on the same network.

## Understanding the Network Inspection Output

When you run `docker network inspect bridge`, Docker shows you a JSON structure that describes everything about that network. Think of it like looking at a building's floor plan to see which apartments are on the same floor.

### The Key Section: "Containers"

The most important part for your question is the **"Containers"** object. This section lists every container currently connected to this network. In your output, I can see two containers listed:

```json
"Containers": {
    "10689c622bd86a1177c8d2994dacf47f62366dcc985068b61164350740c695dd": {
        "Name": "gateway-service",
        "IPv4Address": "172.17.0.3/16"
    },
    "f7836b8936770973f1951f092491f3a49c0caff46e815bf4a5a8a1e21ff00467": {
        "Name": "tf-serving",
        "IPv4Address": "172.17.0.2/16"
    }
}
```

This tells us that **gateway-service** and **tf-serving** are both on the bridge network. However, I notice that your Jupyter container (romantic_roentgen) is **not listed here**, which means it's either on a different network or not running.

## Simple Commands to Check Network Membership

Let me show you several ways to verify which containers are on which networks, starting from simplest to most detailed.

### Method 1: Quick Check - List All Networks and Their Containers

```bash
docker network ls
```

This shows all available networks. Then for each network you care about, you can inspect it:

```bash
docker network inspect bridge
docker network inspect ml-network
```

Look at the "Containers" section in each output. If both your containers appear in the same "Containers" section, they're on the same network.

### Method 2: Check a Specific Container's Networks

You can ask Docker to show you which networks a specific container is connected to:

```bash
docker inspect romantic_roentgen --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
```

This command extracts just the network names that the container is connected to. Run it for both containers:

```bash
docker inspect romantic_roentgen --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
docker inspect tf-serving --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
```

If they both output the same network name (like "bridge" or "ml-network"), then they're on the same network.

### Method 3: Visual Comparison (PowerShell)

If you're using PowerShell, you can get a nice table view:

```powershell
docker ps --format "table {{.Names}}\t{{.ID}}" | ForEach-Object {
    if ($_ -notmatch "NAMES") {
        $name = ($_ -split '\s+')[0]
        $networks = docker inspect $name --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}'
        Write-Output "$name : $networks"
    }
}
```

This will show you each container and its networks in an easy-to-read format.

## Understanding Your Current Situation

Based on your network inspection output, here's what I can tell you:

**The bridge network contains:**

- gateway-service (172.17.0.3)
- tf-serving (172.17.0.2)

**Missing from the bridge network:**

- romantic_roentgen (your Jupyter container)

This explains why you're getting DNS resolution errors when trying to connect using container names. Your Jupyter container is either on a different network entirely, or it might not be running at all.

### Let's Find Your Jupyter Container

Run this command to see all running containers and their networks:

```bash
docker ps --format "table {{.Names}}\t{{.Networks}}"
```

This will show you a clean table with container names and their networks. Look for romantic_roentgen in the output.

## The Critical Networking Concept: Default Bridge vs User-Defined Networks

Here's something really important to understand about Docker networking. There are two types of bridge networks, and they behave very differently:

**Default Bridge Network** (the one in your output):

- Containers can communicate using IP addresses like 172.17.0.2
- Containers **cannot** resolve each other by name (no DNS)
- This is what Docker uses automatically when you don't specify a network
- Think of it like giving someone a phone number but not saving their name in your contacts

**User-Defined Networks** (like ml-network):

- Containers can communicate using both IP addresses and container names
- Built-in DNS resolution works automatically
- This is the modern, recommended approach
- Think of it like having someone's name, phone number, and photo all saved properly

This is why even though tf-serving and gateway-service are on the same network in your output, if you tried to ping one from the other using names, it might not work because they're on the default bridge network.

## How to Fix Your Situation

Since your containers aren't currently on a user-defined network together, here's how to fix it:

```bash
# First, verify romantic_roentgen is actually running
docker ps | findstr romantic_roentgen

# Create a user-defined network (if you haven't already)
docker network create ml-network

# Connect all three containers to it
docker network connect ml-network tf-serving
docker network connect ml-network romantic_roentgen
docker network connect ml-network gateway-service

# Now verify they're all connected
docker network inspect ml-network
```

After running these commands, when you inspect ml-network, you should see all three containers listed in the "Containers" section, which means they can now communicate using their container names.

## Quick Visual Check

Here's a simple mental model: imagine `docker network inspect` output as a guest list for a party. The "Containers" section shows everyone who's at that particular party. If two people you want to introduce aren't both on the guest list, they're at different parties and can't meet. Your job is to make sure both containers are invited to (connected to) the same party (network).

Would you like me to help you verify which network your romantic_roentgen container is currently on? Just run `docker ps` and share the output with me, and I can help you understand the complete picture
----

This error occurs because you're importing `grpc` but need to import the correct module. The `insecure_channel` function is in `grpc` but you might be importing the wrong package or there's a naming conflict.

Here are the solutions:

## Solution 1: Check your import statement

Make sure you're importing the correct gRPC package:

```python
import grpc
```

**Not:**

- `import grpcio`
- `from grpc import grpc`

## Solution 2: Install the correct package

You might have the wrong package installed. Uninstall any grpc-related packages and install the correct one:

```bash
pip uninstall grpc grpcio grpcio-tools
pip install grpcio grpcio-tools
```

## Solution 3: Check for naming conflicts

Make sure you don't have a file named `grpc.py` in your project directory that's shadowing the actual grpc module. If you do, rename it to something else.

## Solution 4: Verify your gateway.py

Your `gateway.py` should look something like this:

```python
import grpc
import tensorflow_serving.apis.predict_pb2 as predict_pb2
import tensorflow_serving.apis.prediction_service_pb2_grpc as prediction_service_pb2_grpc

# Your host configuration
host = 'localhost:8500'  # or whatever your TF Serving host is

# This should work now
channel = grpc.insecure_channel(host)
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
```

Try Solution 2 first (reinstalling grpcio), as this is the most common cause of this error. If you're still having issues, share your import statements and I can help further

---

The issue is clear from your debug line! The `print(hasattr(grpc, "insecure_channel"))` is likely returning `False`, which means the `grpc` module doesn't have the `insecure_channel` attribute.

This is a **package installation issue**. Let me help you fix it:

## Step 1: Check what's installed

```bash
pip list | grep grpc
```

## Step 2: Completely reinstall grpcio

```bash
# Uninstall everything grpc-related
pip uninstall grpc grpcio grpcio-tools -y

# Reinstall the correct packages
pip install grpcio grpcio-tools
```

## Step 3: Also install tensorflow-serving-api

Since you're using TensorFlow Serving, you need:

```bash
pip install tensorflow-serving-api
```

## Step 4: Verify the installation

```bash
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
```

This should print `True`.

## Complete requirements

Here are all the packages you need for this script:

```bash
pip install grpcio grpcio-tools tensorflow-serving-api keras-image-helper flask tensorflow
```

Or create a `requirements.txt`:

```txt
grpcio==1.60.0
grpcio-tools==1.60.0
tensorflow-serving-api==2.14.0
keras-image-helper==0.0.1
flask==3.0.0
tensorflow==2.14.0
```

Then install with:

```bash
pip install -r requirements.txt
```

---

The most common cause is having a conflicting package or the wrong version. The reinstall should fix it. Let me know what the `pip list | grep grpc` shows and whether the reinstall works

---

Ah, Windows 11! Let me adjust the commands for you:

## Step 1: Check what's installed_

```bash
pip list | findstr grpc
```

## Step 2: Completely reinstall grpcio_

```bash
# Uninstall everything grpc-related
pip uninstall grpc grpcio grpcio-tools -y

# Reinstall the correct packages
pip install grpcio grpcio-tools
```

## Step 3: Also install tensorflow-serving-api_

```bash
pip install tensorflow-serving-api
```

## Step 4: Verify the installation_

```bash
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
```

This should print `True`.

## If you're using PowerShell

If the above `findstr` doesn't work and you're in PowerShell, use:

```powershell
pip list | Select-String grpc
```

## Common Windows-specific issues

1. **Multiple Python installations**: Make sure you're using the same Python environment. Check with:

   ```bash
   python --version
   pip --version
   ```

2. **Virtual environment**: If you're using a virtual environment, make sure it's activated:

   ```bash
   # Activate venv on Windows
   .\venv\Scripts\activate
   ```

3. **Anaconda/Conda**: If you're using Anaconda, use conda instead:

   ```bash
   conda uninstall grpc grpcio grpcio-tools -y
   conda install -c conda-forge grpcio grpcio-tools
   ```

## Complete requirements for Windows

Create a `requirements.txt`:

```txt
grpcio==1.60.0
grpcio-tools==1.60.0
tensorflow-serving-api==2.14.0
keras-image-helper==0.0.1
flask==3.0.0
tensorflow==2.14.0
```

Then install:

```bash
pip install -r requirements.txt
```

Try the reinstall and let me know what happens! If it still doesn't work, share the output of `pip list | findstr grpc` and we'll troubleshoot further

---

Great! You have `grpcio` and `grpcio-tools` installed. Now let's check if you have the TensorFlow Serving API:

```bash
pip list | findstr tensorflow
```

The issue is likely that you're **missing `tensorflow-serving-api`**, which provides the protobuf definitions you're importing.

## Install tensorflow-serving-api

```bash
pip install tensorflow-serving-api
```

## If that doesn't work, try this alternative approach

Some versions of `tensorflow-serving-api` have compatibility issues. Try:

```bash
# Try a specific version
pip install tensorflow-serving-api==2.14.0
```

Or if that fails:

```bash
# Use the latest stable version
pip install tensorflow-serving-api==2.15.0
```

## After installation, test again

```bash
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
```

This should print `True`.

Then try running your script again:

```bash
python gateway.py
```

---

**Note**: The `grpc.insecure_channel` function should definitely exist in `grpcio==1.76.0`. If the `hasattr` check is returning `False`, there might be a module shadowing issue.

Let me know what `pip list | findstr tensorflow` shows, and whether installing `tensorflow-serving-api` fixes it

---

Perfect! You have both `tensorflow` and `tensorflow-serving-api` installed. Now let's diagnose why `grpc.insecure_channel` isn't being found.

## Quick Test_

Run this in your terminal:

```bash
python -c "import grpc; print(grpc.__file__); print(dir(grpc))"
```

This will show you:

1. Where the `grpc` module is being loaded from
2. All available attributes in the module

## Most Likely Issue: File Naming Conflict

Check if you have a file named `grpc.py` in your current directory:

```bash
dir grpc.py
```

If this file exists, **that's your problem!** Python is importing your local `grpc.py` instead of the `grpcio` package.

**Solution**: Rename or delete the local `grpc.py` file.

## Alternative: Test in Python Interactive Shell

Open Python and test:

```bash
python
```

Then type:

```python
import grpc
print(grpc.__file__)
print(hasattr(grpc, 'insecure_channel'))
```

This should show you exactly what's being imported.

## If there's no naming conflict

Try reinstalling grpcio even though it's already installed:

```bash
pip uninstall grpcio -y
pip install grpcio==1.76.0
```

---

Let me know what the output of that first test command shows, especially the file path where `grpc` is being loaded from

---

**Found it!** The issue is clear now. Your `grpc` module is showing `__file__ = None` and has almost no attributes. This means there's a **namespace package conflict** or a broken installation.

## Solution: You have a conflicting `grpc` package

There's likely a package called `grpc` (not `grpcio`) installed that's shadowing the correct one.

### Step 1: Check for the conflicting package

```bash
pip list | findstr grpc
```

Look for a package literally named `grpc` (not `grpcio`).

### Step 2: Uninstall the conflicting package

```bash
pip uninstall grpc -y
```

### Step 3: Reinstall grpcio

```bash
pip uninstall grpcio grpcio-tools -y
pip install grpcio grpcio-tools
```

### Step 4: Verify it works

```bash
python -c "import grpc; print(grpc.__file__); print(hasattr(grpc, 'insecure_channel'))"
```

Now you should see:

- A proper file path (like `C:\...\site-packages\grpc\__init__.py`)
- `True` for the `hasattr` check

### Step 5: Run your script

```bash
python gateway.py
```

---

The `grpc` package is an old, abandoned package that conflicts with `grpcio` (the correct one). Uninstalling it should fix your issue immediately

---

Good, so there's no package literally named `grpc`. The issue is that `grpcio` is installed but not loading properly.

## Solution: Force reinstall grpcio

```bash
pip uninstall grpcio grpcio-tools -y
pip install --no-cache-dir grpcio grpcio-tools
```

The `--no-cache-dir` flag ensures a fresh download.

## Alternative: Check your Python site-packages

Let's see if there's a conflicting `grpc` folder:

```bash
python -c "import sys; print('\n'.join(sys.path))"
```

Look through those paths for a `grpc` or `grpc.py` file that shouldn't be there.

## Nuclear option: Check for grpc files manually

Navigate to your Python site-packages directory and check:

```bash
# Find your site-packages location
python -c "import site; print(site.getsitepackages())"
```

Then go to that directory and look for:

- A folder named `grpc`
- A file named `grpc.py`

## If reinstall doesn't work

Try creating a fresh virtual environment:

```bash
# Create new virtual environment
python -m venv venv_test

# Activate it
.\venv_test\Scripts\activate

# Install packages
pip install grpcio grpcio-tools tensorflow-serving-api keras-image-helper flask tensorflow

# Test
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
```

Try the force reinstall first with `--no-cache-dir`. That usually fixes this exact issue on Windows

---

Ah! That's the key information! **UV** (the ultra-fast Python package manager) sometimes has issues with namespace packages like `grpcio`.

## Solution for UV

### Step 1: Reinstall with UV

```bash
uv pip uninstall grpcio grpcio-tools
uv pip install grpcio grpcio-tools --reinstall
```

### Step 2: If that doesn't work, use the `--no-binary` flag

```bash
uv pip uninstall grpcio grpcio-tools
uv pip install grpcio grpcio-tools --no-binary grpcio
```

### Step 3: Or try forcing a rebuild

```bash
uv pip install grpcio grpcio-tools --reinstall --no-cache
```

### Step 4: Verify

```bash
python -c "import grpc; print(grpc.__file__); print(hasattr(grpc, 'insecure_channel'))"
```

## Known UV Issue with grpcio

UV sometimes doesn't properly install the native extensions for `grpcio` on Windows. If the above doesn't work, you might need to:

### Option A: Use pip for just grpcio

```bash
# Temporarily use pip for grpcio
pip install grpcio grpcio-tools --force-reinstall

# Then continue using uv for other packages
```

### Option B: Use a different Python version

UV works better with certain Python versions. Check your Python version:

```bash
python --version
```

If you're on Python 3.13, try downgrading to 3.11 or 3.12, as grpcio has better support there.

---

Try the `--reinstall --no-cache` approach first. UV's caching can sometimes cause issues with native extensions like grpcio on Windows. Let me know if this fixes it

---

Excellent! 🎉 Now `grpc.insecure_channel` is available and working!

## Run your script

Now you can run your gateway script:

```bash
python gateway.py
```

Or if you want to activate the Flask app (uncomment the last line in your script):

```python
if __name__ == "__main__":
    url = "http://bit.ly/mlbookcamp-pants"
    response = predict(url)
    print(response)
    app.run(debug=True, host="0.0.0.0", port=9696)  # Uncomment this line
```

## Just to confirm everything works

The script should:

1. Connect to TensorFlow Serving on `localhost:8500`
2. Make a prediction on the test image
3. Print the classification results

If TensorFlow Serving isn't running yet, you'll need to start it first. But at least the import error is fixed!

Let me know if you encounter any other issues! 👍

---

I've created a comprehensive debugging guide that explains:

1. **Why the error occurs** - covering all possible causes (wrong package, corrupted installation, file conflicts, UV-specific issues)

2. **Diagnostic steps** - how to identify which specific problem you're facing

3. **Complete solutions** - step-by-step fixes for each scenario, including UV-specific commands

4. **Verification steps** - how to confirm the fix worked

5. **The specific UV issue** - explaining why UV had trouble with grpcio on Windows (native extensions, caching, binary compatibility)

The document is structured so anyone encountering this error can:

- Understand what went wrong
- Diagnose their specific situation
- Apply the appropriate fix
- Verify it worked

In your case, the issue was UV's caching mechanism keeping a broken installation of grpcio, which was resolved by using `--reinstall --no-cache` flags to force a fresh download and installation

---

I've created a comprehensive guide explaining what gRPC is and how it works! Here are the key points:

## In Simple Terms

**gRPC** is a way for different programs (often written in different languages) to talk to each other efficiently. It's like a super-fast phone system for software services.

## In Your Code Specifically

In your `gateway.py`, you're using gRPC to:

1. **Connect** to TensorFlow Serving (a separate service running your ML model)
2. **Send** image data for prediction
3. **Receive** classification results back

This is much faster than using regular HTTP/JSON because:

- **Binary format** (protobuf) is smaller than JSON
- **HTTP/2** is faster than HTTP/1.1
- **Strongly typed** - both sides agree on the data format

## Why TensorFlow Serving Uses gRPC

TensorFlow Serving needs to handle thousands of prediction requests per second with minimal latency. gRPC's efficiency makes this possible - it's about 5-10x faster than REST APIs for this use case.

The document covers everything from basic concepts to real-world comparisons with REST APIs, plus specific examples from your code. Let me know if you'd like me to explain any particular aspect in more detail

---

This is a **protobuf version compatibility issue**. The TensorFlow Serving API was generated with an older version of protobuf, but you have a newer incompatible version installed.

## Quick Fix: Downgrade protobuf

```bash
uv pip install protobuf==3.20.3
```

Then try running again:

```bash
uv run python gateway.py
```

## Why This Happens-

- `tensorflow-serving-api==2.19.1` was built with protobuf 3.x
- You likely have protobuf 4.x or 5.x installed
- Protobuf 4.0+ changed how descriptors are created, breaking compatibility with older generated code

## Check Your Current Protobuf Version

```bash
uv pip list | findstr protobuf
```

## If Downgrade Doesn't Work

Try these alternatives in order:

### Option 1: Use a compatible tensorflow-serving-api version

```bash
uv pip uninstall tensorflow-serving-api
uv pip install tensorflow-serving-api==2.14.0
uv pip install protobuf==3.20.3
```

### Option 2: Set environment variable (slower but works)

```bash
# PowerShell
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python"
uv run python gateway.py

# Or add to your script permanently
```

In your `gateway.py`, add at the very top (before any imports):

```python
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import grpc
from flask import Flask, jsonify, request
# ... rest of imports
```

### Option 3: Compatible package versions

Use this specific combination that's known to work:

```bash
uv pip install protobuf==3.20.3
uv pip install tensorflow==2.14.0
uv pip install tensorflow-serving-api==2.14.0
```

## Recommended Solution

The cleanest fix is to use compatible versions:

```bash
# Uninstall current versions
uv pip uninstall tensorflow tensorflow-serving-api protobuf

# Install compatible versions
uv pip install tensorflow==2.14.0 tensorflow-serving-api==2.14.0 protobuf==3.20.3
```

This combination is tested and stable.

## Verify It Works

```bash
python -c "from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc; print('Success!')"
```

Try the protobuf downgrade first - it's the simplest solution and usually works immediately

---

Ah! You have **two protobuf packages** installed, and that's causing the conflict:

- `protobuf==6.33.2` (way too new)
- `tensorflow-protobuf==2.7.0` (TensorFlow's fork)

## Solution: Remove Both and Install Compatible Version

```bash
# Remove both protobuf packages
uv pip uninstall protobuf tensorflow-protobuf -y

# Install the compatible version
uv pip install protobuf==3.20.3
```

Then test:

```bash
uv run python gateway.py
```

## Why This Happened

- `tensorflow-protobuf` is a special fork that sometimes gets installed alongside TensorFlow
- Having both `protobuf` and `tensorflow-protobuf` creates conflicts
- `protobuf==6.33.2` is too new for `tensorflow-serving-api==2.19.1`

## If You Still Get Errors

Try this complete reinstall with compatible versions:

```bash
# Remove all problematic packages
uv pip uninstall tensorflow tensorflow-serving-api protobuf tensorflow-protobuf -y

# Install compatible versions in order
uv pip install protobuf==3.20.3
uv pip install tensorflow==2.14.0
uv pip install tensorflow-serving-api==2.14.0
```

## Verify Installation

```bash
# Check what's installed
uv pip list | findstr protobuf

# Should only show:
# protobuf    3.20.3

# Test the import
python -c "from tensorflow_serving.apis import predict_pb2; print('Success!')"
```

The key is to have **only one protobuf package** at version `3.20.3`. Try that uninstall/reinstall and it should work

---

Ah, UV doesn't use the `-y` flag like pip does. Here's the correct syntax:

```bash
# UV doesn't need confirmation flag
uv pip uninstall protobuf tensorflow-protobuf

# Install the compatible version
uv pip install protobuf==3.20.3
```

When prompted, just confirm the uninstall.

## Alternative: Use `--no-input` if you want to skip confirmation

```bash
uv pip uninstall protobuf tensorflow-protobuf --no-input
uv pip install protobuf==3.20.3
```

Then test:

```bash
uv run python gateway.py
```

## If You Need Complete Reinstall

```bash
# Remove all problematic packages
uv pip uninstall tensorflow tensorflow-serving-api protobuf tensorflow-protobuf

# Install compatible versions
uv pip install protobuf==3.20.3
uv pip install tensorflow==2.14.0
uv pip install tensorflow-serving-api==2.14.0
```

## Verify After Installation

```bash
# Check protobuf version
uv pip list | findstr protobuf

# Should show only:
# protobuf    3.20.3

# Test import
python -c "from tensorflow_serving.apis import predict_pb2; print('Works!')"
```

The `-y` flag is a pip thing - UV just prompts you (or you can use `--no-input` to skip prompts). Try it now

---

The `tensorflow-serving-api` package is broken or incomplete. Let's fix this:

## Solution: Reinstall tensorflow-serving-api

```bash
# Uninstall and reinstall tensorflow-serving-api
uv pip uninstall tensorflow-serving-api
uv pip install tensorflow-serving-api==2.14.0
```

## If That Doesn't Work: Complete Clean Reinstall

```bash
# Remove TensorFlow packages
uv pip uninstall tensorflow tensorflow-serving-api

# Install in this specific order
uv pip install protobuf==3.20.3
uv pip install tensorflow==2.14.0
uv pip install tensorflow-serving-api==2.14.0
```

## Verify the Installation

```bash
# Check if the files exist
python -c "import tensorflow_serving.apis.predict_pb2 as pb2; print('Success!')"
```

## Alternative: Try a Different Version

If 2.14.0 doesn't work, try 2.13.0:

```bash
uv pip uninstall tensorflow-serving-api
uv pip install tensorflow-serving-api==2.13.0
```

## Check What's Actually Installed

```bash
python -c "from tensorflow_serving.apis import *; import tensorflow_serving.apis; print(dir(tensorflow_serving.apis))"
```

This will show you what's actually available in the package.

## Note About UV Warning

The warning about hardlinking is not critical - it just means UV is copying files instead of creating hard links (which is fine, just a bit slower). You can ignore it or set:

```bash
$env:UV_LINK_MODE="copy"
```

Try the reinstall of `tensorflow-serving-api==2.14.0` first - that's the most likely fix

---

The `tostring()` method was deprecated and removed in newer versions of NumPy. It's been replaced with `tobytes()`.

## Solution: Update proto.py

You need to modify your `proto.py` file. Change line 18 from:

```python
tensor_proto.tensor_content = data.tostring()
```

To:

```python
tensor_proto.tensor_content = data.tobytes()
```

## Check Your NumPy Version

```bash
python -c "import numpy; print(numpy.__version__)"
```

If you have NumPy 1.20+, `tostring()` doesn't exist anymore.

## Alternative: Use TensorFlow's Built-in Function

Instead of using a custom `make_tensor_proto`, use TensorFlow's version directly in your `gateway.py`:

Change this line:

```python
from tensorflow import make_tensor_proto
```

And in your `prepare_request` function:

```python
def prepare_request(X):
    predict_request = predict_pb2.PredictRequest()
    
    predict_request.model_spec.name = "clothing-model"
    predict_request.model_spec.signature_name = "serving_default"
    
    # Use TensorFlow's make_tensor_proto directly
    from tensorflow import make_tensor_proto
    predict_request.inputs["input_8"].CopyFrom(make_tensor_proto(X))
    
    return predict_request
```

## If You Want to Keep Your Custom proto.py

Show me your `proto.py` file and I can help you fix it properly. But the quick fix is:

1. Open `proto.py`
2. Find `data.tostring()`
3. Replace with `data.tobytes()`

---

# **How to Read and Identify Python Errors**

## Understanding Python Error Anatomy

Every Python error (traceback) follows a specific structure. Let me break it down:

## Basic Error Structure

```python
Traceback (most recent call last):          ← Header
  File "path/to/file.py", line 10           ← Location
    some_code_here()                        ← Code that failed
    ^^^^^^^^^^^^^^^                         ← Visual indicator (Python 3.11+)
ErrorType: Error message                    ← The actual error
```

## Reading Errors: Top to Bottom vs Bottom to Top

### Strategy 1: Read Bottom-Up (Recommended for Beginners)

**Start at the BOTTOM** - that's where the actual error is:

```python
Traceback (most recent call last):
  File "gateway.py", line 74
    response = predict(url)
  File "gateway.py", line 57
    predict_request = prepare_request(X)
  File "gateway.py", line 29
    predict_request.inputs["input_8"].CopyFrom(np_to_protobuf(X))
  File "proto.py", line 26
    return make_tensor_proto(data)
  File "proto.py", line 18
    tensor_proto.tensor_content = data.tostring()
                                  ^^^^^^^^^^^^^
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
                 ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                 THIS IS THE ACTUAL PROBLEM!
```

**What I see at the bottom:**

1. **Error Type**: `AttributeError`
2. **What failed**: `'numpy.ndarray' object has no attribute 'tostring'`
3. **Where it failed**: `proto.py`, line 18
4. **The problematic code**: `data.tostring()`

### Strategy 2: Read Top-Down (For Understanding Flow)

Once you know the error, read top-down to understand HOW you got there:

```python
1. gateway.py, line 74: response = predict(url)
   ↓ predict() was called
   
2. gateway.py, line 57: predict_request = prepare_request(X)
   ↓ prepare_request() was called
   
3. gateway.py, line 29: predict_request.inputs["input_8"].CopyFrom(np_to_protobuf(X))
   ↓ np_to_protobuf() was called
   
4. proto.py, line 26: return make_tensor_proto(data)
   ↓ make_tensor_proto() was called
   
5. proto.py, line 18: tensor_proto.tensor_content = data.tostring()
   ↓ BOOM! Error happened here
```

This is called the **call stack** - it shows the chain of function calls.

## Common Error Types and How to Identify Them

### 1. AttributeError

```python
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
```

**What it means:** You're trying to use a method/attribute that doesn't exist on that object.

**How to identify:**

- Error type: `AttributeError`
- Pattern: `'ObjectType' object has no attribute 'method_name'`
- **Root cause**: The method was removed, renamed, or never existed

**Solution approach:**

- Check the documentation for the correct method name
- Check if the method was deprecated (like `tostring()` → `tobytes()`)
- Verify you're using the right object type

### 2. ImportError / ModuleNotFoundError

```python
ImportError: cannot import name 'predict_pb2' from 'tensorflow_serving.apis'
```

**What it means:** Python can't find the module or specific item you're trying to import.

**How to identify:**

- Error type: `ImportError` or `ModuleNotFoundError`
- Pattern: `cannot import name 'X' from 'Y'` or `No module named 'X'`
- **Root cause**: Package not installed, wrong version, or broken installation

**Solution approach:**

- Check if package is installed: `pip list | grep package_name`
- Reinstall the package
- Check for version compatibility

### 3. TypeError

```python
TypeError: Descriptors cannot be created directly.
```

**What it means:** You're using a value of the wrong type, or calling something incorrectly.

**How to identify:**

- Error type: `TypeError`
- Often mentions "expected X, got Y"
- **Root cause**: Version mismatch, wrong argument types, or API changes

**Solution approach:**

- Check function signature and argument types
- Look for version compatibility issues
- Read the full error message for hints

### 4. NameError

```python
NameError: name 'grpc' is not defined
```

**What it means:** You're using a variable/module that hasn't been defined or imported.

**How to identify:**

- Error type: `NameError`
- Pattern: `name 'X' is not defined`
- **Root cause**: Missing import or typo

**Solution approach:**

- Add the missing import
- Check for typos
- Verify the variable exists in that scope

### 5. FileNotFoundError

```python
FileNotFoundError: [Errno 2] No such file or directory: 'model.h5'
```

**What it means:** Python can't find the file at the specified path.

**How to identify:**

- Error type: `FileNotFoundError`
- Shows the path it's looking for
- **Root cause**: Wrong path, file doesn't exist, or working directory issue

**Solution approach:**

- Check if file exists: `ls` or `dir`
- Verify the path is correct
- Check current working directory

## My Error Analysis Process

When I see an error, here's my mental checklist:

### Step 1: Read the Bottom Line

```python
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
```

✅ **Error Type**: AttributeError  
✅ **Object**: numpy.ndarray  
✅ **Problem**: Method 'tostring' doesn't exist  

### Step 2: Find the Exact Location

```python
  File "proto.py", line 18
    tensor_proto.tensor_content = data.tostring()
                                  ^^^^^^^^^^^^^
```

✅ **File**: proto.py  
✅ **Line**: 18  
✅ **Code**: `data.tostring()`  

### Step 3: Understand the Context

```python
  File "gateway.py", line 29
    predict_request.inputs["input_8"].CopyFrom(np_to_protobuf(X))
  File "proto.py", line 26
    return make_tensor_proto(data)
```

✅ **Context**: Converting numpy array to protobuf  
✅ **Flow**: gateway.py → proto.py → error  

### Step 4: Identify the Root Cause

- `tostring()` doesn't exist → Check NumPy documentation
- Search: "numpy tostring deprecated"
- **Finding**: `tostring()` was removed in NumPy 1.20+, replaced with `tobytes()`

### Step 5: Apply the Fix

```python
# Old (broken):
tensor_proto.tensor_content = data.tostring()

# New (fixed):
tensor_proto.tensor_content = data.tobytes()
```

## Visual Guide to Your Recent Errors

### Error 1: grpc.insecure_channel

```python
AttributeError: module 'grpc' has no attribute 'insecure_channel'
                ^^^^^^        ^^^^
                What?         What attribute?
```

**My analysis:**

- **Type**: AttributeError (method missing)
- **Object**: grpc module
- **Missing**: insecure_channel
- **Diagnosis**: Package installation issue (wrong or broken grpc package)

### Error 2: protobuf descriptors

```python
TypeError: Descriptors cannot be created directly.
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           What's wrong?
```

**My analysis:**

- **Type**: TypeError (wrong way of doing something)
- **Key phrase**: "regenerated with protoc >= 3.19.0"
- **Diagnosis**: Version incompatibility (protobuf too new)

### Error 3: numpy.tostring()

```python
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
                 ^^^^^^^^^^^^^^                         ^^^^^^^^
                 What object?                           What's missing?
```

**My analysis:**

- **Type**: AttributeError (method missing)
- **Object**: numpy array
- **Missing**: tostring
- **Diagnosis**: Deprecated method (NumPy version too new)

## Pro Tips for Error Reading

### 1. Look for Keywords

Certain words tell you immediately what's wrong:

- **"cannot import"** → Installation/import issue
- **"has no attribute"** → Wrong method name or version
- **"is not defined"** → Missing import or typo
- **"expected X, got Y"** → Wrong type
- **"deprecated"** → Update your code
- **"regenerate"** / "out of date"** → Version mismatch

### 2. Use the Visual Indicators (Python 3.11+)

```python
    tensor_proto.tensor_content = data.tostring()
                                  ^^^^^^^^^^^^^
```

The `^^^^^` shows EXACTLY what part failed!

### 3. Check Line Numbers Carefully

```python
  File "gateway.py", line 74, in <module>
    response = predict(url)
               ^^^^^^^^^^^^
```

- **Line 74** is where the error was triggered
- But the actual bug might be deeper in the call stack

### 4. Read the Full Message

Sometimes the error message contains the solution:

```python
If you cannot immediately regenerate your protos, some other possible workarounds are:  
 1. Downgrade the protobuf package to 3.20.x or lower.
```

**The error literally tells you what to do!**

### 5. Google Strategically

Don't copy the entire traceback. Google the key parts:

❌ Bad: "Traceback most recent call last File gateway.py..."  
✅ Good: "numpy ndarray has no attribute tostring"  
✅ Better: "numpy tostring deprecated replacement"

## Practice Exercise

Let's analyze this error together:

```python
Traceback (most recent call last):
  File "app.py", line 45, in process_data
    result = model.predict(data)
  File "model.py", line 23, in predict
    features = self.extract_features(data)
  File "model.py", line 67, in extract_features
    normalized = data / self.scaler.mean_
                       ^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'mean_'
```

**Your turn - try to analyze:**

1. What type of error? `AttributeError`
2. What's the object? `NoneType` (which means `None`)
3. What's missing? `mean_` attribute
4. Where's the problem? `model.py`, line 67
5. What's the real issue? `self.scaler` is `None` (probably not initialized)
6. How to fix? Initialize or load the scaler before using it

## Summary: The 5-Second Error Analysis

1. **Bottom line** → What broke?
2. **Error type** → Category of problem
3. **File + Line** → Exact location
4. **Keywords** → Clues to solution
5. **Context** → Why did this happen?

With practice, you'll be able to diagnose errors in seconds just by glancing at the bottom line and recognizing patterns

---

## **What is gRPC?**

## Overview

**gRPC** (gRPC Remote Procedure Call) is a modern, high-performance framework developed by Google for enabling communication between services. It allows programs to call functions on other machines as if they were local function calls.

Think of it like making a phone call: you dial a number (connect to a service), ask for something (make a request), and get an answer back (receive a response) - all without worrying about the underlying network details.

## Key Concepts

### Remote Procedure Call (RPC)

RPC lets you execute a function on a remote server as if it were a local function:

```python
# Instead of making HTTP requests manually:
response = requests.post('http://server.com/predict', json={'data': [1,2,3]})

# With gRPC, it feels like calling a local function:
result = prediction_service.Predict(request)
```

### Protocol Buffers (protobuf)

gRPC uses Protocol Buffers as its data format - a binary serialization format that's:

- **Smaller** than JSON (faster network transfer)
- **Faster** to serialize/deserialize
- **Strongly typed** (defines exact data structures)

Example protobuf definition:

```protobuf
message PredictRequest {
  string model_name = 1;
  repeated float input_data = 2;
}

message PredictResponse {
  repeated float predictions = 1;
}
```

## How gRPC Works

```python
Client Application                    Server Application
       |                                     |
       |  1. Create gRPC request             |
       |------------------------------------>|
       |                                     |
       |  2. Serialize using protobuf        |
       |     (binary format)                 |
       |                                     |
       |  3. Send over HTTP/2                |
       |====================================>|
       |                                     |
       |                          4. Deserialize request
       |                          5. Execute function
       |                          6. Serialize response
       |                                     |
       |  7. Send response back              |
       |<====================================|
       |                                     |
       |  8. Deserialize response            |
       |  9. Use the data                    |
```

## Why Use gRPC?

### 1. **Performance**

- **Binary format**: Much smaller and faster than JSON
- **HTTP/2**: Multiplexing, header compression, persistent connections
- **Streaming**: Efficient for real-time data

**Comparison:**

```python
JSON over HTTP/1.1:  {"name": "John", "age": 30, "city": "NYC"}  (45 bytes)
Protobuf over HTTP/2: [binary data]                              (~10 bytes)
```

### 2. **Strongly Typed**

The API contract is defined in `.proto` files, ensuring both client and server agree on data structures:

```protobuf
service PredictionService {
  rpc Predict(PredictRequest) returns (PredictResponse);
}
```

This prevents common errors like typos in field names or wrong data types.

### 3. **Language Agnostic**

Write your server in Python and client in Go, Java, C++, or 50+ other languages:

```python
# Python server
def Predict(request):
    return PredictResponse(predictions=[0.8, 0.2])
```

```javascript
// JavaScript client
const response = await client.predict(request);
console.log(response.predictions);
```

### 4. **Built-in Features**

- **Authentication** (SSL/TLS, token-based)
- **Load balancing**
- **Timeouts and deadlines**
- **Streaming** (client, server, bidirectional)
- **Error handling**

## gRPC vs REST API

| Feature             | gRPC                     | REST                  |
|---------------------|--------------------------|-----------------------|
| **Protocol**        | HTTP/2                   | HTTP/1.1 (typically)  |
| **Data Format**     | Protobuf (binary)        | JSON (text)           |
| **Speed**           | Very fast                | Slower                |
| **Size**            | Small                    | Larger                |
| **Streaming**       | Built-in                 | Limited               |
| **Browser Support** | Limited (needs proxy)    | Full                  |
| **Human Readable**  | No (binary)              | Yes (JSON)            |
| **Code Generation** | Automatic                | Manual or via tools   |
| **Best For**        | Microservices, real-time | Public APIs, web apps |

## Real-World Example: Your TensorFlow Serving Code

In your `gateway.py`, you're using gRPC to communicate with TensorFlow Serving:

```python
# 1. Create a channel (connection) to TensorFlow Serving
host = "localhost:8500"
channel = grpc.insecure_channel(host)

# 2. Create a stub (client) for the prediction service
prediction_service_stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# 3. Prepare a request using protobuf
predict_request = predict_pb2.PredictRequest()
predict_request.model_spec.name = "clothing-model"
predict_request.inputs["input_8"].CopyFrom(make_tensor_proto(X))

# 4. Call the remote Predict function (feels like local call!)
predict_response = prediction_service_stub.Predict(predict_request, timeout=20.0)

# 5. Use the response
predictions = predict_response.outputs["dense_7"].float_val
```

**What's happening:**

1. Your Python gateway connects to TensorFlow Serving (running separately)
2. It sends image data as a protobuf message
3. TensorFlow Serving processes it and returns predictions
4. All communication is fast, efficient, and type-safe

**Architecture:**

```python
User Browser
    |
    | HTTP/JSON (REST)
    v
Flask Gateway (Python)
    |
    | gRPC/Protobuf (efficient!)
    v
TensorFlow Serving (C++)
    |
    v
ML Model (makes prediction)
```

## Types of gRPC Communication

### 1. Unary RPC (Request-Response)

One request, one response - like your prediction service:

```python
response = stub.Predict(request)
```

### 2. Server Streaming

Client sends one request, server sends multiple responses:

```python
# Stock price updates
for price_update in stub.StreamPrices(request):
    print(price_update)
```

### 3. Client Streaming

Client sends multiple requests, server sends one response:

```python
# Upload large file in chunks
response = stub.UploadFile(chunk_generator())
```

### 4. Bidirectional Streaming

Both send multiple messages (like chat):

```python
# Real-time chat
for message in stub.Chat(message_generator()):
    print(message)
```

## When to Use gRPC

✅ **Good For:**

- Microservices communication (internal services)
- Real-time applications (streaming data)
- Mobile apps (battery efficiency)
- Polyglot environments (multiple languages)
- High-performance requirements
- ML model serving (like TensorFlow Serving)

❌ **Not Ideal For:**

- Public web APIs (limited browser support)
- Simple CRUD applications
- When human-readable data is important
- When you need to debug easily in browser

## Popular Use Cases

1. **Google**: Uses gRPC for almost all internal services (millions of RPCs per second)
2. **Netflix**: Microservices communication
3. **Square**: Payment processing
4. **Cisco**: Network management
5. **Machine Learning**: TensorFlow Serving, PyTorch Serve

## Summary_

gRPC is like a **super-efficient telephone system** for services to talk to each other:

- Uses a **compact binary language** (protobuf) instead of verbose text (JSON)
- Works over **modern phone lines** (HTTP/2) instead of old ones (HTTP/1.1)
- Has **built-in features** like call waiting, conferencing (streaming), and caller ID (authentication)
- **Faster, smaller, and more reliable** than traditional REST APIs

In your case, it allows your Python Flask app to communicate efficiently with TensorFlow Serving, sending images and receiving predictions with minimal overhead

---

## **Debugging: AttributeError: module 'grpc' has no attribute 'insecure_channel'**

## Error Message

```python
File "gateway.py", line 13, in <module>       
    channel = grpc.insecure_channel(host)
              ^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'grpc' has no attribute 'insecure_channel'
```

## Why This Error Occurs

This error happens when Python imports a `grpc` module that doesn't contain the expected attributes from the `grpcio` package. There are several possible causes:

### 1. **Wrong Package Installed**

- There's an old, abandoned package called `grpc` (different from `grpcio`)
- If `grpc` is installed, it shadows the correct `grpcio` package
- The `grpc` package is a namespace package with no actual functionality

### 2. **Corrupted or Incomplete Installation**

- `grpcio` package didn't install correctly
- Native extensions failed to compile or weren't included
- Cached files from a previous broken installation

### 3. **File Naming Conflict**

- A local file named `grpc.py` in your project directory
- Python imports the local file instead of the installed package

### 4. **Package Manager Issues (UV-specific)**

- UV (ultra-fast Python package manager) sometimes has issues with native extensions
- UV's caching mechanism can cause incomplete installations on Windows
- Binary wheel compatibility issues with certain Python versions

## Diagnostic Steps

### Step 1: Check What's Being Imported

```bash
python -c "import grpc; print(grpc.__file__); print(dir(grpc))"
```

**What to look for:**

- `__file__` should point to a real file path (e.g., `site-packages\grpc\__init__.py`)
- `dir(grpc)` should show many attributes including `insecure_channel`

**Problem indicators:**

- `__file__ = None` → Namespace package conflict
- Very few attributes in `dir(grpc)` → Broken installation
- `__file__` points to your project directory → Local file conflict

### Step 2: Check Installed Packages

```bash
# Windows
pip list | findstr grpc

# Expected output:
# grpcio                    1.76.0
# grpcio-tools              1.76.0
```

**Problem indicators:**

- A package literally named `grpc` (not `grpcio`)
- Missing `grpcio` entirely

### Step 3: Verify the Attribute Exists

```bash
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
```

Should print `True`.

## Solutions_

### Solution 1: Remove Conflicting `grpc` Package

If you have a package named `grpc` installed:

```bash
# Standard pip
pip uninstall grpc -y
pip uninstall grpcio grpcio-tools -y
pip install grpcio grpcio-tools

# Using UV
uv pip uninstall grpc
uv pip uninstall grpcio grpcio-tools
uv pip install grpcio grpcio-tools --reinstall
```

### Solution 2: Force Reinstall with No Cache

This clears any corrupted cached files:

```bash
# Standard pip
pip uninstall grpcio grpcio-tools -y
pip install --no-cache-dir grpcio grpcio-tools

# Using UV
uv pip uninstall grpcio grpcio-tools
uv pip install grpcio grpcio-tools --reinstall --no-cache
```

### Solution 3: Check for Local File Conflicts

```bash
# Windows - check current directory
dir grpc.py

# If exists, rename or delete it
ren grpc.py grpc_old.py
```

Also check your Python site-packages:

```bash
python -c "import site; print(site.getsitepackages())"
```

Navigate to that directory and look for unexpected `grpc.py` files.

### Solution 4: UV-Specific Fix (Windows)

UV sometimes fails to install native extensions properly on Windows:

```bash
# Option A: Use --no-binary flag
uv pip uninstall grpcio grpcio-tools
uv pip install grpcio grpcio-tools --no-binary grpcio

# Option B: Fallback to pip for grpcio
pip install grpcio grpcio-tools --force-reinstall
# Then continue using UV for other packages
```

### Solution 5: Fresh Virtual Environment

If all else fails, create a clean environment:

```bash
# Create new virtual environment
python -m venv venv_clean

# Activate it
# Windows Command Prompt:
venv_clean\Scripts\activate
# Windows PowerShell:
.\venv_clean\Scripts\activate

# Install packages fresh
pip install grpcio grpcio-tools tensorflow-serving-api keras-image-helper flask tensorflow
```

## Complete Requirements

For your TensorFlow Serving gateway, you need these packages:

```txt
grpcio==1.76.0
grpcio-tools==1.76.0
tensorflow-serving-api==2.19.1
keras-image-helper==0.0.1
flask==3.0.0
tensorflow==2.20.0
```

Install with:

```bash
pip install -r requirements.txt
# or
uv pip install -r requirements.txt
```

## Verification

After applying the solution, verify everything works:

```bash
# Test 1: Check file location
python -c "import grpc; print(grpc.__file__)"
# Should show: path\to\site-packages\grpc\__init__.py

# Test 2: Check attribute exists
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
# Should print: True

# Test 3: List all grpc attributes
python -c "import grpc; print([x for x in dir(grpc) if not x.startswith('_')])"
# Should show many functions including insecure_channel
```

## Why UV Specifically Had Issues

In this case, UV was the package manager being used, and it had trouble with `grpcio` on Windows because:

1. **Native Extensions**: `grpcio` contains C++ extensions that need to be compiled or properly extracted from binary wheels
2. **Caching Issues**: UV's aggressive caching sometimes keeps broken installations
3. **Binary Compatibility**: UV may select incompatible binary wheels for certain Windows/Python combinations

The `--reinstall --no-cache` flags force UV to download fresh packages and skip its cache, which resolved the issue.

## Key Takeaway

The error occurs because Python imports a `grpc` module that lacks the expected functionality. The solution is always to ensure `grpcio` (not `grpc`) is properly installed with all its native extensions, and that no conflicting packages or files are shadowing it.
----Great question! Let me explain how to read and identify Python errors systematically.I've created a comprehensive guide on how to read Python errors! Here's the quick summary of my process:

## My Mental Checklist When I See an Error

1. **Read the BOTTOM line first** - that's the actual error
2. **Identify the error type** - AttributeError, ImportError, TypeError, etc.
3. **Find the exact location** - which file and line number
4. **Look for keywords** - "has no attribute", "cannot import", "deprecated", etc.
5. **Trace the call stack** (top-down) - understand how we got there
6. **Apply pattern matching** - I've seen these errors before!

## For Your Recent Error

```python
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
```

I immediately saw:

- **Type**: `AttributeError` (method doesn't exist)
- **Object**: `numpy.ndarray`
- **Missing**: `tostring()`
- **My knowledge**: "I know `tostring()` was deprecated in NumPy!"
- **Solution**: Replace with `tobytes()`

The key is **pattern recognition** - after seeing hundreds of errors, you start recognizing common patterns instantly. The guide shows you how to build that skill

---

The error is clear: **TensorFlow 2.20.0 doesn't support Python 3.14 yet**. TensorFlow only has wheels for Python 3.11, 3.12, and 3.13.

## Solution: Use a Compatible Python Version

You need to use Python 3.11, 3.12, or 3.13 in your Docker image.

### Option 1: Update Your Dockerfile to Use Python 3.12

Change the base image in your `image-gateway.dockerfile`:

```dockerfile
# Change from Python 3.14 to 3.12
FROM python:3.12-slim

# Rest of your Dockerfile...
```

### Option 2: Update to Python 3.13

```dockerfile
FROM python:3.13-slim
```

### Option 3: Use Python 3.11 (Most Stable for ML)

```dockerfile
FROM python:3.11-slim
```

## Full Dockerfile Example

Here's what your `image-gateway.dockerfile` should look like:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy uv lockfile and pyproject.toml
COPY pyproject.toml uv.lock ./

# Install uv
RUN pip install uv

# Install required packages using uv
RUN uv sync --locked

# Copy gateway and protobuf scripts in the working dir
COPY gateway.py proto.py ./

# Expose the Flask port
EXPOSE 9696

# Run the gateway
CMD ["uv", "run", "python", "gateway.py"]
```

## If You Want to Update Your Local Environment Too

```bash
# Check your current Python version
python --version

# If you're using Python 3.14 locally, you'll need to downgrade or use a virtual environment with an older version
```

### Using UV to Specify Python Version

If you have multiple Python versions installed:

```bash
# Create venv with specific Python version
uv venv --python 3.12

# Activate and install
.\.venv\Scripts\activate
uv pip install -r requirements.txt
```

## Recommended: Python 3.12

Python 3.12 is the sweet spot right now:

- ✅ Supported by TensorFlow 2.20.0
- ✅ Stable and well-tested
- ✅ Good performance improvements over 3.11
- ✅ Not bleeding edge like 3.14

Change your Dockerfile base image to `python:3.12-slim` and rebuild

---

There are several issues with your Dockerfile:

1. **Python 3.8.12 is too old** - TensorFlow 2.20.0 requires Python 3.11+
2. **Wrong ENTRYPOINT** - You're using `uvicorn` (for FastAPI) but your app uses Flask
3. **Wrong syntax** - `--bind` is gunicorn syntax, not uvicorn

## Fixed Dockerfile

```dockerfile
FROM python:3.12-slim

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create working directory in docker image
WORKDIR /app

# Copy dependency files
COPY ["pyproject.toml", "uv.lock", "./"]

# Install required packages using uv
RUN uv sync --locked

# Copy application files
COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

# Run Flask app with uv
ENTRYPOINT ["uv", "run", "python", "gateway.py"]
```

## Key Changes

1. **`FROM python:3.12-slim`** - Compatible with TensorFlow 2.20.0
2. **`ENTRYPOINT ["uv", "run", "python", "gateway.py"]`** - Runs your Flask app correctly

## Alternative: If You Want to Use Gunicorn (Production)

For production deployments, you might want to use Gunicorn:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

# Use gunicorn for production
ENTRYPOINT ["uv", "run", "gunicorn", "--bind=0.0.0.0:9696", "gateway:app"]
```

But make sure to add `gunicorn` to your `pyproject.toml` dependencies.

## If You Want to Keep Using Flask's Built-in Server

Update your `gateway.py` to uncomment the Flask run line:

```python
if __name__ == "__main__":
    # Comment out test code
    # url = "http://bit.ly/mlbookcamp-pants"
    # response = predict(url)
    # print(response)
    
    # Run Flask app
    app.run(debug=False, host="0.0.0.0", port=9696)
```

And use this Dockerfile:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

ENTRYPOINT ["uv", "run", "python", "gateway.py"]
```

## Build and Run

```bash
# Build the image
docker build -t gateway-app -f image-gateway.dockerfile .

# Run the container
docker run -p 9696:9696 gateway-app
```

The main fix is changing `python:3.8.12-slim` to `python:3.12-slim`

---

The error means `gunicorn` is not installed in your Docker image. You have two options:

## Option 1: Use Flask's Built-in Server (Simpler)

Update your Dockerfile:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

# Run with Flask's built-in server
ENTRYPOINT ["uv", "run", "python", "gateway.py"]
```

And update your `gateway.py` to enable the Flask server:

```python
if __name__ == "__main__":
    # Remove or comment out test code
    # url = "http://bit.ly/mlbookcamp-pants"
    # response = predict(url)
    # print(response)
    
    # Run Flask app
    app.run(debug=False, host="0.0.0.0", port=9696)
```

## Option 2: Add Gunicorn (Production-Ready)

### Step 1: Add gunicorn to your `pyproject.toml`

```toml
[project]
dependencies = [
    "grpcio",
    "flask",
    "keras-image-helper",
    "tensorflow",
    "tensorflow-serving-api",
    "gunicorn",  # Add this
    # ... other dependencies
]
```

### Step 2: Update lockfile

```bash
uv lock
```

### Step 3: Keep your Dockerfile with gunicorn

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

ENTRYPOINT ["uv", "run", "gunicorn", "--bind=0.0.0.0:9696", "gateway:app"]
```

## Recommendation: Use Option 1 (Flask) for Now

For development and testing, Flask's built-in server is fine. Use the first option with:

```dockerfile
ENTRYPOINT ["uv", "run", "python", "gateway.py"]
```

Then rebuild and run:

```bash
# Rebuild
docker build -t gateway-app -f image-gateway.dockerfile .

# Run
docker run -p 9696:9696 gateway-app
```

This should work immediately without needing to modify dependencies

---

The error shows that `tensorflow-serving-api` is not installed in your Docker container, even though `uv sync --locked` ran.

## Issue: UV Virtual Environment Path

When you run `uv sync`, it installs packages in `.venv`, but gunicorn might not be using that virtual environment correctly.

## Solution: Use UV Run to Execute Gunicorn

Update your Dockerfile ENTRYPOINT to use `uv run`:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY ["gateway.py", "proto.py", "./"]

EXPOSE 9696

# Use 'uv run' to ensure it uses the correct virtual environment
ENTRYPOINT ["uv", "run", "gunicorn", "--bind=0.0.0.0:9696", "gateway:app"]
```

The key change is adding `uv run` before `gunicorn`, which ensures gunicorn runs within the UV-managed virtual environment where all packages are installed.

## Rebuild and Run

```bash
# Rebuild the image
docker build -t gateway-app -f image-gateway.dockerfile .

# Run the container
docker run -p 9696:9696 gateway-app
```

## Alternative: If That Still Doesn't Work

Check your `pyproject.toml` to ensure all dependencies are listed:

```toml
[project]
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "tensorflow-serving-api>=2.14.0",  # Make sure this is here
    "keras-image-helper>=0.0.1",
    "flask>=3.0.0",
    "tensorflow>=2.14.0",
    "gunicorn>=23.0.0",
    "protobuf==3.20.3",  # Important for compatibility
]
```

Then regenerate the lockfile:

```bash
uv lock
```

And rebuild the Docker image.

The `uv run` prefix is crucial - it activates the virtual environment automatically before running gunicorn

---

Good! You already have `uv run` in your ENTRYPOINT. The issue is that `tensorflow-serving-api` isn't installed in the container.

## Check Your pyproject.toml

Make sure `tensorflow-serving-api` is listed in your dependencies. Share your `pyproject.toml` file, or check if it has this:

```toml
[project]
name = "your-project"
version = "0.1.0"
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "tensorflow-serving-api>=2.14.0",  # <-- Must be here
    "keras-image-helper>=0.0.1",
    "flask>=3.0.0",
    "tensorflow>=2.14.0",
    "gunicorn>=23.0.0",
    "protobuf==3.20.3",
]
```

## If tensorflow-serving-api is Missing

Add it to your `pyproject.toml`:

```bash
uv add tensorflow-serving-api==2.14.0
```

This will:

1. Add it to `pyproject.toml`
2. Update `uv.lock`

## If It's Already There

The `uv.lock` file might be out of sync. Regenerate it:

```bash
# Remove old lockfile
rm uv.lock

# Regenerate
uv lock

# Rebuild Docker image
docker build -t gateway-app -f image-gateway.dockerfile .

# Run
docker run -p 9696:9696 gateway-app
```

## Debug: Check What's in the Container

To see what's actually installed in your container:

```bash
# Build the image
docker build -t gateway-app -f image-gateway.dockerfile .

# Run interactively to debug
docker run -it gateway-app /bin/bash

# Inside the container, check packages
uv pip list | grep tensorflow
```

Can you share your `pyproject.toml` file? That will help me see what's missing
-----

Perfect! Your gateway is working, but it **can't connect to TensorFlow Serving** because TensorFlow Serving isn't running or isn't accessible at `localhost:8500`.

## The Problem

Your gateway is trying to connect to:

```python
host = "localhost:8500"
```

But inside a Docker container, `localhost` refers to the container itself, not your host machine.

## Solutions

### Solution 1: Use Docker Host Network (Simplest)

If TensorFlow Serving is running on your host machine:

```bash
# Run with host network mode
docker run --network="host" gateway-app
```

This makes the container use your host's network, so `localhost:8500` will work.

### Solution 2: Use host.docker.internal (Recommended)

Update your `gateway.py` to use `host.docker.internal` instead of `localhost`:

```python
# Change this line:
host = "localhost:8500"

# To this:
host = "host.docker.internal:8500"
```

Then rebuild and run:

```bash
docker build -t gateway-app -f image-gateway.dockerfile .
docker run -p 9696:9696 gateway-app
```

### Solution 3: Run Both in Docker Network (Best Practice)

Create a Docker network and run both services in it:

```bash
# Create a network
docker network create ml-network

# Run TensorFlow Serving
docker run -d \
  --name tf-serving \
  --network ml-network \
  -p 8500:8500 \
  -v /path/to/your/model:/models/clothing-model \
  tensorflow/serving \
  --model_name=clothing-model

# Update gateway.py host to:
# host = "tf-serving:8500"

# Run gateway
docker run -d \
  --name gateway \
  --network ml-network \
  -p 9696:9696 \
  gateway-app
```

### Solution 4: Use Environment Variable (Most Flexible)

Update `gateway.py` to use an environment variable:

```python
import os

# Use environment variable with fallback
host = os.getenv("TF_SERVING_HOST", "localhost:8500")
channel = grpc.insecure_channel(host)
```

Then run with:

```bash
# For local TensorFlow Serving
docker run -p 9696:9696 -e TF_SERVING_HOST="host.docker.internal:8500" gateway-app

# Or if using Docker network
docker run -p 9696:9696 -e TF_SERVING_HOST="tf-serving:8500" gateway-app
```

## Quick Fix: Use Host Network

The fastest way to test right now:

```bash
docker run --network="host" gateway-app
```

Then test your endpoint:

```bash
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://bit.ly/mlbookcamp-pants"}'
```

## Is TensorFlow Serving Running?

First, verify TensorFlow Serving is actually running:

```bash
# Check if port 8500 is listening
netstat -an | findstr 8500

# Or try connecting from your host
curl http://localhost:8500/v1/models/clothing-model
```

If TensorFlow Serving isn't running, you need to start it first. Let me know which solution you want to use, and I can help you set it up properly

---

Perfect! Both containers are running. The issue is that they're on **separate networks** and can't communicate with each other.

## Solution: Connect Both Containers to the Same Network

### Step 1: Create a Docker Network

```bash
docker network create ml-network
```

### Step 2: Stop Both Containers

```bash
docker stop 399a7f919029 08c2601d0558
```

### Step 3: Run TensorFlow Serving on the Network

```bash
docker run -d \
  --name tf-serving \
  --network ml-network \
  -p 8500:8500 \
  clothing-model:xception-v4-001
```

### Step 4: Update gateway.py

Change the host in your `gateway.py`:

```python
# Change from:
host = "localhost:8500"

# To:
host = "tf-serving:8500"
```

### Step 5: Rebuild Gateway Image

```bash
docker build -t clothing-model-gateway:001 -f image-gateway.dockerfile .
```

### Step 6: Run Gateway on the Same Network

```bash
docker run -d \
  --name gateway \
  --network ml-network \
  -p 9696:9696 \
  clothing-model-gateway:001
```

### Step 7: Test

```bash
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://bit.ly/mlbookcamp-pants"}'
```

## Alternative: Quick Fix Without Rebuilding

If you don't want to rebuild, you can connect the existing containers to the same network:

```bash
# Create network
docker network create ml-network

# Connect both containers to the network
docker network connect ml-network angry_mendeleev
docker network connect ml-network epic_jemison

# Restart gateway to pick up network changes
docker restart epic_jemison
```

But you still need to update `gateway.py` to use `angry_mendeleev:8500` instead of `localhost:8500`.

## Better: Use Environment Variable (Recommended)

Update your `gateway.py` to be flexible:

```python
import os

# Use environment variable
host = os.getenv("TF_SERVING_HOST", "localhost:8500")
channel = grpc.insecure_channel(host)
```

Rebuild the image, then run:

```bash
docker run -d \
  --name gateway \
  --network ml-network \
  -p 9696:9696 \
  -e TF_SERVING_HOST="tf-serving:8500" \
  clothing-model-gateway:001
```

This way you don't need to hardcode the hostname!

**Try the network approach - it's the proper way to connect Docker containers!**

---

## **Docker Container Networking Guide: TensorFlow Serving & Jupyter**

A comprehensive guide to running TensorFlow Serving and Jupyter Notebook in separate Docker containers and connecting them properly.

---

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Common Errors & Solutions](#common-errors--solutions)
3. [Best Practices](#best-practices)
4. [Complete Working Example](#complete-working-example)

---

## Initial Setup

### Starting TensorFlow Serving Container

```bash
docker run -d \
  --name tf-serving \
  -p 8500:8500 \
  -p 8501:8501 \
  -v /path/to/your/models:/models \
  -e MODEL_NAME=your_model \
  tensorflow/serving:2.7.0
```

### Starting Jupyter Notebook Container

**Windows Command Prompt (CMD):**

```bash
docker run -it --rm \
  --name jupyter-client \
  -v "%cd%:/tf/notebooks" \
  -p 8888:8888 \
  tensorflow/tensorflow:latest-jupyter
```

**Windows PowerShell:**

```powershell
docker run -it --rm `
  --name jupyter-client `
  -v "${pwd}:/tf/notebooks" `
  -p 8888:8888 `
  tensorflow/tensorflow:latest-jupyter
```

**Git Bash (Windows):**

```bash
docker run -it --rm \
  --name jupyter-client \
  -v "$(pwd):/tf/notebooks" \
  -p 8888:8888 \
  tensorflow/tensorflow:latest-jupyter
```

**Linux/Mac:**

```bash
docker run -it --rm \
  --name jupyter-client \
  -v "$(pwd):/tf/notebooks" \
  -p 8888:8888 \
  tensorflow/tensorflow:latest-jupyter
```

---

## Common Errors & Solutions

### Error 1: grpcio Installation Failed on Windows

#### Error Message_

```python
DistutilsPlatformError: Microsoft Visual C++ 14.0 or greater is required.
Get it with "Microsoft C++ Build Tools"
```

#### Problem

The `grpcio` package requires C++ compiler to build from source on Windows, but it's not installed.

#### Solutions__

**Option A: Use Pre-built Binary (Recommended)**_

```bash
pip install --upgrade pip
pip install grpcio --only-binary grpcio
```

**Option B: Install Build Tools**_

1. Download [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install with "Desktop development with C++" workload
3. Restart terminal and retry installation

---

### Error 2: Connection Refused - IPv6 Issue

#### Error Message__

```python
_InactiveRpcError: failed to connect to all addresses
last error: UNKNOWN: ipv6:[::1]:8500: Connection refused (111)
```

#### Problem_

gRPC is trying to connect via IPv6, but the server might not be listening on IPv6, or there's a networking issue.

#### Solution

Force IPv4 connection by using `127.0.0.1` instead of `localhost`:

```python
# ❌ Don't use this
channel = grpc.insecure_channel('localhost:8500')

# ✅ Use this instead
channel = grpc.insecure_channel('127.0.0.1:8500')
```

---

### Error 3: Connection Refused - Wrong Environment

#### Error Message___

```python
_InactiveRpcError: failed to connect to all addresses
last error: UNKNOWN: ipv4:127.0.0.1:8500: Connection refused (111)
```

#### Problem__

You're running the client inside a Docker container, and `127.0.0.1` refers to the **container itself**, not the host machine where the server is running.

#### Diagnosis_

Check if you're in a Docker container:

```python
import os
import platform

print("System:", platform.system())
if os.path.exists('/.dockerenv'):
    print("⚠️  Running inside Docker container")
    print("   'localhost' refers to THIS container, not the host")
```

#### Understanding Docker Networking

```docker
┌─────────────────────────────────────────────┐
│ Host Machine (Windows/Linux/Mac)            │
│                                             │
│  ┌────────────────────────────┐             │
│  │ Client Container           │             │
│  │ (Jupyter)                  │             │
│  │                            │             │
│  │ localhost:8500 ──► ❌      |            │
│  │ (looks inside container)   │            │
│  └────────────────────────────┘            │
│                                            │
│  ┌────────────────────────────┐            │
│  │ Server Container           │            │
│  │ (TF Serving)               │            │
│  │                            │            │
│  │ Port 8500 is HERE! ✓       │            │
│  └────────────────────────────┘            │
│                                            │
└────────────────────────────────────────────┘
```

#### Solutions___

-**Solution A: Use Docker Bridge Gateway (Quick Fix)**

The Docker bridge network gateway IP (`172.17.0.1`) allows containers to reach the host's exposed ports:

```python
import grpc
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Connect via Docker bridge gateway
channel = grpc.insecure_channel('172.17.0.1:8500')
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Test connection
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print("✓ Connected successfully!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

**How it works:**

```python
Client Container → 172.17.0.1:8500 (host gateway)
                 → Host machine's port 8500
                 → Mapped to Server Container
```

-**Solution B: Use Container Name (Best Practice)**

Connect both containers to the same Docker network, then use the server's container name:

```bash
# 1. Create a custom network
docker network create ml-network

# 2. Connect both containers
docker network connect ml-network tf-serving
docker network connect ml-network jupyter-client

# 3. Verify connection
docker network inspect ml-network
```

Now in your Jupyter notebook:

```python
# Use the server container's name
channel = grpc.insecure_channel('tf-serving:8500')
```

---

### Error 4: DNS Resolution Failed

#### Error Message____

```python
_InactiveRpcError: DNS resolution failed for gallant_brahmagupta:8500
C-ares status is not ARES_SUCCESS
Domain name not found
```

#### Problem____

Containers are on the **default bridge network**, which doesn't support DNS resolution by container name. Containers can only resolve each other's names when on a **user-defined network**.

#### Solution_

Connect containers to a user-defined network:

```bash
# Check existing containers
docker ps

# Create network
docker network create ml-network

# Connect both containers (use actual container names from 'docker ps')
docker network connect ml-network <server-container-name>
docker network connect ml-network <client-container-name>

# Verify both are connected
docker network inspect ml-network
```

Now you can use container names for connection:

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

#### Why This Happens_

| Network Type                  | DNS Resolution     | Use Case                                  |
|-------------------------------|--------------------|-------------------------------------------|
| Default Bridge (`bridge`)     | ❌ No DNS by name  | Legacy compatibility                      |
| User-defined Network          | ✅ DNS by name     | Modern best practice                      |

---

### Error 5: Volume Mount Path Issues (Windows)

#### Error Message_____

```python
Error: invalid reference format
or
Directory not found
```

#### Problem___

Using Unix/Linux path syntax on Windows, or using relative paths incorrectly.

#### Solutions by Shell

**Windows Command Prompt (CMD):**

```bash
# Current directory
docker run -v "%cd%:/tf/notebooks" ...

# Absolute path
docker run -v "D:\Learning\project:/tf/notebooks" ...
```

**Windows PowerShell:**

```powershell
# Current directory
docker run -v "${pwd}:/tf/notebooks" ...

# Absolute path
docker run -v "D:\Learning\project:/tf/notebooks" ...
```

**Git Bash (Windows):**

```bash
# Current directory
docker run -v "$(pwd):/tf/notebooks" ...

# Absolute path (note the /d/ format)
docker run -v "/d/Learning/project:/tf/notebooks" ...
```

**Linux/Mac:**

```bash
# Current directory
docker run -v "$(pwd):/tf/notebooks" ...

# Absolute path
docker run -v "/home/user/project:/tf/notebooks" ...
```

---

## Best Practices

### 1. Use Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  tf-serving:
    image: tensorflow/serving:2.7.0
    container_name: tf-serving
    ports:
      - "8500:8500"
      - "8501:8501"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=your_model
    networks:
      - ml-network

  jupyter:
    image: tensorflow/tensorflow:latest-jupyter
    container_name: jupyter-client
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/tf/notebooks
    depends_on:
      - tf-serving
    environment:
      - TF_SERVING_HOST=tf-serving
    networks:
      - ml-network

networks:
  ml-network:
    driver: bridge
```

Start everything:

```bash
docker-compose up -d
```

In your Jupyter notebook:

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

### 2. Connection Priority

Use this order when deciding how to connect:

1. **Container name** (if on same network) - `tf-serving:8500`
   - ✅ Fastest
   - ✅ Most readable
   - ✅ Survives restarts

2. **Docker bridge gateway** - `172.17.0.1:8500`
   - ✅ Works without network setup
   - ⚠️  Adds extra hop through host

3. **Container IP** - `172.17.0.2:8500`
   - ⚠️  IP changes on restart
   - ⚠️  Not recommended

### 3. Always Name Your Containers

```bash
# ✅ Good - named containers
docker run --name tf-serving ...
docker run --name jupyter-client ...

# ❌ Bad - random names like "gallant_brahmagupta"
docker run ...
```

---

## Complete Working Example_

### Step 1: Start Containers with Docker Compose

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  tf-serving:
    image: tensorflow/serving:2.7.0
    container_name: tf-serving
    ports:
      - "8500:8500"
      - "8501:8501"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=clothing-model
    command:
      - "--model_base_path=/models/clothing-model"
      - "--rest_api_port=8501"
    networks:
      - ml-network

  jupyter:
    image: tensorflow/tensorflow:latest-jupyter
    container_name: jupyter-client
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/tf/notebooks
    depends_on:
      - tf-serving
    networks:
      - ml-network

networks:
  ml-network:
    driver: bridge
```

**Start:**

```bash
docker-compose up -d
```

### Step 2: Connect from Jupyter Notebook

**Complete example notebook code:**

```python
import grpc
import numpy as np
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc

# Configuration
SERVER_HOST = 'tf-serving'  # Container name from docker-compose
SERVER_PORT = 8500
MODEL_NAME = 'clothing-model'
SIGNATURE_NAME = 'serving_default'

# Create gRPC channel
channel = grpc.insecure_channel(f'{SERVER_HOST}:{SERVER_PORT}')
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Test connection
print("Testing connection...")
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print(f"✓ Successfully connected to {SERVER_HOST}:{SERVER_PORT}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    raise

# Prepare prediction request
def predict(data):
    """
    Make a prediction using TensorFlow Serving
    
    Args:
        data: numpy array of shape (batch_size, height, width, channels)
    
    Returns:
        Prediction response
    """
    # Create request
    request = predict_pb2.PredictRequest()
    request.model_spec.name = MODEL_NAME
    request.model_spec.signature_name = SIGNATURE_NAME
    
    # Add input tensor
    request.inputs['input_8'].CopyFrom(
        tf.make_tensor_proto(data, dtype=tf.float32)
    )
    
    # Make prediction
    try:
        response = stub.Predict(request, timeout=20.0)
        return response
    except grpc.RpcError as e:
        print(f"Prediction failed: {e}")
        raise

# Example usage
print("\nMaking prediction...")
# Assuming input shape is (1, 299, 299, 3) for your model
sample_data = np.random.random((1, 299, 299, 3)).astype(np.float32)

response = predict(sample_data)
predictions = tf.make_ndarray(response.outputs['dense_7'])
print(f"✓ Prediction successful!")
print(f"Output shape: {predictions.shape}")
print(f"Predictions: {predictions}")
```

### Step 3: Verify Everything Works

```bash
# Check running containers
docker ps

# Check network connections
docker network inspect ml-network

# View TF Serving logs
docker logs tf-serving

# View Jupyter logs
docker logs jupyter-client
```

---

## Troubleshooting Checklist

When you encounter connection issues, work through this checklist:

- [ ] **Are both containers running?**

  ```bash
  docker ps
  ```

- [ ] **Are they on the same network?**

  ```bash
  docker network inspect ml-network
  ```

- [ ] **Is the server listening on the correct port?**

  ```bash
  docker logs tf-serving | grep "Exporting HTTP/REST API"
  ```

- [ ] **Can you reach the server from the client container?**

  ```bash
  docker exec jupyter-client ping tf-serving
  ```

- [ ] **Is the correct connection string used?**
  - ✅ `tf-serving:8500` (same network)
  - ✅ `172.17.0.1:8500` (via host)
  - ❌ `localhost:8500` (wrong - refers to client container)

- [ ] **Are you using the correct model name and signature?**

  ```bash
  # Check available models
  curl http://localhost:8501/v1/models/clothing-model
  ```

---

## Quick Reference

### Connection Strings by Scenario

| Scenario | Connection String | Notes |
|----------|------------------|-------|
| Same Docker network | `tf-serving:8500` | Best practice |
| Default bridge network | `172.17.0.1:8500` | Via host gateway |
| Host to container | `localhost:8500` | Only from host machine |
| Container to container IP | `172.17.0.x:8500` | Fragile, not recommended |

### Common Commands

```bash
# List networks
docker network ls

# Inspect network
docker network inspect ml-network

# Connect container to network
docker network connect ml-network <container-name>

# Check container IP
docker inspect <container-name> | grep IPAddress

# Test connectivity
docker exec <client-container> ping <server-container>
```

---

## Summary__

The key takeaways for Docker container networking:

1. **`localhost` in a container refers to that container only**, not the host or other containers
2. **Use user-defined networks** for DNS resolution by container name
3. **Docker Compose** is the easiest way to set up multi-container applications
4. **Name your containers** for easier management and debugging
5. **Use container names** instead of IPs when possible

This guide should help you avoid the most common pitfalls when working with Docker containers that need to communicate with each other!

---
Looking at this error, the issue is clear: **grpcio requires Microsoft Visual C++ 14.0 or greater to build on Windows**, but it's not installed on your system.

Here are your solutions:

## Solution 1: Install Pre-built Binary (Recommended)_

Instead of building from source, install a pre-built wheel:

```bash
pip install --upgrade pip
pip install grpcio --only-binary grpcio
```

Or specify a version:

```bash
pip install grpcio==1.60.0 --only-binary grpcio
```

## Solution 2: Install Microsoft C++ Build Tools

If you need to build from source:

1. Download and install **Microsoft C++ Build Tools** from:
   <https://visualstudio.microsoft.com/visual-cpp-build-tools/>

2. During installation, select:
   - "Desktop development with C++"
   - Windows 10/11 SDK
   - MSVC v143 or later

3. Restart your terminal and try installing again

## Solution 3: Use Python 3.12+ (if compatible with your project)

Newer Python versions often have better wheel support:

```bash
# If using uv
uv python install 3.12
uv venv --python 3.12
```

## Solution 4: Downgrade to a version with wheels

Sometimes older versions have pre-built wheels:

```bash
pip install grpcio==1.56.0
```

**I'd recommend trying Solution 1 first** - it's the quickest and avoids the large Build Tools installation. The `--only-binary` flag forces pip to use pre-built wheels instead of trying to compile from source.

---

# Complete Guide: gRPC, Docker Networking & TensorFlow Serving

## Part 1: Understanding gRPC

### What is gRPC?

gRPC (gRPC Remote Procedure Call) is a modern, high-performance framework developed by Google that allows programs to call functions on other machines as if they were local function calls. Think of it like making a phone call: you dial a number (connect to a service), ask for something (make a request), and get an answer back—all without worrying about underlying network details.

### Core Components

**Remote Procedure Call (RPC)**: This concept lets you execute a function on a remote server seamlessly. Instead of manually constructing HTTP requests and parsing responses, RPC makes it feel like calling a local function. Your client code looks clean and straightforward.

**Protocol Buffers (Protobuf)**: gRPC uses Protocol Buffers as its data format—a binary serialization standard that's significantly smaller than JSON and much faster to serialize and deserialize. Protobuf files define exact data structures, ensuring both client and server agree on the data format. This prevents common errors like typos in field names or mismatched data types.

### Performance Advantages

gRPC significantly outperforms traditional REST APIs for several reasons. The binary format is much smaller (often 10 bytes of protobuf versus 45 bytes of JSON for similar data), and HTTP/2 provides multiplexing, header compression, and persistent connections. For machine learning services that handle thousands of requests per second, these efficiencies matter tremendously.

### Key Strengths

gRPC's language-agnostic nature means you can write your server in Python and your client in Go, JavaScript, Java, or any of 50+ supported languages. It provides built-in features for authentication using SSL/TLS and token-based systems, load balancing across multiple servers, timeouts and deadlines to prevent hanging requests, bidirectional streaming for real-time communication, and comprehensive error handling.

### When to Use gRPC

gRPC shines in microservices architectures where internal services need to communicate efficiently, applications requiring real-time data streaming, scenarios prioritizing performance and low latency, and polyglot environments with multiple programming languages. REST APIs remain better for public-facing APIs (due to browser compatibility), simple CRUD applications, or situations where human-readable data format matters.

## Part 2: Docker Networking Fundamentals

### The Localhost Problem in Docker

The most critical concept to understand about Docker networking is that `localhost` (or `127.0.0.1`) inside a container refers to **that container itself**, not your host machine or other containers. This distinction causes more connection errors than any other single issue.

When you run two Docker containers, they're like separate islands in a network. Container A cannot reach localhost on Container B—it can only reach localhost within itself. This is why you get "Connection refused" errors when trying to connect to `localhost:8500` from inside a container where the server is in a different container.

### Docker Network Types

Docker provides different network types with distinct characteristics. The default bridge network allows containers to communicate using IP addresses, but importantly, it does not support DNS resolution by container name. Containers can only be discovered by their IP addresses, which is fragile because IPs change on container restart.

User-defined networks are the modern approach. When you create a custom bridge network, Docker includes an embedded DNS server that automatically resolves container names to IP addresses. This is why `tf-serving:8500` works when containers are on the same user-defined network but fails on the default bridge network.

### Connection Methods Ranked by Practicality

Using a container name like `tf-serving:8500` is the best approach when containers are on the same user-defined network. This is readable, fast (direct container communication), and survives container restarts.

Using the Docker bridge gateway IP like `172.17.0.1:8500` works without requiring network setup, but adds an extra hop through the host machine, making it slightly slower.

Using a container's IP address like `172.17.0.2:8500` is fragile because the IP changes whenever you restart a container, making it unsuitable for production.

Using `localhost:8500` only works when connecting from your host machine to a container, never from container to container.

### Visual Network Architecture

Imagine your host machine as a central hub with two separate containers connected to it. When a container uses `localhost`, it's checking only within its own isolated network space. When it uses the Docker bridge gateway (172.17.0.1), it goes out to the host machine, which then routes the traffic to the appropriate container based on port mappings. When containers are on the same user-defined network, they can see each other directly through DNS resolution.

## Part 3: Setting Up TensorFlow Serving with Docker

### Starting TensorFlow Serving

```bash
# Basic TensorFlow Serving setup
docker run -d \
  --name tf-serving \
  -p 8500:8500 \
  -p 8501:8501 \
  -v /path/to/your/models:/models \
  -e MODEL_NAME=your_model \
  tensorflow/serving:2.7.0
```

**Command explanation:**

- `-d`: Run in detached mode (background)
- `--name tf-serving`: Give the container a memorable name
- `-p 8500:8500`: Map gRPC port (internal:external)
- `-p 8501:8501`: Map REST API port
- `-v /path/to/your/models:/models`: Mount your model directory
- `-e MODEL_NAME=your_model`: Set environment variable

**Check if running:**

```bash
docker ps
```

**View logs:**

```bash
docker logs tf-serving
```

**Stop the container:**

```bash
docker stop tf-serving
```

**Remove the container:**

```bash
docker rm tf-serving
```

### Starting Jupyter for Development

The volume mount command differs significantly depending on your shell environment.

**Windows Command Prompt (CMD):**

```bash
docker run -it --rm ^
  --name jupyter-client ^
  -v "%cd%:/tf/notebooks" ^
  -p 8888:8888 ^
  tensorflow/tensorflow:latest-jupyter
```

**Windows PowerShell:**

```powershell
docker run -it --rm `
  --name jupyter-client `
  -v "${pwd}:/tf/notebooks" `
  -p 8888:8888 `
  tensorflow/tensorflow:latest-jupyter
```

**Git Bash (Windows):**

```bash
docker run -it --rm \
  --name jupyter-client \
  -v "$(pwd):/tf/notebooks" \
  -p 8888:8888 \
  tensorflow/tensorflow:latest-jupyter
```

**Linux/Mac:**

```bash
docker run -it --rm \
  --name jupyter-client \
  -v "$(pwd):/tf/notebooks" \
  -p 8888:8888 \
  tensorflow/tensorflow:latest-jupyter
```

**Access Jupyter:**

After running the command, look for output like:

```
http://127.0.0.1:8888/?token=abc123def456
```

Copy this URL into your browser.

### Docker Compose: The Best Practice Approach

Rather than running individual docker commands for each service, Docker Compose lets you define your entire multi-container application in a YAML file. This approach is reproducible, documented, and can be shared with team members or deployed to production with minimal changes.

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  tf-serving:
    image: tensorflow/serving:2.7.0
    container_name: tf-serving
    ports:
      - "8500:8500"
      - "8501:8501"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=clothing-model
    command:
      - "--model_base_path=/models/clothing-model"
      - "--rest_api_port=8501"
    networks:
      - ml-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/v1/models/clothing-model"]
      interval: 30s
      timeout: 10s
      retries: 3

  jupyter:
    image: tensorflow/tensorflow:latest-jupyter
    container_name: jupyter-client
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/tf/notebooks
    depends_on:
      - tf-serving
    networks:
      - ml-network
    environment:
      - TF_SERVING_HOST=tf-serving

  gateway:
    image: your-gateway-app:latest
    container_name: flask-gateway
    ports:
      - "9696:9696"
    depends_on:
      - tf-serving
    networks:
      - ml-network
    environment:
      - TF_SERVING_HOST=tf-serving
      - TF_SERVING_PORT=8500

networks:
  ml-network:
    driver: bridge
```

**Start all services:**

```bash
docker-compose up -d
```

**View logs for all services:**

```bash
docker-compose logs -f
```

**View logs for specific service:**

```bash
docker-compose logs -f tf-serving
```

**Stop all services:**

```bash
docker-compose down
```

**Stop and remove volumes:**

```bash
docker-compose down -v
```

**Restart all services:**

```bash
docker-compose restart
```

**Rebuild images:**

```bash
docker-compose build
```

**View running services:**

```bash
docker-compose ps
```

## Part 4: Debugging Connection Errors

### Error: Connection Refused (IPv6)

**Problem:** Error mentions `[::1]:8500` (IPv6 loopback address)

**Solution - Force IPv4:**

```python
import grpc

# ❌ Don't use this
channel = grpc.insecure_channel('localhost:8500')

# ✅ Use this instead
channel = grpc.insecure_channel('127.0.0.1:8500')
```

**Or set environment variable:**

Windows Command Prompt:

```bash
set GRPC_DNS_RESOLVER=native
python your_script.py
```

Windows PowerShell:

```powershell
$env:GRPC_DNS_RESOLVER="native"
python your_script.py
```

Linux/Mac:

```bash
export GRPC_DNS_RESOLVER=native
python your_script.py
```

### Error: Connection Refused (Wrong Environment)

**Problem:** Client is inside Docker container, server elsewhere

**Diagnosis - Check if in Docker:**

```bash
python -c "import os; print('In Docker' if os.path.exists('/.dockerenv') else 'Not in Docker')"
```

**Solution A: Use Docker Bridge Gateway**

```python
import grpc

# Connect via Docker bridge gateway
channel = grpc.insecure_channel('172.17.0.1:8500')
```

**Solution B: Use Container Name (Recommended)**

First, connect containers to same network:

```bash
# Create network
docker network create ml-network

# Connect existing containers
docker network connect ml-network tf-serving
docker network connect ml-network jupyter-client

# Verify connection
docker network inspect ml-network
```

Then in your code:

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

### Error: DNS Resolution Failed

**Problem:** Error says "Domain name not found"

**Diagnosis - Check networks:**

```bash
# List all networks
docker network ls

# Inspect the network
docker network inspect ml-network

# Check which networks a container is on
docker inspect jupyter-client | grep -A 10 "Networks"
```

**Solution - Create and Connect to User-Defined Network:**

```bash
# Create custom network
docker network create ml-network

# Connect both containers (use actual names from 'docker ps')
docker network connect ml-network tf-serving
docker network connect ml-network jupyter-client

# Verify both are connected
docker network inspect ml-network
```

Now use container name in code:

```python
channel = grpc.insecure_channel('tf-serving:8500')
```

### Error: Protobuf Descriptor Error

**Problem:** "Descriptors cannot be created directly"

**Diagnosis - Check protobuf version:**

```bash
pip list | grep protobuf
```

**Solution - Downgrade protobuf:**

```bash
pip uninstall protobuf -y
pip install protobuf==3.20.3
```

Or for UV:

```bash
uv pip uninstall protobuf
uv pip install protobuf==3.20.3
```

### Error: numpy.ndarray has no attribute 'tostring'

**Problem:** Method removed in NumPy 1.20+

**Diagnosis - Check NumPy version:**

```bash
python -c "import numpy; print(numpy.__version__)"
```

**Solution - Replace tostring with tobytes:**

```python
# ❌ Old (broken):
tensor_proto.tensor_content = data.tostring()

# ✅ New (fixed):
tensor_proto.tensor_content = data.tobytes()
```

## Part 5: Python Error Reading and Diagnosis

### Error Anatomy

Every Python error (traceback) follows a consistent structure. The header indicates it's a traceback, followed by one or more file locations showing the call stack, then the actual error at the bottom. Most developers read from the bottom up to find the actual error, then read top-down to understand how the error occurred.

### My Error Diagnosis Checklist

1. **Read the BOTTOM line first** - that's the actual error
2. **Identify the error type** - AttributeError, ImportError, TypeError, etc.
3. **Find the exact location** - which file and line number
4. **Look for keywords** - "has no attribute", "cannot import", "deprecated", etc.
5. **Trace the call stack** (top-down) - understand how we got there
6. **Apply pattern matching** - recognize the error pattern

### Error Types and Their Patterns

**AttributeError:**

```
AttributeError: 'numpy.ndarray' object has no attribute 'tostring'
                ^^^^^^^^^^^^^^                         ^^^^^^^^
                Object type                           Missing attribute
```

Solution: Check documentation for correct method name or if method was renamed/removed.

**ImportError/ModuleNotFoundError:**

```
ImportError: cannot import name 'predict_pb2' from 'tensorflow_serving.apis'
```

Solution: Check if package is installed, reinstall if needed, verify compatibility.

**TypeError:**

```
TypeError: Descriptors cannot be created directly.
```

Solution: Usually a version compatibility issue. Check package versions.

**NameError:**

```
NameError: name 'grpc' is not defined
```

Solution: Add missing import statement.

**FileNotFoundError:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'model.h5'
```

Solution: Verify file path and current working directory.

## Part 6: Package Installation and Management

### Installing gRPC and Dependencies

**Standard pip:**

```bash
# Uninstall conflicting packages
pip uninstall grpc grpcio grpcio-tools -y

# Install fresh
pip install grpcio grpcio-tools tensorflow-serving-api
```

**With UV:**

```bash
# Uninstall
uv pip uninstall grpcio grpcio-tools tensorflow-serving-api

# Reinstall with cache clearing
uv pip install grpcio grpcio-tools tensorflow-serving-api --reinstall --no-cache
```

**For Windows C++ compilation issues:**

```bash
# Use pre-built binaries instead of compiling
pip install grpcio --only-binary grpcio
```

### Creating Requirements File

**Create `requirements.txt`:**

```txt
grpcio==1.76.0
grpcio-tools==1.76.0
tensorflow-serving-api==2.14.0
keras-image-helper==0.0.1
flask==3.0.0
tensorflow==2.20.0
protobuf==3.20.3
gunicorn==23.0.0
```

**Install from file:**

```bash
# Using pip
pip install -r requirements.txt

# Using UV
uv pip install -r requirements.txt
```

### Creating pyproject.toml (Modern Approach)

```toml
[project]
name = "tf-serving-gateway"
version = "0.1.0"
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "tensorflow-serving-api>=2.14.0",
    "keras-image-helper>=0.0.1",
    "flask>=3.0.0",
    "tensorflow>=2.14.0",
    "protobuf==3.20.3",
    "gunicorn>=23.0.0",
]
```

**Update dependencies with UV:**

```bash
# Add a package
uv add tensorflow-serving-api==2.14.0

# Create lock file
uv lock

# Sync from lock file
uv sync --locked
```

## Part 7: Implementing Your Gateway Service

### Basic Gateway Structure

```python
import os
import grpc
from flask import Flask, jsonify, request
from tensorflow_serving.apis import predict_pb2, prediction_service_pb2_grpc
import tensorflow as tf
from keras_image_helper import create_preprocessor

# Configuration from environment variables
TF_SERVING_HOST = os.getenv("TF_SERVING_HOST", "localhost")
TF_SERVING_PORT = os.getenv("TF_SERVING_PORT", "8500")
MODEL_NAME = os.getenv("MODEL_NAME", "clothing-model")

# Create Flask app
app = Flask(__name__)

# Create gRPC channel
host = f"{TF_SERVING_HOST}:{TF_SERVING_PORT}"
channel = grpc.insecure_channel(host)
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

# Preprocessor for images
preprocessor = create_preprocessor('xception', target_size=(299, 299))

def predict(url):
    """Make prediction using TensorFlow Serving"""
    try:
        # Prepare image
        X = preprocessor.from_url(url)
        
        # Create prediction request
        request_obj = predict_pb2.PredictRequest()
        request_obj.model_spec.name = MODEL_NAME
        request_obj.model_spec.signature_name = "serving_default"
        request_obj.inputs["input_8"].CopyFrom(
            tf.make_tensor_proto(X, dtype=tf.float32)
        )
        
        # Get prediction
        response = stub.Predict(request_obj, timeout=20.0)
        predictions = tf.make_ndarray(response.outputs["dense_7"])
        
        return predictions.tolist()[0]
    except grpc.RpcError as e:
        raise Exception(f"gRPC Error: {e}")
    except Exception as e:
        raise Exception(f"Prediction Error: {e}")

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    """HTTP endpoint for predictions"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL not provided'}), 400
        
        result = predict(url)
        return jsonify({'predictions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        grpc.channel_ready_future(channel).result(timeout=2)
        return jsonify({'status': 'healthy'})
    except:
        return jsonify({'status': 'unhealthy'}), 503

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=9696)
```

**Test locally:**

```bash
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://bit.ly/mlbookcamp-pants"}'
```

### Docker Gateway Image

**Create `Dockerfile`:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gateway.py .

EXPOSE 9696

CMD ["python", "gateway.py"]
```

**Build the image:**

```bash
docker build -t gateway-app:latest .
```

**Run the container:**

```bash
# On same Docker network
docker run -d \
  --name flask-gateway \
  --network ml-network \
  -p 9696:9696 \
  -e TF_SERVING_HOST=tf-serving \
  -e TF_SERVING_PORT=8500 \
  gateway-app:latest
```

## Part 8: Complete Working Setup

### Full Docker Compose Setup

**Full `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  tf-serving:
    image: tensorflow/serving:2.14.0
    container_name: tf-serving
    ports:
      - "8500:8500"
      - "8501:8501"
    volumes:
      - ./models:/models
      - ./model_config.conf:/config/model_config.conf
    environment:
      - MODEL_NAME=clothing-model
      - MODEL_BASE_PATH=/models/clothing-model
    command:
      - "--port=8500"
      - "--rest_api_port=8501"
      - "--model_config_file=/config/model_config.conf"
    networks:
      - ml-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/v1/models/clothing-model"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  gateway:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flask-gateway
    ports:
      - "9696:9696"
    depends_on:
      tf-serving:
        condition: service_healthy
    environment:
      - TF_SERVING_HOST=tf-serving
      - TF_SERVING_PORT=8500
      - MODEL_NAME=clothing-model
      - FLASK_ENV=production
    networks:
      - ml-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  jupyter:
    image: tensorflow/tensorflow:latest-jupyter
    container_name: jupyter-notebook
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/tf/notebooks
      - ./models:/models
    environment:
      - TF_SERVING_HOST=tf-serving
      - JUPYTER_ENABLE_LAB=yes
    networks:
      - ml-network
    command: bash -c "jupyter lab --ip=0.0.0.0 --no-browser --allow-root"
    restart: unless-stopped

networks:
  ml-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Start entire stack:**

```bash
docker-compose up -d
```

**Check all services:**

```bash
docker-compose ps
```

**View all logs:**

```bash
docker-compose logs -f
```

**View specific service logs:**

```bash
docker-compose logs -f tf-serving
docker-compose logs -f gateway
docker-compose logs -f jupyter
```

**Stop everything:**

```bash
docker-compose down
```

**Stop and remove volumes:**

```bash
docker-compose down -v
```

### Verification Commands

**Check if services are running:**

```bash
docker ps
```

**Inspect the network:**

```bash
docker network inspect ml-network
```

**Check TensorFlow Serving is healthy:**

```bash
curl http://localhost:8501/v1/models/clothing-model
```

**Test gateway endpoint:**

```bash
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://bit.ly/mlbookcamp-pants"}'
```

**Get Jupyter token:**

```bash
docker logs jupyter-notebook | grep token
```

**Enter container for debugging:**

```bash
docker exec -it flask-gateway bash
```

**Test connectivity between containers:**

```bash
docker exec gateway-app ping tf-serving
```

## Part 9: Troubleshooting Checklist

### Connection Issues

```bash
# 1. Are services running?
docker ps

# 2. Are they on the same network?
docker network inspect ml-network

# 3. Can they see each other?
docker exec flask-gateway ping tf-serving

# 4. Check ports
docker inspect tf-serving | grep -A 10 Ports

# 5. View service logs
docker logs tf-serving
docker logs flask-gateway

# 6. Test gRPC connection
python -c "
import grpc
channel = grpc.insecure_channel('localhost:8500')
try:
    grpc.channel_ready_future(channel).result(timeout=5)
    print('✓ Connected')
except:
    print('✗ Failed')
"
```

### Package Issues

```bash
# Check installed packages
pip list | grep grpc
pip list | grep tensorflow
pip list | grep protobuf

# Verify imports work
python -c "import grpc; print(hasattr(grpc, 'insecure_channel'))"
python -c "from tensorflow_serving.apis import predict_pb2; print('OK')"

# Check Python version
python --version
```

### Docker Issues

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused networks
docker network prune

# Full cleanup (careful!)
docker system prune -a

# Check resource usage
docker stats

# View detailed container info
docker inspect <container-name>
```

## Part 10: Quick Reference Commands

### Essential Docker Commands

```bash
# Build image
docker build -t image-name:tag .

# Run container
docker run -d --name container-name -p 8500:8500 image-name:tag

# List containers
docker ps
docker ps -a  # including stopped

# View logs
docker logs container-name
docker logs -f container-name  # follow logs

# Stop/Start container
docker stop container-name
docker start container-name

# Remove container
docker rm container-name

# Execute command in container
docker exec -it container-name bash

# Copy files to/from container
docker cp local-file container-name:/path/in/container
docker cp container-name:/path/in/container local-file

# Network management
docker network ls
docker network create network-name
docker network connect network-name container-name
docker network inspect network-name
```

### Essential Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild images
docker-compose build

# Restart services
docker-compose restart

# Scale service
docker-compose up -d --scale service-name=3

# Run command in service
docker-compose exec service-name bash
```

### Connection String Reference

| Scenario | String | Notes |
|----------|--------|-------|
| Same user-defined network | `tf-serving:8500` | ✅ Best practice |
| Host to container | `localhost:8500` | ✅ Works from host |
| Default bridge network | `172.17.0.1:8500` | ⚠️ Via host gateway |
| Container IP | `172.17.0.2:8500` | ❌ Fragile, changes on restart |

## Summary

This comprehensive guide provides everything needed to successfully work with gRPC, Docker, and TensorFlow Serving. The key is understanding Docker networking fundamentals, using Docker Compose for reliable setups, and following systematic debugging approaches when issues arise.

Always remember: **`localhost` in a container refers only to that container**. This single concept clarifies most connection issues. Use Docker Compose to set up user-defined networks, name your containers explicitly, and make all configuration environment-variable driven for flexibility across different deployment scenarios.

---

# Docker & Kubernetes Project Setup Guide

## Project Overview

This guide covers setting up a Python Flask application with Docker and Kubernetes. The project uses `uv` (a fast Python package manager) for dependency management and runs a simple ping service on port 9696.

**Project Structure:**

```
10-kubernetes/
├── pyproject.toml           (Root workspace configuration)
├── uv.lock                  (Locked dependencies)
├── ping/
│   ├── pyproject.toml       (Ping service configuration)
│   ├── ping.py              (Flask application)
│   └── Dockerfile           (Container definition)
└── README.md
```

---

## Prerequisites

### Required Software

- **Python 3.11+** - For local development
- **Docker Desktop** - For containerization (Windows/Mac) or Docker Engine (Linux)
- **uv package manager** - Fast Python package manager

### Installing Prerequisites on Windows

```powershell
# Install uv via pip
pip install uv

# Verify installation
uv --version
```

For Docker Desktop, download from: <https://www.docker.com/products/docker-desktop>

---

## Step-by-Step Workflow

### Step 1: Initialize and Manage Dependencies

#### Understanding the Project Structure

The project uses a **workspace setup** where:

- Root `pyproject.toml` defines the overall project
- `ping/pyproject.toml` defines the ping service as a workspace member

#### Root Configuration (`pyproject.toml`)

```toml
[project]
name = "10-kubernetes"
version = "0.1.0"
description = "Kubernetes learning project"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.1.2",
    "gunicorn>=23.0.0",
    # ... other dependencies
]

[tool.uv.workspace]
members = [
    "ping",  # Declares ping as a workspace member
]
```

This configuration tells `uv` that the `ping` directory is a member of the workspace and has its own `pyproject.toml`.

#### Ping Service Configuration (`ping/pyproject.toml`)

```toml
[project]
name = "ping"
version = "0.1.0"
description = "Ping service"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.1.2",
    "gunicorn>=23.0.0",
]
```

#### Generate Dependency Lock File

**Command:**

```powershell
cd D:\Learning\machine-learning-zoomcamp\10-kubernetes
uv lock
```

**What it does:**

- Resolves all dependencies from both `pyproject.toml` files
- Creates a `uv.lock` file with pinned versions
- Ensures reproducible builds (everyone gets the same versions)
- Takes 1-2 minutes on first run

**Why it matters:**

- `uv.lock` guarantees the same environment in development, testing, and production
- Prevents "works on my machine" problems
- Required for Docker builds with the `--locked` flag

**Troubleshooting:**

- If you see "lockfile needs to be updated," run this command again after modifying `pyproject.toml`
- The workspace member error means you're missing `ping/pyproject.toml` - create it as shown above

---

### Step 2: Prepare the Dockerfile

#### Dockerfile Breakdown

```dockerfile
FROM python:3.11-slim
```

- **Purpose:** Base image with Python 3.11
- **Why 3.11:** TensorFlow 2.20.0 only supports Python 3.11, 3.12, 3.13
- **Why slim:** Lightweight image (~160MB vs 900MB+)

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

- **Purpose:** Copy `uv` from the official `uv` image
- **Benefits:** Keeps your image small by not installing uv in the base image
- **Multi-stage pattern:** Uses one image to copy a tool, discards it, keeps the tool

```dockerfile
WORKDIR /app
```

- **Purpose:** Sets the working directory inside the container
- **Effect:** All subsequent commands run from `/app`

```dockerfile
COPY ["pyproject.toml", "uv.lock", "./"]
```

- **Purpose:** Copy dependency files
- **Why separate step:** Enables Docker layer caching - dependencies only reinstall if these files change

```dockerfile
RUN uv sync --locked
```

- **Purpose:** Install dependencies using the locked versions
- **What it does:**
  - Reads `uv.lock`
  - Creates `.venv` virtual environment
  - Installs all pinned packages
- **`--locked` flag:** Fails if `uv.lock` is outdated (prevents stale dependencies)

```dockerfile
COPY "ping/ping.py" .
```

- **Purpose:** Copy the application code
- **Why last:** Application code changes frequently; earlier layers (dependencies) cache better if unchanged

```dockerfile
EXPOSE 9696
```

- **Purpose:** Documents that the app listens on port 9696
- **Note:** Doesn't actually publish the port; that happens at runtime

```dockerfile
ENTRYPOINT [".venv/bin/gunicorn", "--bind=0.0.0.0:9696", "ping:app"]
```

- **Purpose:** Runs the Flask app using gunicorn
- **`.venv/bin/gunicorn`:** Uses gunicorn from the virtual environment
- **`--bind=0.0.0.0:9696`:** Listen on all interfaces, port 9696
- **`ping:app`:** Import `app` from `ping.py` module

#### Complete Dockerfile

```dockerfile
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ["pyproject.toml", "uv.lock", "./"]

RUN uv sync --locked

COPY "ping/ping.py" .

EXPOSE 9696

ENTRYPOINT [".venv/bin/gunicorn", "--bind=0.0.0.0:9696", "ping:app"]
```

---

### Step 3: Build the Docker Image

#### Build Command

```powershell
cd D:\Learning\machine-learning-zoomcamp\10-kubernetes
docker build -f ping/Dockerfile -t ping:v001 .
```

**Command Explanation:**

| Part | Purpose |
|------|---------|
| `docker build` | Build a Docker image |
| `-f ping/Dockerfile` | Use this Dockerfile |
| `-t ping:v001` | Tag the image as `ping:v001` (name:version) |
| `.` | Build context is current directory |

**What happens:**

1. Docker reads `ping/Dockerfile`
2. Pulls `python:3.11-slim` from Docker Hub
3. Pulls `uv` image and copies the tool
4. Sets working directory to `/app`
5. Copies `pyproject.toml` and `uv.lock`
6. Runs `uv sync --locked` (installs dependencies)
7. Copies `ping.py`
8. Exposes port 9696

**Build output example:**

```
[1/7] FROM docker.io/library/python:3.11-slim
[2/7] COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
[3/7] WORKDIR /app
[4/7] COPY ["pyproject.toml", "uv.lock", "./"]
[5/7] RUN uv sync --locked
[6/7] COPY "ping/ping.py" .
[7/7] ENTRYPOINT [".venv/bin/gunicorn", "--bind=0.0.0.0:9696", "ping:app"]
```

**Typical build time:** 2-5 minutes (first build takes longer)

#### Troubleshooting Build Errors

| Error | Solution |
|-------|----------|
| `COPY ["pyproject.toml", "uv.lock", "./"]` not found | Run `uv lock` in project root |
| `uv sync --locked` fails with lockfile error | Run `uv lock` to update dependencies |
| TensorFlow platform error | Ensure Dockerfile uses `python:3.11-slim` or higher |
| `gunicorn: executable not found` | Use `.venv/bin/gunicorn` in ENTRYPOINT |

---

### Step 4: Run the Container

#### Basic Run Command

```powershell
docker run -p 9696:9696 ping:v001
```

**Command Explanation:**

| Part | Purpose |
|------|---------|
| `docker run` | Create and start a container |
| `-p 9696:9696` | Map port 9696 (host) to 9696 (container) |
| `ping:v001` | Use this image |

**Expected output:**

```
[2024-12-18 10:30:45 +0000] [1] [INFO] Starting gunicorn 23.0.0
[2024-12-18 10:30:45 +0000] [1] [INFO] Listening at: http://0.0.0.0:9696 (1)
[2024-12-18 10:30:45 +0000] [1] [INFO] Using worker: sync
[2024-12-18 10:30:45 +0000] [8] [INFO] Booted worker with pid: 8
```

#### Run with Additional Options

```powershell
# Run in background (detached mode)
docker run -d -p 9696:9696 --name ping-service ping:v001

# Run with environment variables
docker run -p 9696:9696 -e LOG_LEVEL=DEBUG ping:v001

# Run with volume mount (for development)
docker run -p 9696:9696 -v C:\path\to\code:/app ping:v001
```

---

### Step 5: Test the Application

#### Using PowerShell's Invoke-WebRequest

```powershell
Invoke-WebRequest -Uri "http://localhost:9696/ping"
```

**Short alias:**

```powershell
iwr http://localhost:9696/ping
```

**Expected response:**

```http
StatusCode        : 200
StatusDescription : OK
Content           : pong
RawContent        : HTTP/1.1 200 OK
```

#### Using curl (if installed)

```powershell
curl http://localhost:9696/ping
```

#### Check Running Containers

```powershell
# List running containers
docker ps

# View logs
docker logs <container-id-or-name>

# Stop container
docker stop <container-id-or-name>

# Remove container
docker rm <container-id-or-name>
```

---

## Common Workflows

### Workflow: Update Dependencies

1. Edit `ping/pyproject.toml` or root `pyproject.toml`
2. Regenerate lock file:

   ```powershell
   uv lock
   ```

3. Rebuild Docker image:

   ```powershell
   docker build -f ping/Dockerfile -t ping:v001 .
   ```

### Workflow: Update Application Code

1. Edit `ping/ping.py`
2. Rebuild Docker image:

   ```powershell
   docker build -f ping/Dockerfile -t ping:v001 .
   ```

3. Run new container:

   ```powershell
   docker run -p 9696:9696 ping:v001
   ```

### Workflow: Clean Up Docker

```powershell
# Remove unused images
docker image prune

# Remove all stopped containers
docker container prune

# Remove image
docker rmi ping:v001

# View all images
docker images
```

---

## Key Concepts Explained

### Virtual Environments (`.venv`)

Docker creates a virtual environment with `uv sync`. This isolates Python packages from the system Python, preventing conflicts.

**Location in container:** `/app/.venv`
**Used in ENTRYPOINT:** `.venv/bin/gunicorn`

### Dependency Pinning (`uv.lock`)

The lock file pins exact versions, ensuring reproducibility:

- Development machine gets TensorFlow 2.20.0
- Docker build gets TensorFlow 2.20.0
- Production deployment gets TensorFlow 2.20.0

### Layer Caching

Docker caches each layer. When you rebuild:

- Changed code layer → rebuilds
- Unchanged dependency layers → reused (fast)

This is why we copy dependencies first, then code.

### Port Mapping (`-p 9696:9696`)

The container listens internally on port 9696. The `-p` flag maps:

- Host port 9696 → Container port 9696
- So you access via `http://localhost:9696`

---

## Python Application Example (`ping.py`)

```python
from flask import Flask

app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'pong'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9696)
```

When running via Docker, gunicorn (not Flask's dev server) handles requests.

---

## Quick Reference_

| Task | Command |
|------|---------|
| Generate lock file | `uv lock` |
| Build image | `docker build -f ping/Dockerfile -t ping:v001 .` |
| Run container | `docker run -p 9696:9696 ping:v001` |
| Test endpoint | `iwr http://localhost:9696/ping` |
| List images | `docker images` |
| List containers | `docker ps` |
| View logs | `docker logs <container-id>` |
| Stop container | `docker stop <container-id>` |
| Remove image | `docker rmi ping:v001` |

---

## Next Steps

- Deploy to Kubernetes using `kubectl`
- Set up CI/CD pipeline to automate builds
- Add health checks to the Flask app
- Configure environment-specific settings
- Add logging and monitoring

---
I'll help you work through this Kubernetes homework assignment. Let me address each question:

## Question 1: Conversion Probability

To find the answer, you need to run:

```bash
docker run -it --rm -p 9696:9696 zoomcamp-model:3.13.10-hw10
```

Then in another terminal:

```bash
python q6_test.py
```

The output will show the conversion probability. Based on typical homework patterns, you should see one of the provided values (0.29, 0.49, 0.69, or 0.89).

## Question 2: Kind Version

Run:

```bash
kind --version
```

This will output something like `kind v0.20.0` or similar.

## Question 3: Smallest Deployable Unit

**Answer: Pod**

In Kubernetes, a Pod is the smallest deployable computing unit. It represents a single instance of a running process and can contain one or more containers.

## Question 4: Type of Running Service

Run:

```bash
kubectl get services
```

**Answer: ClusterIP**

The default service that runs in a new Kubernetes cluster is the `kubernetes` service with type ClusterIP.

## Question 5: Register Docker Image with Kind

**Answer: kind load docker-image**

The command would be:

```bash
kind load docker-image zoomcamp-model:3.13.10-hw10
```

## Question 6: Port Value

**Answer: 9696**

Based on the Docker run command and the service testing, the application runs on port 9696.

Complete deployment.yaml:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: subscription
spec:
  selector:
    matchLabels:
      app: subscription
  replicas: 1
  template:
    metadata:
      labels:
        app: subscription
    spec:
      containers:
      - name: subscription
        image: zoomcamp-model:3.13.10-hw10
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"            
          limits:
            memory: "128Mi"
            cpu: "500m"
        ports:
        - containerPort: 9696
```

Apply with:

```bash
kubectl apply -f deployment.yaml
kubectl get pods
```

## Question 7: Service Selector

**Answer: subscription**

Complete service.yaml:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: subscription-service
spec:
  type: LoadBalancer
  selector:
    app: subscription
  ports:
  - port: 80
    targetPort: 9696
```

The `selector` must match the labels in the deployment (`app: subscription`).

Apply with:

```bash
kubectl apply -f service.yaml
```

## Question 8: Maximum Replicas (Optional)

When you run the load test with the modified script and monitor with:

```bash
kubectl get hpa subscription-hpa --watch
```

**Answer: 3**

Given the HPA configuration (`--max=3`) and a CPU threshold of 20%, the continuous load from the loop should eventually scale up to the maximum of 3 replicas.

---

**Summary of Key Commands:**

```bash
# Create cluster
kind create cluster

# Load image
kind load docker-image zoomcamp-model:3.13.10-hw10

# Apply configs
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Test service
kubectl port-forward service/subscription-service 9696:80

# Create HPA
kubectl autoscale deployment subscription --name subscription-hpa --cpu-percent=20 --min=1 --max=3

# Monitor
kubectl get hpa subscription-hpa --watch
```

---

# Kubernetes Ping Service - Complete Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Docker Setup](#docker-setup)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Service Configuration](#service-configuration)
7. [Testing the Application](#testing-the-application)
8. [Troubleshooting](#troubleshooting)
9. [Common Commands Reference](#common-commands-reference)

---

## Project Overview

This project deploys a simple ping service to a Kubernetes cluster. The service exposes an HTTP endpoint that responds to ping requests, demonstrating containerization with Docker and orchestration with Kubernetes.

**Architecture:**

- **Application**: Python-based ping service running on port 9696
- **Container**: Docker image tagged as `ping:v001`
- **Orchestration**: Kubernetes Deployment with 1 replica
- **Networking**: Kubernetes Service for internal/external access

---

## Prerequisites

### Required Tools

- **Docker Desktop** (with Kubernetes enabled) or **Minikube**
- **kubectl** (Kubernetes command-line tool)
- **Python 3.11+** (for local testing)
- **Git** (for version control)

### Verify Installation

```bash
# Check Docker
docker --version

# Check Kubernetes
kubectl version --client

# Check cluster connection
kubectl cluster-info
```

---

## Project Structure

```
10-kubernetes/
├── ping/
│   ├── Dockerfile              # Container image definition
│   ├── app.py                  # Python application code
│   ├── requirements.txt        # Python dependencies
│   ├── deployment.yaml         # Kubernetes Deployment config
│   └── service.yaml            # Kubernetes Service config
└── test.py                     # Client test script
```

---

## Docker Setup

### Step 1: Create the Dockerfile

```dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port 9696 (where the app listens)
EXPOSE 9696

# Command to run when container starts
CMD ["python", "app.py"]
```

**Explanation:**

- `FROM python:3.11-slim`: Uses a lightweight Python base image
- `WORKDIR /app`: Sets `/app` as the working directory
- `COPY requirements.txt .`: Copies dependency list
- `RUN pip install`: Installs Python packages
- `EXPOSE 9696`: Documents which port the app uses
- `CMD`: Defines the startup command

### Step 2: Build the Docker Image

```bash
# Navigate to the project directory
cd D:\Learning\machine-learning-zoomcamp\10-kubernetes\ping

# Build the image with tag ping:v001
docker build -t ping:v001 .
```

**Command Breakdown:**

- `docker build`: Builds a Docker image from a Dockerfile
- `-t ping:v001`: Tags the image as "ping" with version "v001"
- `.`: Uses the current directory as build context

**Verify the build:**

```bash
# List Docker images
docker images | grep ping
```

Expected output:

```
ping         v001      abc123def456   2 minutes ago   200MB
```

### Step 3: Test Locally (Optional)

```bash
# Run container locally
docker run -p 9696:9696 ping:v001

# In another terminal, test with curl
curl http://localhost:9696/ping
```

**Command Breakdown:**

- `docker run`: Creates and starts a container
- `-p 9696:9696`: Maps host port 9696 to container port 9696
- `ping:v001`: Specifies the image to use

---

## Kubernetes Deployment

### Step 1: Create deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ping-deployment
spec:
  replicas: 1                    # Number of pod instances
  selector:
    matchLabels:
      app: ping                  # Selector to identify pods
  template:
    metadata:
      labels:
        app: ping                # Label applied to each pod
    spec:
      containers:
      - name: ping-pod
        image: ping:v001         # Docker image to use
        imagePullPolicy: Never   # Use local image (for Docker Desktop/Minikube)
        resources:
          limits:
            memory: "256Mi"      # Maximum memory allocation
            cpu: "500m"          # Maximum CPU (0.5 cores)
          requests:
            memory: "128Mi"      # Minimum memory reservation
            cpu: "250m"          # Minimum CPU reservation
        ports:
        - containerPort: 9696    # Port the container exposes
```

**Key Concepts:**

- **Deployment**: Manages the desired state of pods
- **Replicas**: Number of identical pods to run
- **Selector**: How the Deployment finds its pods
- **Template**: Blueprint for creating pods
- **Resources**: Memory and CPU limits/requests
- **imagePullPolicy: Never**: Uses local Docker images (important for local development)

### Step 2: Apply the Deployment

```bash
# Create the deployment
kubectl apply -f deployment.yaml
```

**What happens:**

1. Kubernetes reads the YAML configuration
2. Creates a Deployment object
3. The Deployment creates a ReplicaSet
4. The ReplicaSet creates the specified number of pods
5. Each pod starts a container using the `ping:v001` image

### Step 3: Verify the Deployment

```bash
# Check deployment status
kubectl get deployments

# Check pods
kubectl get pods

# Get detailed pod information
kubectl describe pod <pod-name>
```

**Expected output:**

```bash
# Deployments
NAME              READY   UP-TO-DATE   AVAILABLE   AGE
ping-deployment   1/1     1            1           2m

# Pods
NAME                               READY   STATUS    RESTARTS   AGE
ping-deployment-5754b77896-qkjb6   1/1     Running   0          2m
```

**Status meanings:**

- `Running`: Pod is running successfully
- `Pending`: Pod is waiting to be scheduled
- `CrashLoopBackOff`: Pod keeps crashing
- `ImagePullBackOff`: Can't pull the Docker image

---

## Service Configuration

### Step 1: Create service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ping                     # Service name (used for DNS)
spec:
  type: LoadBalancer             # Service type
  selector:
    app: ping                    # Targets pods with label app=ping
  ports:
  - port: 80                     # Service port (external)
    targetPort: 9696             # Pod port (internal)
    protocol: TCP
```

**Service Types:**

- **ClusterIP** (default): Only accessible within cluster
- **NodePort**: Accessible on each node's IP at a static port
- **LoadBalancer**: Exposes service externally using cloud provider's load balancer

**Port Configuration:**

- `port: 80`: Port that the service listens on
- `targetPort: 9696`: Port on the pod where traffic is sent
- Traffic flow: External → Service:80 → Pod:9696

### Step 2: Apply the Service

```bash
# Create the service
kubectl apply -f service.yaml
```

### Step 3: Verify the Service

```bash
# Check service status
kubectl get svc ping

# Check service endpoints (pod IPs)
kubectl get endpoints ping
```

**Expected output:**

```bash
# Service
NAME   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
ping   LoadBalancer   10.96.123.45    localhost     80:30123/TCP   1m

# Endpoints
NAME   ENDPOINTS          AGE
ping   10.244.0.5:9696    1m
```

**Understanding the output:**

- **CLUSTER-IP**: Internal IP for cluster communication
- **EXTERNAL-IP**: External access point (may be `<pending>` on local setups)
- **PORT(S)**: Shows `80:30123/TCP` where 30123 is the NodePort
- **ENDPOINTS**: Actual pod IPs that receive traffic

---

## Testing the Application

### Method 1: Internal Testing (Inside Cluster)

```bash
# Access a pod shell
kubectl exec -it <pod-name> -- bash

# Install curl (if needed)
apt update && apt install -y curl

# Test using service DNS name (short form)
curl ping/ping

# Test using fully qualified domain name (FQDN)
curl ping.default.svc.cluster.local/ping

# Test DNS resolution
getent hosts ping.default.svc.cluster.local
```

**DNS Resolution in Kubernetes:**

- Short name: `ping`
- With namespace: `ping.default`
- FQDN: `ping.default.svc.cluster.local`

All three work from inside the cluster, within the same namespace.

### Method 2: Port Forwarding (Local Access)

```bash
# Forward service port to localhost
kubectl port-forward service/ping 8080:80
```

**What this does:**

- Maps localhost:8080 to service:80
- Keeps running until you press Ctrl+C
- Great for development and debugging

**Test from your machine:**

```bash
# Using curl
curl http://localhost:8080/ping

# Using Python
python test.py  # (update URL to http://localhost:8080/ping)
```

### Method 3: NodePort Access

If using NodePort service type:

```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 9696
    nodePort: 30080  # Optional: specify port (30000-32767)
```

Access via:

```bash
curl http://localhost:30080/ping
```

### Method 4: LoadBalancer Access (Docker Desktop)

On Docker Desktop Kubernetes:

```bash
# Check external IP
kubectl get svc ping

# If EXTERNAL-IP shows localhost
curl http://localhost/ping
```

### Python Test Script

```python
# test.py
import requests

# Update URL based on your access method
url = 'http://localhost:8080/ping'  # Port forward
# url = 'http://localhost:30080/ping'  # NodePort
# url = 'http://localhost/ping'        # LoadBalancer

data = {"message": "hello"}

try:
    result = requests.post(url, json=data).json()
    print(f"Response: {result}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Troubleshooting

### Problem 1: Pod Not Starting

**Symptoms:**

```bash
kubectl get pods
# Shows: CrashLoopBackOff or Error
```

**Diagnosis:**

```bash
# Check pod logs
kubectl logs <pod-name>

# Check pod events
kubectl describe pod <pod-name>
```

**Common causes:**

- Application crashes on startup
- Missing dependencies
- Port already in use
- Insufficient resources

**Solution:**

```bash
# Increase resources in deployment.yaml
resources:
  limits:
    memory: "512Mi"  # Increase from 256Mi
    cpu: "1000m"
```

### Problem 2: ImagePullBackOff

**Symptoms:**

```bash
kubectl get pods
# Shows: ImagePullBackOff
```

**Cause:** Kubernetes can't find the Docker image

**Solution:**

```bash
# For local images, add to deployment.yaml:
imagePullPolicy: Never

# Verify image exists locally
docker images | grep ping

# Rebuild if necessary
docker build -t ping:v001 .
```

### Problem 3: DNS Resolution Fails

**Symptoms:**

```bash
curl ping.default.svc.cluster.local/ping
# Error: Could not resolve host
```

**Diagnosis:**

```bash
# Check if service exists
kubectl get svc ping

# Check service endpoints
kubectl get endpoints ping

# Test DNS from inside pod
kubectl exec -it <pod-name> -- bash
getent hosts ping.default.svc.cluster.local
```

**Common causes:**

- Service doesn't exist (forgot to apply service.yaml)
- Service name mismatch
- CoreDNS not running

**Solution:**

```bash
# Apply or reapply service
kubectl apply -f service.yaml

# Check CoreDNS
kubectl get pods -n kube-system | grep coredns

# Restart CoreDNS if needed
kubectl rollout restart deployment/coredns -n kube-system
```

### Problem 4: Connection Refused

**Symptoms:**

```bash
curl ping/ping
# Error: Connection refused
```

**Diagnosis:**

```bash
# Check if pod is ready
kubectl get pods

# Check pod logs
kubectl logs <pod-name>

# Check if app is listening on correct port
kubectl exec -it <pod-name> -- netstat -tlnp
```

**Common causes:**

- App not running inside container
- Wrong port configuration
- Pod selector mismatch

**Solution:**

```bash
# Verify port in deployment.yaml matches app
containerPort: 9696  # Must match app's listening port

# Verify service targetPort
targetPort: 9696  # Must match containerPort

# Check selector matches
# deployment.yaml: app: ping
# service.yaml: selector.app: ping
```

### Problem 5: Out of Memory (Exit Code 137)

**Symptoms:**

```bash
kubectl get pods
# Pod keeps restarting

kubectl describe pod <pod-name>
# Shows: Exit Code: 137
```

**Cause:** Container exceeded memory limits

**Solution:**

```bash
# Increase memory in deployment.yaml
resources:
  limits:
    memory: "512Mi"  # Increase allocation
  requests:
    memory: "256Mi"
```

---

## Common Commands Reference

### Docker Commands

```bash
# Build image
docker build -t ping:v001 .

# List images
docker images

# Run container locally
docker run -p 9696:9696 ping:v001

# Stop container
docker stop <container-id>

# Remove image
docker rmi ping:v001

# View container logs
docker logs <container-id>
```

### Kubectl Commands

#### Deployment Management

```bash
# Apply deployment
kubectl apply -f deployment.yaml

# Get deployments
kubectl get deployments

# Describe deployment
kubectl describe deployment ping-deployment

# Delete deployment
kubectl delete deployment ping-deployment

# Scale deployment
kubectl scale deployment ping-deployment --replicas=3

# Update image
kubectl set image deployment/ping-deployment ping-pod=ping:v002
```

#### Pod Management

```bash
# List pods
kubectl get pods

# List pods with more details
kubectl get pods -o wide

# Describe pod
kubectl describe pod <pod-name>

# View pod logs
kubectl logs <pod-name>

# Follow logs (like tail -f)
kubectl logs -f <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- bash

# Delete pod (will be recreated by deployment)
kubectl delete pod <pod-name>
```

#### Service Management

```bash
# Apply service
kubectl apply -f service.yaml

# Get services
kubectl get svc

# Describe service
kubectl describe svc ping

# Get service endpoints
kubectl get endpoints ping

# Delete service
kubectl delete svc ping

# Port forward
kubectl port-forward service/ping 8080:80
```

#### Debugging Commands

```bash
# Get all resources
kubectl get all

# Check cluster info
kubectl cluster-info

# Check node status
kubectl get nodes

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods

# Get pod YAML
kubectl get pod <pod-name> -o yaml

# Check DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup ping
```

#### Cleanup Commands

```bash
# Delete all resources in namespace
kubectl delete all --all -n default

# Delete specific resources
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml

# Force delete pod
kubectl delete pod <pod-name> --grace-period=0 --force
```

### Useful One-Liners

```bash
# Watch pods in real-time
watch kubectl get pods

# Get pod IP addresses
kubectl get pods -o custom-columns=NAME:.metadata.name,IP:.status.podIP

# Restart deployment (rolling restart)
kubectl rollout restart deployment ping-deployment

# Check rollout status
kubectl rollout status deployment ping-deployment

# Undo last deployment
kubectl rollout undo deployment ping-deployment

# View rollout history
kubectl rollout history deployment ping-deployment
```

---

## Best Practices

### Development Workflow

1. **Build** → Create/update Docker image
2. **Test Locally** → Run with `docker run`
3. **Deploy** → Apply Kubernetes manifests
4. **Verify** → Check pods, services, endpoints
5. **Test** → Access via port-forward or service
6. **Monitor** → Check logs and events
7. **Iterate** → Update and reapply

### Configuration Management

- Keep YAML files in version control (Git)
- Use meaningful names and labels
- Document resource limits
- Use namespace for organization
- Add annotations for metadata

### Resource Allocation

- Start with conservative limits
- Monitor actual usage with `kubectl top`
- Adjust based on observed patterns
- Set requests lower than limits
- Consider horizontal pod autoscaling for production

### Security Considerations

- Don't run containers as root
- Use minimal base images
- Scan images for vulnerabilities
- Use network policies
- Store secrets in Kubernetes Secrets

---

## Next Steps

### Scaling the Application

```yaml
# In deployment.yaml, increase replicas
spec:
  replicas: 3  # Run 3 instances
```

### Adding Health Checks

```yaml
# In deployment.yaml, add probes
livenessProbe:
  httpGet:
    path: /ping
    port: 9696
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ping
    port: 9696
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Environment Variables

```yaml
# In deployment.yaml
env:
- name: LOG_LEVEL
  value: "INFO"
- name: PORT
  value: "9696"
```

### Using ConfigMaps

```bash
# Create ConfigMap
kubectl create configmap ping-config --from-literal=log.level=debug

# Reference in deployment
envFrom:
- configMapRef:
    name: ping-config
```

---

## Additional Resources

- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

---

## Summary

This documentation covered:
✅ Docker image creation and local testing  
✅ Kubernetes deployment configuration  
✅ Service exposure and networking  
✅ Multiple testing methods  
✅ Comprehensive troubleshooting guide  
✅ Essential command reference  

You now have a complete workflow for developing, deploying, and managing containerized applications in Kubernetes!

---

## Complete Docker and Kubernetes Workflow for ML Model Deployment

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Docker Workflow](#docker-workflow)
4. [Kubernetes Workflow](#kubernetes-workflow)
5. [Testing and Validation](#testing-and-validation)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Project Overview

This documentation covers the complete workflow for deploying a machine learning model using Docker and Kubernetes. The project consists of two main components:

- **TensorFlow Serving**: Serves the trained ML model
- **Gateway Service**: Python Flask/FastAPI application that acts as an interface to the model

### Architecture

```python
Client Request → Gateway Service → TensorFlow Serving → Model Prediction → Response
                 (Port 9696)       (Port 8500)
```

---

## Prerequisites

### Required Tools

```bash
# Docker
docker --version
# Expected: Docker version 20.10.0 or higher

# Kubernetes CLI (kubectl)
kubectl version --client
# Expected: Client Version 1.24.0 or higher

# kind (Kubernetes in Docker) - for local development
kind version
# Expected: kind v0.20.0 or higher

# Python
python --version
# Expected: Python 3.8 or higher
```

### Installation Links

- **Docker Desktop**: <https://www.docker.com/products/docker-desktop>
- **kubectl**: <https://kubernetes.io/docs/tasks/tools/>
- **kind**: <https://kind.sigs.k8s.io/docs/user/quick-start/#installation>

---

## Docker Workflow

### 1. Understanding Docker Images

Docker images are lightweight, standalone packages that contain everything needed to run an application: code, runtime, libraries, and dependencies.

### 2. Building Docker Images

#### For TensorFlow Serving Model

**Dockerfile structure:**

```dockerfile
FROM tensorflow/serving:2.7.0

# Copy your saved model to the serving directory
COPY clothing-model /models/clothing-model/1

# Set environment variable for model name
ENV MODEL_NAME=clothing-model
```

**Build command:**

```bash
docker build -t clothing-model:xception-v4-001 .
```

**Command breakdown:**

- `docker build`: Initiates the image building process
- `-t clothing-model:xception-v4-001`: Tags the image with name and version
  - `clothing-model`: Image name
  - `xception-v4-001`: Version tag
- `.`: Build context (current directory)

**What happens during build:**

1. Docker reads the Dockerfile
2. Downloads the base image (tensorflow/serving:2.7.0)
3. Copies your model files into the image
4. Sets environment variables
5. Creates layers for each instruction
6. Tags the final image

#### For Gateway Service

**Dockerfile structure:**

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gateway.py .
COPY proto.py .

# Expose port
EXPOSE 9696

# Set environment variable
ENV TF_SERVING_HOST=localhost:8500

# Run the application
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:9696", "gateway:app"]
```

**Build command:**

```bash
docker build -t clothing-model-gateway:001 .
```

**Command breakdown:**

- Uses Python 3.11 slim base image (smaller size)
- Installs Python dependencies from requirements.txt
- Copies application code
- Configures the container to run gunicorn web server

### 3. Running Docker Containers Locally

#### Run TensorFlow Serving

```bash
docker run -it --rm \
  -p 8500:8500 \
  clothing-model:xception-v4-001
```

**Command breakdown:**

- `docker run`: Creates and starts a container
- `-it`: Interactive mode with terminal
  - `-i`: Keep STDIN open
  - `-t`: Allocate a pseudo-TTY
- `--rm`: Automatically remove container when it stops
- `-p 8500:8500`: Port mapping
  - Format: `HOST_PORT:CONTAINER_PORT`
  - Maps container's port 8500 to host's port 8500
- `clothing-model:xception-v4-001`: Image to run

#### Run Gateway Service

```bash
docker run -it --rm \
  -p 9696:9696 \
  -e TF_SERVING_HOST=host.docker.internal:8500 \
  clothing-model-gateway:001
```

**Command breakdown:**

- `-p 9696:9696`: Maps gateway port to host
- `-e TF_SERVING_HOST=host.docker.internal:8500`: Sets environment variable
  - `host.docker.internal`: Special DNS name to reach host machine from container
  - Used to connect gateway container to TF Serving on host

### 4. Docker Compose (Optional)

For running both services together:

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  tf-serving:
    image: clothing-model:xception-v4-001
    ports:
      - "8500:8500"
    networks:
      - ml-network

  gateway:
    image: clothing-model-gateway:001
    ports:
      - "9696:9696"
    environment:
      - TF_SERVING_HOST=tf-serving:8500
    depends_on:
      - tf-serving
    networks:
      - ml-network

networks:
  ml-network:
    driver: bridge
```

**Run with Docker Compose:**

```bash
# Start all services
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f gateway
```

### 5. Useful Docker Commands

```bash
# List all images
docker images

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs <container-id>

# Follow container logs in real-time
docker logs -f <container-id>

# Stop a container
docker stop <container-id>

# Remove an image
docker rmi <image-name>

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Execute command in running container
docker exec -it <container-id> /bin/bash

# Inspect container details
docker inspect <container-id>

# View container resource usage
docker stats
```

---

## Kubernetes Workflow

### 1. Understanding Kubernetes Concepts

**Core Concepts:**

- **Pod**: Smallest deployable unit (runs one or more containers)
- **Deployment**: Manages pod replicas and updates
- **Service**: Exposes pods to network traffic
- **Namespace**: Virtual cluster for resource isolation
- **ConfigMap**: Stores configuration data
- **Secret**: Stores sensitive data

### 2. Setting Up Local Kubernetes with kind

#### Create a Cluster

```bash
kind create cluster --name ml-cluster
```

**Command breakdown:**

- `kind create cluster`: Creates a Kubernetes cluster in Docker
- `--name ml-cluster`: Names the cluster
- Creates a single-node cluster by default

**What happens:**

1. Pulls kind node image
2. Creates Docker container running Kubernetes
3. Configures kubectl to connect to the cluster
4. Sets up networking and core services

#### Verify Cluster

```bash
# Check cluster info
kubectl cluster-info

# Check nodes
kubectl get nodes

# Expected output:
# NAME                       STATUS   ROLES           AGE   VERSION
# ml-cluster-control-plane   Ready    control-plane   2m    v1.27.0
```

### 3. Loading Images into kind

**Why is this needed?**
kind runs Kubernetes in Docker, creating an isolated environment. Images built on your host machine aren't automatically available inside the kind cluster.

```bash
# Load TensorFlow Serving image
kind load docker-image clothing-model:xception-v4-001 --name ml-cluster

# Load Gateway image
kind load docker-image clothing-model-gateway:001 --name ml-cluster
```

**Command breakdown:**

- `kind load docker-image`: Loads image into kind cluster
- `clothing-model:xception-v4-001`: Image to load
- `--name ml-cluster`: Target cluster name

**What happens:**

1. Exports image from Docker
2. Imports into kind's internal registry
3. Makes image available to Kubernetes pods

**Verify images are loaded:**

```bash
docker exec -it ml-cluster-control-plane crictl images
```

### 4. Creating Kubernetes Deployments

#### TensorFlow Serving Deployment

**tf-serving-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tf-serving-clothing-model
  labels:
    app: tf-serving
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tf-serving
  template:
    metadata:
      labels:
        app: tf-serving
    spec:
      containers:
      - name: tf-serving
        image: clothing-model:xception-v4-001
        ports:
        - containerPort: 8500
          name: grpc
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
          requests:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          tcpSocket:
            port: 8500
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          tcpSocket:
            port: 8500
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Configuration breakdown:**

- `replicas: 1`: Number of pod copies to run
- `selector.matchLabels`: How deployment finds its pods
- `template`: Pod specification
- `containerPort: 8500`: Port exposed by container
- `resources.limits`: Maximum resources container can use
- `resources.requests`: Guaranteed minimum resources
- `livenessProbe`: Health check to restart unhealthy pods
- `readinessProbe`: Determines when pod can receive traffic

**Apply deployment:**

```bash
kubectl apply -f tf-serving-deployment.yaml
```

**Command breakdown:**

- `kubectl apply`: Creates or updates resources
- `-f tf-serving-deployment.yaml`: File containing configuration
- Creates deployment and pods based on specification

#### Gateway Deployment

**gateway-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  labels:
    app: gateway
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: clothing-model-gateway:001
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 9696
        env:
        - name: TF_SERVING_HOST
          value: tf-serving-clothing-model.default.svc.cluster.local:8500
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9696
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9696
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Configuration breakdown:**

- `imagePullPolicy: IfNotPresent`: Use local image if available
- `env`: Environment variables
  - `TF_SERVING_HOST`: DNS name of TF Serving service
  - Format: `service-name.namespace.svc.cluster.local:port`
- `livenessProbe.httpGet`: HTTP health check
- `/health`: Endpoint to check (must exist in your app)

**Apply deployment:**

```bash
kubectl apply -f gateway-deployment.yaml
```

### 5. Creating Kubernetes Services

Services provide stable networking for pods, which have ephemeral IPs.

#### TensorFlow Serving Service

**tf-serving-service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: tf-serving-clothing-model
spec:
  type: ClusterIP
  selector:
    app: tf-serving
  ports:
  - protocol: TCP
    port: 8500
    targetPort: 8500
    name: grpc
```

**Configuration breakdown:**

- `type: ClusterIP`: Internal-only service (not exposed outside cluster)
- `selector`: Matches pods with label `app: tf-serving`
- `port: 8500`: Service port (how other services connect)
- `targetPort: 8500`: Pod port (where container listens)

**Apply service:**

```bash
kubectl apply -f tf-serving-service.yaml
```

#### Gateway Service

**gateway-service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
spec:
  type: LoadBalancer
  selector:
    app: gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9696
    name: http
```

**Configuration breakdown:**

- `type: LoadBalancer`: Exposes service externally
  - In kind, use NodePort or port-forward instead
- `port: 80`: External port
- `targetPort: 9696`: Pod port

**For kind, use NodePort instead:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
spec:
  type: NodePort
  selector:
    app: gateway
  ports:
  - protocol: TCP
    port: 9696
    targetPort: 9696
    nodePort: 30096
    name: http
```

**Apply service:**

```bash
kubectl apply -f gateway-service.yaml
```

### 6. Essential Kubernetes Commands

#### Viewing Resources

```bash
# Get all resources
kubectl get all

# Get pods
kubectl get pods

# Get pods with more details
kubectl get pods -o wide

# Get deployments
kubectl get deployments

# Get services
kubectl get services

# Get events
kubectl get events --sort-by='.lastTimestamp'

# Watch resources in real-time
kubectl get pods -w
```

#### Describing Resources

```bash
# Describe pod (shows detailed information)
kubectl describe pod <pod-name>

# Describe deployment
kubectl describe deployment <deployment-name>

# Describe service
kubectl describe service <service-name>
```

#### Viewing Logs

```bash
# View pod logs
kubectl logs <pod-name>

# Follow logs in real-time
kubectl logs -f <pod-name>

# View logs from previous container (if crashed)
kubectl logs <pod-name> --previous

# View logs for all pods with label
kubectl logs -l app=gateway --follow

# View last 100 lines
kubectl logs <pod-name> --tail=100
```

#### Executing Commands in Pods

```bash
# Execute command in pod
kubectl exec <pod-name> -- <command>

# Open interactive shell
kubectl exec -it <pod-name> -- /bin/bash

# Example: Check if service is accessible
kubectl exec -it <pod-name> -- curl localhost:9696/health
```

#### Port Forwarding

```bash
# Forward pod port to localhost
kubectl port-forward pod/<pod-name> 9696:9696

# Forward service port to localhost
kubectl port-forward service/gateway-service 9696:9696

# Forward deployment port to localhost
kubectl port-forward deployment/gateway 9696:9696

# Forward to different local port
kubectl port-forward pod/<pod-name> 8080:9696
```

**What happens:**

- Creates tunnel from localhost to pod/service
- Useful for local testing without exposing service
- Runs in foreground (Ctrl+C to stop)

#### Scaling Applications

```bash
# Scale deployment to 3 replicas
kubectl scale deployment gateway --replicas=3

# Verify scaling
kubectl get pods

# Autoscaling based on CPU
kubectl autoscale deployment gateway --cpu-percent=70 --min=2 --max=10
```

#### Updating Deployments

```bash
# Update image
kubectl set image deployment/gateway gateway=clothing-model-gateway:002

# Check rollout status
kubectl rollout status deployment/gateway

# View rollout history
kubectl rollout history deployment/gateway

# Rollback to previous version
kubectl rollout undo deployment/gateway

# Rollback to specific revision
kubectl rollout undo deployment/gateway --to-revision=2
```

#### Deleting Resources

```bash
# Delete pod (deployment will recreate it)
kubectl delete pod <pod-name>

# Delete deployment
kubectl delete deployment <deployment-name>

# Delete service
kubectl delete service <service-name>

# Delete using file
kubectl delete -f gateway-deployment.yaml

# Delete all resources with label
kubectl delete all -l app=gateway

# Force delete pod
kubectl delete pod <pod-name> --force --grace-period=0
```

#### Resource Management

```bash
# View resource usage (requires metrics-server)
kubectl top nodes
kubectl top pods

# Edit resource live
kubectl edit deployment gateway

# Apply changes from file
kubectl apply -f deployment.yaml

# Dry run (see what would happen)
kubectl apply -f deployment.yaml --dry-run=client

# Show differences before applying
kubectl diff -f deployment.yaml
```

### 7. Complete Deployment Workflow

**Step-by-step deployment:**

```bash
# 1. Create cluster
kind create cluster --name ml-cluster

# 2. Load images
kind load docker-image clothing-model:xception-v4-001 --name ml-cluster
kind load docker-image clothing-model-gateway:001 --name ml-cluster

# 3. Deploy TensorFlow Serving
kubectl apply -f tf-serving-deployment.yaml
kubectl apply -f tf-serving-service.yaml

# 4. Wait for TF Serving to be ready
kubectl wait --for=condition=ready pod -l app=tf-serving --timeout=120s

# 5. Deploy Gateway
kubectl apply -f gateway-deployment.yaml
kubectl apply -f gateway-service.yaml

# 6. Wait for Gateway to be ready
kubectl wait --for=condition=ready pod -l app=gateway --timeout=120s

# 7. Check status
kubectl get all

# 8. View logs
kubectl logs -l app=gateway --follow
```

---

## Testing and Validation

### 1. Local Testing with Port Forward

```bash
# Terminal 1: Set up port forwarding
kubectl port-forward deployment/gateway 9696:9696

# Terminal 2: Test with Python
python test.py
```

### 2. Test Script

**test.py:**

```python
import requests

url = "http://localhost:9696/predict"
data = {"url": "http://bit.ly/mlbookcamp-pants"}

try:
    response = requests.post(url, json=data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Prediction: {result}")
    else:
        print(f"Error: {response.text}")
        
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: {e}")
    print("Make sure port-forward is running and pod is ready")
except requests.exceptions.Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Error: {e}")
```

### 3. Health Check Testing

```bash
# Test gateway health endpoint
kubectl exec -it deployment/gateway -- curl localhost:9696/health

# Test TF Serving
kubectl exec -it deployment/gateway -- curl tf-serving-clothing-model:8500
```

### 4. Load Testing

**load_test.py:**

```python
import requests
import concurrent.futures
import time

url = "http://localhost:9696/predict"
data = {"url": "http://bit.ly/mlbookcamp-pants"}

def make_request(i):
    try:
        start = time.time()
        response = requests.post(url, json=data, timeout=10)
        duration = time.time() - start
        return {"index": i, "status": response.status_code, "duration": duration}
    except Exception as e:
        return {"index": i, "error": str(e)}

# Run 100 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request, i) for i in range(100)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

# Analyze results
successful = [r for r in results if r.get("status") == 200]
failed = [r for r in results if "error" in r]

print(f"Successful: {len(successful)}")
print(f"Failed: {len(failed)}")
print(f"Average duration: {sum(r['duration'] for r in successful) / len(successful):.2f}s")
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. ImagePullBackOff Error

**Symptoms:**

```bash
kubectl get pods
# NAME                       READY   STATUS             RESTARTS   AGE
# gateway-xxx                0/1     ImagePullBackOff   0          2m
```

**Cause:** Kubernetes can't find the image

**Solutions:**

```bash
# For kind, load the image
kind load docker-image clothing-model-gateway:001 --name ml-cluster

# For other environments, check image name and tag
kubectl describe pod <pod-name> | grep -A 5 "Events"

# Set imagePullPolicy to IfNotPresent in deployment
imagePullPolicy: IfNotPresent
```

#### 2. CrashLoopBackOff Error

**Symptoms:**

```bash
kubectl get pods
# NAME                       READY   STATUS             RESTARTS   AGE
# gateway-xxx                0/1     CrashLoopBackOff   5          10m
```

**Diagnosis:**

```bash
# Check logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous

# Describe pod for events
kubectl describe pod <pod-name>
```

**Common causes:**

- OOMKilled (insufficient memory)
- Application error
- Missing dependencies
- Wrong command/entrypoint

**Solutions:**

```yaml
# Increase resources
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

#### 3. Service Connection Issues

**Symptoms:**

- Gateway can't connect to TF Serving
- Connection refused errors

**Diagnosis:**

```bash
# Check if service exists
kubectl get services

# Test connectivity from gateway pod
kubectl exec -it deployment/gateway -- curl tf-serving-clothing-model:8500

# Check service endpoints
kubectl get endpoints tf-serving-clothing-model
```

**Solutions:**

```bash
# Verify service selector matches pod labels
kubectl get pods --show-labels
kubectl describe service tf-serving-clothing-model

# Check if TF Serving pods are ready
kubectl get pods -l app=tf-serving
```

#### 4. Port Forward Not Working

**Symptoms:**

- Can't connect to localhost:9696
- Connection refused

**Solutions:**

```bash
# Ensure pod is running and ready
kubectl get pods

# Check pod logs
kubectl logs -l app=gateway

# Try different port forward method
kubectl port-forward service/gateway-service 9696:9696

# Check if port is already in use
netstat -an | grep 9696  # Linux/Mac
netstat -an | findstr 9696  # Windows
```

#### 5. Resource Exhaustion

**Symptoms:**

- Pods pending
- Nodes not ready

**Diagnosis:**

```bash
# Check node resources
kubectl top nodes
kubectl describe node

# Check pod resource requests
kubectl describe pod <pod-name> | grep -A 5 "Requests"
```

**Solutions:**

```bash
# Reduce resource requests
# or
# Add more nodes to cluster
# or
# Delete unnecessary pods
kubectl delete pod <pod-name>
```

---

## Best Practices

### 1. Docker Best Practices

```dockerfile
# Use specific versions, not 'latest'
FROM python:3.11-slim

# Use multi-stage builds for smaller images
FROM python:3.11 as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .

# Don't run as root
USER 1000:1000

# Use .dockerignore to exclude unnecessary files
# .dockerignore:
# .git
# __pycache__
# *.pyc
# .env
```

### 2. Kubernetes Best Practices

```yaml
# Always set resource limits and requests
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "200m"

# Use health checks
livenessProbe:
  httpGet:
    path: /health
    port: 9696
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 9696
  initialDelaySeconds: 10
  periodSeconds: 5

# Use labels consistently
metadata:
  labels:
    app: gateway
    version: v1
    environment: production

# Use namespaces for isolation
metadata:
  namespace: ml-services

# Use ConfigMaps for configuration
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-config
data:
  TF_SERVING_HOST: "tf-serving-clothing-model:8500"
  LOG_LEVEL: "INFO"

# Reference in deployment
env:
- name: TF_SERVING_HOST
  valueFrom:
    configMapKeyRef:
      name: gateway-config
      key: TF_SERVING_HOST
```

### 3. Development Workflow

```bash
# 1. Build and test locally
docker build -t gateway:dev .
docker run -p 9696:9696 gateway:dev

# 2. Load into kind
kind load docker-image gateway:dev

# 3. Deploy with dev tag
kubectl set image deployment/gateway gateway=gateway:dev

# 4. Monitor deployment
kubectl rollout status deployment/gateway
kubectl logs -l app=gateway --follow

# 5. Test
curl http://localhost:9696/health

# 6. If issues, rollback
kubectl rollout undo deployment/gateway
```

### 4. Production Checklist

- [ ] Resource limits properly configured
- [ ] Health checks implemented and working
- [ ] Logging configured and centralized
- [ ] Monitoring and alerting set up
- [ ] Horizontal Pod Autoscaling configured
- [ ] Network policies in place
- [ ] Secrets properly managed (not in code)
- [ ] Backup and disaster recovery plan
- [ ] Load testing completed
- [ ] Documentation updated

---

## Summary

This guide covered:

1. **Docker Workflow**: Building images, running containers, and using Docker Compose
2. **Kubernetes Workflow**: Creating clusters, deployments, services, and managing resources
3. **Testing**: Port forwarding, health checks, and load testing
4. **Troubleshooting**: Common issues and their solutions
5. **Best Practices**: Production-ready configurations

### Quick Reference Commands

```bash
# Docker
docker build -t image:tag .
docker run -p HOST:CONTAINER image:tag
docker ps
docker logs <container-id>

# Kubernetes
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs <pod-name>
kubectl describe pod <pod-name>
kubectl port-forward deployment/gateway 9696:9696
kubectl delete -f deployment.yaml

# kind
kind create cluster --name ml-cluster
kind load docker-image image:tag --name ml-cluster
kind delete cluster --name ml-cluster
```

### Additional Resources

- Docker Documentation: <https://docs.docker.com/>
- Kubernetes Documentation: <https://kubernetes.io/docs/>
- kind Documentation: <https://kind.sigs.k8s.io/>
- TensorFlow Serving: <https://www.tensorflow.org/tfx/guide/serving>
- kubectl Cheat Sheet: <https://kubernetes.io/docs/reference/kubectl/cheatsheet/>
