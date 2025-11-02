/**
 * SDN Visualizer - Frontend Application
 * Handles D3.js visualization, WebSocket communication, and UI interactions
 */

const API_URL = window.location.origin;
const socket = io(API_URL);

// UI Elements
const loading = document.getElementById('loading');
const statusElement = document.getElementById('status');
const statusText = document.getElementById('status-text');
const activityLog = document.getElementById('activity-log');

const createBtn = document.getElementById('create-btn');
const stopBtn = document.getElementById('stop-btn');
const pingallBtn = document.getElementById('pingall-btn');

const topoType = document.getElementById('topo-type');
const topoSize = document.getElementById('topo-size');

// Stats elements
const statSwitches = document.getElementById('stat-switches');
const statHosts = document.getElementById('stat-hosts');
const statLinks = document.getElementById('stat-links');
const statPackets = document.getElementById('stat-packets');

// D3 Setup
const svg = d3.select('#topology-graph');
const width = window.innerWidth * 0.5;
const height = window.innerHeight - 60;

svg.attr('width', width).attr('height', height);

// Simulation
let simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(30));

let linkGroup = svg.append('g').attr('class', 'links');
let nodeGroup = svg.append('g').attr('class', 'nodes');

// State
let currentTopology = { nodes: [], edges: [] };

// ============== LOGGING ==============

function log(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    activityLog.insertBefore(entry, activityLog.firstChild);
    
    // Keep only last 50 entries
    while (activityLog.children.length > 50) {
        activityLog.removeChild(activityLog.lastChild);
    }
}

// ============== API CALLS ==============

async function createTopology() {
    const type = topoType.value;
    const size = parseInt(topoSize.value);
    
    if (size < 2 || size > 20) {
        log('❌ Size must be between 2 and 20', 'error');
        return;
    }
    
    loading.classList.add('active');
    log(`Creating ${type} topology with size ${size}...`, 'info');
    
    try {
        const response = await fetch(`${API_URL}/api/topology/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, size })
        });
        
        const data = await response.json();
        
        if (data.success) {
            log(`✅ ${data.message}`, 'success');
        } else {
            log(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
    } finally {
        loading.classList.remove('active');
    }
}

async function stopTopology() {
    loading.classList.add('active');
    log('Stopping topology...', 'info');
    
    try {
        const response = await fetch(`${API_URL}/api/topology/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            log('✅ Topology stopped', 'success');
            renderTopology({ nodes: [], edges: [] });
            updateStats(0, 0, 0, 0);
        } else {
            log(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
    } finally {
        loading.classList.remove('active');
    }
}

async function runPingAll() {
    log('Running pingall test...', 'info');
    
    try {
        const response = await fetch(`${API_URL}/api/topology/pingall`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const loss = data.packet_loss;
            if (loss === 0) {
                log(`✅ Pingall: 0% packet loss - all hosts reachable!`, 'success');
            } else if (loss < 50) {
                log(`⚠️ Pingall: ${loss}% packet loss`, 'error');
            } else {
                log(`❌ Pingall: ${loss}% packet loss - network issues!`, 'error');
            }
        } else {
            log(`❌ ${data.error}`, 'error');
        }
    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
    }
}

// ============== VISUALIZATION ==============

function renderTopology(data) {
    currentTopology = data;
    const { nodes, edges, topology_type } = data;
    
    // Update stats
    updateStats(
        data.switch_count || nodes.filter(n => n.type === 'switch').length,
        data.host_count || nodes.filter(n => n.type === 'host').length,
        data.link_count || edges.length,
        null // Keep current packet count
    );
    
    // Apply topology-specific positioning
    if (topology_type === 'linear') {
        positionLinearTopology(nodes, edges);
    } else if (topology_type === 'star') {
        positionStarTopology(nodes, edges);
    }
    
    // Update links
    const link = linkGroup.selectAll('line')
        .data(edges, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    
    link.exit().remove();
    
    const linkEnter = link.enter()
        .append('line')
        .attr('class', 'link');
    
    // Update nodes
    const node = nodeGroup.selectAll('g')
        .data(nodes, d => d.id);
    
    node.exit().remove();
    
    const nodeEnter = node.enter()
        .append('g')
        .attr('class', d => `node ${d.type}`)
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded))
        .on('click', nodeClicked);
    
    nodeEnter.append('circle')
        .attr('r', 20);
    
    nodeEnter.append('text')
        .attr('dy', 35)
        .text(d => d.name || d.id);
    
    // Update simulation
    simulation.nodes(nodes);
    simulation.force('link').links(edges);
    
    // For linear/star, use weaker forces to maintain custom positioning
    if (topology_type === 'linear' || topology_type === 'star') {
        simulation
            .force('charge', d3.forceManyBody().strength(-100))
            .force('link', d3.forceLink().id(d => d.id).distance(120).strength(0.5));
    } else {
        // Default force-directed layout for other topologies
        simulation
            .force('charge', d3.forceManyBody().strength(-400))
            .force('link', d3.forceLink().id(d => d.id).distance(150));
    }
    
    simulation.alpha(1).restart();
    
    simulation.on('tick', () => {
        linkGroup.selectAll('line')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        nodeGroup.selectAll('g')
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function positionLinearTopology(nodes, edges) {
    // Sort switches by name (s1, s2, s3, ...)
    const switches = nodes.filter(n => n.type === 'switch')
        .sort((a, b) => {
            const numA = parseInt(a.id.substring(1));
            const numB = parseInt(b.id.substring(1));
            return numA - numB;
        });
    
    const hosts = nodes.filter(n => n.type === 'host');
    
    // Calculate positions for linear chain
    const spacing = Math.min(200, (width - 100) / (switches.length + 1));
    const centerY = height / 2;
    const startX = (width - (spacing * (switches.length - 1))) / 2;
    
    // Position switches in a horizontal line
    switches.forEach((sw, i) => {
        sw.x = startX + (i * spacing);
        sw.y = centerY;
        sw.fx = sw.x; // Fix position
        sw.fy = sw.y;
    });
    
    // Position hosts below their corresponding switches
    hosts.forEach(host => {
        const hostNum = parseInt(host.id.substring(1));
        const sw = switches.find(s => parseInt(s.id.substring(1)) === hostNum);
        if (sw) {
            host.x = sw.x;
            host.y = sw.y + 100; // Below switch
            host.fx = host.x;
            host.fy = host.y;
        }
    });
}

function positionStarTopology(nodes, edges) {
    const switches = nodes.filter(n => n.type === 'switch');
    const hosts = nodes.filter(n => n.type === 'host');
    
    // Central switch at center
    if (switches.length > 0) {
        const centralSwitch = switches[0];
        centralSwitch.x = width / 2;
        centralSwitch.y = height / 2;
        centralSwitch.fx = centralSwitch.x;
        centralSwitch.fy = centralSwitch.y;
        
        // Arrange hosts in a circle around the switch
        const radius = Math.min(200, Math.min(width, height) / 3);
        const angleStep = (2 * Math.PI) / hosts.length;
        
        hosts.forEach((host, i) => {
            const angle = i * angleStep;
            host.x = centralSwitch.x + radius * Math.cos(angle);
            host.y = centralSwitch.y + radius * Math.sin(angle);
            host.fx = host.x;
            host.fy = host.y;
        });
    }
}

function updateStats(switches, hosts, links, packets) {
    if (switches !== null) statSwitches.textContent = switches;
    if (hosts !== null) statHosts.textContent = hosts;
    if (links !== null) statLinks.textContent = links;
    if (packets !== null) statPackets.textContent = packets.toLocaleString();
}

// ============== D3 DRAG HANDLERS ==============

function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function nodeClicked(event, d) {
    log(`Clicked: ${d.name || d.id} (${d.type})`, 'info');
    
    // If it's a switch, we could fetch flow table (future feature)
    if (d.type === 'switch') {
        log(`Switch ${d.name} - DPID: ${d.dpid}`, 'info');
    } else if (d.type === 'host') {
        log(`Host ${d.name} - MAC: ${d.mac}, IP: ${d.ip}`, 'info');
    }
}

// ============== WEBSOCKET EVENTS ==============

socket.on('connect', () => {
    statusElement.classList.remove('disconnected');
    statusText.textContent = 'Connected';
    log('✅ Connected to server', 'success');
});

socket.on('disconnect', () => {
    statusElement.classList.add('disconnected');
    statusText.textContent = 'Disconnected';
    log('❌ Disconnected from server', 'error');
});

socket.on('connection_status', (data) => {
    log(`Server: ${data.message}`, 'info');
});

socket.on('topology_update', (data) => {
    log('📡 Topology updated', 'info');
    renderTopology(data);
});

socket.on('stats_update', (stats) => {
    const totalPackets = stats.total_packets || 0;
    updateStats(null, null, null, totalPackets);
});

socket.on('error', (data) => {
    log(`❌ Server error: ${data.message}`, 'error');
});

// ============== EVENT LISTENERS ==============

createBtn.addEventListener('click', createTopology);
stopBtn.addEventListener('click', stopTopology);
pingallBtn.addEventListener('click', runPingAll);

// Allow Enter key in size input
topoSize.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createTopology();
    }
});

// ============== INITIALIZATION ==============

window.addEventListener('load', () => {
    log('Frontend initialized', 'success');
    
    // Request current topology if any
    socket.emit('request_topology');
});

// Handle window resize
window.addEventListener('resize', () => {
    const newWidth = window.innerWidth * 0.5;
    const newHeight = window.innerHeight - 60;
    
    svg.attr('width', newWidth).attr('height', newHeight);
    simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
    simulation.alpha(0.3).restart();
});
