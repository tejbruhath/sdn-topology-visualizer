#!/bin/bash
# Health Check Script - Verify all components are working

echo "=========================================="
echo "SDN Visualizer - Health Check"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall health
ALL_GOOD=true

echo ""
echo "1. Checking System Components"
echo "------------------------------"

# Check Mininet
echo -n "Mininet: "
if command -v mn &> /dev/null; then
    VERSION=$(mn --version 2>&1 | head -n 1)
    echo -e "${GREEN}✓ Installed${NC} - $VERSION"
else
    echo -e "${RED}✗ Not installed${NC}"
    ALL_GOOD=false
fi

# Check Open vSwitch
echo -n "Open vSwitch: "
if command -v ovs-vsctl &> /dev/null; then
    VERSION=$(ovs-vsctl --version | head -n 1)
    echo -e "${GREEN}✓ Installed${NC} - $VERSION"
    
    # Check if service is running
    if sudo systemctl is-active --quiet openvswitch-switch; then
        echo -e "  ${GREEN}✓ Service running${NC}"
    else
        echo -e "  ${RED}✗ Service not running${NC}"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}✗ Not installed${NC}"
    ALL_GOOD=false
fi

# Check Python
echo -n "Python 3: "
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Installed${NC} - $VERSION"
else
    echo -e "${RED}✗ Not installed${NC}"
    ALL_GOOD=false
fi

# Check Ryu
echo -n "Ryu: "
if command -v ryu-manager &> /dev/null; then
    VERSION=$(ryu-manager --version 2>&1 | head -n 1)
    echo -e "${GREEN}✓ Installed${NC} - $VERSION"
else
    echo -e "${RED}✗ Not installed${NC}"
    ALL_GOOD=false
fi

echo ""
echo "2. Checking Running Processes"
echo "------------------------------"

# Check Ryu process
echo -n "Ryu Controller: "
if pgrep -f "ryu-manager" > /dev/null; then
    PID=$(pgrep -f "ryu-manager")
    echo -e "${GREEN}✓ Running${NC} (PID: $PID)"
else
    echo -e "${YELLOW}⊘ Not running${NC}"
fi

# Check Flask process
echo -n "Flask Backend: "
if pgrep -f "python.*app.py" > /dev/null; then
    PID=$(pgrep -f "python.*app.py")
    echo -e "${GREEN}✓ Running${NC} (PID: $PID)"
else
    echo -e "${YELLOW}⊘ Not running${NC}"
fi

echo ""
echo "3. Checking Ports"
echo "------------------------------"

# Check OpenFlow port (6633)
echo -n "OpenFlow (6633): "
if sudo netstat -tuln 2>/dev/null | grep -q ":6633 "; then
    echo -e "${GREEN}✓ Listening${NC}"
else
    echo -e "${YELLOW}⊘ Not listening${NC}"
fi

# Check Ryu REST API port (8080)
echo -n "Ryu REST (8080): "
if sudo netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    echo -e "${GREEN}✓ Listening${NC}"
else
    echo -e "${YELLOW}⊘ Not listening${NC}"
fi

# Check Flask port (5000)
echo -n "Flask (5000): "
if sudo netstat -tuln 2>/dev/null | grep -q ":5000 "; then
    echo -e "${GREEN}✓ Listening${NC}"
else
    echo -e "${YELLOW}⊘ Not listening${NC}"
fi

echo ""
echo "4. Checking API Connectivity"
echo "------------------------------"

# Check Ryu API
echo -n "Ryu REST API: "
if curl -s -f http://localhost:8080/v1.0/topology/switches > /dev/null 2>&1; then
    SWITCHES=$(curl -s http://localhost:8080/v1.0/topology/switches | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Responding${NC} ($SWITCHES switches)"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check Flask API
echo -n "Flask Backend: "
if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo ""
echo "5. Checking Mininet State"
echo "------------------------------"

# Check for OVS bridges (indicates active Mininet)
BRIDGES=$(sudo ovs-vsctl list-br 2>/dev/null | wc -l)
echo -n "OVS Bridges: "
if [ $BRIDGES -eq 0 ]; then
    echo -e "${GREEN}✓ Clean${NC} (no active networks)"
else
    echo -e "${YELLOW}⊘ Found $BRIDGES bridges${NC}"
    sudo ovs-vsctl list-br | while read bridge; do
        echo "  - $bridge"
    done
fi

echo ""
echo "=========================================="

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✅ System Health: GOOD${NC}"
    echo ""
    echo "All required components are installed."
    
    if pgrep -f "ryu-manager" > /dev/null && pgrep -f "python.*app.py" > /dev/null; then
        echo "All services are running."
        echo ""
        echo "Access the visualizer at: http://localhost:5000"
    else
        echo ""
        echo "To start the system:"
        echo "  1. ./scripts/start_ryu.sh"
        echo "  2. ./scripts/start_backend.sh"
        echo "  3. Open http://localhost:5000"
    fi
else
    echo -e "${RED}❌ System Health: ISSUES DETECTED${NC}"
    echo ""
    echo "Please run ./scripts/setup.sh to install missing components."
fi

echo ""
echo "=========================================="
