# Cloud Deployment Guide (AWS EKS)

This guide walks you through deploying the Smart Fashion Classifier to **AWS Elastic Kubernetes Service (EKS)**.

## 1. Prerequisites

Ensure you have the following installed and configured:
1.  **AWS CLI**: Configured with your credentials (`aws configure`).
2.  **eksctl**: The CLI for Amazon EKS.
3.  **kubectl**: The Kubernetes CLI.
4.  **Docker Account**: To publish your images (or use AWS ECR).

## 2. Publish Docker Images

Your local images (`clothing-model:v1`, etc.) exist only on your laptop. The cloud cluster needs to download them from a registry. We will use **Docker Hub** for simplicity.

1.  **Login to Docker Hub:**
    ```bash
    docker login
    ```

2.  **Tag Images with your Username:**
    Replace `fsamura01` with your Docker Hub username.
    ```bash
    export DOCKER_USER=fsamura01 
    
    docker tag clothing-model:v1 $DOCKER_USER/clothing-model:v1
    docker tag fashion-gateway:v1 $DOCKER_USER/fashion-gateway:v1
    docker tag fashion-frontend:v1 $DOCKER_USER/fashion-frontend:v1
    ```

3.  **Push Images:**
    ```bash
    docker push $DOCKER_USER/clothing-model:v1
    docker push $DOCKER_USER/fashion-gateway:v1
    docker push $DOCKER_USER/fashion-frontend:v1
    ```

4.  **Update Kubernetes Files:**
    You must update your YAML files in `kube-config/` to point to these new public image names.
    *   `model-deployment.yaml`: `image: clothing-model:v1` -> `image: fsamura01/clothing-model:v1`
    *   `gateway-deployment.yaml`: `image: fashion-gateway:v1` -> `image: fsamura01/fashion-gateway:v1`
    *   `frontend-deployment.yaml`: `image: fashion-frontend:v1` -> `image: fsamura01/fashion-frontend:v1`

## 3. Create EKS Cluster

You already have an EKS configuration file: `kube-config/eks-config.yaml`.

1.  **Create the Cluster:**
    This command will provision EC2 instances (m5.xlarge) and set up the control plane. It takes **15-20 minutes**.
    ```bash
    eksctl create cluster -f kube-config/eks-config.yaml
    ```

2.  **Verify Connection:**
    ```bash
    kubectl get nodes
    ```

## 4. Deploy Application

Once the cluster is ready, deploy your application just like you did locally.

1.  **Apply Manifests:**
    ```bash
    kubectl apply -f kube-config/
    ```

2.  **Wait for Load Balancers:**
    On AWS, `type: LoadBalancer` provisions a real **Classic Load Balancer (CLB)** or NLB.
    ```bash
    kubectl get services
    ```
    *Look for the `EXTERNAL-IP` column. It will be a long DNS name (e.g., `a1b2c...eu-west-1.elb.amazonaws.com`).*

## 5. Access the App

1.  **Frontend:** Copy the `EXTERNAL-IP` of the `frontend` service. Paste it into your browser (port 80).
2.  **Gateway:** The `gateway` service also has an external IP, allowing you to run `test.py` against it from your laptop (update `url` in `test.py`).

## 6. Cleanup (Important!)

EKS is expensive. When finished, delete the cluster to avoid charges.

```bash
eksctl delete cluster -f kube-config/eks-config.yaml
```
