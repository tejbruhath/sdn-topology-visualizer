# 🐛 Real-World Debugging Log

**Complete troubleshooting guide based on actual issues encountered during SDN Visualizer deployment.**

Stack: **Ryu + Flask + Mininet + D3.js**

---

## 🧩 Issue #1: Wrong File Paths for Ryu Apps

### ❌ Problem
```bash
ryu-manager: error: No such file or directory: 'ryu_apps/simple_monitor.py'
```

### 🔍 Root Cause
- Running script from wrong directory (`sdnn/` instead of `sdn-topology-visualizer/`)
- Relative paths broke when executed from parent folder

### ✅ Solution

**Step 1: Verify project structure**
```bash
ls ~/sdn-topology-visualizer/ryu_apps
# Should show: simple_monitor.py, learning_switch.py
```

**Step 2: Always use absolute paths in scripts**
```bash
# In start_ryu.sh
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ryu-manager $PROJECT_ROOT/ryu_apps/simple_monitor.py
```

**Step 3: Run from correct directory**
```bash
cd ~/sdn-topology-visualizer  # Always start here
./scripts/start_ryu.sh
```

### 🎯 Prevention
- Use `$PROJECT_ROOT` in all scripts
- Never use relative paths like `../ryu_apps/`
- Add directory check at script start

---

## 🧩 Issue #2: Ryu Controller Exiting Immediately

### ❌ Problem
```bash
$ ./scripts/start_ryu.sh
loading app ryu.app.ofctl_rest
loading app ryu.app.rest_topology
instantiating app ryu.app.simple_switch_13
# ... then back to prompt (no error, just exits)
```

### 🔍 Root Cause
- Running in foreground and session got killed (Ctrl+C, timeout, SSH disconnect)
- No persistent process management
- Mininet not connected, so Ryu had nothing to do

### ✅ Solution

**Option 1: Use nohup (backgrounds and persists)**
```bash
nohup ryu-manager \
    --wsapi-port 8080 \
    ryu.app.ofctl_rest \
    ryu.app.rest_topology \
    ryu.app.simple_switch_13 \
    ryu_apps/simple_monitor.py \
    > ryu.log 2>&1 &

# Verify
ps aux | grep ryu-manager
tail -f ryu.log
```

**Option 2: Use tmux (recommended for debugging)**
```bash
tmux new -s ryu
./scripts/start_ryu.sh
# Detach: Ctrl+b, then d
# Reattach: tmux attach -t ryu
```

**Option 3: Use screen**
```bash
screen -S ryu
./scripts/start_ryu.sh
# Detach: Ctrl+a, then d
# Reattach: screen -r ryu
```

### 🎯 Prevention
- Always use tmux or screen for long-running processes
- Check process is actually running: `pgrep -f ryu-manager`
- Monitor logs: `tail -f ryu.log`

---

## 🧩 Issue #3: Flask Backend Couldn't Reach Ryu

### ❌ Problem
```bash
requests.exceptions.ConnectionError: 
HTTPConnectionPool(host='localhost', port=8080): 
Max retries exceeded with url: /v1.0/topology/switches
```

or

```bash
Unable to contact the remote controller at 127.0.0.1:6633
```

### 🔍 Root Cause
- **Port 8080:** Flask started before Ryu → Ryu REST API not ready
- **Port 6633:** Ryu OpenFlow not listening yet
- Timing issue: Backend tries to connect immediately after Ryu starts

### ✅ Solution

**Fix 1: Start Ryu first, wait, then backend**
```bash
# Terminal 1: Start Ryu
./scripts/start_ryu.sh

# WAIT 5 seconds for "listening on 0.0.0.0:6633"

# Terminal 2: Start backend
./scripts/start_backend.sh
```

**Fix 2: Verify Ryu is ready before backend starts**
```bash
# Add to start_backend.sh
echo "Checking Ryu availability..."
for i in {1..10}; do
    if curl -s http://localhost:8080/v1.0/topology/switches &> /dev/null; then
        echo "✓ Ryu is ready"
        break
    fi
    echo "Waiting for Ryu... ($i/10)"
    sleep 2
done
```

**Fix 3: Check ports manually**
```bash
# Check Ryu REST API (port 8080)
curl http://localhost:8080/v1.0/topology/switches
# Should return: [] or [{"dpid": "..."}]

# Check Ryu OpenFlow (port 6633)
sudo netstat -tulpn | grep 6633
# Should show: LISTEN on 6633
```

### 🎯 Prevention
- Start Ryu → Wait 5s → Start Backend
- Add health check loops in backend startup
- Use systemd with proper dependencies (production)

---

## 🧩 Issue #4: REST API Endpoint Not Found

### ❌ Problem
```bash
$ curl http://localhost:8080/v1.0/topology/switches
404 Not Found
```

### 🔍 Root Cause
- `ryu.app.rest_topology` module NOT loaded
- Only loaded `ofctl_rest` but not `rest_topology`

### ✅ Solution

**Check what's loaded:**
```bash
# In ryu.log, look for:
loading app ryu.app.rest_topology  # Must see this!
```

**Fix the startup command:**
```bash
# ❌ WRONG (missing rest_topology)
ryu-manager ryu.app.ofctl_rest ryu.app.simple_switch_13

# ✅ CORRECT (includes rest_topology)
ryu-manager \
    ryu.app.ofctl_rest \
    ryu.app.rest_topology \
    ryu.app.simple_switch_13
```

**Verify available endpoints:**
```bash
# These should ALL work:
curl http://localhost:8080/v1.0/topology/switches
curl http://localhost:8080/v1.0/topology/links
curl http://localhost:8080/v1.0/topology/hosts
```

### 🎯 Prevention
- Always load BOTH `ofctl_rest` AND `rest_topology`
- Test endpoints immediately after Ryu starts
- Check ryu.log for "loading app" messages

---

## 🧩 Issue #5: Script Permission Denied

### ❌ Problem
```bash
$ ./scripts/start_backend.sh
bash: ./scripts/start_backend.sh: Permission denied
```

### 🔍 Root Cause
- Scripts don't have executable permission
- Git may not preserve `+x` flag on clone

### ✅ Solution

**Fix all scripts at once:**
```bash
chmod +x scripts/*.sh

# Verify
ls -la scripts/*.sh
# Should show: -rwxr-xr-x (x = executable)
```

**Or fix individual script:**
```bash
chmod +x scripts/start_backend.sh
```

### 🎯 Prevention
- Run `chmod +x scripts/*.sh` after cloning
- Add to setup.sh (already included)
- Check permissions if script fails

---

## 🧩 Issue #6: Virtual Environment Not Activated

### ❌ Problem
```bash
$ ./scripts/start_ryu.sh
Traceback (most recent call last):
  File "/usr/local/bin/ryu-manager", line 5, in <module>
    from ryu.cmd.manager import main
ModuleNotFoundError: No module named 'ryu'
```

### 🔍 Root Cause
- Python packages installed in venv, but script runs with system Python
- `source venv/bin/activate` not called before running ryu-manager

### ✅ Solution

**Manual activation:**
```bash
source venv/bin/activate
./scripts/start_ryu.sh
```

**Automatic activation (already in scripts):**
```bash
# In start_ryu.sh
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$PROJECT_ROOT/venv/bin/activate"
```

**Verify venv is active:**
```bash
which python
# Should show: /path/to/sdn-visualizer/venv/bin/python

echo $VIRTUAL_ENV
# Should show: /path/to/sdn-visualizer/venv
```

### 🎯 Prevention
- All start scripts auto-activate venv
- Check `$VIRTUAL_ENV` is set
- Use absolute path to venv/bin/python if needed

---

## 🧩 Issue #7: Controller Not Linked to Mininet

### ❌ Problem
```bash
# In backend.log:
Unable to contact the remote controller at 127.0.0.1:6633
```

or

```bash
mininet> net
c0 controller:127.0.0.1:6653 (disconnected)
```

### 🔍 Root Cause
- Mininet created without specifying remote controller
- Default controller port (6653) doesn't match Ryu (6633)
- Mininet started before Ryu was ready

### ✅ Solution

**Fix 1: Always specify remote controller**
```bash
# ❌ WRONG (uses default controller)
sudo mn --topo tree,2

# ✅ CORRECT (connects to Ryu)
sudo mn --controller=remote,ip=127.0.0.1,port=6633 --topo tree,2
```

**Fix 2: In Python code (mininet_manager.py)**
```python
from mininet.node import RemoteController

net = Mininet(
    controller=RemoteController,
    switch=OVSSwitch
)

# Add controller
c0 = net.addController(
    'c0',
    controller=RemoteController,
    ip='127.0.0.1',
    port=6633
)
```

**Verify connection:**
```bash
# In Mininet CLI
mininet> net
# Should show: c0 controller:127.0.0.1:6633 (connected)

# Check Ryu logs
tail -f ryu.log
# Should show: "switch connected" messages
```

### 🎯 Prevention
- Always start Ryu BEFORE Mininet
- Specify `controller=remote,ip=127.0.0.1,port=6633`
- Check `mininet> net` shows "connected"

---

## 🧩 Issue #8: Cross-Process Startup Chaos

### ❌ Problem
- Starting processes out of order caused cascading failures
- Hard to track which process failed
- Multiple terminals hard to manage

### 🔍 Root Cause
- No standardized startup sequence
- Manual coordination between 3+ terminals
- Easy to forget steps or start in wrong order

### ✅ Solution

**Option 1: Use tmux (Recommended)**
```bash
# Create tmux session with 3 panes
tmux new -s sdn

# Pane 1 (Ryu)
./scripts/start_ryu.sh

# Split horizontal: Ctrl+b then "
# Pane 2 (Backend)
./scripts/start_backend.sh

# Split vertical: Ctrl+b then %
# Pane 3 (Monitor)
watch -n 2 'sudo ovs-vsctl show'

# Detach: Ctrl+b then d
# All processes keep running!
```

**Option 2: Master startup script**
```bash
#!/bin/bash
# scripts/start_all.sh

echo "Starting Ryu..."
./scripts/start_ryu.sh &
sleep 5

echo "Starting Backend..."
./scripts/start_backend.sh &
sleep 3

echo "All services started!"
echo "Check logs: tail -f ryu.log backend.log"
```

**Option 3: Manual with verification**
```bash
# Terminal 1: Ryu
./scripts/start_ryu.sh
# Wait for: "listening on 0.0.0.0:6633"

# Terminal 2: Backend
./scripts/start_backend.sh
# Wait for: "Running on http://0.0.0.0:5000"

# Terminal 3: Test
curl http://localhost:5000/health
# Should return: {"status": "healthy"}
```

### 🎯 Prevention
- Use tmux or screen for multi-process management
- Create master startup script
- Add health checks between each step

---

## ✅ FINAL WORKING SETUP

### Complete Startup Sequence

```bash
# 1. Clean slate
./scripts/cleanup.sh

# 2. Start Ryu (Terminal 1 or tmux pane 1)
./scripts/start_ryu.sh
# Wait for: "listening on 0.0.0.0:6633"

# 3. Start Backend (Terminal 2 or tmux pane 2)
./scripts/start_backend.sh
# Wait for: "Running on http://0.0.0.0:5000"

# 4. Access UI
http://localhost:5000
```

### Verification Checklist

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Ryu process | `pgrep -f ryu-manager` | Shows PID |
| Ryu OpenFlow | `netstat -tuln \| grep 6633` | LISTEN on 6633 |
| Ryu REST API | `curl localhost:8080/v1.0/topology/switches` | `[]` or JSON |
| Backend process | `pgrep -f "python.*app.py"` | Shows PID |
| Backend port | `netstat -tuln \| grep 5000` | LISTEN on 5000 |
| Backend health | `curl localhost:5000/health` | `{"status":"healthy"}` |
| venv active | `echo $VIRTUAL_ENV` | Shows venv path |

### Emergency Shutdown

```bash
# Kill all processes
pkill -f ryu-manager
pkill -f "python.*app.py"
sudo mn -c

# Or use cleanup script
./scripts/cleanup.sh
```

---

## 🔥 Quick Troubleshooting Commands

```bash
# Check what's running
ps aux | grep -E 'ryu|flask|python.*app.py'

# Check what's listening
sudo netstat -tulpn | grep -E '5000|6633|8080'

# Check Ryu is reachable
curl http://localhost:8080/v1.0/topology/switches

# Check Backend is reachable
curl http://localhost:5000/health

# Check Mininet state
sudo ovs-vsctl show

# View real-time logs
tail -f ryu.log backend.log

# Search for errors
grep -i error ryu.log backend.log

# Nuclear option (kill everything)
./scripts/cleanup.sh
```

---

## 📊 Process Dependencies

```
┌─────────────────────────────────┐
│  1. Ryu Controller              │
│     Port 6633 (OpenFlow)        │
│     Port 8080 (REST API)        │
└────────────┬────────────────────┘
             │
             │ (Must be ready first)
             ▼
┌─────────────────────────────────┐
│  2. Flask Backend               │
│     Port 5000 (Web UI)          │
│     Connects to Ryu:8080        │
└────────────┬────────────────────┘
             │
             │ (Creates networks)
             ▼
┌─────────────────────────────────┐
│  3. Mininet Networks            │
│     Switches connect to:6633    │
└─────────────────────────────────┘
```

**Start order:** Ryu → Backend → (Mininet created by Backend)

---

## 🎯 Summary of Fixes

1. ✅ Use absolute paths in all scripts
2. ✅ Start Ryu before Backend (wait 5 seconds)
3. ✅ Load both `ofctl_rest` AND `rest_topology`
4. ✅ Set script permissions: `chmod +x scripts/*.sh`
5. ✅ Auto-activate venv in all scripts
6. ✅ Specify remote controller in Mininet
7. ✅ Use tmux for process management
8. ✅ Verify each service before starting next

---

**Status:** All issues resolved ✅  
**Last Updated:** 2024-11-02  
**Tested On:** Ubuntu 20.04, 22.04, 24.04
