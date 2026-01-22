#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Adding Prometheus community Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

echo "==> Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "==> Installing kube-prometheus-stack..."
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values "${SCRIPT_DIR}/values.yaml" \
  --wait \
  --timeout 10m

echo "==> Waiting for Grafana to be ready..."
kubectl wait --namespace monitoring \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=grafana \
  --timeout=120s

echo "==> Waiting for Prometheus to be ready..."
kubectl wait --namespace monitoring \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=prometheus \
  --timeout=120s

echo "==> Installing Ingress Service for monitoring stack..."
kubectl apply -f ingress-service.yaml

echo ""
echo "==> kube-prometheus-stack installed successfully!"
echo ""
echo "Access URLs (add to /etc/hosts: 127.0.0.1 grafana.localhost prometheus.localhost alertmanager.localhost):"
echo "  - Grafana:      http://grafana.localhost"
echo "  - Prometheus:   http://prometheus.localhost"
echo "  - Alertmanager: http://alertmanager.localhost"
echo ""
echo "Grafana credentials:"
echo "  - Username: admin"
echo "  - Password: admin"
echo ""
echo "Or use port-forward:"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090"
echo "  kubectl port-forward -n monitoring svc/kube-prometheus-stack-alertmanager 9093:9093"