#!/usr/bin/env python3
"""
Collect resource utilization metrics from Prometheus.
Queries CPU, memory, and network metrics for specified namespaces/pods.
"""

import argparse
import json
import requests
from datetime import datetime
from urllib.parse import urljoin


class PrometheusClient:
    """Simple Prometheus query client."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def query(self, promql: str) -> dict:
        """Execute an instant query."""
        url = f"{self.base_url}/api/v1/query"
        response = requests.get(url, params={'query': promql}, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def query_range(self, promql: str, start: float, end: float, step: str = '15s') -> dict:
        """Execute a range query."""
        url = f"{self.base_url}/api/v1/query_range"
        response = requests.get(url, params={
            'query': promql,
            'start': start,
            'end': end,
            'step': step
        }, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_scalar_value(self, promql: str) -> float:
        """Get a single scalar value from a query."""
        result = self.query(promql)
        if result.get('status') == 'success' and result.get('data', {}).get('result'):
            value = result['data']['result'][0]['value'][1]
            return float(value)
        return 0.0


def collect_pod_metrics(client: PrometheusClient, namespaces: list, duration_minutes: int = 5) -> dict:
    """Collect resource utilization metrics for pods in specified namespaces."""
    
    ns_selector = '|'.join(namespaces)
    
    metrics = {
        'namespaces': namespaces,
        'collection_time': datetime.now().isoformat(),
        'duration_minutes': duration_minutes,
        'cpu': {},
        'memory': {},
        'network': {},
    }
    
    # CPU Usage (cores)
    cpu_query = f'sum by (namespace, pod) (rate(container_cpu_usage_seconds_total{{namespace=~"{ns_selector}", container!=""}}[{duration_minutes}m]))'
    cpu_result = client.query(cpu_query)
    if cpu_result.get('status') == 'success':
        for item in cpu_result.get('data', {}).get('result', []):
            ns = item['metric'].get('namespace', 'unknown')
            pod = item['metric'].get('pod', 'unknown')
            value = float(item['value'][1])
            if ns not in metrics['cpu']:
                metrics['cpu'][ns] = {}
            metrics['cpu'][ns][pod] = {
                'usage_cores': round(value, 4),
                'usage_millicores': round(value * 1000, 2),
            }
    
    # Memory Usage (bytes)
    mem_query = f'sum by (namespace, pod) (container_memory_working_set_bytes{{namespace=~"{ns_selector}", container!=""}})'
    mem_result = client.query(mem_query)
    if mem_result.get('status') == 'success':
        for item in mem_result.get('data', {}).get('result', []):
            ns = item['metric'].get('namespace', 'unknown')
            pod = item['metric'].get('pod', 'unknown')
            value = float(item['value'][1])
            if ns not in metrics['memory']:
                metrics['memory'][ns] = {}
            metrics['memory'][ns][pod] = {
                'usage_bytes': round(value, 0),
                'usage_mb': round(value / (1024 * 1024), 2),
            }
    
    # Network I/O (bytes/sec)
    net_rx_query = f'sum by (namespace, pod) (rate(container_network_receive_bytes_total{{namespace=~"{ns_selector}"}}[{duration_minutes}m]))'
    net_tx_query = f'sum by (namespace, pod) (rate(container_network_transmit_bytes_total{{namespace=~"{ns_selector}"}}[{duration_minutes}m]))'
    
    net_rx_result = client.query(net_rx_query)
    net_tx_result = client.query(net_tx_query)
    
    if net_rx_result.get('status') == 'success':
        for item in net_rx_result.get('data', {}).get('result', []):
            ns = item['metric'].get('namespace', 'unknown')
            pod = item['metric'].get('pod', 'unknown')
            value = float(item['value'][1])
            if ns not in metrics['network']:
                metrics['network'][ns] = {}
            if pod not in metrics['network'][ns]:
                metrics['network'][ns][pod] = {}
            metrics['network'][ns][pod]['rx_bytes_per_sec'] = round(value, 2)
            metrics['network'][ns][pod]['rx_kb_per_sec'] = round(value / 1024, 2)
    
    if net_tx_result.get('status') == 'success':
        for item in net_tx_result.get('data', {}).get('result', []):
            ns = item['metric'].get('namespace', 'unknown')
            pod = item['metric'].get('pod', 'unknown')
            value = float(item['value'][1])
            if ns not in metrics['network']:
                metrics['network'][ns] = {}
            if pod not in metrics['network'][ns]:
                metrics['network'][ns][pod] = {}
            metrics['network'][ns][pod]['tx_bytes_per_sec'] = round(value, 2)
            metrics['network'][ns][pod]['tx_kb_per_sec'] = round(value / 1024, 2)
    
    return metrics


def collect_ingress_metrics(client: PrometheusClient, hosts: list, duration_minutes: int = 5) -> dict:
    """Collect NGINX Ingress Controller metrics for specified hosts."""
    
    host_selector = '|'.join(hosts)
    
    metrics = {
        'hosts': hosts,
        'ingress': {},
    }
    
    # Request count per host
    req_query = f'sum by (host) (nginx_ingress_controller_requests{{host=~"{host_selector}"}})'
    req_result = client.query(req_query)
    if req_result.get('status') == 'success':
        for item in req_result.get('data', {}).get('result', []):
            host = item['metric'].get('host', 'unknown')
            value = float(item['value'][1])
            if host not in metrics['ingress']:
                metrics['ingress'][host] = {}
            metrics['ingress'][host]['total_requests'] = int(value)
    
    # Request rate per host
    rate_query = f'sum by (host) (rate(nginx_ingress_controller_requests{{host=~"{host_selector}"}}[{duration_minutes}m]))'
    rate_result = client.query(rate_query)
    if rate_result.get('status') == 'success':
        for item in rate_result.get('data', {}).get('result', []):
            host = item['metric'].get('host', 'unknown')
            value = float(item['value'][1])
            if host not in metrics['ingress']:
                metrics['ingress'][host] = {}
            metrics['ingress'][host]['requests_per_sec'] = round(value, 2)
    
    # Response time percentiles per host
    for percentile, label in [(0.50, 'p50'), (0.95, 'p95'), (0.99, 'p99')]:
        latency_query = f'histogram_quantile({percentile}, sum by (host, le) (rate(nginx_ingress_controller_request_duration_seconds_bucket{{host=~"{host_selector}"}}[{duration_minutes}m])))'
        latency_result = client.query(latency_query)
        if latency_result.get('status') == 'success':
            for item in latency_result.get('data', {}).get('result', []):
                host = item['metric'].get('host', 'unknown')
                value = float(item['value'][1])
                if host not in metrics['ingress']:
                    metrics['ingress'][host] = {}
                metrics['ingress'][host][f'{label}_latency_ms'] = round(value * 1000, 2)
    
    return metrics


def generate_markdown_report(pod_metrics: dict, ingress_metrics: dict) -> str:
    """Generate a Markdown report from collected metrics."""
    
    md = "## 📊 Resource Utilization Metrics\n\n"
    md += f"*Collected at {pod_metrics.get('collection_time', 'N/A')} (last {pod_metrics.get('duration_minutes', 5)} minutes)*\n\n"
    
    # CPU and Memory per namespace
    md += "### Pod Resource Usage\n\n"
    md += "| Namespace | Pod | CPU (millicores) | Memory (MB) | Network RX (KB/s) | Network TX (KB/s) |\n"
    md += "|-----------|-----|------------------|-------------|-------------------|-------------------|\n"
    
    for ns in pod_metrics.get('cpu', {}):
        for pod in pod_metrics['cpu'].get(ns, {}):
            cpu = pod_metrics['cpu'].get(ns, {}).get(pod, {}).get('usage_millicores', 0)
            mem = pod_metrics['memory'].get(ns, {}).get(pod, {}).get('usage_mb', 0)
            rx = pod_metrics['network'].get(ns, {}).get(pod, {}).get('rx_kb_per_sec', 0)
            tx = pod_metrics['network'].get(ns, {}).get(pod, {}).get('tx_kb_per_sec', 0)
            # Truncate long pod names
            pod_display = pod[:40] + '...' if len(pod) > 40 else pod
            md += f"| {ns} | {pod_display} | {cpu} | {mem} | {rx} | {tx} |\n"
    
    # Ingress metrics
    if ingress_metrics.get('ingress'):
        md += "\n### Ingress Controller Metrics (from Prometheus)\n\n"
        md += "| Host | Requests | Req/sec | p50 (ms) | p95 (ms) | p99 (ms) |\n"
        md += "|------|----------|---------|----------|----------|----------|\n"
        
        for host, data in ingress_metrics.get('ingress', {}).items():
            total_req = data.get('total_requests', 0)
            rps = data.get('requests_per_sec', 0)
            p50 = data.get('p50_latency_ms', 0)
            p95 = data.get('p95_latency_ms', 0)
            p99 = data.get('p99_latency_ms', 0)
            md += f"| {host} | {total_req} | {rps} | {p50} | {p95} | {p99} |\n"
    
    md += "\n"
    return md


def load_config_from_urls_file(urls_file: str) -> tuple:
    """Load namespaces and hosts from urls.json file."""
    with open(urls_file, 'r') as f:
        urls_config = json.load(f)
    
    namespaces = set()
    hosts = []
    
    for entry in urls_config:
        # Extract namespace
        if 'namespace' in entry:
            namespaces.add(entry['namespace'])
        
        # Extract host from URL
        url = entry.get('url', '')
        if url:
            # Parse host from URL (e.g., http://foo.localhost -> foo.localhost)
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc:
                hosts.append(parsed.netloc)
    
    # Always include ingress-nginx namespace for ingress metrics
    namespaces.add('ingress-nginx')
    
    return list(namespaces), hosts


def main():
    parser = argparse.ArgumentParser(description='Collect resource metrics from Prometheus')
    parser.add_argument('--prometheus-url', type=str, default='http://localhost:9090',
                        help='Prometheus server URL')
    parser.add_argument('--urls', type=str, default=None,
                        help='JSON file containing URLs config (extracts namespaces and hosts)')
    parser.add_argument('--namespaces', type=str, default=None,
                        help='Comma-separated list of namespaces to monitor (overrides --urls)')
    parser.add_argument('--hosts', type=str, default=None,
                        help='Comma-separated list of ingress hosts to monitor (overrides --urls)')
    parser.add_argument('--duration', type=int, default=5,
                        help='Duration in minutes for rate calculations')
    parser.add_argument('--output-dir', type=str, default='results',
                        help='Output directory for results')
    parser.add_argument('--output-format', type=str, choices=['json', 'markdown', 'both'],
                        default='both', help='Output format')
    
    args = parser.parse_args()
    
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"==> Collecting metrics from Prometheus at {args.prometheus_url}")
    
    client = PrometheusClient(args.prometheus_url)
    
    # Load config from urls file or use explicit arguments
    if args.urls and os.path.isfile(args.urls):
        namespaces_from_file, hosts_from_file = load_config_from_urls_file(args.urls)
        namespaces = [ns.strip() for ns in args.namespaces.split(',')] if args.namespaces else namespaces_from_file
        hosts = [h.strip() for h in args.hosts.split(',')] if args.hosts else hosts_from_file
    else:
        namespaces = [ns.strip() for ns in args.namespaces.split(',')] if args.namespaces else ['default', 'ingress-nginx']
        hosts = [h.strip() for h in args.hosts.split(',')] if args.hosts else ['foo.localhost', 'bar.localhost']
    
    print(f"    Namespaces: {namespaces}")
    print(f"    Hosts: {hosts}")
    print(f"    Duration: {args.duration} minutes")
    
    # Collect metrics
    pod_metrics = collect_pod_metrics(client, namespaces, args.duration)
    ingress_metrics = collect_ingress_metrics(client, hosts, args.duration)
    
    # Combine metrics
    combined = {
        **pod_metrics,
        **ingress_metrics,
    }
    
    # Save outputs
    if args.output_format in ['json', 'both']:
        json_path = os.path.join(args.output_dir, 'resource_metrics.json')
        with open(json_path, 'w') as f:
            json.dump(combined, f, indent=2)
        print(f"==> JSON saved to {json_path}")
    
    if args.output_format in ['markdown', 'both']:
        md_path = os.path.join(args.output_dir, 'resource_metrics.md')
        md_report = generate_markdown_report(pod_metrics, ingress_metrics)
        with open(md_path, 'w') as f:
            f.write(md_report)
        print(f"==> Markdown saved to {md_path}")
        print("\n" + md_report)
    
    print("\n==> Metrics collection complete!")


if __name__ == '__main__':
    main()
