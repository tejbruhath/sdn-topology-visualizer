# SDN Visualizer - Arch Linux Setup Guide

Complete installation and setup guide for **Arch Linux**, **Manjaro**, **EndeavourOS**, and other Arch-based distributions.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/sdn-visualizer.git
cd sdn-visualizer

# Run Arch-specific setup
chmod +x scripts/setup_arch.sh
./scripts/setup_arch.sh
```

---

## 📋 Prerequisites

- **OS:** Arch Linux, Manjaro, EndeavourOS, or Arch-based distro
- **Privileges:** sudo access
- **Internet:** For downloading packages
- **Disk:** ~500MB for dependencies

---

## 📦 What Gets Installed

### System Packages (via pacman)

```bash
base-devel          # Build tools (gcc, make, etc.)
git                 # Version control
curl                # HTTP client
wget                # File downloader
python              # Python interpreter (usually 3.11+)
python-pip          # Package installer
openvswitch         # Virtual switch
```

### Mininet (via AUR)

```bash
mininet             # Network emulator (from yay/AUR)
```

**Note:** If you don't have `yay` (AUR helper), the script installs it automatically.

### Python Packages (in venv)

All Python packages are installed in a virtual environment:

```
Flask==2.3.3
Werkzeug==2.3.7
Flask-SocketIO==5.3.4
python-socketio==5.9.0
python-engineio==4.7.1
Flask-CORS==4.0.0
eventlet==0.33.3
greenlet==2.0.2
requests==2.31.0
ryu==4.34
(and dependencies...)
```

---

## 🔧 Manual Installation

If you prefer step-by-step installation:

### 1. Update System

```bash
sudo pacman -Syu
```

### 2. Install Development Tools

```bash
sudo pacman -S --needed base-devel git curl wget python python-pip
```

### 3. Install yay (AUR Helper)

```bash
cd /tmp
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
cd -
```

### 4. Install Mininet

```bash
yay -S mininet
```

**Alternative: Install from source**

```bash
git clone https://github.com/mininet/mininet
cd mininet
sudo util/install.sh -a
```

### 5. Install Open vSwitch

```bash
sudo pacman -S openvswitch

# Enable and start service
sudo systemctl enable ovs-vswitchd
sudo systemctl start ovs-vswitchd

# Verify
sudo systemctl status ovs-vswitchd
```

### 6. Create Virtual Environment

```bash
cd ~/sdn-visualizer
python -m venv venv
source venv/bin/activate
```

### 7. Install Python Packages

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 8. Verify Installation

```bash
# Check Python packages
pip list | grep -E 'Flask|ryu'

# Check Mininet
sudo mn --version

# Check OVS
sudo ovs-vsctl --version
```

---

## ▶️ Running the Application

### Start Services

```bash
# Terminal 1: Start Ryu Controller
source venv/bin/activate
./scripts/start_ryu.sh

# Terminal 2: Start Backend
source venv/bin/activate
./scripts/start_backend.sh

# Terminal 3: Open browser
firefox http://localhost:5000
```

**Or use tmux:**

```bash
tmux new -s sdn

# Pane 1: Ryu
./scripts/start_ryu.sh

# Split pane: Ctrl+b then "
# Pane 2: Backend
./scripts/start_backend.sh

# Detach: Ctrl+b then d
```

---

## 🐛 Arch-Specific Troubleshooting

### Issue: `yay: command not found`

**Solution:** Install yay manually

```bash
cd /tmp
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
```

### Issue: Mininet package not found in AUR

**Solution:** Install from source

```bash
git clone https://github.com/mininet/mininet
cd mininet
sudo util/install.sh -nfv
```

### Issue: OVS service won't start

**Check service status:**

```bash
sudo systemctl status ovs-vswitchd
```

**Start manually:**

```bash
sudo systemctl start ovs-vswitchd
sudo systemctl enable ovs-vswitchd
```

**Check logs:**

```bash
sudo journalctl -u ovs-vswitchd -n 50
```

### Issue: Python version too old

Arch usually has latest Python. If somehow you need specific version:

```bash
# Install Python 3.10 (if needed)
yay -S python310

# Create venv with specific version
python3.10 -m venv venv
```

### Issue: Permission denied on scripts

```bash
chmod +x scripts/*.sh
```

### Issue: `eventlet` import error with Ryu

**Downgrade eventlet:**

```bash
source venv/bin/activate
pip install eventlet==0.30.2
```

### Issue: Firewall blocking ports

**Check firewall:**

```bash
sudo ufw status
```

**Allow ports (if using ufw):**

```bash
sudo ufw allow 5000/tcp
sudo ufw allow 6633/tcp
sudo ufw allow 8080/tcp
```

**Or disable firewall for development:**

```bash
sudo systemctl stop ufw
```

---

## 📊 Arch vs Debian Differences

| Aspect | Arch Linux | Ubuntu/Debian |
|--------|------------|---------------|
| Package Manager | `pacman` | `apt-get` |
| AUR Support | Yes (yay/paru) | No (PPA instead) |
| Python Version | Latest (3.11+) | 3.8-3.12 (depends) |
| Mininet Install | AUR or source | apt package |
| OVS Service | `ovs-vswitchd` | `openvswitch-switch` |
| Update Command | `sudo pacman -Syu` | `sudo apt-get update` |

---

## 🔍 Verification Commands

```bash
# System packages
pacman -Q | grep -E 'mininet|openvswitch|python'

# Python version
python --version

# Virtual environment
source venv/bin/activate
python --version  # Should match system Python

# Installed packages
pip list

# Services
sudo systemctl status ovs-vswitchd

# Ports
sudo ss -tulpn | grep -E '5000|6633|8080'
```

---

## 🎯 Performance Tips for Arch

### Use faster mirrors

```bash
sudo pacman -S reflector
sudo reflector --country 'United States,Canada' --age 12 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -Syu
```

### Enable parallel downloads

Edit `/etc/pacman.conf`:

```bash
sudo nano /etc/pacman.conf
```

Uncomment:

```
ParallelDownloads = 5
```

### Clear package cache

```bash
sudo pacman -Sc
```

---

## 🧹 Cleanup

### Stop all services

```bash
./scripts/cleanup.sh
```

### Remove virtual environment

```bash
rm -rf venv
```

### Uninstall packages (if needed)

```bash
# Remove Mininet
yay -R mininet

# Remove OVS
sudo pacman -R openvswitch

# Remove development tools (optional)
sudo pacman -R base-devel
```

---

## 🔄 Update Guide

### Update system

```bash
sudo pacman -Syu
```

### Update Python packages

```bash
source venv/bin/activate
pip install --upgrade -r backend/requirements.txt
```

### Update Mininet (if from AUR)

```bash
yay -Syu mininet
```

---

## 💡 Arch-Specific Tips

### Use `makepkg` safely

Always review PKGBUILDs before building:

```bash
yay -G mininet  # Download PKGBUILD
cd mininet
cat PKGBUILD    # Review
makepkg -si     # Build and install
```

### Use `systemctl` for services

```bash
# Check all network services
systemctl list-units --type=service | grep -E 'network|ovs'

# Enable service to start on boot
sudo systemctl enable ovs-vswitchd

# View logs
sudo journalctl -u ovs-vswitchd -f
```

### Optimize for development

Install useful tools:

```bash
sudo pacman -S \
    htop \        # Process monitor
    iotop \       # I/O monitor
    tmux \        # Terminal multiplexer
    vim \         # Text editor
    networkmanager-openvpn  # VPN support
```

---

## 📚 Additional Resources

- **Arch Wiki - Mininet:** https://wiki.archlinux.org/
- **AUR - Mininet:** https://aur.archlinux.org/packages/mininet
- **Open vSwitch Arch:** https://wiki.archlinux.org/title/Open_vSwitch
- **Python venv:** https://docs.python.org/3/library/venv.html

---

## ✅ Quick Command Reference

```bash
# Setup
./scripts/setup_arch.sh

# Start
source venv/bin/activate
./scripts/start_ryu.sh &
./scripts/start_backend.sh

# Test
./scripts/test_connection.sh

# Stop
./scripts/cleanup.sh

# Update system
sudo pacman -Syu

# Update Python packages
source venv/bin/activate
pip install --upgrade -r backend/requirements.txt
```

---

## 🆘 Getting Help

1. **Check logs:**
   ```bash
   tail -f ryu.log backend.log
   ```

2. **Run health check:**
   ```bash
   ./scripts/health_check.sh
   ```

3. **Check services:**
   ```bash
   sudo systemctl status ovs-vswitchd
   ps aux | grep -E 'ryu|flask'
   ```

4. **Arch Wiki:** Search for specific errors
   ```bash
   # Example
   https://wiki.archlinux.org/title/Mininet
   ```

---

**Status:** Tested on Arch Linux and Manjaro  
**Last Updated:** 2024-11-02  
**Python Version:** 3.11+ (Arch default)
