"""
Mininet Network Manager
Handles creation, management, and cleanup of Mininet topologies
"""

import os
import time
import logging
from typing import Dict, Optional, Tuple
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
import config

logger = logging.getLogger(__name__)


class MininetManager:
    """Manager for Mininet network topologies"""
    
    def __init__(self):
        """Initialize Mininet manager"""
        self.net: Optional[Mininet] = None
        self.topology_type: Optional[str] = None
        self.topology_size: int = 0
        
    def _cleanup_existing(self):
        """Clean up any existing Mininet network"""
        if self.net is not None:
            try:
                logger.info("Stopping existing network...")
                self.net.stop()
            except Exception as e:
                logger.error(f"Error stopping network: {e}")
            finally:
                self.net = None
        
        # Nuclear cleanup
        try:
            logger.info("Running Mininet cleanup...")
            os.system('sudo mn -c > /dev/null 2>&1')
            time.sleep(1)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def create(self, topology_type: str, size: int) -> Dict:
        """
        Create a new Mininet topology
        
        Args:
            topology_type: Type of topology ('star', 'linear', 'tree', 'mesh')
            size: Number of hosts/switches
            
        Returns:
            Dictionary with creation status and info
        """
        # Validate inputs
        if topology_type not in config.TOPOLOGY_TYPES:
            raise ValueError(f"Invalid topology type: {topology_type}")
        
        if size < config.MIN_SIZE or size > config.MAX_SIZE:
            raise ValueError(f"Size must be between {config.MIN_SIZE} and {config.MAX_SIZE}")
        
        # Clean up any existing network
        self._cleanup_existing()
        
        # Store topology info
        self.topology_type = topology_type
        self.topology_size = size
        
        # Create topology based on type
        logger.info(f"Creating {topology_type} topology with size {size}")
        
        if topology_type == 'star':
            return self._create_star(size)
        elif topology_type == 'linear':
            return self._create_linear(size)
        elif topology_type == 'tree':
            return self._create_tree(size)
        elif topology_type == 'mesh':
            return self._create_mesh(size)
        else:
            raise ValueError(f"Unsupported topology: {topology_type}")
    
    def _create_star(self, num_hosts: int) -> Dict:
        """
        Create star topology with one central switch
        
        Args:
            num_hosts: Number of hosts to connect
            
        Returns:
            Creation status dictionary
        """
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True
        )
        
        # Add controller
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=config.OPENFLOW_PORT
        )
        
        # Add central switch
        s1 = self.net.addSwitch('s1', protocols=config.OPENFLOW_VERSION)
        
        # Add hosts and connect to central switch
        hosts = []
        for i in range(1, num_hosts + 1):
            h = self.net.addHost(f'h{i}', ip=f'10.0.0.{i}')
            self.net.addLink(h, s1)
            hosts.append(h)
        
        return self._start_network(switches=1, hosts=num_hosts, links=num_hosts)
    
    def _create_linear(self, num_switches: int) -> Dict:
        """
        Create linear topology with switches in a line
        
        Args:
            num_switches: Number of switches to create
            
        Returns:
            Creation status dictionary
        """
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True
        )
        
        # Add controller
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=config.OPENFLOW_PORT
        )
        
        # Create switches and hosts
        switches = []
        hosts = []
        
        for i in range(1, num_switches + 1):
            # Add switch
            s = self.net.addSwitch(f's{i}', protocols=config.OPENFLOW_VERSION)
            switches.append(s)
            
            # Add host connected to this switch
            h = self.net.addHost(f'h{i}', ip=f'10.0.0.{i}')
            self.net.addLink(h, s)
            hosts.append(h)
            
            # Link to previous switch (create chain)
            if i > 1:
                self.net.addLink(switches[i-2], s)
        
        links = num_switches + (num_switches - 1)  # host links + inter-switch links
        return self._start_network(switches=num_switches, hosts=num_switches, links=links)
    
    def _create_tree(self, depth: int) -> Dict:
        """
        Create binary tree topology
        
        Args:
            depth: Depth of tree (2-4 recommended)
            
        Returns:
            Creation status dictionary
        """
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True
        )
        
        # Add controller
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=config.OPENFLOW_PORT
        )
        
        # Build tree structure
        switches = []
        hosts = []
        host_count = 0
        
        # Level 0: Root switch
        s1 = self.net.addSwitch('s1', protocols=config.OPENFLOW_VERSION)
        switches.append(s1)
        
        # Build tree levels
        switch_count = 1
        for level in range(1, min(depth, 3)):  # Limit depth to avoid too many switches
            parent_start = len(switches) - (2 ** (level - 1))
            parent_end = len(switches)
            
            for parent_idx in range(parent_start, parent_end):
                parent = switches[parent_idx]
                
                # Add two child switches
                for child in range(2):
                    switch_count += 1
                    s = self.net.addSwitch(f's{switch_count}', protocols=config.OPENFLOW_VERSION)
                    switches.append(s)
                    self.net.addLink(parent, s)
        
        # Add hosts to leaf switches (last level)
        leaf_start = len(switches) - (2 ** (min(depth, 3) - 1))
        for i, switch in enumerate(switches[leaf_start:], 1):
            host_count += 1
            h = self.net.addHost(f'h{host_count}', ip=f'10.0.0.{host_count}')
            self.net.addLink(h, switch)
            hosts.append(h)
        
        links = len(switches) - 1 + len(hosts)  # tree links + host links
        return self._start_network(switches=len(switches), hosts=len(hosts), links=links)
    
    def _create_mesh(self, num_switches: int) -> Dict:
        """
        Create full mesh topology (all switches connected)
        
        Args:
            num_switches: Number of switches (2-6 recommended)
            
        Returns:
            Creation status dictionary
        """
        # Limit mesh size to avoid explosion
        num_switches = min(num_switches, 6)
        
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True
        )
        
        # Add controller
        c0 = self.net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=config.OPENFLOW_PORT
        )
        
        # Create switches
        switches = []
        for i in range(1, num_switches + 1):
            s = self.net.addSwitch(f's{i}', protocols=config.OPENFLOW_VERSION)
            switches.append(s)
        
        # Create full mesh (every switch connected to every other)
        mesh_links = 0
        for i in range(len(switches)):
            for j in range(i + 1, len(switches)):
                self.net.addLink(switches[i], switches[j])
                mesh_links += 1
        
        # Add one host per switch
        hosts = []
        for i in range(1, num_switches + 1):
            h = self.net.addHost(f'h{i}', ip=f'10.0.0.{i}')
            self.net.addLink(h, switches[i-1])
            hosts.append(h)
        
        links = mesh_links + len(hosts)
        return self._start_network(switches=num_switches, hosts=num_switches, links=links)
    
    def _start_network(self, switches: int, hosts: int, links: int) -> Dict:
        """
        Start the Mininet network and wait for controller connection
        
        Args:
            switches: Number of switches created
            hosts: Number of hosts created
            links: Number of links created
            
        Returns:
            Status dictionary
        """
        try:
            logger.info("Starting Mininet network...")
            self.net.start()
            
            # Set OpenFlow version for all switches
            logger.info("Setting OpenFlow 1.3 for all switches...")
            for switch in self.net.switches:
                switch.cmd(f'ovs-vsctl set Bridge {switch.name} protocols={config.OPENFLOW_VERSION}')
            
            # Wait for switches to connect to controller
            logger.info(f"Waiting {config.SWITCH_CONNECTION_WAIT}s for switches to connect to Ryu...")
            time.sleep(config.SWITCH_CONNECTION_WAIT)
            
            # Verify switches are connected
            for switch in self.net.switches:
                result = switch.cmd('ovs-vsctl show')
                if 'is_connected: true' not in result:
                    logger.warning(f"Switch {switch.name} may not be connected to controller")
            
            logger.info("Network started successfully")
            
            return {
                "success": True,
                "topology_type": self.topology_type,
                "size": self.topology_size,
                "switches": switches,
                "hosts": hosts,
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Failed to start network: {e}")
            self._cleanup_existing()
            raise
    
    def stop(self) -> Dict:
        """
        Stop the current Mininet network
        
        Returns:
            Status dictionary
        """
        try:
            self._cleanup_existing()
            logger.info("Network stopped successfully")
            return {"success": True, "message": "Network stopped"}
        except Exception as e:
            logger.error(f"Error stopping network: {e}")
            return {"success": False, "error": str(e)}
    
    def pingall(self) -> Dict:
        """
        Run pingall test on the network
        
        Returns:
            Dictionary with ping results
        """
        if self.net is None:
            raise RuntimeError("No network is running")
        
        try:
            logger.info("Running pingall test...")
            loss = self.net.pingAll(timeout='1')
            
            return {
                "success": True,
                "packet_loss": loss,
                "message": f"Ping completed with {loss}% packet loss"
            }
        except Exception as e:
            logger.error(f"Pingall failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def ping(self, src: str, dst: str) -> Dict:
        """
        Ping between two hosts
        
        Args:
            src: Source host name (e.g., 'h1')
            dst: Destination host name (e.g., 'h2')
            
        Returns:
            Ping result dictionary
        """
        if self.net is None:
            raise RuntimeError("No network is running")
        
        try:
            src_host = self.net.get(src)
            dst_host = self.net.get(dst)
            
            if not src_host or not dst_host:
                raise ValueError(f"Host not found: {src} or {dst}")
            
            result = self.net.ping([src_host, dst_host], timeout='1')
            
            return {
                "success": True,
                "packet_loss": result,
                "src": src,
                "dst": dst
            }
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_network_info(self) -> Dict:
        """
        Get information about the current network
        
        Returns:
            Network info dictionary
        """
        if self.net is None:
            return {
                "active": False,
                "message": "No network running"
            }
        
        return {
            "active": True,
            "topology_type": self.topology_type,
            "size": self.topology_size,
            "switches": [s.name for s in self.net.switches],
            "hosts": [h.name for h in self.net.hosts],
            "controllers": [c.name for c in self.net.controllers]
        }
    
    def cli(self):
        """Start Mininet CLI for debugging (blocking)"""
        if self.net is None:
            raise RuntimeError("No network is running")
        
        CLI(self.net)
