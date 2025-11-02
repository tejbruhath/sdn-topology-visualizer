# Quick Start Guide

Get the SDN Visualizer running in 5 minutes!

## Prerequisites

- **Operating System**: Debian/Ubuntu Linux
- **Privileges**: sudo access
- **Internet**: For downloading packages

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd sdn-visualizer
```

### Step 2: Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This installs:
- Mininet
- Open vSwitch
- Ryu Controller
- Python dependencies (Flask, Socket.IO, etc.)

**Time**: ~5-10 minutes

---

## Running the Application

You need **3 terminals**.

### Terminal 1: Start Ryu Controller

```bash
./scripts/start_ryu.sh
```

**Wait for**: `"listening on 0.0.0.0:6633"`

### Terminal 2: Start Backend Server

```bash
./scripts/start_backend.sh
```

**Wait for**: `"Running on http://0.0.0.0:5000"`

### Terminal 3: Open Frontend

```bash
./scripts/start_frontend.sh
```

Or manually open your browser to: `http://localhost:5000`

---

## First Topology

1. **Select** "Star Topology" from dropdown
2. **Set** size to 4
3. **Click** "Create Topology"
4. **Wait** 5 seconds
5. **See** visualization appear!

![Star Topology](docs/images/star_topology_example.png)

---

## Test Connectivity

1. **Click** "Run Ping All" button
2. **Check** Activity Log
3. **Expected**: "✅ Pingall: 0% packet loss"

---

## Stopping

### Stop Topology

Click **"Stop Topology"** button in UI

### Stop Application

In each terminal, press **Ctrl+C**

### Clean Up

```bash
./scripts/cleanup.sh
```

---

## Troubleshooting

### "Cannot connect to Ryu controller"

**Solution**: Start Ryu first (Terminal 1), then Backend (Terminal 2)

### "Permission denied"

**Solution**: Backend needs sudo for Mininet
```bash
sudo -E python3 backend/app.py
```

### "Address already in use"

**Solution**: Clean up processes
```bash
./scripts/cleanup.sh
```

### Frontend shows "Disconnected"

**Solution**: Make sure Backend is running
```bash
pgrep -f "python.*app.py"
```

---

## Next Steps

- **Learn Concepts**: Read [docs/concepts.md](docs/concepts.md)
- **Try Different Topologies**: Linear, Tree, Mesh
- **View Documentation**: See [docs/](docs/) folder
- **Run Tests**: `./scripts/test_connection.sh`

---

## Common Commands

```bash
# Check system health
./scripts/health_check.sh

# Test everything
./scripts/test_connection.sh

# Clean up
./scripts/cleanup.sh

# View logs
tail -f backend.log
tail -f ryu.log
```

---

## Demo Mode (Single Terminal)

For presentations, use screen multiplexer:

```bash
# Install tmux
sudo apt-get install tmux

# Run demo script (creates panes automatically)
tmux new-session -d -s sdn 'scripts/start_ryu.sh' \; \
  split-window -v 'sleep 5; scripts/start_backend.sh' \; \
  attach
```

---

## Quick Reference

| Component | Port | Check Command |
|-----------|------|---------------|
| Ryu OpenFlow | 6633 | `netstat -tuln \| grep 6633` |
| Ryu REST API | 8080 | `curl localhost:8080/v1.0/topology/switches` |
| Flask Backend | 5000 | `curl localhost:5000/health` |

---

## Getting Help

- **Health Check**: `./scripts/health_check.sh`
- **Documentation**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **Test Connection**: `./scripts/test_connection.sh`
- **View Logs**: `backend.log`, `ryu.log`

---

## What's Next?

1. **Experiment**: Try all 4 topology types
2. **Learn**: Read SDN concepts in [docs/concepts.md](docs/concepts.md)
3. **Customize**: Modify `backend/config.py`
4. **Extend**: Add custom Ryu apps in `ryu_apps/`

Happy SDN learning! 🚀
