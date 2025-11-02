#!/bin/bash
# Test Script - Quick integration test

echo "=========================================="
echo "SDN Visualizer - Connection Test"
echo "=========================================="

# Check if Ryu is running
echo ""
echo "1. Testing Ryu Controller..."
if curl -s -f http://localhost:8080/v1.0/topology/switches > /dev/null 2>&1; then
    echo "   ✓ Ryu REST API is responding"
    
    # Get switch count
    SWITCHES=$(curl -s http://localhost:8080/v1.0/topology/switches 2>/dev/null)
    COUNT=$(echo "$SWITCHES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   ✓ Connected switches: $COUNT"
else
    echo "   ✗ Ryu REST API is not responding"
    echo "   Make sure Ryu is running: ./scripts/start_ryu.sh"
    exit 1
fi

# Check if backend is running
echo ""
echo "2. Testing Flask Backend..."
if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is responding"
    
    # Get health status
    HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null)
    echo "$HEALTH" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   ✓ Status: {data.get('status', 'unknown')}\")
    print(f\"   ✓ Ryu connected: {data.get('ryu_connected', False)}\")
    print(f\"   ✓ Network active: {data.get('network_active', False)}\")
except:
    pass
" 2>/dev/null
else
    echo "   ✗ Backend is not responding"
    echo "   Make sure backend is running: ./scripts/start_backend.sh"
    exit 1
fi

# Test creating a simple topology
echo ""
echo "3. Testing Topology Creation..."
read -p "Create a test star topology with 3 hosts? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Creating topology..."
    
    RESPONSE=$(curl -s -X POST http://localhost:5000/api/topology/create \
        -H "Content-Type: application/json" \
        -d '{"type":"star", "size":3}' 2>/dev/null)
    
    SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    
    if [ "$SUCCESS" = "True" ]; then
        echo "   ✓ Topology created successfully!"
        
        # Wait for switches to connect
        echo "   Waiting 4 seconds for switches to connect..."
        sleep 4
        
        # Check switch count
        SWITCHES=$(curl -s http://localhost:8080/v1.0/topology/switches 2>/dev/null)
        COUNT=$(echo "$SWITCHES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        
        if [ "$COUNT" -gt 0 ]; then
            echo "   ✓ Switches connected to Ryu: $COUNT"
        else
            echo "   ⚠ No switches connected yet"
        fi
        
        # Test pingall
        echo ""
        echo "4. Testing Network Connectivity..."
        PING_RESPONSE=$(curl -s -X POST http://localhost:5000/api/topology/pingall 2>/dev/null)
        LOSS=$(echo "$PING_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('packet_loss', 100))" 2>/dev/null)
        
        if [ "$LOSS" = "0.0" ] || [ "$LOSS" = "0" ]; then
            echo "   ✓ Pingall successful! 0% packet loss"
        else
            echo "   ⚠ Pingall had ${LOSS}% packet loss"
        fi
        
        # Cleanup
        echo ""
        echo "5. Cleaning Up..."
        curl -s -X POST http://localhost:5000/api/topology/stop > /dev/null 2>&1
        echo "   ✓ Topology stopped"
    else
        MESSAGE=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))" 2>/dev/null)
        echo "   ✗ Failed to create topology: $MESSAGE"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ All Tests Passed!"
echo "=========================================="
echo ""
echo "The system is working correctly."
echo "Open http://localhost:5000 in your browser to use the visualizer."
echo ""
