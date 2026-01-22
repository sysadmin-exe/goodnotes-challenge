#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python 3.8+."
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import locust" 2>/dev/null; then
    echo "==> Installing Python dependencies..."
    pip3 install -r "${SCRIPT_DIR}/requirements.txt"
fi

# Default URLs file
URLS_FILE="${URLS_FILE:-${SCRIPT_DIR}/urls.json}"

# Create results directory
mkdir -p "${SCRIPT_DIR}/results"

# Build command arguments
CMD_ARGS=(
    --users "${USERS:-20}"
    --spawn-rate "${SPAWN_RATE:-5}"
    --duration "${DURATION:-180}"
    --threshold-p95 "${THRESHOLD_P95:-500}"
    --threshold-p99 "${THRESHOLD_P99:-1000}"
    --threshold-error-rate "${THRESHOLD_ERROR_RATE:-5}"
    --output-dir "${SCRIPT_DIR}/results"
)

# Add URLs file if it exists
if [[ -f "${URLS_FILE}" ]]; then
    CMD_ARGS+=(--urls "${URLS_FILE}")
fi

echo "==> Running load test"
echo "    URLs file: ${URLS_FILE}"
echo "    Users: ${USERS:-20}"
echo "    Duration: ${DURATION:-180}s"
echo ""

# Run load test
python3 "${SCRIPT_DIR}/loadtest.py" "${CMD_ARGS[@]}"

echo ""
echo "==> Load test completed!"
echo "    Results saved to: ${SCRIPT_DIR}/results/"
echo "    - summary.json: Raw JSON results"
echo "    - summary.md: Markdown summary"
