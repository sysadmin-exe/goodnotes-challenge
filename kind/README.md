# KinD Cluster Configuration

This directory contains configuration files for provisioning a local Kubernetes cluster using [KinD](https://kind.sigs.k8s.io/) (Kubernetes in Docker).

## Cluster Architecture

| Node | Role | Description |
|------|------|-------------|
| goodnotes-cluster-control-plane | Control Plane | Kubernetes master node with ingress support |
| goodnotes-cluster-worker | Worker | Application workload node |
| goodnotes-cluster-worker2 | Worker | Application workload node |

## Files

| File | Description |
|------|-------------|
| `main.yaml` | KinD cluster configuration (3 nodes, port mappings) |
| `ingress-nginx.yaml` | NGINX Ingress controller manifest |

## Prerequisites

- [Docker](https://www.docker.com/) installed and running
- [KinD](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed

## Quick Start

### Create Cluster

```bash
kind create cluster --config main.yaml
```

### Deploy Ingress Controller

```bash
kubectl apply -f ingress-nginx.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### Verify Cluster

```bash
# Check nodes
kubectl get nodes

# Check ingress controller
kubectl get pods -n ingress-nginx
```

## Configuration Details

### Cluster (`main.yaml`)

| Setting | Value | Description |
|---------|-------|-------------|
| Cluster Name | goodnotes-cluster | Name of the KinD cluster |
| Kubernetes Version | v1.34.0 | Version of Kubernetes to deploy |
| API Server Port | 7893 | Local port for kubectl access |
| Nodes | 3 | 1 control-plane + 2 workers |

### Port Mappings

The control-plane node exposes ports for ingress:

| Host Port | Container Port | Protocol | Purpose |
|-----------|----------------|----------|---------|
| 80 | 80 | TCP | HTTP traffic |
| 443 | 443 | TCP | HTTPS traffic |

### Node Labels

The control-plane node has `ingress-ready=true` label, allowing the ingress controller to be scheduled on it with host port bindings.

## Ingress Controller

The `ingress-nginx.yaml` deploys the NGINX Ingress controller configured for KinD:

- Runs on nodes with `ingress-ready=true` label
- Uses `hostPort` for direct port binding
- Includes admission webhook for Ingress validation

## Common Commands

```bash
# List clusters
kind get clusters

# Get cluster info
kubectl cluster-info --context kind-goodnotes-cluster

# Delete cluster
kind delete cluster --name goodnotes-cluster

# Load local Docker image into cluster
kind load docker-image my-image:tag --name goodnotes-cluster
```

## Troubleshooting

### Cluster won't start
```bash
# Check Docker is running
docker ps

# Check for port conflicts
lsof -i :80
lsof -i :443
```

### Ingress not working
```bash
# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify ingress resources
kubectl get ingress -A
```

### Reset cluster
```bash
kind delete cluster --name goodnotes-cluster
kind create cluster --config main.yaml
```