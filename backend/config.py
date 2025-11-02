"""
Configuration file for SDN Visualizer
Centralized settings for all components
"""

# Ryu Controller Settings
RYU_HOST = 'localhost'
RYU_REST_PORT = 8080
OPENFLOW_PORT = 6633

# Ryu REST API Base URL
RYU_BASE_URL = f'http://{RYU_HOST}:{RYU_REST_PORT}'

# Flask Server Settings
FLASK_HOST = '0.0.0.0'  # Listen on all interfaces
FLASK_PORT = 5000
FLASK_DEBUG = True

# WebSocket Settings
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"  # Allow all origins (development only)
SOCKETIO_ASYNC_MODE = 'threading'

# Topology Settings
DEFAULT_TOPOLOGY = 'star'
DEFAULT_SIZE = 4
MIN_SIZE = 2
MAX_SIZE = 20

# Supported topology types
TOPOLOGY_TYPES = ['star', 'linear', 'tree', 'mesh']

# Monitoring Settings
STATS_UPDATE_INTERVAL = 2  # seconds
CONNECTION_TIMEOUT = 5  # seconds for API calls

# Mininet Settings
MININET_CLEANUP_TIMEOUT = 5  # seconds to wait for cleanup
SWITCH_CONNECTION_WAIT = 3  # seconds to wait for switches to connect to Ryu

# OpenFlow Settings
OPENFLOW_VERSION = 'OpenFlow13'  # OpenFlow 1.3

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '[%(asctime)s] %(levelname)s - %(message)s'

# Paths
RYU_APPS_DIR = '../ryu_apps'

# Security (for production, set these properly)
SECRET_KEY = 'dev-secret-key-change-in-production'  # Flask secret key

# Feature Flags
ENABLE_FLOW_STATS = True
ENABLE_PORT_STATS = True
ENABLE_PACKET_CAPTURE = False  # Future feature
ENABLE_CUSTOM_TOPOLOGIES = False  # Future feature
