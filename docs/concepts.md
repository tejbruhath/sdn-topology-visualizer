# SDN Concepts - Visual Guide

A beginner-friendly explanation of key Software-Defined Networking concepts used in this visualizer.

## Table of Contents

1. [What is SDN?](#what-is-sdn)
2. [Data Plane vs Control Plane](#data-plane-vs-control-plane)
3. [OpenFlow Protocol](#openflow-protocol)
4. [Flow Tables](#flow-tables)
5. [Topology Types](#topology-types)
6. [Ryu Controller](#ryu-controller)
7. [Mininet Emulation](#mininet-emulation)

---

## What is SDN?

**Software-Defined Networking** separates the network control logic (brain) from the forwarding hardware (muscle).

### Traditional Networks

```
┌─────────────────┐
│   Router/Switch │
│  ┌───────────┐  │
│  │  Control  │  │  ← Brain (routing logic)
│  │   Plane   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │   Data    │  │  ← Muscle (packet forwarding)
│  │   Plane   │  │
│  └───────────┘  │
└─────────────────┘
Problem: Tightly coupled, hard to change
```

### SDN Architecture

```
┌──────────────────────┐
│  SDN Controller      │
│  (Centralized Brain) │ ← All routing logic here
└──────────┬───────────┘
           │ OpenFlow
    ┌──────┴──────┐
    │             │
┌───▼───┐    ┌───▼───┐
│Switch │    │Switch │  ← Simple forwarding only
└───────┘    └───────┘
Advantage: Easy to program, centralized view
```

---

## Data Plane vs Control Plane

### Data Plane (Forwarding Layer)

**What**: The actual packet forwarding hardware

**Components**: 
- Open vSwitch (OVS) switches in Mininet
- Physical switches in real networks

**Job**:
1. Receive packet
2. Check flow table for matching rule
3. Execute action (forward, drop, send to controller)

**Analogy**: Like a mail sorting machine - fast but dumb, just follows rules

```
Packet arrives → Check table → Forward to port 2
                             ↓
                    No match? → Send to controller
```

---

### Control Plane (Decision Layer)

**What**: The intelligence that decides routing

**Components**:
- Ryu Controller
- Application logic you write

**Job**:
1. Discover network topology
2. Calculate best paths
3. Install forwarding rules in switches
4. Handle errors and failures

**Analogy**: Like a traffic control center - smart but slower, makes decisions

```
New host appears → Learn MAC address
                 → Calculate path
                 → Install flow rules in switches
                 → Future packets handled by data plane
```

---

### Why Separate Them?

| Aspect | Traditional | SDN |
|--------|------------|-----|
| **Flexibility** | Hard to change | Easy to reprogram |
| **View** | Each device isolated | Global network view |
| **Updates** | Manual config on each device | Centralized update |
| **Innovation** | Vendor-dependent | Open programmability |

---

## OpenFlow Protocol

**OpenFlow** is the language switches use to talk to the SDN controller.

### Communication Flow

```
1. HELLO
   Switch: "I'm alive, I speak OpenFlow 1.3"
   Controller: "Great, I speak 1.3 too"

2. FEATURES_REQUEST
   Controller: "Tell me about yourself"
   
3. FEATURES_REPLY
   Switch: "I'm switch #1, I have 4 ports"

4. FLOW_MOD (Flow Modification)
   Controller: "Install this rule: if dst=h2, forward to port 2"
   
5. PACKET_IN
   Switch: "I got a packet for unknown destination, help!"
   
6. PACKET_OUT
   Controller: "Forward it to port 3, and I've installed a rule for next time"
```

### Key Messages

| Message | Direction | Purpose |
|---------|-----------|---------|
| HELLO | Both | Initial handshake |
| FEATURES_REQUEST | Controller → Switch | Query capabilities |
| FEATURES_REPLY | Switch → Controller | Report capabilities |
| PACKET_IN | Switch → Controller | Unknown packet |
| PACKET_OUT | Controller → Switch | Send specific packet |
| FLOW_MOD | Controller → Switch | Install/delete flow rule |
| STATS_REQUEST | Controller → Switch | Query statistics |
| STATS_REPLY | Switch → Controller | Report statistics |

### Example: First Ping

```
h1 pings h2 for the first time:

1. h1 sends ARP request (who has 10.0.0.2?)
2. Switch s1 has no rule for this → PACKET_IN to Ryu
3. Ryu sees it's a broadcast → tells s1 to flood
4. h2 receives ARP, replies with MAC address
5. s1 → PACKET_IN with h2's reply
6. Ryu learns: h1 on port 1, h2 on port 2
7. Ryu → FLOW_MOD: "if dst=h1, forward to port 1"
8. Ryu → FLOW_MOD: "if dst=h2, forward to port 2"
9. h1 sends ICMP ping
10. s1 finds rule in table → forwards directly (no controller)
11. Future pings handled by switch (fast path)
```

---

## Flow Tables

A **flow table** is like a forwarding instruction manual for switches.

### Structure

```
Priority | Match Condition         | Action
---------|------------------------|------------------
1000     | dst_mac=00:00:00:00:02 | OUTPUT:port_2
1000     | dst_mac=00:00:00:00:01 | OUTPUT:port_1
500      | in_port=1              | OUTPUT:port_2
0        | (any packet)           | CONTROLLER
```

### How Matching Works

```
Packet arrives with dst_mac=00:00:00:00:02

1. Check highest priority (1000)
   ✓ MATCH! → OUTPUT:port_2

2. Stop checking, forward packet

If no match found at any priority:
→ Use default rule (priority 0)
→ Send to controller
```

### Match Fields

Switches can match on many fields:

| Layer | Field | Example |
|-------|-------|---------|
| L2 (Ethernet) | src_mac | 00:00:00:00:00:01 |
| L2 | dst_mac | 00:00:00:00:00:02 |
| L2 | eth_type | 0x0800 (IPv4) |
| L3 (IP) | src_ip | 10.0.0.1 |
| L3 | dst_ip | 10.0.0.2 |
| L4 (TCP) | src_port | 80 |
| L4 | dst_port | 443 |

### Actions

| Action | Effect |
|--------|--------|
| OUTPUT:port | Forward to specific port |
| OUTPUT:CONTROLLER | Send to controller |
| OUTPUT:FLOOD | Send to all ports except input |
| DROP | Discard packet |
| SET_FIELD | Modify packet header |

---

## Topology Types

### Star Topology

```
       h1
        |
    h2--s1--h3
        |
       h4
```

**Characteristics**:
- Single central switch
- All hosts connected to center
- Simple, but single point of failure

**Use Cases**:
- Small networks
- Testing basic connectivity
- Demonstrating controller basics

---

### Linear Topology

```
h1--s1--s2--s3--s4--h4
    |   |   |   |
    h1  h2  h3  h4
```

**Characteristics**:
- Chain of switches
- Each switch has one host
- Multi-hop paths

**Use Cases**:
- Testing path calculation
- Demonstrating flow installation across multiple switches
- Latency experiments

---

### Tree Topology

```
        s1
       /  \
      s2   s3
     /  \  /  \
    h1 h2 h3 h4
```

**Characteristics**:
- Hierarchical structure
- Binary tree (2 children per node)
- Hosts at leaf nodes

**Use Cases**:
- Data center networks
- Campus networks
- Scalability testing

---

### Mesh Topology

```
h1--s1-----s2--h2
    |  \  / |
    |   \/  |
    |   /\  |
    |  /  \ |
h3--s3-----s4--h4
```

**Characteristics**:
- Every switch connected to every other switch
- Multiple paths between hosts
- High redundancy

**Use Cases**:
- Load balancing
- Fault tolerance testing
- Path diversity experiments

---

## Ryu Controller

**Ryu** is an SDN controller framework written in Python.

### Architecture

```
┌─────────────────────────────────────┐
│         Your Application            │
│   (custom_app.py)                   │
├─────────────────────────────────────┤
│         Ryu Framework               │
│  ┌──────────┐  ┌──────────────┐   │
│  │ OpenFlow │  │  REST APIs   │   │
│  │ Protocol │  │              │   │
│  └────┬─────┘  └──────┬───────┘   │
└───────┼────────────────┼───────────┘
        │                │
        ▼                ▼
    Switches       External Apps
```

### Key Components

#### 1. Event System

```python
@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
def packet_in_handler(self, ev):
    # Handle packet from switch
    pass
```

Events are triggered when:
- Switch connects/disconnects
- Packet arrives at controller
- Flow rule expires
- Port status changes

#### 2. Applications

**simple_switch_13.py**: Basic L2 learning switch
```python
# Learns MAC addresses
# Installs bidirectional flows
# Handles broadcasts
```

**ofctl_rest.py**: REST API for flow management
```
GET /stats/flow/1      # Get flows
POST /stats/flowentry/add   # Add flow
```

**rest_topology.py**: REST API for topology
```
GET /v1.0/topology/switches
GET /v1.0/topology/links
GET /v1.0/topology/hosts
```

---

## Mininet Emulation

**Mininet** creates realistic virtual networks on a single machine.

### How It Works

```
┌─────────────────────────────────────────┐
│          Host Machine (Linux)           │
│                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │Process │  │Process │  │Process │   │
│  │  (h1)  │  │  (h2)  │  │  (h3)  │   │
│  └───┬────┘  └───┬────┘  └───┬────┘   │
│      │           │           │         │
│    ┌─▼───────────▼───────────▼─┐      │
│    │   Open vSwitch (s1)       │      │
│    └───────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

### Components

**Hosts**: Linux processes in network namespaces
```bash
# Each host has its own:
- Network stack
- IP address
- Routing table
- Process space
```

**Switches**: Open vSwitch bridges
```bash
# Each switch has:
- Forwarding table
- OpenFlow connection to controller
- Virtual ports
```

**Links**: Virtual Ethernet pairs (veth)
```bash
# Pairs of virtual interfaces:
h1-eth0 ↔ s1-eth1
```

### Why Mininet?

| Feature | Benefit |
|---------|---------|
| **Fast** | Create 100-node networks in seconds |
| **Cheap** | Runs on laptop, no hardware needed |
| **Realistic** | Real Linux network stack, real protocols |
| **Reproducible** | Same setup every time |
| **Safe** | Isolated from real network |

---

## Putting It All Together

### Complete Workflow

```
1. USER clicks "Create Star Topology"
   ↓
2. FLASK calls Mininet API
   ↓
3. MININET creates:
   - Virtual hosts (h1, h2, h3, h4)
   - Virtual switch (s1)
   - Virtual links (h1-s1, h2-s1, ...)
   ↓
4. OPEN vSWITCH switches start
   ↓
5. SWITCHES connect to RYU (port 6633)
   ↓
6. RYU receives FEATURES_REPLY
   - Stores switch info
   - Installs default "send to controller" rule
   ↓
7. FLASK queries Ryu REST API
   - Gets switches, links, hosts
   ↓
8. D3.JS renders visualization
   - Blue circles = switches
   - Green circles = hosts
   - Lines = links
   ↓
9. USER clicks "Ping All"
   ↓
10. First packet triggers PACKET_IN
   ↓
11. RYU installs flow rules
   ↓
12. Subsequent packets handled by switch (fast)
```

---

## Key Takeaways

1. **SDN separates control and data planes** - Brain and muscle are separate

2. **OpenFlow is the communication protocol** - How controller talks to switches

3. **Flow tables are the forwarding rules** - Instructions for packet handling

4. **Ryu is the SDN controller** - The brain making decisions

5. **Mininet emulates networks** - Virtual lab environment

6. **First packet is slow (controller), rest are fast (switch)** - Learning switch behavior

---

## Further Learning

### Recommended Reading

- **Mininet Walkthrough**: http://mininet.org/walkthrough/
- **Ryu Book**: https://osrg.github.io/ryu-book/en/html/
- **OpenFlow Spec**: https://opennetworking.org/

### Experiments to Try

1. **Modify flow rules**: Make traffic take longer path
2. **Add firewall rules**: Block specific hosts
3. **Implement load balancing**: Split traffic across paths
4. **Create custom topology**: Design your own network
5. **Measure latency**: Compare direct vs multi-hop

### Next Steps

- Read `architecture.md` for implementation details
- Check `api_reference.md` for programming interfaces
- See `troubleshooting.md` when things break
- Follow `testing_guide.md` for verification

---

## Glossary

| Term | Definition |
|------|------------|
| **DPID** | DataPath ID - Unique identifier for switch |
| **Flow** | A rule in the flow table |
| **Match** | Condition that packet must satisfy |
| **Action** | What to do with matched packet |
| **Priority** | Order to check rules (higher first) |
| **Controller** | SDN brain (Ryu) |
| **Switch** | SDN muscle (OVS) |
| **OpenFlow** | Protocol between controller and switch |
| **Namespace** | Isolated network environment in Linux |
| **veth** | Virtual Ethernet pair |
| **OVS** | Open vSwitch - software switch |

---

## Quick Reference Commands

```bash
# Mininet
sudo mn                          # Start default topology
sudo mn --topo=star,3            # Star with 3 hosts
sudo mn --custom topo.py         # Custom topology
sudo mn -c                       # Clean up

# Open vSwitch
sudo ovs-vsctl show              # Show switches/ports
sudo ovs-vsctl list-br           # List bridges
sudo ovs-ofctl dump-flows s1     # Show flow table

# Ryu
ryu-manager app.py               # Start controller
curl localhost:8080/v1.0/topology/switches  # Query via REST

# Testing
mininet> pingall                 # Test connectivity
mininet> net                     # Show topology
mininet> h1 ping h2              # Ping between hosts
```
