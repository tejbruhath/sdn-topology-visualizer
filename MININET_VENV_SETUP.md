# Mininet Virtual Environment Setup

## The Problem

**Mininet must be installed system-wide** (via `apt`) because it requires kernel modules and system-level network configuration. However, **Python virtual environments are isolated** and can't see system packages by default.

```
System Python (/usr/bin/python3)
  └── Can import mininet ✅

Venv Python (venv/bin/python)
  └── Cannot import mininet ❌
```

## The Solution: Symlink

Create a **symbolic link** from the system Mininet installation to the venv's site-packages directory.

```bash
ln -s /usr/lib/python3/dist-packages/mininet venv/lib/python3.8/site-packages/mininet
```

This allows the venv's Python to access Mininet while keeping other packages isolated.

---

## Manual Setup (If setup.sh didn't work)

### Step 1: Install Mininet System-Wide

```bash
sudo apt update
sudo apt install mininet -y
```

**Verify installation:**
```bash
mn --version
# Should output: mininet 2.3.0
```

### Step 2: Locate System Mininet

```bash
python3 -c "import mininet; print(mininet.__file__)"
# Output: /usr/lib/python3/dist-packages/mininet/__init__.py
```

Common paths:
- Ubuntu 20.04: `/usr/lib/python3/dist-packages/mininet`
- Ubuntu 22.04: `/usr/lib/python3/dist-packages/mininet`

### Step 3: Create Symlink

```bash
cd ~/sdn-topology-visualizer
source venv/bin/activate

# Create symlink
ln -s /usr/lib/python3/dist-packages/mininet venv/lib/python3.8/site-packages/mininet
```

**Verify the symlink:**
```bash
ls -la venv/lib/python3.8/site-packages/mininet
# Should show: mininet -> /usr/lib/python3/dist-packages/mininet
```

### Step 4: Test Import

```bash
python -c "from mininet.net import Mininet; print('✓ Mininet import successful')"
```

---

## Why This Approach?

### ✅ Benefits

1. **Clean separation:** System packages (Mininet) vs app packages (Flask, Ryu)
2. **No PYTHONPATH hacks:** Works directly with venv's Python
3. **Sudo compatibility:** `sudo -E venv/bin/python` can import Mininet
4. **Reproducible:** Easy to set up on new systems

### ❌ Alternatives (Not Recommended)

**Option 1: Install everything system-wide**
```bash
sudo pip3 install flask ryu  # Don't do this!
```
- ❌ Pollutes system Python
- ❌ Version conflicts with other projects
- ❌ Violates PEP 668 on Ubuntu 23.04+

**Option 2: Use PYTHONPATH**
```bash
PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH python app.py
```
- ❌ Must set every time
- ❌ Fragile (path can change)
- ❌ Doesn't work well with sudo

**Option 3: Install Mininet in venv**
```bash
pip install mininet  # This doesn't work properly
```
- ❌ Mininet needs kernel access
- ❌ Missing system dependencies

---

## Troubleshooting

### Issue: Symlink already exists

```bash
$ ln -s /usr/lib/python3/dist-packages/mininet venv/lib/python3.8/site-packages/mininet
ln: failed to create symbolic link: File exists
```

**Solution:** It's already set up! Test it:
```bash
python -c "from mininet.net import Mininet; print('OK')"
```

### Issue: Mininet not found at system path

```bash
$ ls /usr/lib/python3/dist-packages/mininet
ls: cannot access: No such file or directory
```

**Solution:** Install Mininet:
```bash
sudo apt install mininet
```

### Issue: Wrong Python version in venv

```bash
$ python --version
Python 3.10.x  # Expected 3.8
```

**Solution:** Recreate venv with Python 3.8:
```bash
rm -rf venv
python3.8 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
ln -s /usr/lib/python3/dist-packages/mininet venv/lib/python3.8/site-packages/mininet
```

### Issue: Import works but sudo fails

```bash
$ python -c "from mininet.net import Mininet"  # Works ✓
$ sudo python -c "from mininet.net import Mininet"  # Fails ✗
```

**Solution:** Use venv's Python with sudo:
```bash
sudo -E venv/bin/python -c "from mininet.net import Mininet"
```

The `-E` flag preserves environment variables.

---

## Automatic Setup

The `setup.sh` script now automatically creates this symlink in **Step 7.5: Linking Mininet to Virtual Environment**.

To re-run just this step:

```bash
cd ~/sdn-topology-visualizer
source venv/bin/activate

# Remove old symlink if exists
rm venv/lib/python3.8/site-packages/mininet 2>/dev/null || true

# Create new symlink
ln -s /usr/lib/python3/dist-packages/mininet venv/lib/python3.8/site-packages/mininet

# Test
python -c "from mininet.net import Mininet; print('✓ Success')"
```

---

## Verification Commands

```bash
# 1. Check system Mininet
python3 -c "import mininet; print(mininet.__file__)"

# 2. Check venv Python
source venv/bin/activate
python -c "import mininet; print(mininet.__file__)"

# 3. Check with sudo
sudo -E venv/bin/python -c "from mininet.net import Mininet; print('OK')"

# 4. Verify symlink
ls -la venv/lib/python3.8/site-packages/mininet

# 5. Test Mininet creation (requires sudo)
sudo -E venv/bin/python -c "
from mininet.net import Mininet
from mininet.node import Controller
net = Mininet(controller=Controller)
net.start()
print('✓ Mininet network created')
net.stop()
"
```

---

## Understanding the Setup

### Directory Structure

```
/usr/lib/python3/dist-packages/    ← System packages
    mininet/
        net.py
        node.py
        ...

~/sdn-topology-visualizer/
    venv/
        lib/python3.8/site-packages/  ← Venv packages
            flask/
            ryu/
            mininet -> /usr/lib/python3/dist-packages/mininet  ← Symlink
```

### Why Symlink Works

When Python imports a module:
1. Checks `sys.path` (includes venv/lib/python3.8/site-packages)
2. Finds `mininet` entry
3. Follows symlink to system location
4. Imports from system location ✅

---

## Best Practices

1. **Never use `sudo pip install`** - keeps venv clean
2. **Always activate venv** before running scripts
3. **Use `sudo -E venv/bin/python`** when needing root
4. **Check symlink** after recreating venv
5. **Test with** `from mininet.net import Mininet` before running app

---

**Status:** Implemented in setup.sh  
**Last Updated:** 2024-11-02
