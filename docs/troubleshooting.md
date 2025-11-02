# Troubleshooting Guide

Complete guide for diagnosing and fixing common issues with the SDN Visualizer.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Startup Problems](#startup-problems)
4. [Runtime Errors](#runtime-errors)
5. [Performance Issues](#performance-issues)
6. [Network Connectivity](#network-connectivity)
7. [Advanced Debugging](#advanced-debugging)

---

## Quick Diagnostics

Run these commands first to identify the problem area:

```bash
# Check system health
./scripts/health_check.sh

# Test connectivity
./scripts/test_connection.sh

# View logs
tail -f backend.log
tail -f ryu.log
```

---

## Installation Issues

### Issue: "mn: command not found"

**Symptom**: Mininet is not installed

**Solution**:
```bash
sudo apt-get update
sudo apt-get install mininet
mn --version  # Verify installation
```

---

### Issue: "ryu-manager: command not found"

**Symptom**: Ryu is not installed

**Solution**:
```bash
python3 -m pip install ryu
ryu-manager --version  # Verify installation
```

---

### Issue: "ovs-vsctl: command not found"

**Symptom**: Open vSwitch is not installed

**Solution**:
```bash
sudo apt-get install openvswitch-switch openvswitch-common
sudo systemctl start openvswitch-switch
sudo ovs-vsctl show  # Verify installation
```

---

### Issue: pip install fails with "permission denied"

**Solution**:
```bash
# Install to user directory
python3 -m pip install --user -r backend/requirements.txt

# OR use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

## Startup Problems

### Issue: "Address already in use" (Port 6633)

**Symptom**: Ryu can't start, port is occupied

**Diagnosis**:
```bash
sudo netstat -tulpn | grep 6633
# OR
sudo lsof -i :6633
```

**Solution**:
```bash
# Kill the process using the port
sudo kill -9 <PID>

# OR use different port
ryu-manager --ofp-tcp-listen-port 6634 ...
```

---

### Issue: "Address already in use" (Port 8080)

**Symptom**: Ryu REST API can't start

**Common Culprits**: Jenkins, Tomcat, previous Ryu instance

**Solution**:
```bash
# Find and kill
sudo lsof -i :8080
sudo kill -9 <PID>

# OR change port
ryu-manager --wsapi-port 8081 ...
# Update backend/config.py: RYU_REST_PORT = 8081
```

---

### Issue: "Address already in use" (Port 5000)

**Symptom**: Flask can't start

**Solution**:
```bash
# Kill previous Flask instance
pkill -f "python.*app.py"

# OR change port in config.py
FLASK_PORT = 5001
```

---

### Issue: "Cannot connect to Ryu controller"

**Symptom**: Backend exits with error message

**Diagnosis**:
```bash
# Check if Ryu is running
pgrep -f ryu-manager

# Check if REST API is responding
curl http://localhost:8080/v1.0/topology/switches
```

**Solution**:
```bash
# Start Ryu first
./scripts/start_ryu.sh

# Wait for "listening on 6633" message

# Then start backend
./scripts/start_backend.sh
```

---

### Issue: Backend requires sudo but won't start

**Symptom**: Permission denied errors

**Solution**:
```bash
# Method 1: Run with sudo (simplest)
sudo -E python3 backend/app.py

# Method 2: Add to sudoers (more secure)
sudo visudo
# Add: your_username ALL=(ALL) NOPASSWD: /usr/bin/mn

# Method 3: Use setcap (advanced)
sudo setcap cap_net_admin=eip $(which python3)
```

---

## Runtime Errors

### Issue: "No switches found" after creating topology

**Symptom**: Topology created but appears empty

**Diagnosis**:
```bash
# Check if Mininet is running
sudo ovs-vsctl list-br

# Check if switches connected to Ryu
curl http://localhost:8080/v1.0/topology/switches
```

**Causes**:
1. Didn't wait long enough (need 3 seconds)
2. Ryu not running
3. Wrong OpenFlow version
4. Firewall blocking port 6633

**Solution**:
```bash
# Fix 1: Wait longer
# The backend already waits, but may need more time for large topologies

# Fix 2: Check OpenFlow version
sudo ovs-vsctl list bridge s1 | grep protocols
# Should show: OpenFlow13

# Fix 3: Set OpenFlow version manually
sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

# Fix 4: Check firewall
sudo ufw allow 6633/tcp
# OR disable firewall temporarily
sudo ufw disable
```

---

### Issue: Topology created but pingall fails

**Symptom**: 100% packet loss on pingall

**Diagnosis**:
```bash
# Check if Ryu learning switch is running
ps aux | grep simple_switch_13

# Check if flows are installed
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

**Causes**:
1. Ryu not running learning switch app
2. Flows not being installed
3. Network isolation issue

**Solution**:
```bash
# Restart Ryu with learning switch
ryu-manager \
    --ofp-tcp-listen-port 6633 \
    --wsapi-port 8080 \
    ryu.app.simple_switch_13 \
    ryu.app.ofctl_rest \
    ryu.app.rest_topology

# Verify flows after pingall
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
# Should show multiple flow entries
```

---

### Issue: Zombie processes remain after stopping

**Symptom**: `sudo ovs-vsctl list-br` shows old switches

**Solution**:
```bash
# Nuclear cleanup
./scripts/cleanup.sh

# Manual cleanup
sudo mn -c
sudo killall ryu-manager
sudo killall python
sudo systemctl restart openvswitch-switch

# Verify
sudo ovs-vsctl list-br  # Should be empty
pgrep -f "ryu-manager"  # Should return nothing
```

---

### Issue: Frontend not updating/connecting

**Symptom**: Status shows "Disconnected"

**Diagnosis**:
```bash
# Check browser console for errors
# Press F12 in browser, check Console tab

# Test WebSocket connection
curl http://localhost:5000/socket.io/
```

**Causes**:
1. Backend not running
2. CORS issue
3. Wrong URL in frontend
4. Firewall blocking WebSocket

**Solution**:
```bash
# Fix 1: Ensure backend is running
pgrep -f "python.*app.py"

# Fix 2: Check CORS settings in app.py
# Should have: CORS(app)

# Fix 3: Check frontend app.js
# Should have: const API_URL = window.location.origin;

# Fix 4: Test from browser
# Navigate to: http://localhost:5000
# NOT: http://127.0.0.1:5000 (may cause CORS issues)
```

---

### Issue: Visualization doesn't appear

**Symptom**: Blank screen or empty graph

**Diagnosis**:
```bash
# Open browser console (F12)
# Check for JavaScript errors

# Test API
curl http://localhost:5000/api/topology/data
```

**Causes**:
1. D3.js not loaded
2. No topology created yet
3. Data format issue
4. JavaScript error

**Solution**:
```javascript
// Check browser console for:
// - "D3 is not defined" → CDN blocked
// - "Cannot read property of undefined" → Data format issue

// Fix: Open browser console and run:
console.log(d3.version);  // Should show "7.8.5"

// If D3 not loaded, check internet connection
// or download D3.js locally
```

---

### Issue: Stats panel shows "0" for everything

**Symptom**: No statistics updating

**Diagnosis**:
```bash
# Check if stats thread is running
# Look for "Started stats monitoring thread" in backend logs

# Test Ryu API directly
curl http://localhost:8080/stats/port/1
```

**Causes**:
1. No topology created yet (expected)
2. Stats thread crashed
3. Ryu not responding

**Solution**:
```bash
# Check backend logs for errors
tail -f backend.log | grep "stats"

# Restart backend if needed
./scripts/cleanup.sh
./scripts/start_backend.sh
```

---

## Performance Issues

### Issue: Slow topology creation

**Symptom**: Takes >10 seconds to create small topology

**Causes**:
1. System overloaded
2. Too many flows being installed
3. Slow Ryu response

**Solution**:
```bash
# Check system resources
top
# Look for high CPU/memory usage

# Reduce topology size
# Use size <= 10 for testing

# Check Ryu logs for delays
tail -f ryu.log | grep "slow\|timeout"
```

---

### Issue: Visualization is laggy

**Symptom**: Graph rendering is slow, nodes jittery

**Causes**:
1. Too many nodes (>20)
2. Force simulation too strong
3. Browser limitations

**Solution**:
```javascript
// Reduce topology size
// Or adjust force simulation in app.js:

simulation
    .force('charge', d3.forceManyBody().strength(-200))  // Reduce from -400
    .force('collision', d3.forceCollide().radius(20))    // Reduce from 30
    .alphaDecay(0.05);  // Add this to settle faster
```

---

### Issue: High CPU usage

**Symptom**: CPU at 100% constantly

**Diagnosis**:
```bash
top
# Press 'P' to sort by CPU
# Look for python3 or ryu-manager
```

**Causes**:
1. Stats update interval too short
2. Large topology
3. Memory leak

**Solution**:
```python
# In backend/config.py, increase interval:
STATS_UPDATE_INTERVAL = 5  # Change from 2 to 5 seconds

# Or disable stats monitoring temporarily
# Comment out: start_stats_monitoring()
```

---

## Network Connectivity

### Issue: Switches not connecting to Ryu

**Symptom**: `is_connected: false` in OVS

**Diagnosis**:
```bash
# Check switch status
sudo ovs-vsctl show
# Look for: is_connected: false

# Check Ryu logs
tail -f ryu.log | grep "connect\|disconnect"

# Test OpenFlow connection
sudo ovs-ofctl show s1
```

**Causes**:
1. Ryu not running
2. Wrong controller IP/port
3. Firewall blocking
4. OpenFlow version mismatch

**Solution**:
```bash
# Fix 1: Verify Ryu is listening
netstat -tuln | grep 6633

# Fix 2: Set controller manually
sudo ovs-vsctl set-controller s1 tcp:127.0.0.1:6633

# Fix 3: Disable firewall
sudo ufw disable

# Fix 4: Force OpenFlow 1.3
sudo ovs-vsctl set bridge s1 protocols=OpenFlow13
```

---

### Issue: Hosts can't ping each other

**Symptom**: 100% packet loss

**Diagnosis**:
```bash
# Test manually in Mininet CLI
sudo mn --controller=remote,ip=127.0.0.1
mininet> pingall

# Check flows
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

**Causes**:
1. No flows installed
2. Wrong flow rules
3. MAC address not learned
4. Network isolation

**Solution**:
```bash
# Trigger learning by generating traffic
# Run pingall twice (first time installs flows)

# Manually install flows
sudo ovs-ofctl add-flow s1 \
    "priority=100,in_port=1,actions=output:2"

# Check Ryu is running learning switch
ps aux | grep simple_switch_13
```

---

## Advanced Debugging

### Enable Debug Logging

**Backend**:
```python
# In backend/config.py
LOG_LEVEL = 'DEBUG'  # Change from 'INFO'
```

**Ryu**:
```bash
# Start Ryu with --verbose flag
ryu-manager --verbose ...
```

---

### Capture OpenFlow Messages

```bash
# Install Wireshark
sudo apt-get install wireshark

# Capture on loopback
sudo wireshark -i lo -f "tcp port 6633"

# Filter for OpenFlow
# Display filter: openflow_v4
```

---

### Manual Testing Workflow

```bash
# 1. Test Mininet alone
sudo mn --test pingall
# Should work: 0% loss

# 2. Test Mininet with Ryu
# Terminal 1:
ryu-manager ryu.app.simple_switch_13

# Terminal 2:
sudo mn --controller=remote,ip=127.0.0.1
mininet> pingall
# Should work: 0% loss

# 3. Test Flask without frontend
curl -X POST http://localhost:5000/api/topology/create \
     -H "Content-Type: application/json" \
     -d '{"type":"star", "size":3}'

# 4. Check topology was created
curl http://localhost:5000/api/topology/data | jq

# 5. Test pingall via API
curl -X POST http://localhost:5000/api/topology/pingall | jq
```

---

### Collecting Debug Info

For bug reports, collect:

```bash
#!/bin/bash
# debug_info.sh

echo "=== System Info ==="
uname -a
cat /etc/os-release

echo "=== Python Version ==="
python3 --version

echo "=== Installed Versions ==="
mn --version
ryu-manager --version
ovs-vsctl --version | head -n 1

echo "=== Running Processes ==="
pgrep -fa "ryu-manager|python.*app.py"

echo "=== Port Status ==="
sudo netstat -tulpn | grep -E "6633|8080|5000"

echo "=== OVS Bridges ==="
sudo ovs-vsctl list-br

echo "=== Ryu Switches ==="
curl -s http://localhost:8080/v1.0/topology/switches | jq

echo "=== Recent Logs ==="
tail -n 50 backend.log
tail -n 50 ryu.log
```

---

### Common Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| "switch connected" | Switch successfully connected to Ryu | ✓ Good |
| "Unsupported version" | OpenFlow version mismatch | Set protocols=OpenFlow13 |
| "connection refused" | Can't reach Ryu | Start Ryu first |
| "permission denied" | Insufficient privileges | Use sudo |
| "address already in use" | Port conflict | Kill process on port |
| "no route to host" | Network/firewall issue | Check firewall |

---

## Still Having Issues?

1. **Run cleanup**: `./scripts/cleanup.sh`
2. **Restart from scratch**:
   ```bash
   ./scripts/cleanup.sh
   ./scripts/start_ryu.sh       # Wait for "listening on 6633"
   ./scripts/start_backend.sh   # Wait for "Running on 5000"
   ```
3. **Check logs**: `tail -f backend.log ryu.log`
4. **Test step by step**: Follow manual testing workflow above
5. **Report bug**: Include output from `debug_info.sh`

---

## Getting Help

- **Documentation**: Check other docs in `docs/` folder
- **Health Check**: `./scripts/health_check.sh`
- **Test Connection**: `./scripts/test_connection.sh`
- **Logs**: `backend.log`, `ryu.log`
- **Browser Console**: F12 → Console tab

---

## Prevention Tips

1. **Always start Ryu before backend**
2. **Wait for "listening on 6633" message**
3. **Clean up between runs**: `./scripts/cleanup.sh`
4. **Don't kill processes with Ctrl+Z** (use Ctrl+C)
5. **Check health before demo**: `./scripts/health_check.sh`
6. **Keep logs for debugging**: Don't delete log files
7. **Use stable topology sizes**: 3-8 nodes ideal
8. **Test changes incrementally**: Don't change multiple things at once
