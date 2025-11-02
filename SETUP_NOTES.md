# Setup Notes - Virtual Environment & Mininet

## ✅ What Gets Installed Where

### System-Wide (requires sudo)
These are installed globally on your Ubuntu system:

```bash
# Network Emulation
mininet              # Creates virtual networks
openvswitch-switch   # Virtual switches with OpenFlow support
openvswitch-common   # OVS utilities

# System Tools
python3.8            # Python interpreter (Ubuntu 20.04 default)
python3-pip          # Package installer
git                  # Version control
```

**Why system-wide?**
- Mininet requires root privileges to create network namespaces
- Open vSwitch needs to run as a system service
- These tools need to be accessible by sudo commands

### Virtual Environment (venv/)
All Python packages are installed in an isolated environment:

```bash
# Location: sdn-visualizer/venv/

# SDN Controller
ryu==4.34

# Web Framework
Flask==2.3.3
Werkzeug==2.3.7
Flask-SocketIO==5.3.4
Flask-CORS==4.0.0

# WebSocket
python-socketio==5.9.0
python-engineio==4.7.1

# And all other Python dependencies...
```

**Why virtual environment?**
- Isolates project dependencies from system Python
- Prevents version conflicts with other projects
- Easy to recreate or delete without affecting system
- Best practice for Python development

---

## 🔧 How setup.sh Works

### Step-by-Step Process

```bash
./scripts/setup.sh
```

**What it does:**

1. **Checks Python 3.8+** - Verifies or installs Python 3.8
2. **Installs System Packages** - Mininet, OVS (requires sudo)
3. **Creates Virtual Environment** - `python3 -m venv venv`
4. **Activates venv** - `source venv/bin/activate`
5. **Installs Python Packages** - All requirements in venv
6. **Verifies Installation** - Checks all versions
7. **Configures System** - Cleans Mininet, starts OVS

---

## 📦 Virtual Environment Usage

### Activating venv

**Every time** you open a new terminal to work on this project:

```bash
cd sdn-visualizer
source venv/bin/activate
```

**You'll see:**
```bash
(venv) user@ubuntu:~/sdn-visualizer$
```

The `(venv)` prefix shows you're in the virtual environment.

### Deactivating venv

When you're done:

```bash
deactivate
```

### Why Activate?

When venv is activated:
- `python` points to venv's Python 3.8
- `pip` installs packages in venv (not system-wide)
- All installed packages are available
- Scripts use venv's packages

When venv is NOT activated:
- `python3` points to system Python
- Packages from venv are NOT available
- Scripts will fail with "module not found"

---

## 🚀 Running the Application

### Option 1: Scripts Auto-Activate (Recommended)

The start scripts automatically activate venv:

```bash
# No need to manually activate!
./scripts/start_ryu.sh       # Activates venv, starts Ryu
./scripts/start_backend.sh   # Activates venv, starts Flask
```

### Option 2: Manual Activation

If you prefer to run Python directly:

```bash
# Activate once
source venv/bin/activate

# Now run commands
ryu-manager --version
python backend/app.py
```

---

## 🌐 About Mininet

### What is Mininet?

Mininet creates **virtual networks** on a single machine:
- Virtual hosts (Linux processes in network namespaces)
- Virtual switches (Open vSwitch with OpenFlow)
- Virtual links (virtual Ethernet pairs)

### Why System-Wide?

Mininet MUST be installed system-wide because:

1. **Requires Root Privileges**
   ```bash
   sudo mn --topo star,3  # Needs sudo
   ```

2. **Creates Network Namespaces**
   - Linux kernel feature requiring root
   - Isolates network stack for each virtual host

3. **Manages OVS Bridges**
   - Open vSwitch runs as system service
   - Requires root to create/delete bridges

4. **Cannot Run in venv**
   - Virtual environments don't provide root access
   - Network operations need system-level permissions

### How We Use Mininet

Our Python code (in venv) **controls** Mininet (system-wide):

```python
# backend/mininet_manager.py (runs in venv)
from mininet.net import Mininet  # Imports system Mininet
from mininet.node import RemoteController, OVSSwitch

# Creates network (requires sudo when running Flask)
net = Mininet(controller=RemoteController, switch=OVSSwitch)
net.start()  # System call to create namespaces
```

**Key Point:** Python code runs in venv, but Mininet operations execute with sudo.

---

## 🔐 Sudo Requirements

### Why Sudo for Backend?

```bash
sudo -E python3 backend/app.py
```

The backend needs sudo because:
- Creates Mininet networks (requires root)
- Manages OVS switches (requires root)
- Creates network namespaces (requires root)

The `-E` flag preserves environment variables (including venv path).

### Security Note

⚠️ **This is for development/lab environments only!**

For production:
- Use setcap to grant specific capabilities
- Run Mininet operations in separate privileged process
- Use proper authentication and authorization

---

## 📁 Directory Structure

```
sdn-visualizer/
│
├── venv/                    # Virtual environment (gitignored)
│   ├── bin/
│   │   ├── python          # Python 3.8 in venv
│   │   ├── pip             # pip for venv
│   │   ├── ryu-manager     # Ryu in venv
│   │   └── flask           # Flask in venv
│   ├── lib/
│   │   └── python3.8/
│   │       └── site-packages/  # All Python packages
│   └── ...
│
├── backend/                 # Python code (uses venv)
│   ├── app.py              # Flask app
│   ├── mininet_manager.py  # Mininet control
│   ├── ryu_client.py       # Ryu API client
│   └── requirements.txt    # Package list
│
├── scripts/                 # Bash scripts
│   ├── setup.sh            # Creates venv
│   ├── start_ryu.sh        # Activates venv, starts Ryu
│   └── start_backend.sh    # Activates venv, starts Flask
│
└── ...
```

---

## 🔍 Verification Commands

### Check venv is Active

```bash
which python
# Should show: /path/to/sdn-visualizer/venv/bin/python

echo $VIRTUAL_ENV
# Should show: /path/to/sdn-visualizer/venv
```

### Check Packages in venv

```bash
source venv/bin/activate
pip list | grep -E 'Flask|ryu|mininet'
```

**Expected:**
```
Flask                 2.3.3
Flask-CORS            4.0.0
Flask-SocketIO        5.3.4
ryu                   4.34
```

**Note:** Mininet won't show here (it's system-wide)

### Check System Mininet

```bash
# Outside venv
which mn
# Shows: /usr/bin/mn (system-wide)

sudo mn --version
# Shows: mininet 2.3.0
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

**Problem:** venv not activated

**Solution:**
```bash
source venv/bin/activate
```

### "mn: command not found"

**Problem:** Mininet not installed system-wide

**Solution:**
```bash
sudo apt-get install mininet
```

### "Permission denied" when starting backend

**Problem:** Mininet needs sudo

**Solution:**
```bash
sudo -E python3 backend/app.py
# OR
sudo ./scripts/start_backend.sh
```

### venv Broken or Corrupted

**Problem:** Packages missing or wrong versions

**Solution:**
```bash
# Delete and recreate
rm -rf venv
./scripts/setup.sh
```

---

## 📝 Best Practices

### 1. Always Activate venv

```bash
# Add to your ~/.bashrc for convenience
alias sdnvenv='cd ~/sdn-visualizer && source venv/bin/activate'
```

### 2. Use Scripts (They Handle venv)

```bash
# Preferred
./scripts/start_ryu.sh

# Instead of
source venv/bin/activate
ryu-manager ...
```

### 3. Keep venv in .gitignore

The venv/ directory is already gitignored. Never commit it!

### 4. Recreate venv on New Machine

```bash
git clone <repo>
cd sdn-visualizer
./scripts/setup.sh  # Creates fresh venv
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Create venv | `./scripts/setup.sh` |
| Activate venv | `source venv/bin/activate` |
| Deactivate venv | `deactivate` |
| Check if in venv | `echo $VIRTUAL_ENV` |
| Install package | `pip install <package>` (when venv active) |
| Start Ryu | `./scripts/start_ryu.sh` (auto-activates) |
| Start Backend | `./scripts/start_backend.sh` (auto-activates) |
| Check Mininet | `sudo mn --version` (system-wide) |
| Clean Mininet | `sudo mn -c` |

---

## ✅ Summary

**Virtual Environment (venv/):**
- Contains all Python packages
- Isolated from system
- Must be activated to use
- Scripts auto-activate

**Mininet (System-Wide):**
- Installed globally with apt
- Requires sudo to run
- Cannot be in venv
- Controlled by Python code in venv

**The Setup:**
```
┌─────────────────────────────────────┐
│  Ubuntu System                      │
│  ├── Mininet (sudo)                 │
│  ├── Open vSwitch (sudo)            │
│  └── Python 3.8                     │
└─────────────────────────────────────┘
           ↑
           │ (controlled by)
           │
┌─────────────────────────────────────┐
│  Virtual Environment (venv/)        │
│  ├── Flask, Ryu, etc.               │
│  └── Your Python code               │
└─────────────────────────────────────┘
```

**Yes, we ARE using Mininet!** It's essential for creating virtual networks. It's just installed system-wide instead of in the venv.
