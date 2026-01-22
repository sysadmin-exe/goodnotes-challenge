# Monitoring Stack

This directory contains the configuration for deploying [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack) - a complete monitoring solution for the local Kubernetes cluster

## Components

| Component | Description | Access URL |
|-----------|-------------|------------|
| **Prometheus** | Metrics collection and storage | http://prometheus.localhost |
| **Grafana** | Metrics visualization and dashboards | http://grafana.localhost |
| **Alertmanager** | Alert handling and notifications | http://alertmanager.localhost |
| **Node Exporter** | Hardware and OS metrics from nodes | - |
| **Kube-State-Metrics** | Kubernetes object state metrics | - |

## Files

| File | Description |
|------|-------------|
| `values.yaml` | Helm values for kube-prometheus-stack customization |
| `install.sh` | Installation script |

## Prerequisites

- Kubernetes cluster running (KinD)
- Helm 3 installed
- NGINX Ingress controller deployed

## Installation

```bash
./install.sh
```

This script will:
1. Add the Prometheus community Helm repository
2. Create the `monitoring` namespace
3. Install kube-prometheus-stack with custom values
4. Wait for Grafana and Prometheus to be ready

## Access

After installation, add to `/etc/hosts`:
```
127.0.0.1 grafana.localhost prometheus.localhost alertmanager.localhost
```

### Grafana
- **URL:** http://grafana.localhost
- **Username:** admin
- **Password:** admin

### Prometheus
- **URL:** http://prometheus.localhost

### Alertmanager
- **URL:** http://alertmanager.localhost

## Port Forwarding (Alternative)

If ingress is not working, use port-forwarding:

```bash
# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# Alertmanager
kubectl port-forward -n monitoring svc/kube-prometheus-stack-alertmanager 9093:9093
```

## Configuration

The `values.yaml` file customizes the deployment:

| Setting | Value | Description |
|---------|-------|-------------|
| Grafana persistence | Disabled | Data not persisted (suitable for dev) |
| Prometheus retention | 24h | Metrics kept for 24 hours |
| Resource limits | Set | Optimized for KinD cluster |
| Ingress | Enabled | Access via *.localhost domains |

## Default Dashboards

Grafana comes with pre-configured dashboards for:
- Kubernetes cluster monitoring
- Node metrics
- Pod metrics
- Namespace overview
- Persistent volume usage

## Uninstall

```bash
helm uninstall kube-prometheus-stack -n monitoring
kubectl delete namespace monitoring
```