# Testing Guide

Complete testing checklist for the SDN Visualizer project.

## Table of Contents

1. [Pre-Development Testing](#pre-development-testing)
2. [Component Testing](#component-testing)
3. [Integration Testing](#integration-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Performance Testing](#performance-testing)
6. [Pre-Demo Checklist](#pre-demo-checklist)

---

## Pre-Development Testing

### Environment Verification

Run before starting development:

```bash
# Quick check
./scripts/health_check.sh

# Expected output:
# ✓ Mininet installed
# ✓ Open vSwitch installed
# ✓ Python 3 installed
# ✓ Ryu installed
```

**Checklist**:
- [ ] Ubuntu/Debian Linux (or VM)
- [ ] Python 3.8+
- [ ] sudo privileges
- [ ] 2GB+ RAM available
- [ ] 500MB+ disk space

---

## Component Testing

### Test 1: Mininet Standalone

**Goal**: Verify Mininet works independently

```bash
# Test 1.1: Simple ping test
sudo mn --test pingall

# Expected: 0% packet loss
```

**Pass Criteria**:
- ✅ Network creates without errors
- ✅ Pingall shows 0% loss
- ✅ Clean exit

```bash
# Test 1.2: Custom topology
sudo mn --topo=star,3
mininet> pingall
mininet> exit

# Clean up
sudo mn -c
```

**Pass Criteria**:
- ✅ 3 hosts (h1, h2, h3)
- ✅ 1 switch (s1)
- ✅ All hosts can ping each other

---

### Test 2: Ryu Controller Standalone

**Goal**: Verify Ryu starts and accepts connections

```bash
# Test 2.1: Basic startup
ryu-manager ryu.app.simple_switch_13

# Expected messages:
# - "loading app ryu.app.simple_switch_13"
# - "instantiating app ryu.app.simple_switch_13"
# - Press Ctrl+C to stop
```

**Pass Criteria**:
- ✅ No errors on startup
- ✅ Process stays running
- ✅ Clean shutdown with Ctrl+C

```bash
# Test 2.2: Start with REST API
ryu-manager --wsapi-port 8080 \
            ryu.app.ofctl_rest \
            ryu.app.rest_topology \
            ryu.app.simple_switch_13

# Test API
curl http://localhost:8080/v1.0/topology/switches

# Expected: [] (empty array, but valid JSON)
```

**Pass Criteria**:
- ✅ Ryu starts without errors
- ✅ Port 6633 listening: `netstat -tuln | grep 6633`
- ✅ Port 8080 listening: `netstat -tuln | grep 8080`
- ✅ REST API responds with valid JSON

---

### Test 3: Mininet + Ryu Integration

**Goal**: Verify switches can connect to controller

```bash
# Terminal 1: Start Ryu
ryu-manager --wsapi-port 8080 \
            ryu.app.simple_switch_13 \
            ryu.app.rest_topology

# Terminal 2: Start Mininet with remote controller
sudo mn --controller=remote,ip=127.0.0.1

# In Mininet:
mininet> net
# Expected: Shows controller c0 at 127.0.0.1

mininet> pingall
# Expected: 0% loss (may take 2 tries)

# Terminal 3: Check Ryu discovered switches
curl http://localhost:8080/v1.0/topology/switches | jq
```

**Pass Criteria**:
- ✅ Ryu logs show "switch connected"
- ✅ Mininet shows controller in `net` command
- ✅ Pingall succeeds (0% loss)
- ✅ REST API returns switch data

---

### Test 4: Python Mininet API

**Goal**: Verify programmatic topology creation

Create test file:

```python
# test_mininet_api.py
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.log import setLogLevel

def test_star_topology():
    setLogLevel('info')
    
    net = Mininet(controller=RemoteController, switch=OVSSwitch)
    
    # Add controller
    c0 = net.addController('c0', ip='127.0.0.1', port=6633)
    
    # Add switch
    s1 = net.addSwitch('s1')
    
    # Add hosts
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    
    # Add links
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    
    # Start
    net.start()
    
    # Set OpenFlow 1.3
    s1.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
    
    # Wait
    import time
    time.sleep(3)
    
    # Test
    print("Testing connectivity...")
    loss = net.pingAll()
    print(f"Packet loss: {loss}%")
    
    # Stop
    net.stop()
    
    return loss == 0.0

if __name__ == '__main__':
    # Make sure Ryu is running first!
    success = test_star_topology()
    print("Test passed!" if success else "Test failed!")
```

Run:
```bash
# Start Ryu first
ryu-manager ryu.app.simple_switch_13 &

# Run test
sudo python3 test_mininet_api.py

# Expected: "Test passed!"
```

**Pass Criteria**:
- ✅ Script runs without errors
- ✅ Shows "Packet loss: 0.0%"
- ✅ Clean exit

---

### Test 5: Flask Backend API

**Goal**: Verify Flask can control Mininet

```bash
# Start Ryu (Terminal 1)
./scripts/start_ryu.sh

# Start Flask (Terminal 2)
./scripts/start_backend.sh

# Test endpoints (Terminal 3)

# Test 5.1: Health check
curl http://localhost:5000/health | jq

# Expected:
# {
#   "status": "healthy",
#   "ryu_connected": true,
#   "network_active": false
# }

# Test 5.2: Create topology
curl -X POST http://localhost:5000/api/topology/create \
     -H "Content-Type: application/json" \
     -d '{"type":"star", "size":3}' | jq

# Expected:
# {
#   "success": true,
#   "message": "Created star topology with 3 nodes"
# }

# Test 5.3: Get topology data
curl http://localhost:5000/api/topology/data | jq

# Expected: JSON with nodes and edges

# Test 5.4: Run pingall
curl -X POST http://localhost:5000/api/topology/pingall | jq

# Expected:
# {
#   "success": true,
#   "packet_loss": 0.0
# }

# Test 5.5: Stop topology
curl -X POST http://localhost:5000/api/topology/stop | jq
```

**Pass Criteria**:
- ✅ All endpoints return success
- ✅ Topology data has correct structure
- ✅ Pingall shows 0% loss
- ✅ Stop cleans up properly

---

## Integration Testing

### Test 6: Full Stack (No Frontend)

**Goal**: Verify backend + Ryu + Mininet work together

```bash
# Run automated test
./scripts/test_connection.sh

# This tests:
# 1. Ryu connectivity
# 2. Flask connectivity
# 3. Topology creation
# 4. Pingall
# 5. Cleanup
```

**Pass Criteria**:
- ✅ All tests pass
- ✅ No errors in logs
- ✅ Clean state after test

---

### Test 7: WebSocket Communication

**Goal**: Verify real-time updates work

Create test file:

```html
<!-- test_websocket.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>WebSocket Test</h1>
    <div id="status">Connecting...</div>
    <div id="events"></div>
    
    <script>
        const socket = io('http://localhost:5000');
        const status = document.getElementById('status');
        const events = document.getElementById('events');
        
        function log(msg) {
            const p = document.createElement('p');
            p.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            events.appendChild(p);
        }
        
        socket.on('connect', () => {
            status.textContent = 'Connected';
            status.style.color = 'green';
            log('✓ Connected to server');
        });
        
        socket.on('disconnect', () => {
            status.textContent = 'Disconnected';
            status.style.color = 'red';
            log('✗ Disconnected from server');
        });
        
        socket.on('topology_update', (data) => {
            log(`Topology: ${data.switch_count} switches, ${data.host_count} hosts`);
        });
        
        socket.on('stats_update', (stats) => {
            log(`Stats: ${stats.total_packets} packets`);
        });
    </script>
</body>
</html>
```

**Test Steps**:
1. Start Ryu and Flask
2. Open `test_websocket.html` in browser
3. Create topology via API
4. Watch for events in browser

**Pass Criteria**:
- ✅ Status shows "Connected"
- ✅ Receives topology_update event
- ✅ Receives stats_update events every 2s
- ✅ No errors in browser console

---

## End-to-End Testing

### Test 8: Frontend Visualization

**Goal**: Complete workflow with UI

**Steps**:

1. **Start System**:
   ```bash
   ./scripts/start_ryu.sh       # Terminal 1
   ./scripts/start_backend.sh   # Terminal 2
   ./scripts/start_frontend.sh  # Opens browser
   ```

2. **Test Star Topology**:
   - Select "Star Topology" from dropdown
   - Set size to 4
   - Click "Create Topology"
   - Wait 5 seconds
   - **Expected**: See 1 blue circle (switch) and 4 green circles (hosts)

3. **Test Interactivity**:
   - Drag a node with mouse
   - **Expected**: Node follows cursor, forces re-balance
   - Click on a node
   - **Expected**: Activity log shows node info

4. **Test Ping**:
   - Click "Run Ping All"
   - **Expected**: Activity log shows "✅ Pingall: 0% loss"

5. **Test Stats**:
   - Watch stats panel on right
   - **Expected**: Packet count increases over time

6. **Test Stop**:
   - Click "Stop Topology"
   - **Expected**: Graph clears, stats reset to 0

7. **Test Different Topology**:
   - Select "Linear Topology", size 5
   - Click "Create Topology"
   - **Expected**: See 5 switches in a line, each with 1 host

**Pass Criteria**:
- ✅ All topology types render correctly
- ✅ Visualization is smooth (no lag)
- ✅ All buttons work
- ✅ Stats update in real-time
- ✅ Logs show appropriate messages
- ✅ Clean state after stop

---

### Test 9: All Topology Types

**Goal**: Verify each topology type works

| Type | Size | Expected Switches | Expected Hosts | Expected Links |
|------|------|------------------|----------------|----------------|
| Star | 4 | 1 | 4 | 4 |
| Linear | 5 | 5 | 5 | 9 |
| Tree | 2 | 3 | 2 | 4 |
| Mesh | 4 | 4 | 4 | 10 |

**Test Each**:
```bash
# Star
curl -X POST http://localhost:5000/api/topology/create \
     -d '{"type":"star", "size":4}' -H "Content-Type: application/json" | jq
curl -X POST http://localhost:5000/api/topology/pingall | jq
curl -X POST http://localhost:5000/api/topology/stop | jq

# Repeat for linear, tree, mesh
```

**Pass Criteria**:
- ✅ All topologies create without errors
- ✅ Pingall succeeds on all (0% loss)
- ✅ Correct number of nodes/links
- ✅ Visualization renders correctly

---

## Performance Testing

### Test 10: Large Topology

**Goal**: Test with maximum size

```bash
# Create large topology
curl -X POST http://localhost:5000/api/topology/create \
     -d '{"type":"linear", "size":20}' -H "Content-Type: application/json"

# Wait 10 seconds
sleep 10

# Test connectivity
curl -X POST http://localhost:5000/api/topology/pingall

# Measure time
time curl -X POST http://localhost:5000/api/topology/pingall
```

**Acceptable Performance**:
- ✅ Creation completes in <15 seconds
- ✅ Pingall completes in <30 seconds
- ✅ Visualization renders (may be slower)
- ✅ No crashes or errors

---

### Test 11: Rapid Topology Changes

**Goal**: Test cleanup robustness

```bash
# Rapid create/stop cycles
for i in {1..5}; do
    echo "Cycle $i"
    curl -X POST http://localhost:5000/api/topology/create \
         -d '{"type":"star", "size":3}' -H "Content-Type: application/json"
    sleep 5
    curl -X POST http://localhost:5000/api/topology/stop
    sleep 2
done

# Verify clean state
sudo ovs-vsctl list-br
# Expected: Empty (no bridges)
```

**Pass Criteria**:
- ✅ All cycles complete without errors
- ✅ No zombie processes remain
- ✅ Clean OVS state at end
- ✅ Backend still responsive

---

### Test 12: Long-Running Stability

**Goal**: Test for memory leaks

```bash
# Create topology and let run for 10 minutes
curl -X POST http://localhost:5000/api/topology/create \
     -d '{"type":"star", "size":4}' -H "Content-Type: application/json"

# Monitor resource usage
watch -n 5 'ps aux | grep -E "python|ryu-manager" | grep -v grep'

# Check for memory growth over time
```

**Acceptable Behavior**:
- ✅ Memory usage stabilizes (no continuous growth)
- ✅ CPU usage stays reasonable (<20% average)
- ✅ No error messages in logs
- ✅ WebSocket stays connected

---

## Pre-Demo Checklist

### One Day Before

- [ ] Run full health check: `./scripts/health_check.sh`
- [ ] Test all topology types
- [ ] Verify pingall on each topology
- [ ] Test rapid create/stop cycles
- [ ] Check logs for any warnings
- [ ] Test on clean VM (if possible)
- [ ] Prepare screenshots/recording

### Day of Demo

- [ ] Reboot machine (fresh start)
- [ ] Run cleanup: `./scripts/cleanup.sh`
- [ ] Verify no zombie processes: `sudo ovs-vsctl list-br`
- [ ] Start Ryu: `./scripts/start_ryu.sh`
  - [ ] Wait for "listening on 0.0.0.0:6633"
- [ ] Start Backend: `./scripts/start_backend.sh`
  - [ ] Wait for "Running on http://0.0.0.0:5000"
- [ ] Open browser: `http://localhost:5000`
- [ ] Test one topology to verify everything works
- [ ] Close unnecessary applications
- [ ] Disable notifications
- [ ] Charge laptop (if demo on laptop)
- [ ] Have backup (screenshots/video) ready

### Demo Script

1. **Introduction** (30 seconds)
   - Show architecture diagram
   - Explain SDN concepts

2. **Start Star Topology** (1 minute)
   - Size: 4 hosts
   - Show visualization
   - Run pingall
   - Drag nodes to show interactivity

3. **Show Statistics** (30 seconds)
   - Point out packet counts
   - Show real-time updates

4. **Create Linear Topology** (1 minute)
   - Size: 5 switches
   - Show different structure
   - Run pingall
   - Click on nodes

5. **Show Logs** (30 seconds)
   - Point out activity log
   - Show connection status

6. **Stop and Cleanup** (30 seconds)
   - Click stop
   - Show clean state

Total: ~4 minutes

---

## Acceptance Criteria

### Must Have (MVP)
- [x] Can create all 4 topology types
- [x] Visualization shows nodes and links
- [x] Pingall works (0% loss)
- [x] Stats panel updates
- [x] Can stop topology cleanly
- [x] No zombie processes after stop
- [x] WebSocket real-time updates work
- [x] Activity log shows actions

### Should Have
- [x] Real-time stats updates (packets)
- [x] Flow table viewer (API exists)
- [x] Interactive node dragging
- [x] Connection status indicator
- [x] Health check script

### Nice to Have (Future)
- [ ] Export topology as JSON/PNG
- [ ] Custom topology builder
- [ ] Packet capture visualization
- [ ] Historical metrics graphs

---

## Test Reports

### Create Test Report

After running tests, document:

```markdown
# Test Report - [Date]

## Environment
- OS: Ubuntu 22.04
- Python: 3.10.6
- Mininet: 2.3.0
- Ryu: 4.34

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| Mininet Standalone | ✅ Pass | 0% loss |
| Ryu Standalone | ✅ Pass | All ports listening |
| Integration | ✅ Pass | Switches connected |
| Star Topology | ✅ Pass | 4 hosts, 0% loss |
| Linear Topology | ✅ Pass | 5 switches, 0% loss |
| Tree Topology | ✅ Pass | 3 switches, 0% loss |
| Mesh Topology | ✅ Pass | 4 switches, 0% loss |
| Frontend | ✅ Pass | All UI elements work |
| WebSocket | ✅ Pass | Real-time updates |
| Performance | ✅ Pass | <15s creation |

## Issues Found
None

## Recommendations
- Add export feature
- Improve large topology performance
```

---

## Continuous Testing

For development, run before committing:

```bash
# Quick smoke test
./scripts/cleanup.sh
./scripts/health_check.sh
./scripts/test_connection.sh

# If all pass, code is good to commit
```

---

## Documentation for Testers

- **System Requirements**: See README.md
- **Setup Instructions**: Run `./scripts/setup.sh`
- **Architecture**: See `docs/architecture.md`
- **API Reference**: See `docs/api_reference.md`
- **Troubleshooting**: See `docs/troubleshooting.md`
