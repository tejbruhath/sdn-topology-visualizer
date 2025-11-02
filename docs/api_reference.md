# API Reference

Complete reference for all REST endpoints and WebSocket events in the SDN Visualizer.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, no authentication is required (development mode).

---

## REST API Endpoints

### Health Check

**GET** `/health`

Check if the backend is running and healthy.

**Response**:
```json
{
  "status": "healthy",
  "ryu_connected": true,
  "network_active": false,
  "version": "1.0.0"
}
```

---

### Create Topology

**POST** `/api/topology/create`

Create a new Mininet network topology.

**Request Body**:
```json
{
  "type": "star",  // "star", "linear", "tree", or "mesh"
  "size": 4        // Number of hosts/switches (2-20)
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Created star topology with 4 nodes",
  "data": {
    "success": true,
    "topology_type": "star",
    "size": 4,
    "switches": 1,
    "hosts": 4,
    "links": 4
  }
}
```

**Response (Error)**:
```json
{
  "success": false,
  "error": "Size must be between 2 and 20"
}
```

**Status Codes**:
- 200: Success
- 400: Invalid input
- 500: Server error

---

### Stop Topology

**POST** `/api/topology/stop`

Stop the current Mininet network and clean up resources.

**Response**:
```json
{
  "success": true,
  "message": "Network stopped"
}
```

---

### Get Topology Data

**GET** `/api/topology/data`

Retrieve the current network topology structure.

**Response**:
```json
{
  "nodes": [
    {
      "id": "s1",
      "name": "s1",
      "type": "switch",
      "dpid": "0000000000000001"
    },
    {
      "id": "00:00:00:00:00:01",
      "name": "10.0.0.1",
      "type": "host",
      "mac": "00:00:00:00:00:01",
      "ip": "10.0.0.1",
      "connected_to": "s1"
    }
  ],
  "edges": [
    {
      "source": "00:00:00:00:00:01",
      "target": "s1",
      "type": "host-switch"
    }
  ],
  "switch_count": 1,
  "host_count": 1,
  "link_count": 1
}
```

---

### Run Ping All

**POST** `/api/topology/pingall`

Run a connectivity test between all hosts.

**Response**:
```json
{
  "success": true,
  "packet_loss": 0.0,
  "message": "Ping completed with 0.0% packet loss"
}
```

---

### Run Ping Between Hosts

**POST** `/api/topology/ping`

Ping between two specific hosts.

**Request Body**:
```json
{
  "src": "h1",
  "dst": "h2"
}
```

**Response**:
```json
{
  "success": true,
  "packet_loss": 0.0,
  "src": "h1",
  "dst": "h2"
}
```

---

### Get Flow Statistics

**GET** `/api/stats/flows/<dpid>`

Retrieve flow table entries for a switch.

**Parameters**:
- `dpid`: Switch datapath ID (hex string or integer)

**Example Request**:
```
GET /api/stats/flows/1
```

**Response**:
```json
{
  "success": true,
  "dpid": "1",
  "flows": [
    {
      "priority": 1,
      "match": {
        "in_port": 1,
        "eth_dst": "00:00:00:00:00:02"
      },
      "instructions": [
        {
          "type": "APPLY_ACTIONS",
          "actions": [
            {
              "type": "OUTPUT",
              "port": 2
            }
          ]
        }
      ],
      "packet_count": 100,
      "byte_count": 10000,
      "duration_sec": 60
    }
  ]
}
```

---

### Get Port Statistics

**GET** `/api/stats/ports/<dpid>`

Retrieve port statistics for a switch.

**Parameters**:
- `dpid`: Switch datapath ID

**Example Request**:
```
GET /api/stats/ports/1
```

**Response**:
```json
{
  "success": true,
  "dpid": "1",
  "ports": {
    "1": [
      {
        "port_no": 1,
        "rx_packets": 1000,
        "tx_packets": 950,
        "rx_bytes": 100000,
        "tx_bytes": 95000,
        "rx_dropped": 0,
        "tx_dropped": 0,
        "rx_errors": 0,
        "tx_errors": 0,
        "duration_sec": 120
      }
    ]
  }
}
```

---

### Get Controller Info

**GET** `/api/controller/info`

Get information about the Ryu controller.

**Response**:
```json
{
  "connected": true,
  "switch_count": 3,
  "link_count": 2,
  "host_count": 4,
  "base_url": "http://localhost:8080"
}
```

---

## WebSocket Events

### Connection

**Event**: `connect`

Triggered when a client connects to the server.

**Server Response**:
```json
{
  "event": "connection_status",
  "data": {
    "status": "connected",
    "message": "Connected to SDN Visualizer"
  }
}
```

---

### Topology Update

**Event**: `topology_update`

Emitted when the network topology changes.

**Server Broadcast**:
```json
{
  "nodes": [...],
  "edges": [...],
  "switch_count": 3,
  "host_count": 4,
  "link_count": 5
}
```

**Frontend Handling**:
```javascript
socket.on('topology_update', (data) => {
  renderTopology(data);
});
```

---

### Statistics Update

**Event**: `stats_update`

Emitted every 2 seconds with network statistics.

**Server Broadcast**:
```json
{
  "total_packets": 50000,
  "total_bytes": 5000000,
  "port_stats": {
    "1": [
      {
        "port_no": 1,
        "rx_packets": 10000,
        "tx_packets": 10000,
        "rx_bytes": 1000000,
        "tx_bytes": 1000000
      }
    ]
  },
  "timestamp": 1699876543.123
}
```

---

### Request Topology

**Event**: `request_topology`

Client can request current topology data.

**Client Emit**:
```javascript
socket.emit('request_topology');
```

**Server Response**: Emits `topology_update` event

---

### Request Statistics

**Event**: `request_stats`

Client can request current statistics.

**Client Emit**:
```javascript
socket.emit('request_stats');
```

**Server Response**: Emits `stats_update` event

---

### Error

**Event**: `error`

Emitted when an error occurs.

**Server Emit**:
```json
{
  "message": "Failed to connect to Ryu controller"
}
```

---

## Ryu REST API (Direct Access)

The Ryu controller exposes its own REST API on port 8080.

### Base URL

```
http://localhost:8080
```

### Get Switches

**GET** `/v1.0/topology/switches`

**Response**:
```json
[
  {
    "dpid": "0000000000000001",
    "ports": [
      {
        "port_no": 1,
        "hw_addr": "12:34:56:78:9a:bc",
        "name": "s1-eth1"
      }
    ]
  }
]
```

---

### Get Links

**GET** `/v1.0/topology/links`

**Response**:
```json
[
  {
    "src": {
      "dpid": "0000000000000001",
      "port_no": 2,
      "name": "s1-eth2"
    },
    "dst": {
      "dpid": "0000000000000002",
      "port_no": 1,
      "name": "s2-eth1"
    }
  }
]
```

---

### Get Hosts

**GET** `/v1.0/topology/hosts`

**Response**:
```json
[
  {
    "mac": "00:00:00:00:00:01",
    "ipv4": ["10.0.0.1"],
    "port": {
      "dpid": "0000000000000001",
      "port_no": 1,
      "name": "s1-eth1"
    }
  }
]
```

---

### Get Flow Stats

**GET** `/stats/flow/<dpid>`

**Example**: `/stats/flow/1`

**Response**: Returns flow table entries for the switch

---

### Get Port Stats

**GET** `/stats/port/<dpid>`

**Example**: `/stats/port/1`

**Response**: Returns port statistics for the switch

---

### Add Flow Entry

**POST** `/stats/flowentry/add`

Add a flow rule to a switch.

**Request Body**:
```json
{
  "dpid": 1,
  "priority": 100,
  "match": {
    "in_port": 1,
    "eth_dst": "00:00:00:00:00:02"
  },
  "actions": [
    {
      "type": "OUTPUT",
      "port": 2
    }
  ]
}
```

---

### Delete Flow Entry

**POST** `/stats/flowentry/delete`

Remove a flow rule from a switch.

**Request Body**:
```json
{
  "dpid": 1,
  "priority": 100,
  "match": {
    "in_port": 1
  }
}
```

---

## Error Responses

All API endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "success": false,
  "error": "Invalid topology type. Must be one of: star, linear, tree, mesh"
}
```

### 404 Not Found

```json
{
  "error": "Not found"
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Failed to create topology: [error details]"
}
```

---

## Rate Limits

Currently no rate limiting is implemented (development mode).

For production, consider:
- 10 requests/minute for topology creation
- 100 requests/minute for data queries
- Unlimited WebSocket messages

---

## Examples

### Creating a Linear Topology with curl

```bash
curl -X POST http://localhost:5000/api/topology/create \
  -H "Content-Type: application/json" \
  -d '{"type":"linear", "size":5}'
```

### Getting Topology with Python

```python
import requests

response = requests.get('http://localhost:5000/api/topology/data')
data = response.json()

print(f"Switches: {data['switch_count']}")
print(f"Hosts: {data['host_count']}")
```

### WebSocket Client Example

```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected!');
  socket.emit('request_topology');
});

socket.on('topology_update', (data) => {
  console.log('Topology:', data);
});

socket.on('stats_update', (stats) => {
  console.log('Packets:', stats.total_packets);
});
```

---

## Configuration

API behavior can be configured in `backend/config.py`:

```python
# Ports
RYU_REST_PORT = 8080
FLASK_PORT = 5000
OPENFLOW_PORT = 6633

# Limits
MIN_SIZE = 2
MAX_SIZE = 20

# Intervals
STATS_UPDATE_INTERVAL = 2  # seconds
```

---

## Versioning

Current API version: **v1.0**

No versioning in URLs yet. Future versions may use `/api/v2/...`

---

## Support

For API issues:
- Check logs: `backend.log`, `ryu.log`
- Test connectivity: `./scripts/test_connection.sh`
- Health check: `curl http://localhost:5000/health`
