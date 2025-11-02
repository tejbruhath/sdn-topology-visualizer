#!/bin/bash
# Cleanup Script - Stops all processes and cleans Mininet

echo "=========================================="
echo "SDN Visualizer - Cleanup Script"
echo "=========================================="

echo ""
echo "Stopping all SDN Visualizer processes..."
echo ""

# Stop Flask backend
if pgrep -f "python.*app.py" > /dev/null; then
    echo "Stopping Flask backend..."
    sudo pkill -f "python.*app.py"
    sleep 1
    echo "✓ Backend stopped"
else
    echo "✓ Backend not running"
fi

# Stop Ryu controller
if pgrep -f "ryu-manager" > /dev/null; then
    echo "Stopping Ryu controller..."
    pkill -f "ryu-manager"
    sleep 1
    echo "✓ Ryu stopped"
else
    echo "✓ Ryu not running"
fi

# Clean Mininet
echo ""
echo "Cleaning Mininet..."
sudo mn -c 2>/dev/null
echo "✓ Mininet cleaned"

# Kill any remaining OpenFlow processes
if pgrep -f "controller" > /dev/null; then
    echo "Killing remaining controller processes..."
    sudo pkill -f "controller"
fi

# Restart OVS (ensures clean state)
echo ""
echo "Restarting Open vSwitch..."
sudo systemctl restart openvswitch-switch
sleep 2
echo "✓ OVS restarted"

# Check if everything is clean
echo ""
echo "Verification:"
echo ""

# Check for remaining switches
BRIDGES=$(sudo ovs-vsctl list-br 2>/dev/null | wc -l)
if [ $BRIDGES -eq 0 ]; then
    echo "✓ No OVS bridges found (clean)"
else
    echo "⚠️  Found $BRIDGES OVS bridges (may need manual cleanup)"
    sudo ovs-vsctl list-br
fi

# Check for running processes
echo ""
echo "Process check:"
if pgrep -f "ryu-manager" > /dev/null; then
    echo "⚠️  Ryu still running (PID: $(pgrep -f ryu-manager))"
else
    echo "✓ Ryu not running"
fi

if pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  Backend still running (PID: $(pgrep -f 'python.*app.py'))"
else
    echo "✓ Backend not running"
fi

echo ""
echo "=========================================="
echo "✅ Cleanup Complete!"
echo "=========================================="
echo ""
echo "You can now restart the system with:"
echo "  ./scripts/start_ryu.sh"
echo "  ./scripts/start_backend.sh"
echo ""
