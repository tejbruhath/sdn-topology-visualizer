#!/bin/bash
# Start Flask Backend Server

echo "=========================================="
echo "Starting SDN Visualizer Backend"
echo "=========================================="

# Get project root and activate venv
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "⚠️  Virtual environment not found!"
    echo "   Please run ./scripts/setup.sh first"
    exit 1
fi

# Check if Ryu is running
if ! pgrep -f "ryu-manager" > /dev/null; then
    echo "⚠️  WARNING: Ryu controller is not running!"
    echo "   Please start Ryu first: ./scripts/start_ryu.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Ryu is accessible and wait for it to be fully ready
echo "Checking Ryu REST API..."
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/v1.0/topology/switches > /dev/null 2>&1; then
        echo "✓ Ryu REST API is accessible and ready"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "  Waiting for Ryu to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 1
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo " WARNING: Cannot reach Ryu REST API at http://localhost:8080"
    echo "   Make sure Ryu is running with REST API enabled"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "Configuration:"
echo "  Backend URL: http://0.0.0.0:5000"
echo "  Ryu API: http://localhost:8080"
echo ""

# Check if already running
if pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  Backend is already running!"
    echo "   PID: $(pgrep -f 'python.*app.py')"
    read -p "Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "python.*app.py"
        sleep 2
    else
        exit 0
    fi
fi

echo "Starting Flask backend..."
echo "Backend requires sudo for Mininet"
echo "Press Ctrl+C to stop"
echo ""

# Start Flask app with sudo (required for Mininet)
cd "$PROJECT_ROOT/backend"
sudo -E "$PROJECT_ROOT/venv/bin/python" app.py 2>&1 | tee backend.log

# Note: This will block until Ctrl+C
# The log will be saved to backend.log
