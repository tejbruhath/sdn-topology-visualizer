# Project Structure

Complete overview of the SDN Visualizer file organization.

## Directory Tree

```
sdn-visualizer/
│
├── README.md                    # Main project documentation
├── QUICKSTART.md                # Quick start guide
├── LICENSE                      # MIT License
├── PROJECT_STRUCTURE.md         # This file
├── .gitignore                   # Git ignore rules
│
├── backend/                     # Python Flask backend
│   ├── app.py                   # Main Flask application (WebSocket + REST)
│   ├── config.py                # Configuration settings
│   ├── mininet_manager.py       # Mininet topology management
│   ├── ryu_client.py            # Ryu REST API wrapper
│   └── requirements.txt         # Python dependencies
│
├── frontend/                    # HTML/CSS/JavaScript frontend
│   ├── index.html               # Main UI (single page application)
│   └── static/
│       └── js/
│           └── app.js           # D3.js visualization + WebSocket client
│
├── ryu_apps/                    # Custom Ryu controller applications
│   ├── simple_monitor.py        # Statistics collection app
│   └── learning_switch.py       # Layer 2 learning switch app
│
├── scripts/                     # Bash automation scripts
│   ├── setup.sh                 # Install all dependencies (Debian)
│   ├── start_ryu.sh             # Launch Ryu controller
│   ├── start_backend.sh         # Launch Flask backend
│   ├── start_frontend.sh        # Open browser to frontend
│   ├── cleanup.sh               # Stop all processes and clean state
│   ├── health_check.sh          # Verify system health
│   └── test_connection.sh       # Integration test
│
├── docs/                        # Comprehensive documentation
│   ├── architecture.md          # System design and data flow
│   ├── api_reference.md         # REST/WebSocket API documentation
│   ├── troubleshooting.md       # Common issues and solutions
│   ├── testing_guide.md         # Complete testing checklist
│   └── concepts.md              # SDN fundamentals explained
│
└── tests/                       # Unit and integration tests
    ├── test_mininet.py          # Mininet manager tests
    └── test_api.py              # Flask API tests
```

---

## File Descriptions

### Root Directory

#### README.md
- **Purpose**: Main project documentation
- **Contents**: Features, installation, usage, troubleshooting
- **Audience**: First-time users

#### QUICKSTART.md
- **Purpose**: Get running in 5 minutes
- **Contents**: Minimal installation and usage steps
- **Audience**: Impatient users who want to see it work now

#### LICENSE
- **Purpose**: Legal terms (MIT License)
- **Contents**: Open source license text
- **Note**: Allows commercial and private use

#### .gitignore
- **Purpose**: Git version control exclusions
- **Contents**: Python cache, logs, virtual environments, temp files

---

### Backend Directory (`backend/`)

#### app.py (500 lines)
**The heart of the application**

```python
# Key Components:
- Flask initialization
- WebSocket (Socket.IO) setup
- REST API endpoints (/api/topology/*, /health)
- WebSocket event handlers (connect, disconnect, requests)
- Background statistics monitoring thread
- Error handlers
```

**Dependencies**: Flask, Flask-SocketIO, Flask-CORS

**Important Functions**:
- `create_topology()` - Creates Mininet network
- `get_topology_data()` - Fetches and formats topology from Ryu
- `stats_monitoring_loop()` - Background thread for real-time stats

---

#### config.py (80 lines)
**Centralized configuration**

```python
# Settings:
- Ryu controller ports (6633 for OpenFlow, 8080 for REST)
- Flask server settings (host, port, debug mode)
- Topology constraints (min/max size)
- Monitoring intervals (stats update frequency)
- Feature flags (enable/disable features)
```

**Usage**: Import and use constants everywhere
```python
from config import RYU_BASE_URL, FLASK_PORT
```

---

#### mininet_manager.py (400 lines)
**Mininet topology management**

```python
# Key Methods:
- create(type, size) - Create topology
- _create_star(num_hosts) - Star topology
- _create_linear(num_switches) - Linear topology
- _create_tree(depth) - Tree topology
- _create_mesh(num_switches) - Mesh topology
- stop() - Stop and cleanup network
- pingall() - Test connectivity
```

**Critical**: Handles cleanup properly to avoid zombie processes

---

#### ryu_client.py (300 lines)
**Wrapper for Ryu REST API**

```python
# Key Methods:
- get_switches() - List all switches
- get_links() - List all links
- get_hosts() - List all hosts
- get_flow_stats(dpid) - Get flow table
- get_port_stats(dpid) - Get port statistics
- is_connected() - Check Ryu availability
```

**Error Handling**: Gracefully handles Ryu being offline

---

#### requirements.txt (15 lines)
**Python package dependencies**

```
Flask==2.3.3              # Web framework
flask-socketio==5.3.4     # WebSocket support
flask-cors==4.0.0         # Cross-origin requests
requests==2.31.0          # HTTP client
ryu==4.34                 # SDN controller
eventlet==0.33.3          # Async support
pytest==7.4.2             # Testing framework
```

**Installation**: `pip install -r backend/requirements.txt`

---

### Frontend Directory (`frontend/`)

#### index.html (350 lines)
**Complete single-page application UI**

```html
<!-- Structure: -->
<header>Logo + Status</header>
<aside class="left-panel">Controls + Log</aside>
<main>D3.js Visualization</main>
<aside class="right-panel">Statistics</aside>

<!-- Styling: -->
- Modern gradient backgrounds
- Glass morphism effects
- Responsive grid layout
- Custom scrollbars
```

**External Dependencies**: D3.js v7, Socket.IO Client (from CDN)

---

#### static/js/app.js (300 lines)
**Frontend application logic**

```javascript
// Key Functions:
- createTopology() - Call backend API
- renderTopology(data) - D3.js force-directed graph
- dragStarted/dragged/dragEnded() - Node dragging
- updateStats() - Update statistics panel
- log(message, type) - Activity logging

// WebSocket Handlers:
socket.on('connect') - Connection established
socket.on('topology_update') - Redraw graph
socket.on('stats_update') - Update numbers
```

**D3.js Features**: Force simulation, drag, zoom (future), click events

---

### Ryu Apps Directory (`ryu_apps/`)

#### simple_monitor.py (150 lines)
**Statistics collection application**

```python
# Functionality:
- Requests flow/port stats every 10 seconds
- Logs statistics to console
- Used with main controller apps
```

**Usage**: `ryu-manager ryu_apps/simple_monitor.py`

---

#### learning_switch.py (200 lines)
**Layer 2 learning switch implementation**

```python
# Functionality:
- Learns MAC→port mappings
- Installs bidirectional flows
- Handles broadcasts (flooding)
- OpenFlow 1.3 compatible
```

**Educational**: Demonstrates basic SDN logic

---

### Scripts Directory (`scripts/`)

All scripts are **bash** and **executable** (`chmod +x`).

#### setup.sh (200 lines)
**One-time installation script**

```bash
# Installs:
1. System dependencies (git, python3, pip)
2. Mininet
3. Open vSwitch
4. Python packages from requirements.txt
5. Makes all scripts executable
6. Runs verification checks
```

**Usage**: `./scripts/setup.sh` (run once)

---

#### start_ryu.sh (40 lines)
**Launch Ryu controller**

```bash
# Starts:
- Ryu with OpenFlow on port 6633
- REST API on port 8080
- Required apps: ofctl_rest, rest_topology, simple_switch_13
- Custom app: simple_monitor.py

# Logs to: ryu.log
```

**Usage**: `./scripts/start_ryu.sh` (Terminal 1)

---

#### start_backend.sh (50 lines)
**Launch Flask backend**

```bash
# Checks:
- Ryu is running
- Ports are available

# Starts:
- Flask with sudo (required for Mininet)
- Logs to: backend.log
```

**Usage**: `./scripts/start_backend.sh` (Terminal 2)

---

#### start_frontend.sh (30 lines)
**Open browser**

```bash
# Checks:
- Backend is running
- Health endpoint responds

# Opens:
- Default browser to http://localhost:5000
```

**Usage**: `./scripts/start_frontend.sh` (Terminal 3)

---

#### cleanup.sh (80 lines)
**Stop all and clean up**

```bash
# Kills:
- Flask backend
- Ryu controller
- Mininet processes

# Cleans:
- OVS bridges (sudo mn -c)
- Restarts OVS service

# Verifies:
- No remaining processes
- No zombie switches
```

**Usage**: `./scripts/cleanup.sh` (when done or troubleshooting)

---

#### health_check.sh (150 lines)
**System diagnostics**

```bash
# Checks:
1. Components installed (Mininet, Ryu, OVS)
2. Processes running
3. Ports listening (6633, 8080, 5000)
4. API connectivity
5. OVS state

# Output: Color-coded status report
```

**Usage**: `./scripts/health_check.sh` (before demos)

---

#### test_connection.sh (100 lines)
**Integration test**

```bash
# Tests:
1. Ryu connectivity
2. Flask connectivity
3. Create test topology
4. Run pingall
5. Cleanup

# Output: Pass/fail for each step
```

**Usage**: `./scripts/test_connection.sh` (verify system works)

---

### Documentation Directory (`docs/`)

#### architecture.md (600 lines)
- System design
- Component interactions
- Data flow diagrams
- Technology choices
- Performance considerations

**Audience**: Developers, advanced users

---

#### api_reference.md (500 lines)
- All REST endpoints
- WebSocket events
- Request/response formats
- Code examples
- Ryu API documentation

**Audience**: API consumers, developers

---

#### troubleshooting.md (800 lines)
- Common issues and solutions
- Diagnostic commands
- Log interpretation
- Step-by-step debugging
- Prevention tips

**Audience**: All users (essential reading)

---

#### testing_guide.md (700 lines)
- Unit test instructions
- Integration test procedures
- Pre-demo checklist
- Acceptance criteria
- Test report templates

**Audience**: QA, pre-demo preparation

---

#### concepts.md (600 lines)
- SDN fundamentals
- OpenFlow explained
- Flow tables
- Topology types
- Learning resources

**Audience**: Students, beginners

---

### Tests Directory (`tests/`)

#### test_mininet.py (150 lines)
**Unit tests for Mininet Manager**

```python
# Tests:
- Initialization
- Input validation
- Topology creation (requires sudo)
- Cleanup
```

**Run**: `python3 -m pytest tests/test_mininet.py`

---

#### test_api.py (200 lines)
**Integration tests for Flask API**

```python
# Tests:
- Health endpoint
- Topology CRUD operations
- Pingall functionality
- Ryu API (direct)
```

**Requires**: Ryu running on localhost:8080

**Run**: `python3 -m pytest tests/test_api.py`

---

## Key Concepts

### Separation of Concerns

```
Frontend (UI)
    ↓ REST/WebSocket
Backend (Orchestration)
    ↓ Python API
Mininet (Network)
    ↓ OpenFlow
Ryu (Control)
```

Each layer is independent and testable.

---

### Configuration Hierarchy

```
1. config.py (defaults)
2. Environment variables (overrides)
3. Command-line arguments (future)
```

---

### Error Handling Strategy

```
Try/Catch → Log error → Return error JSON → Show in UI
```

All errors are logged and displayed to user.

---

## Development Workflow

1. **Edit code**: Modify Python/JavaScript files
2. **Restart service**: Kill and rerun affected component
3. **Test**: Use `test_connection.sh` or manual testing
4. **Check logs**: `tail -f backend.log ryu.log`
5. **Cleanup**: `./scripts/cleanup.sh` if things break

---

## Deployment Notes

**Development Mode** (current):
- Flask debug=True
- No authentication
- CORS allows all origins
- Logs to console

**Production Mode** (future):
- Use Gunicorn + Nginx
- Add authentication
- Restrict CORS
- Log to files with rotation
- Use HTTPS/WSS
- Run as non-root (use setcap)

---

## File Size Summary

| Component | Lines of Code | Percentage |
|-----------|--------------|------------|
| Backend Python | ~1,200 | 30% |
| Frontend JS/HTML | ~650 | 16% |
| Ryu Apps | ~350 | 9% |
| Scripts | ~650 | 16% |
| Documentation | ~3,200 | 80% |
| Tests | ~350 | 9% |
| **Total** | **~6,400** | **100%** |

*Note: Documentation is 50% of the project - essential for learning!*

---

## Important Files for Different Roles

### Students Learning SDN
1. `docs/concepts.md` - Start here!
2. `ryu_apps/learning_switch.py` - See SDN logic
3. `backend/mininet_manager.py` - See topology creation
4. `docs/architecture.md` - Understand the system

### Developers Extending Project
1. `backend/config.py` - Add settings
2. `backend/app.py` - Add API endpoints
3. `frontend/static/js/app.js` - Add UI features
4. `ryu_apps/` - Add custom Ryu apps

### Administrators/Demo Preparation
1. `scripts/health_check.sh` - Pre-demo check
2. `docs/troubleshooting.md` - When things break
3. `scripts/cleanup.sh` - Clean slate
4. `docs/testing_guide.md` - Test checklist

### Report Writers
1. `docs/architecture.md` - System design
2. `docs/concepts.md` - SDN theory
3. `README.md` - Project overview
4. Screenshots from running application

---

## Getting Started Path

```
1. Read README.md (5 min)
2. Run setup.sh (10 min)
3. Follow QUICKSTART.md (5 min)
4. Read concepts.md (15 min)
5. Experiment with different topologies (30 min)
6. Deep dive into docs/ (2 hours)
7. Modify code and extend (∞ hours)
```

Total to working demo: **20 minutes**
Total to understand: **2-3 hours**

---

## Common Navigation

**Want to...**

- **Install**: `./scripts/setup.sh`
- **Run**: See `QUICKSTART.md`
- **Learn**: Read `docs/concepts.md`
- **Debug**: Check `docs/troubleshooting.md`
- **Test**: Run `./scripts/test_connection.sh`
- **Extend**: Read `docs/architecture.md` + `docs/api_reference.md`
- **Demo**: Follow `docs/testing_guide.md` → "Pre-Demo Checklist"

---

## Maintenance

### Regular Updates
- Update `requirements.txt` when adding dependencies
- Update `docs/` when changing APIs
- Update `tests/` when adding features
- Update `.gitignore` for new file types

### Log Management
```bash
# Logs grow over time, rotate them
mv backend.log backend.log.old
mv ryu.log ryu.log.old
```

### Cleanup Schedule
- After each demo: `./scripts/cleanup.sh`
- Weekly: `sudo apt-get update && sudo apt-get upgrade`
- Monthly: Review and archive logs

---

## Questions?

- Check `README.md` first
- Then `docs/troubleshooting.md`
- Then `docs/` folder
- Still stuck? Check logs: `backend.log`, `ryu.log`
