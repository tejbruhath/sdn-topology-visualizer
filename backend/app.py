"""
SDN Visualizer - Main Flask Application
Provides REST API and WebSocket endpoints for network visualization
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from mininet_manager import MininetManager
from ryu_client import RyuClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app)

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS,
    async_mode=config.SOCKETIO_ASYNC_MODE
)

# Global instances
mininet_manager = MininetManager()
ryu_client = RyuClient()

# Stats monitoring thread control
stats_thread = None
stats_running = False


# ============== HELPER FUNCTIONS ==============

def get_topology_data():
    """
    Fetch current topology from Ryu and format for D3.js
    
    Returns:
        Dictionary with nodes and edges arrays
    """
    try:
        switches = ryu_client.get_switches()
        links = ryu_client.get_links()
        hosts = ryu_client.get_hosts()
        
        nodes = []
        edges = []
        
        # Add switch nodes
        for switch in switches:
            nodes.append({
                "id": f"s{switch['dpid_int']}",
                "name": f"s{switch['dpid_int']}",
                "type": "switch",
                "dpid": switch['dpid']
            })
        
        # Add host nodes (deduplicate by MAC)
        seen_macs = set()
        for host in hosts:
            mac = host['mac']
            
            # Skip duplicate MACs
            if mac in seen_macs:
                continue
            seen_macs.add(mac)
            
            # Find which switch the host is connected to
            port_info = host.get('port', {})
            switch_dpid = port_info.get('dpid', '')
            
            # Get host IP or use MAC-based name
            ip_list = host.get('ipv4', [])
            ip_addr = ip_list[0] if ip_list else None
            host_name = ip_addr if ip_addr else mac[-8:]  # Last 8 chars of MAC
            
            nodes.append({
                "id": mac,
                "name": host_name,
                "type": "host",
                "mac": mac,
                "ip": ip_addr if ip_addr else 'Unknown',
                "connected_to": f"s{int(switch_dpid, 16)}" if switch_dpid else None
            })
            
            # Add link from host to switch
            if switch_dpid:
                edges.append({
                    "source": mac,
                    "target": f"s{int(switch_dpid, 16)}",
                    "type": "host-switch"
                })
        
        # Add switch-to-switch links (deduplicate bidirectional links)
        seen_links = set()
        for link in links:
            src_dpid = int(link['src']['dpid'], 16)
            dst_dpid = int(link['dst']['dpid'], 16)
            
            # Create a canonical link ID (smaller dpid first)
            link_id = tuple(sorted([src_dpid, dst_dpid]))
            
            # Skip if we've already added this link
            if link_id in seen_links:
                continue
            seen_links.add(link_id)
            
            edges.append({
                "source": f"s{src_dpid}",
                "target": f"s{dst_dpid}",
                "src_port": link['src']['port_no'],
                "dst_port": link['dst']['port_no'],
                "type": "switch-switch"
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "switch_count": len(switches),
            "host_count": len(hosts),
            "link_count": len(edges),
            "topology_type": mininet_manager.topology_type
        }
        
    except Exception as e:
        logger.error(f"Error fetching topology data: {e}")
        return {
            "nodes": [],
            "edges": [],
            "switch_count": 0,
            "host_count": 0,
            "link_count": 0,
            "topology_type": None,
            "error": str(e)
        }


def start_stats_monitoring():
    """Start the statistics monitoring thread"""
    global stats_thread, stats_running
    
    if not stats_running:
        stats_running = True
        stats_thread = threading.Thread(target=stats_monitoring_loop, daemon=True)
        stats_thread.start()
        logger.info("Started stats monitoring thread")


def stop_stats_monitoring():
    """Stop the statistics monitoring thread"""
    global stats_running
    stats_running = False
    logger.info("Stopped stats monitoring thread")


def stats_monitoring_loop():
    """Background thread that polls Ryu for statistics"""
    global stats_running
    
    while stats_running:
        try:
            # Get port statistics from all switches
            port_stats = ryu_client.get_port_stats()
            
            # Calculate total packet counts
            total_packets = 0
            total_bytes = 0
            
            for switch_dpid, ports in port_stats.items():
                for port in ports:
                    total_packets += port.get('rx_packets', 0) + port.get('tx_packets', 0)
                    total_bytes += port.get('rx_bytes', 0) + port.get('tx_bytes', 0)
            
            # Emit stats update to all connected clients
            stats_data = {
                "total_packets": total_packets,
                "total_bytes": total_bytes,
                "port_stats": port_stats,
                "timestamp": time.time()
            }
            
            socketio.emit('stats_update', stats_data, broadcast=True)
            
        except Exception as e:
            logger.error(f"Error in stats monitoring: {e}")
        
        # Wait before next update
        time.sleep(config.STATS_UPDATE_INTERVAL)


# ============== REST API ENDPOINTS ==============

@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/health')
def health_check():
    """Health check endpoint"""
    ryu_connected = ryu_client.is_connected()
    network_active = mininet_manager.net is not None
    
    return jsonify({
        "status": "healthy",
        "ryu_connected": ryu_connected,
        "network_active": network_active,
        "version": "1.0.0"
    })


@app.route('/api/topology/create', methods=['POST'])
def create_topology():
    """
    Create a new Mininet topology
    
    Request Body:
        {
            "type": "star|linear|tree|mesh",
            "size": <number>
        }
    
    Returns:
        Success/error status and topology info
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        topology_type = data.get('type', config.DEFAULT_TOPOLOGY)
        size = data.get('size', config.DEFAULT_SIZE)
        
        # Validate inputs
        if topology_type not in config.TOPOLOGY_TYPES:
            return jsonify({
                "success": False,
                "error": f"Invalid topology type. Must be one of: {', '.join(config.TOPOLOGY_TYPES)}"
            }), 400
        
        try:
            size = int(size)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Size must be a number"}), 400
        
        if size < config.MIN_SIZE or size > config.MAX_SIZE:
            return jsonify({
                "success": False,
                "error": f"Size must be between {config.MIN_SIZE} and {config.MAX_SIZE}"
            }), 400
        
        # Stop any existing topology
        mininet_manager.stop()
        time.sleep(1)
        
        # Create new topology
        logger.info(f"Creating {topology_type} topology with size {size}")
        result = mininet_manager.create(topology_type, size)
        
        # Wait for switches to connect to Ryu
        logger.info("Waiting for switches to connect to Ryu...")
        time.sleep(config.SWITCH_CONNECTION_WAIT)
        
        # Verify switches are connected
        switches = ryu_client.get_switches()
        if not switches:
            logger.warning("No switches connected to Ryu yet")
        
        # Start stats monitoring
        start_stats_monitoring()
        
        # Get topology data and send to frontend
        topology_data = get_topology_data()
        socketio.emit('topology_update', topology_data, broadcast=True)
        
        logger.info(f"Successfully created {topology_type} topology")
        
        return jsonify({
            "success": True,
            "message": f"Created {topology_type} topology with {size} nodes",
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error creating topology: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/topology/stop', methods=['POST'])
def stop_topology():
    """Stop the current Mininet topology"""
    try:
        stop_stats_monitoring()
        result = mininet_manager.stop()
        
        # Notify frontend
        socketio.emit('topology_update', {"nodes": [], "edges": [], "topology_type": None}, broadcast=True)
        
        logger.info("Topology stopped")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error stopping topology: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/topology/data', methods=['GET'])
def get_topology():
    """Get current topology structure"""
    try:
        data = get_topology_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting topology data: {e}")
        return jsonify({
            "error": str(e),
            "nodes": [],
            "edges": []
        }), 500


@app.route('/api/topology/pingall', methods=['POST'])
def run_pingall():
    """Run pingall connectivity test"""
    try:
        result = mininet_manager.pingall()
        logger.info(f"Pingall result: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running pingall: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/topology/ping', methods=['POST'])
def run_ping():
    """
    Ping between two hosts
    
    Request Body:
        {
            "src": "h1",
            "dst": "h2"
        }
    """
    try:
        data = request.get_json()
        src = data.get('src')
        dst = data.get('dst')
        
        if not src or not dst:
            return jsonify({
                "success": False,
                "error": "Both 'src' and 'dst' are required"
            }), 400
        
        result = mininet_manager.ping(src, dst)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error running ping: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats/flows/<dpid>', methods=['GET'])
def get_flows(dpid):
    """Get flow table for a specific switch"""
    try:
        flows = ryu_client.get_flow_stats(dpid)
        return jsonify({
            "success": True,
            "dpid": dpid,
            "flows": flows
        })
    except Exception as e:
        logger.error(f"Error getting flows for {dpid}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats/ports/<dpid>', methods=['GET'])
def get_ports(dpid):
    """Get port statistics for a specific switch"""
    try:
        ports = ryu_client.get_port_stats(dpid)
        return jsonify({
            "success": True,
            "dpid": dpid,
            "ports": ports
        })
    except Exception as e:
        logger.error(f"Error getting ports for {dpid}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/controller/info', methods=['GET'])
def get_controller_info():
    """Get Ryu controller information"""
    try:
        info = ryu_client.get_controller_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting controller info: {e}")
        return jsonify({
            "connected": False,
            "error": str(e)
        }), 500


# ============== WEBSOCKET EVENTS ==============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connection_status', {'status': 'connected', 'message': 'Connected to SDN Visualizer'})
    
    # Send current topology if available
    if mininet_manager.net is not None:
        topology_data = get_topology_data()
        emit('topology_update', topology_data)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")


@socketio.on('request_topology')
def handle_topology_request():
    """Handle explicit topology data request"""
    try:
        topology_data = get_topology_data()
        emit('topology_update', topology_data)
    except Exception as e:
        logger.error(f"Error sending topology: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_stats')
def handle_stats_request():
    """Handle explicit stats request"""
    try:
        port_stats = ryu_client.get_port_stats()
        emit('stats_update', {'port_stats': port_stats})
    except Exception as e:
        logger.error(f"Error sending stats: {e}")
        emit('error', {'message': str(e)})


# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ============== MAIN ==============

if __name__ == '__main__':
    # Check if Ryu is running
    if not ryu_client.is_connected():
        logger.error("=" * 70)
        logger.error("ERROR: Cannot connect to Ryu controller!")
        logger.error(f"Make sure Ryu is running on {config.RYU_BASE_URL}")
        logger.error("Start Ryu with: ./scripts/start_ryu.sh")
        logger.error("=" * 70)
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info("SDN Visualizer Backend Starting...")
    logger.info(f"Ryu Controller: {config.RYU_BASE_URL}")
    logger.info(f"Flask Server: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    logger.info("=" * 70)
    
    # Run Flask with SocketIO
    socketio.run(
        app,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        allow_unsafe_werkzeug=True  # For development only
    )
