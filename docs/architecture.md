# SDN Visualizer - System Architecture

## Overview

The SDN Visualizer is a layered application that combines network emulation (Mininet), SDN control (Ryu), web backend (Flask), and visualization (D3.js) to create an interactive network topology viewer.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend Layer                         │
│         (HTML5 + D3.js + Socket.IO Client)              │
│  • Topology visualization                                │
│  • User interactions                                     │
│  • Real-time updates                                     │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP REST + WebSocket
┌────────────────▼────────────────────────────────────────┐
│                    API Layer                             │
│              (Flask + Socket.IO Server)                  │
│  • REST endpoints                                        │
│  • WebSocket event handling                              │
│  • Request validation                                    │
└────────────┬───────────────┬────────────────────────────┘
             │               │
    ┌────────▼──────┐   ┌───▼──────────┐
    │   Mininet     │   │  Ryu Client  │
    │   Manager     │   │   (Wrapper)  │
    └────────┬──────┘   └───┬──────────┘
             │               │
┌────────────▼───────┐   ┌───▼──────────────────────────┐
│  Network Layer     │   │   Controller Layer           │
│  (Mininet + OVS)   │◄──┤   (Ryu SDN Framework)        │
│                    │   │                              │
│  • Virtual hosts   │   │  • OpenFlow switch mgmt      │
│  • Virtual switches│   │  • Flow table installation   │
│  • Virtual links   │   │  • Network stats collection  │
└────────────────────┘   └──────────────────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technology**: HTML5, CSS3, JavaScript, D3.js v7, Socket.IO Client

**Responsibilities**:
- Render interactive force-directed graphs
- Handle user input (topology selection, tests)
- Display real-time statistics
- Show activity logs
- Provide intuitive UI controls

**Key Files**:
- `frontend/index.html` - Main UI structure
- `frontend/static/js/app.js` - Application logic and D3.js visualization

**Communication**:
- REST API calls for actions (create topology, run tests)
- WebSocket for real-time updates (topology changes, statistics)

### 2. API Layer (Backend)

**Technology**: Python 3, Flask, Flask-SocketIO, Flask-CORS

**Responsibilities**:
- Expose REST endpoints for topology management
- Handle WebSocket connections for real-time updates
- Coordinate between Mininet and Ryu
- Run background threads for statistics monitoring
- Validate user input and handle errors

**Key Files**:
- `backend/app.py` - Main Flask application
- `backend/config.py` - Configuration settings
- `backend/requirements.txt` - Python dependencies

**REST Endpoints**:
```
POST   /api/topology/create   - Create new topology
POST   /api/topology/stop     - Stop current topology
POST   /api/topology/pingall  - Run connectivity test
GET    /api/topology/data     - Get current topology structure
GET    /api/stats/flows/:dpid - Get flow table for switch
GET    /api/stats/ports/:dpid - Get port statistics
GET    /health                - Health check
```

**WebSocket Events**:
```
Outbound:
  - topology_update    (topology structure changes)
  - stats_update       (periodic statistics)
  - connection_status  (connection state)
  - error              (error messages)

Inbound:
  - request_topology   (client requests current topology)
  - request_stats      (client requests statistics)
```

### 3. Mininet Manager

**Technology**: Python 3, Mininet Python API

**Responsibilities**:
- Create network topologies programmatically
- Start/stop Mininet networks
- Run network tests (pingall, ping)
- Clean up resources properly
- Configure OpenFlow versions

**Key Files**:
- `backend/mininet_manager.py`

**Supported Topologies**:
1. **Star**: Single central switch with N hosts
2. **Linear**: Chain of switches, each with one host
3. **Tree**: Binary tree of switches with hosts at leaves
4. **Mesh**: Full mesh of switches (all-to-all)

**Critical Operations**:
```python
# Creation sequence
1. Clean up existing network
2. Create Mininet object with RemoteController
3. Add switches (set OpenFlow 1.3)
4. Add hosts with IP addresses
5. Create links
6. Start network
7. Wait for switches to connect to Ryu
```

### 4. Ryu Client

**Technology**: Python 3, Requests library, Ryu REST APIs

**Responsibilities**:
- Abstract Ryu REST API calls
- Handle API errors gracefully
- Convert data formats (DPID hex to int)
- Provide high-level network queries

**Key Files**:
- `backend/ryu_client.py`

**API Methods**:
- `get_switches()` - List all connected switches
- `get_links()` - List all inter-switch links
- `get_hosts()` - List all discovered hosts
- `get_flow_stats(dpid)` - Get flow table for switch
- `get_port_stats(dpid)` - Get port statistics
- `is_connected()` - Check Ryu availability

### 5. Controller Layer (Ryu)

**Technology**: Python 3, Ryu SDN Framework, OpenFlow 1.3

**Responsibilities**:
- Manage OpenFlow switches
- Install flow rules for packet forwarding
- Collect network statistics
- Expose REST APIs for external access
- Implement SDN control logic

**Key Applications**:
- `ryu.app.simple_switch_13` - Layer 2 learning switch
- `ryu.app.ofctl_rest` - REST API for flow management
- `ryu.app.rest_topology` - REST API for topology discovery
- `ryu_apps/simple_monitor.py` - Custom statistics collector
- `ryu_apps/learning_switch.py` - Custom L2 switch

**OpenFlow Communication**:
```
1. Switch connects → HELLO handshake
2. Ryu requests features → FEATURES_REQUEST
3. Switch responds → FEATURES_REPLY (DPID, ports)
4. Ryu installs default rules → FLOW_MOD
5. Unknown packet arrives → PACKET_IN
6. Ryu decides forwarding → FLOW_MOD + PACKET_OUT
```

### 6. Network Layer (Mininet)

**Technology**: Mininet, Open vSwitch (OVS), Linux network namespaces

**Responsibilities**:
- Emulate network hosts using Linux processes
- Create virtual switches using OVS
- Connect components with virtual links
- Execute network commands (ping, iperf)
- Provide isolated network environments

**Components**:
- **Hosts**: Linux processes in separate network namespaces
- **Switches**: OVS bridges with OpenFlow support
- **Links**: Virtual Ethernet pairs (veth)
- **Controller**: Remote connection to Ryu on port 6633

## Data Flow Example: Creating a Star Topology

```
1. User clicks "Create Star Topology" (size=4)
   ↓
2. Frontend → POST /api/topology/create {"type":"star", "size":4}
   ↓
3. Flask validates input
   ↓
4. Flask → MininetManager.create("star", 4)
   ↓
5. Mininet creates:
   - 1 switch (s1)
   - 4 hosts (h1, h2, h3, h4)
   - 4 links (h1-s1, h2-s1, h3-s1, h4-s1)
   ↓
6. Mininet starts network
   ↓
7. OVS switches connect to Ryu (port 6633)
   ↓
8. Ryu receives switch connections → stores DPID and ports
   ↓
9. Flask waits 3 seconds for connections to stabilize
   ↓
10. Flask → RyuClient.get_switches()
    ↓
11. RyuClient → GET http://localhost:8080/v1.0/topology/switches
    ↓
12. Ryu returns switch data
    ↓
13. Flask → RyuClient.get_links() and get_hosts()
    ↓
14. Flask formats data for D3.js:
    nodes: [{id:"s1", type:"switch"}, {id:"h1", type:"host"}, ...]
    edges: [{source:"h1", target:"s1"}, ...]
    ↓
15. Flask → SocketIO.emit('topology_update', data)
    ↓
16. Frontend receives WebSocket event
    ↓
17. D3.js renders graph:
    - Creates SVG nodes (circles for switches/hosts)
    - Creates SVG links (lines between nodes)
    - Applies force simulation for layout
    ↓
18. User sees interactive visualization
```

## Statistics Monitoring Flow

```
[Background Thread in Flask]
   ↓
Every 2 seconds:
   ↓
1. Query Ryu → GET /stats/port/:dpid
   ↓
2. Parse port statistics (rx_packets, tx_packets, etc.)
   ↓
3. Calculate totals
   ↓
4. Emit via WebSocket → stats_update event
   ↓
[Frontend receives update]
   ↓
5. Update stats panel (packet count, bytes)
   ↓
6. No page refresh needed
```

## Critical Dependencies

### Port Usage
- **6633**: OpenFlow protocol (OVS → Ryu)
- **8080**: Ryu REST API (Flask → Ryu)
- **5000**: Flask web server (Browser → Flask)

### Startup Sequence (MUST follow this order)
1. Start Ryu controller (wait for "listening on 6633")
2. Start Flask backend (wait for "Running on 5000")
3. Create topology (wait 3s for switches to connect)
4. Access frontend

### Shutdown Sequence (MUST follow this order)
1. Stop topology via API or stop backend
2. Run `sudo mn -c` to clean Mininet
3. Kill Ryu process
4. Verify with `sudo ovs-vsctl list-br` (should be empty)

## Technology Choices & Rationale

| Component | Choice | Why | Alternative |
|-----------|--------|-----|-------------|
| Network Emulator | Mininet | Industry standard, Python API, fast | GNS3 (heavyweight), Containerlab (newer) |
| SDN Controller | Ryu | Mature, good REST APIs, Python | ONOS (complex), ODL (Java) |
| Backend | Flask | Lightweight, easy integration | FastAPI (async overkill), Django (too heavy) |
| Real-time | Socket.IO | Bidirectional, auto-reconnect | SSE (one-way only), Raw WebSocket (manual handling) |
| Visualization | D3.js | Best for graphs, flexible | Cytoscape.js (easier but less flexible) |
| Switch | Open vSwitch | OpenFlow 1.3, well-tested | Linux bridge (no OpenFlow) |

## Performance Considerations

### Scalability Limits
- **Max topology size**: 20 nodes (configurable)
  - Reason: D3.js force simulation becomes slow
  - Mininet can handle more, but visualization suffers
  
- **Stats update interval**: 2 seconds (configurable)
  - Reason: Balance between freshness and CPU usage
  - Faster updates cause Ryu API overload

- **Switch connection timeout**: 3 seconds
  - Reason: OpenFlow handshake + flow installation time
  - Larger topologies may need more time

### Resource Usage
- **Memory**: ~500MB for full stack
- **CPU**: <10% idle, ~30% during topology creation
- **Disk**: ~100MB for logs (rotating)

## Security Considerations

⚠️ **This is a development/educational tool, NOT production-ready**

**Current Limitations**:
- No authentication on Flask API
- WebSocket accepts all origins (CORS: *)
- Backend requires sudo (Mininet needs root)
- No input sanitization on topology size
- Ryu REST API exposed without auth
- Logs may contain sensitive network info

**For Production Use**:
1. Add authentication (JWT, OAuth)
2. Restrict CORS to specific origins
3. Run backend as non-root (use setcap)
4. Add rate limiting on API endpoints
5. Sanitize all user inputs
6. Enable HTTPS/WSS
7. Use environment variables for secrets
8. Implement audit logging

## Extension Points

### Adding New Topology Types
1. Add to `config.TOPOLOGY_TYPES`
2. Implement `_create_<type>()` in `MininetManager`
3. Add option to frontend dropdown
4. Update documentation

### Adding Custom Ryu Apps
1. Create Python file in `ryu_apps/`
2. Inherit from `ryu.base.app_manager.RyuApp`
3. Add to `start_ryu.sh` command line
4. Optionally expose via REST API

### Adding New Visualizations
1. Add D3.js code to `frontend/static/js/app.js`
2. Create new endpoint in `backend/app.py`
3. Add UI controls in `frontend/index.html`
4. Document in API reference

## Troubleshooting Architecture Issues

| Issue | Layer | Likely Cause |
|-------|-------|--------------|
| No visualization | Frontend | WebSocket not connected, check browser console |
| Topology creation fails | API/Mininet | Ryu not running, permissions issue |
| Switches don't connect | Network/Controller | Wrong OpenFlow version, firewall blocking port 6633 |
| Stats not updating | API | Background thread crashed, check backend logs |
| Pingall fails | Network | Flows not installed, check Ryu logs |
| Frontend doesn't load | API | Flask not running, wrong URL |

See [troubleshooting.md](troubleshooting.md) for detailed solutions.
