# Python Version Requirements - IMPORTANT

## ✅ What Was Fixed in setup.sh

### 1. Python 3.10+ Version Check (NEW)
The setup script now:
- **Checks current Python version** before proceeding
- **Automatically installs Python 3.10** if not present (using deadsnakes PPA)
- **Updates alternatives** to set Python 3.10 as default
- **Verifies version** before installing packages

### 2. Package Version Verification (NEW)
After installing packages, the script now:
- **Verifies each package** is installed with correct version
- **Shows version comparison** (installed vs expected)
- **Reports any missing packages** 

### 3. Exit on Version Mismatch (NEW)
The script will **exit with error** if:
- Python 3.10+ is not available and cannot be installed
- Required packages fail to install

## 📦 Exact Package Versions (from requirements.txt)

All packages install with **pinned versions**:

```
Flask==3.0.0              ✓ Specified (Latest stable)
Flask-SocketIO==5.3.5     ✓ Specified
Flask-CORS==4.0.0         ✓ Specified
requests==2.31.0          ✓ Specified
ryu==4.34                 ✓ Specified
python-socketio==5.10.0   ✓ Specified
python-engineio==4.8.0    ✓ Specified
eventlet==0.33.3          ✓ Specified
werkzeug==3.0.1           ✓ Specified
python-dotenv==1.0.0      ✓ Specified
pytest==7.4.2             ✓ Specified
pytest-cov==4.1.0         ✓ Specified
```

These are installed via `pip install -r requirements.txt` which respects the `==` version pins.

## 🔍 What the Script Does Now

### Step 2: Python Version Check (NEW)
```bash
# Checks if Python 3.10+ is installed
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "✓ Python 3.10+ is installed"
else
    # Installs Python 3.10 from deadsnakes PPA
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get install -y python3.10 python3.10-dev python3.10-venv
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
fi
```

### Step 6: Package Installation with Verification (NEW)
```bash
# Verifies Python 3.10+ before installing
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Python 3.10+ is required but not found"
    exit 1
fi

# Installs with exact versions
python3 -m pip install -r backend/requirements.txt

# Verifies installed versions
python3 -c "
required_packages = {
    'Flask': '3.0.0',
    'flask_socketio': '5.3.5',
    'python_socketio': '5.10.0',
    'python_engineio': '4.8.0',
    ...
}
# Checks each package version
"
```

## 🎯 Verification Commands

After running setup.sh, verify:

```bash
# Check Python version
python3 --version
# Should show: Python 3.10.x or higher

# Check Flask version
python3 -c "import flask; print(flask.__version__)"
# Should show: 3.0.0

# Check Ryu version
ryu-manager --version
# Should show: ryu-manager 4.34

# Check all packages
python3 -c "
import flask, flask_socketio, flask_cors, requests, ryu
print(f'Flask: {flask.__version__}')
print(f'Flask-SocketIO: {flask_socketio.__version__}')
print(f'Flask-CORS: {flask_cors.__version__}')
print(f'Requests: {requests.__version__}')
print(f'Ryu: {ryu.__version__}')
"
```

## ⚠️ Important Notes

### For Debian Systems:
- **Debian 11 (Bullseye)**: Comes with Python 3.9 → setup.sh will upgrade to 3.10
- **Debian 12 (Bookworm)**: Comes with Python 3.11 → already satisfies requirement ✓
- **Ubuntu 20.04**: Comes with Python 3.8 → setup.sh will upgrade to 3.10
- **Ubuntu 22.04**: Comes with Python 3.10 → already satisfies requirement ✓

### The setup.sh Script Will:
1. ✅ Detect if Python < 3.10
2. ✅ Add deadsnakes PPA repository
3. ✅ Install Python 3.10 specifically
4. ✅ Set Python 3.10 as the default `python3` command
5. ✅ Verify before installing packages
6. ✅ Install all packages with exact versions from requirements.txt
7. ✅ Verify each package was installed correctly

## 🔄 If You Already Ran Old setup.sh

If you ran the setup before this fix:

```bash
# Clean up
./scripts/cleanup.sh

# Check current Python version
python3 --version

# If < 3.10, manually install:
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-dev python3.10-venv

# Set as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Reinstall packages with correct Python version
python3 -m pip install -r backend/requirements.txt

# Verify
python3 --version  # Should show 3.10.x
```

## ✅ Summary

**Before Fix:**
- ❌ No Python version check
- ❌ Could install with any Python 3.x
- ❌ No package version verification
- ❌ Silent failures possible

**After Fix:**
- ✅ Enforces Python 3.10+
- ✅ Automatically installs Python 3.10 if needed
- ✅ Verifies Python version before package installation

## requirements.txt Already Had Correct Versions

Good news: The **`requirements.txt`** now has all correct versions pinned:
- `Flask==3.0.0` 
- `Flask-SocketIO==5.3.5` 
- `Flask-CORS==4.0.0` 
- `requests==2.31.0` 
- `ryu==4.34` 
- `python-socketio==5.10.0` 
- `python-engineio==4.8.0` 
- `werkzeug==3.0.1` 
- All other packages with exact versions 

The only issue was that the **setup.sh script didn't enforce Python 3.10+**. This is now fixed.
