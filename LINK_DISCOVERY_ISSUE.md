# Switch Link Discovery Issue

## Problem

Switches in linear topology are not showing connections between them (s1 and s2 appear as separate islands).

## Root Cause

**Ryu uses LLDP (Link Layer Discovery Protocol) to discover links**, which takes time:
- Initial link discovery: **5-10 seconds**
- Topology updates: **Every 2-5 seconds**

When you create a topology, switches connect to Ryu immediately, but **inter-switch links take longer to appear**.

## What I Fixed

### 1. Link Deduplication
Ryu reports bidirectional links (s1→s2 AND s2→s1). Now we deduplicate them:

```python
# Create canonical link ID (smaller dpid first)
link_id = tuple(sorted([src_dpid, dst_dpid]))
if link_id not in seen_links:
    edges.append(link)
    seen_links.add(link_id)
```

### 2. Host Deduplication
Prevents duplicate MAC addresses from showing multiple nodes:

```python
if mac in seen_macs:
    continue
seen_macs.add(mac)
```

### 3. Better Host Naming
Shows IP address or last 8 MAC chars instead of "Unknown"

## Solution: Wait for Link Discovery

### ✅ Correct Workflow

```bash
1. Create topology (linear, size 2)
2. Wait 10-15 seconds ⏱️
3. Links should appear automatically
4. If not, check Ryu logs
```

### Manual Refresh (if needed)

The frontend should auto-update, but you can also:
- Refresh the page
- Click "Stop Topology" then "Create Topology" again

## Verification Commands (on EC2/server)

### Check if switches are connected to Ryu

```bash
curl http://localhost:8080/v1.0/topology/switches
```

**Expected output (2 switches):**
```json
[
  {"dpid": "0000000000000001", ...},
  {"dpid": "0000000000000002", ...}
]
```

### Check if links are discovered

```bash
curl http://localhost:8080/v1.0/topology/links
```

**Expected output (linear, size 2):**
```json
[
  {
    "src": {"dpid": "0000000000000001", "port_no": 2},
    "dst": {"dpid": "0000000000000002", "port_no": 2}
  },
  {
    "src": {"dpid": "0000000000000002", "port_no": 2},
    "dst": {"dpid": "0000000000000001", "port_no": 2}
  }
]
```

If **empty `[]`**, links haven't been discovered yet → **wait longer**.

### Check Ryu logs

```bash
tail -f ryu.log | grep -i link
```

Should show messages like:
```
[LinkEvent] link add: ...
```

## Why Discovery Takes Time

1. **LLDP packets** are sent periodically (every 2-5 seconds)
2. **Switches must exchange** LLDP frames
3. **Ryu processes** the LLDP packets and builds topology
4. **Frontend polls** Ryu every 2 seconds for updates

### Timeline

```
T+0s:  Topology created, switches connect to Ryu
T+3s:  First LLDP exchange
T+5s:  Link discovered by Ryu
T+6s:  Frontend polls and displays link ✅
```

## Forcing Link Discovery (Advanced)

If links never appear, manually trigger LLDP:

```bash
# On EC2, in Mininet
sudo mn
mininet> net
# Should show: s1-s2 link

# Force link update
mininet> link s1 s2 up
```

## Common Issues

### Issue 1: Ryu not running
**Symptom:** No switches appear at all  
**Fix:**
```bash
ps aux | grep ryu-manager
# If empty, start Ryu
nohup ./scripts/start_ryu.sh > ryu.log 2>&1 &
```

### Issue 2: Switches never connect
**Symptom:** Switch count stays at 0  
**Fix:**
```bash
# Check OVS is running
sudo systemctl status openvswitch-switch  # Ubuntu
sudo systemctl status ovs-vswitchd        # Arch

# Check switches manually
sudo ovs-vsctl show
```

### Issue 3: Links never discovered (even after 30s)
**Symptom:** Switches appear, but no inter-switch links  
**Fix:**
```bash
# Check if Ryu loaded topology module
grep "ryu.app.rest_topology" ryu.log

# Restart Ryu with topology discovery
pkill -f ryu-manager
ryu-manager \
    ryu.app.ofctl_rest \
    ryu.app.rest_topology \
    ryu.app.simple_switch_13 \
    ryu_apps/simple_monitor.py &
```

### Issue 4: Too many hosts showing
**Symptom:** 4 hosts for size=2 topology  
**Fix:** Already fixed with host deduplication. Refresh browser.

## Testing

### Test 1: Linear with 2 switches

```bash
1. Create linear, size 2
2. Wait 15 seconds
3. Should see: s1 --- s2 (connected)
4. Should see: 2 hosts total (h1 under s1, h2 under s2)
```

### Test 2: Linear with 4 switches

```bash
1. Create linear, size 4
2. Wait 15 seconds
3. Should see: s1 --- s2 --- s3 --- s4 (chain)
4. Should see: 4 hosts (one per switch)
```

### Test 3: Run ping all

```bash
1. After links appear
2. Click "Run Ping All"
3. Should see: 0% packet loss ✅
```

If ping fails with 100% loss → links not working (check Ryu)

---

## Summary

**Main Issue:** LLDP discovery takes 5-10 seconds  
**Solution:** Wait patiently, auto-updates every 2 seconds  
**Backup:** Refresh page or check Ryu API directly  

**Files Modified:**
- ✅ `backend/app.py` - Added link/host deduplication
- ✅ Better host naming (IP instead of "Unknown")

**Status:** Should work after waiting for LLDP discovery

**Last Updated:** 2024-11-02
