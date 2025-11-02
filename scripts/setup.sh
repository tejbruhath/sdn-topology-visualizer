#!/bin/bash
# SDN Visualizer - Complete Setup Script for Debian/Ubuntu
# This script installs all required dependencies

set -e  # Exit on error

echo "=========================================="
echo "SDN Visualizer - Setup Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Please run this script as a regular user (not root)"
    echo "   The script will ask for sudo when needed"
    exit 1
fi

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    echo "✓ Detected OS: $PRETTY_NAME"
else
    echo "❌ Cannot detect OS. This script is for Debian/Ubuntu."
    exit 1
fi

if [[ "$OS" != "debian" && "$OS" != "ubuntu" ]]; then
    echo "⚠️  This script is designed for Debian/Ubuntu"
    echo "   Your OS: $OS"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Step 1: Updating Package Lists"
echo "=========================================="
sudo apt-get update

echo ""
echo "=========================================="
echo "Step 2: Checking Python Version"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"

echo "Current Python version: $PYTHON_VERSION"

# Compare versions - now checking for Python 3.8+
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✓ Python 3.8+ is installed"
else
    echo "⚠️  Python 3.8+ required, but found $PYTHON_VERSION"
    echo "Installing Python 3.8..."
    
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.8 python3.8-dev python3.8-venv
    
    # Update alternatives to use Python 3.8
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
    
    echo "✓ Python 3.8 installed"
fi

echo ""
echo "=========================================="
echo "Step 3: Installing System Dependencies"
echo "=========================================="
sudo apt-get install -y \
    git \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    wget

echo ""
echo "=========================================="
echo "Step 4: Installing Mininet"
echo "=========================================="
if command -v mn &> /dev/null; then
    echo "✓ Mininet already installed"
    mn --version
else
    echo "Installing Mininet..."
    sudo apt-get install -y mininet
    
    # Verify installation
    if command -v mn &> /dev/null; then
        echo "✓ Mininet installed successfully"
        mn --version
    else
        echo "❌ Mininet installation failed"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Step 5: Installing Open vSwitch"
echo "=========================================="
if command -v ovs-vsctl &> /dev/null; then
    echo "✓ Open vSwitch already installed"
    ovs-vsctl --version | head -n 1
else
    echo "Installing Open vSwitch..."
    sudo apt-get install -y openvswitch-switch openvswitch-common
    
    # Start OVS service
    sudo systemctl start openvswitch-switch
    sudo systemctl enable openvswitch-switch
    
    # Verify installation
    if command -v ovs-vsctl &> /dev/null; then
        echo "✓ Open vSwitch installed successfully"
        ovs-vsctl --version | head -n 1
    else
        echo "❌ Open vSwitch installation failed"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Step 6: Creating Python Virtual Environment"
echo "=========================================="

# Get project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if venv already exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python 3.8 virtual environment..."
    python3 -m venv venv
    
    if [ ! -d "venv" ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated: $VIRTUAL_ENV"

echo ""
echo "=========================================="
echo "Step 7: Installing Python Dependencies"
echo "=========================================="

# Upgrade pip in venv
echo "Upgrading pip in virtual environment..."
pip install --upgrade pip

# Verify Python version
echo "Verifying Python 3.8+ in virtual environment..."
python --version
if ! python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ is required but not found in venv"
    exit 1
fi

# Install from requirements.txt with exact versions
echo "Installing Python packages with specified versions..."
pip install -r backend/requirements.txt

# Verify key packages
echo ""
echo "Verifying installed packages..."
python3 -c "
import sys
required_packages = {
    'Flask': '2.3.3',
    'Werkzeug': '2.3.7',
    'flask_socketio': '5.3.4',
    'flask_cors': '4.0.0',
    'requests': '2.31.0',
    'ryu': '4.34',
    'python_socketio': '5.9.0',
    'python_engineio': '4.7.1',
    'eventlet': '0.33.3',
    'greenlet': '2.0.2'
}

print('Package verification:')
for package, expected_version in required_packages.items():
    try:
        module = __import__(package.lower().replace('-', '_'))
        actual_version = getattr(module, '__version__', 'unknown')
        status = '✓' if actual_version.startswith(expected_version.split('.')[0]) else '⚠️'
        print(f'{status} {package}: {actual_version} (expected {expected_version})')
    except ImportError:
        print(f'✗ {package}: NOT INSTALLED')
"

# Verify Ryu installation
if python3 -c "import ryu" 2>/dev/null; then
    echo "✓ Ryu installed successfully"
    ryu-manager --version
else
    echo "❌ Ryu installation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 8: Configuring System"
echo "=========================================="

# Clean any existing Mininet processes
echo "Cleaning up any existing Mininet processes..."
sudo mn -c 2>/dev/null || true

# Check if OVS is running
if sudo systemctl is-active --quiet openvswitch-switch; then
    echo "✓ Open vSwitch service is running"
else
    echo "⚠️  Starting Open vSwitch service..."
    sudo systemctl start openvswitch-switch
fi

echo ""
echo "=========================================="
echo "Step 9: Creating Helper Scripts"
echo "=========================================="

# Make all scripts executable
chmod +x scripts/*.sh

echo "✓ Scripts are now executable"

echo ""
echo "=========================================="
echo "Step 10: Final Verification"
echo "=========================================="

echo ""
echo "Checking installed components..."
echo ""

# Python version
echo -n "Python: "
python3 --version

# Mininet
echo -n "Mininet: "
mn --version 2>&1 | head -n 1

# OVS
echo -n "Open vSwitch: "
ovs-vsctl --version | head -n 1

# Ryu
echo -n "Ryu: "
ryu-manager --version 2>&1 | head -n 1

# Flask
echo -n "Flask: "
python3 -c "import flask; print(flask.__version__)"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Activate virtual environment before running:"
echo ""
echo "   source venv/bin/activate"
echo ""
echo "Next steps:"
echo "1. Activate venv:         source venv/bin/activate"
echo "2. Start Ryu controller:  ./scripts/start_ryu.sh"
echo "3. Start Flask backend:   ./scripts/start_backend.sh"
echo "4. Open browser:          http://localhost:5000"
echo ""
echo "For testing:              ./scripts/test_connection.sh"
echo "For cleanup:              ./scripts/cleanup.sh"
echo ""
echo "Note: Mininet is installed system-wide (required for network emulation)"
echo "      Python packages are in the virtual environment (venv/)"
echo ""
echo "See README.md for detailed usage instructions"
echo ""
