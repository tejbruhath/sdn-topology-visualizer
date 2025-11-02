#!/bin/bash
# Start Ryu Controller with required applications

echo "=========================================="
echo "Starting Ryu SDN Controller"
echo "=========================================="

# Check if Ryu is installed
if ! command -v ryu-manager &> /dev/null; then
    echo "❌ ryu-manager not found!"
    echo "   Please run ./scripts/setup.sh first"
    exit 1
fi

# Check if already running
if pgrep -f "ryu-manager" > /dev/null; then
    echo "⚠️  Ryu is already running!"
    echo "   PID: $(pgrep -f ryu-manager)"
    read -p "Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f ryu-manager
        sleep 2
    else
        exit 0
    fi
fi

echo ""
echo "Configuration:"
echo "  OpenFlow Port: 6633"
echo "  REST API Port: 8080"
echo "  Protocol: OpenFlow 1.3"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Start Ryu with all required applications
echo "Starting Ryu controller..."
echo "Press Ctrl+C to stop"
echo ""

ryu-manager \
    --verbose \
    --ofp-tcp-listen-port 6633 \
    --wsapi-port 8080 \
    ryu.app.ofctl_rest \
    ryu.app.rest_topology \
    ryu.app.simple_switch_13 \
    "$PROJECT_ROOT/ryu_apps/simple_monitor.py" \
    2>&1 | tee ryu.log

# Note: This will block until Ctrl+C
# The log will be saved to ryu.log
