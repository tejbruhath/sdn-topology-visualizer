# Ubuntu 24.04 Python 3.12 Compatibility Fix

## ❌ Problem
Ubuntu 24.04 comes with Python 3.12.3, but **Ryu 4.34 only works with Python 3.8-3.11**.

Error: `AttributeError: 'types.SimpleNamespace' object has no attribute 'get_script_args'`

## ✅ Solution: Install Python 3.8

### Quick Fix (Manual)

```bash
# Install Python 3.8
sudo apt-get update
sudo apt-get install -y python3.8 python3.8-venv python3.8-dev

# Verify
python3.8 --version
# Should show: Python 3.8.x

# Remove broken venv
cd ~/sdn-topology-visualizer
rm -rf venv

# Create venv with Python 3.8
python3.8 -m venv venv

# Activate and install
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Automatic Fix (Pull Latest Code)

I've updated `setup.sh` to automatically:
1. Detect if Python 3.8 is available
2. Install Python 3.8 if missing
3. Create venv with Python 3.8 specifically

**On your EC2:**

```bash
cd ~/sdn-topology-visualizer

# Pull latest changes
git pull

# Remove old venv
rm -rf venv

# Run setup (now uses Python 3.8)
./scripts/setup.sh
```

The script will now:
- ✅ Install Python 3.8 automatically
- ✅ Create venv with Python 3.8
- ✅ Install all packages successfully

### Verify Installation

```bash
# Check venv Python version
source venv/bin/activate
python --version
# Should show: Python 3.8.x

# Check Ryu
pip list | grep ryu
# Should show: ryu 4.34
```

## Why This Happens

| Ubuntu Version | Default Python | Ryu 4.34 Compatible? |
|----------------|----------------|---------------------|
| 20.04 LTS | 3.8.10 | ✅ Yes |
| 22.04 LTS | 3.10.x | ✅ Yes |
| 24.04 LTS | 3.12.3 | ❌ No (this issue) |

**Ryu 4.34 requirements:**
- Python 3.8, 3.9, 3.10, or 3.11
- Does NOT support Python 3.12 yet

## Alternative: Use Ubuntu 20.04 or 22.04

If you can recreate your EC2 instance:
- **Ubuntu 20.04 LTS**: Python 3.8 by default (perfect!)
- **Ubuntu 22.04 LTS**: Python 3.10 (also works!)

## Checking Your Setup

```bash
# System Python
python3 --version

# Venv Python (after activation)
source venv/bin/activate
python --version

# Should be different!
# System: 3.12.3
# Venv: 3.8.x ✓
```

## Status

✅ **Fixed in latest code**
- Pull latest changes
- Run `./scripts/setup.sh`
- Will automatically use Python 3.8
