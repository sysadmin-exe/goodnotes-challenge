## 📊 Resource Utilization Metrics

*Collected at 2026-01-22T13:06:16.637483 (last 5 minutes)*

### Pod Resource Usage

| Namespace | Pod | CPU (millicores) | Memory (MB) | Network RX (KB/s) | Network TX (KB/s) |
|-----------|-----|------------------|-------------|-------------------|-------------------|
| default | http-echo-bar-567ff47c48-d77fm | 8.96 | 14.4 | 9.67 | 4.71 |
| default | http-echo-foo-6ffcbb6445-277fv | 9.56 | 13.48 | 9.79 | 4.77 |
| ingress-nginx | ingress-nginx-controller-5cbbcf6489-8qxk... | 40.59 | 173.69 | 21.5 | 31.18 |

### Ingress Controller Metrics (from Prometheus)

| Host | Requests | Req/sec | p50 (ms) | p95 (ms) | p99 (ms) |
|------|----------|---------|----------|----------|----------|
| bar.localhost | 11612 | 20.32 | 2.5 | 4.76 | 4.96 |
| foo.localhost | 11780 | 20.74 | 2.5 | 4.76 | 4.96 |

