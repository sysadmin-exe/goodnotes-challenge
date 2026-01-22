# GoodNotes Challenge
[Github](https://github.com/sysadmin-exe/goodnotes-challenge)
Duration: 4hrs, 32 mins
A complete Kubernetes infrastructure solution featuring a multi-node KinD cluster, HTTP echo services, monitoring stack, and automated load testing with CI integration.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        KinD Cluster                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Control Plane  │  │     Worker 1    │  │     Worker 2    │  │
│  │  (ingress-ready)│  │                 │  │                 │  │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘  │
│           │                                                      │
│  ┌────────▼────────┐                                            │
│  │ NGINX Ingress   │                                            │
│  │ Controller      │                                            │
│  └────────┬────────┘                                            │
│           │                                                      │
│     ┌─────┴─────┬─────────────┬─────────────┐                   │
│     ▼           ▼             ▼             ▼                   │
│ ┌───────┐  ┌───────┐   ┌──────────┐  ┌────────────┐            │
│ │  foo  │  │  bar  │   │ Grafana  │  │ Prometheus │            │
│ │ ns:foo│  │ ns:bar│   │          │  │            │            │
│ └───────┘  └───────┘   └──────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Load Tester   │
                    │    (Locust)     │
                    └─────────────────┘
```

## Components

| Component | Description | Directory |
|-----------|-------------|-----------|
| **KinD Cluster** | Multi-node Kubernetes cluster (1 control-plane + 2 workers) | [kind/](kind/) |
| **http-echo** | Helm chart deploying foo and bar echo services | [echo/](echo/) |
| **Monitoring** | Prometheus, Grafana, Alertmanager stack | [monitoring/](monitoring/) |
| **Load Testing** | Python-based load testing with Locust | [loadtest/](loadtest/) |
| **CI/CD** | GitHub Actions for automated load testing on PRs | [.github/workflows/](.github/workflows/) |

## Quick Start

### Prerequisites

- Docker
- [KinD](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm 3](https://helm.sh/docs/intro/install/)
- Python 3.8+

### 1. Create Cluster

```bash
kind create cluster --config kind/main.yaml
```

### 2. Deploy Ingress Controller

```bash
kubectl apply -f kind/ingress-nginx.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### 3. Deploy http-echo Services

```bash
helm install http-echo ./echo
```

### 4. Deploy Monitoring (Optional)

```bash
./monitoring/install.sh
```

### 5. Configure Local DNS

Add to `/etc/hosts`:
```
echo "127.0.0.1 foo.localhost bar.localhost grafana.localhost prometheus.localhost alertmanager.localhost" | sudo tee -a /etc/hosts
```

### 6. Verify Deployment

```bash
curl http://foo.localhost   # Returns: foo
curl http://bar.localhost   # Returns: bar
```

## Load Testing

Run load tests against the deployed services:

```bash
cd loadtest
pip install -r requirements.txt
python loadtest.py --urls urls.json --duration 60
```

See [loadtest/README.md](loadtest/README.md) for detailed configuration options.

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| foo | http://foo.localhost | - |
| bar | http://bar.localhost | - |
| Grafana | http://grafana.localhost | admin / admin |
| Prometheus | http://prometheus.localhost | - |
| Alertmanager | http://alertmanager.localhost | - |

## CI/CD Integration

The repository includes a GitHub Actions workflow that:
1. Provisions a KinD cluster on PR
2. Deploys all services
3. Runs load tests
4. Posts results as PR comment

See [.github/workflows/load-test.yaml](.github/workflows/load-test.yaml).

## Directory Structure

```
.
├── README.md                 # This file
├── kind/                     # KinD cluster configuration
│   ├── README.md
│   ├── main.yaml            # Cluster config (3 nodes)
│   └── ingress-nginx.yaml   # Ingress controller manifest
├── echo/                     # http-echo Helm chart
│   ├── README.md
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── monitoring/               # Prometheus/Grafana stack
│   ├── README.md
│   ├── install.sh
│   └── values.yaml
├── loadtest/                 # Load testing suite
│   ├── README.md
│   ├── loadtest.py
│   ├── urls.json
│   ├── requirements.txt
│   └── run.sh
└── .github/
    └── workflows/
        └── load-test.yaml   # CI workflow
```

## Documentation

- [KinD Cluster Setup](kind/README.md)
- [http-echo Helm Chart](echo/README.md)
- [Monitoring Stack](monitoring/README.md)
- [Load Testing](loadtest/README.md)

## Cleanup

```bash
# Delete the cluster (removes everything)
kind delete cluster --name goodnotes-cluster
```

