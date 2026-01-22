# Load Testing

This directory contains Python-based load testing using [Locust](https://locust.io/) for the http-echo services.

## Why Locust?

| Reason | Benefit |
|--------|---------|
| **Pure Python** | Easy to understand and modify without learning a new language or DSL |
| **Simple syntax** | Tests are just Python classes with `@task` decorators |
| **Programmatic control** | Runs headless (no UI needed) and generates reports programmatically - perfect for CI |
| **Flexible traffic patterns** | Easy to randomize between endpoints with standard Python |
| **Built-in statistics** | Provides percentiles (p50, p90, p95, p99), request counts, failure rates out of the box |
| **Lightweight** | Single pip install, no external dependencies like browsers or JVM |
| **Well-documented** | Active community with good documentation |

**Alternatives considered:**

| Tool | Why not chosen |
|------|----------------|
| k6 | JavaScript-based |
| JMeter | Heavy, XML-based config, requires Java |
| Gatling | Scala-based, steeper learning curve |
| wrk/ab | Too basic - hard to randomize traffic and generate detailed reports |
| Artillery | JavaScript/YAML based |

## Prerequisites

- Python 3.8+
- http-echo services deployed and accessible

## Installation

```bash
pip install -r requirements.txt
```

## Local Usage

### Quick Start

```bash
./run.sh
```

### Custom Configuration

```bash
FOO_HOST=http://foo.localhost BAR_HOST=http://bar.localhost USERS=50 DURATION=300 ./run.sh
```

### Direct Python Execution

```bash
python loadtest.py --users 20 --spawn-rate 5 --duration 180 --output-dir results
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--users` | Number of concurrent users | 20 |
| `--spawn-rate` | Users to spawn per second | 5 |
| `--duration` | Test duration in seconds | 180 |
| `--output-dir` | Output directory for results | results |
| `--urls` | JSON file or inline JSON array of URLs to test | See below |
| `--threshold-p95` | p95 response time threshold (ms) | 500 |
| `--threshold-p99` | p99 response time threshold (ms) | 1000 |
| `--threshold-error-rate` | Error rate threshold (%) | 5.0 |

### URL Configuration

URLs can be configured in three ways:

**1. JSON file:**
```bash
python loadtest.py --urls urls.json
```

**2. Inline JSON:**
```bash
python loadtest.py --urls '[{"name": "api", "url": "http://api.localhost", "expected": "ok"}]'
```

**3. Environment variables (default):**
```bash
FOO_HOST=http://foo.localhost BAR_HOST=http://bar.localhost python loadtest.py
```

URL JSON format:
```json
[
  {"name": "foo", "url": "http://foo.localhost", "expected": "foo"},
  {"name": "bar", "url": "http://bar.localhost", "expected": "bar"}
]
```

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Display name for the endpoint | Yes |
| `url` | Full URL to test | Yes |
| `expected` | Expected text in response (for validation) | No |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FOO_HOST` | URL for foo service | http://foo.localhost |
| `BAR_HOST` | URL for bar service | http://bar.localhost |

## Test Behavior

The load test:
- Tests all URLs specified in the configuration
- Randomly selects between endpoints for each request
- Waits 100-500ms between requests (per user)
- Validates response status and content (if `expected` is set)
- Prints detailed per-URL results

## Output

Results are saved to the `results/` directory:
- `summary.json` - Full JSON metrics
- `summary.md` - Markdown summary (used for PR comments)

Console output includes:
- Overall summary (total requests, failures, response times)
- Per-URL breakdown with individual metrics

## Thresholds

The test will fail if any threshold is exceeded. Default thresholds:
- p95 response time > 500ms
- p99 response time > 1000ms
- Error rate > 5%

Thresholds are configurable via command-line arguments:

```bash
# Stricter thresholds
python loadtest.py --threshold-p95 100 --threshold-p99 200 --threshold-error-rate 1

# More lenient thresholds
python loadtest.py --threshold-p95 1000 --threshold-p99 2000 --threshold-error-rate 10
```

## Output

Results are saved to the `results/` directory:
- `summary.json` - Full JSON metrics
- `summary.md` - Markdown summary (used for PR comments)

## CI Integration

The load test runs automatically on Pull Requests via GitHub Actions. Results are posted as a comment on the PR.

## Resource Metrics Collection

The `collect_metrics.py` script queries Prometheus to capture resource utilization during load tests.

### Usage

```bash
python collect_metrics.py \
  --prometheus-url http://localhost:9090 \
  --namespaces "foo,bar,ingress-nginx" \
  --hosts "foo.localhost,bar.localhost" \
  --duration 5 \
  --output-dir results
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--prometheus-url` | Prometheus server URL | http://localhost:9090 |
| `--namespaces` | Comma-separated namespaces to monitor | foo,bar,ingress-nginx |
| `--hosts` | Comma-separated ingress hosts | foo.localhost,bar.localhost |
| `--duration` | Minutes for rate calculations | 5 |
| `--output-dir` | Output directory | results |
| `--output-format` | Output format: json, markdown, or both | both |

### Collected Metrics

**Pod Metrics:**
- CPU usage (millicores)
- Memory usage (MB)
- Network RX/TX (KB/s)

**Ingress Metrics:**
- Total requests per host
- Requests per second
- Response time percentiles (p50, p95, p99)

### Output

- `resource_metrics.json` - Full JSON metrics from Prometheus
- `resource_metrics.md` - Markdown table (combined with load test results in CI)

### Prerequisites

- Prometheus must be deployed and accessible
- ServiceMonitor for ingress-nginx must be applied (see `/monitoring/ingress-servicemonitor.yaml`)
