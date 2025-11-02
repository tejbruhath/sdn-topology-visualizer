"""
Ryu REST API Client
Wrapper for interacting with Ryu controller's REST APIs
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import config

logger = logging.getLogger(__name__)


class RyuClient:
    """Client for Ryu Controller REST API"""
    
    def __init__(self, base_url: str = None):
        """
        Initialize Ryu client
        
        Args:
            base_url: Base URL for Ryu REST API (default from config)
        """
        self.base_url = base_url or config.RYU_BASE_URL
        self.timeout = config.CONNECTION_TIMEOUT
        
    def _get(self, endpoint: str) -> Any:
        """
        Make GET request to Ryu API
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ryu API request failed: {url} - {e}")
            raise
    
    def _post(self, endpoint: str, data: Dict) -> Any:
        """
        Make POST request to Ryu API
        
        Args:
            endpoint: API endpoint path
            data: JSON data to send
            
        Returns:
            JSON response data
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ryu API POST failed: {url} - {e}")
            raise
    
    def get_switches(self) -> List[Dict]:
        """
        Get all connected switches
        
        Returns:
            List of switch dictionaries with dpid
            Example: [{"dpid": "0000000000000001"}, ...]
        """
        try:
            data = self._get("/v1.0/topology/switches")
            # Convert DPID from hex string to readable format
            for switch in data:
                switch['dpid_int'] = int(switch['dpid'], 16)
            return data
        except Exception as e:
            logger.error(f"Failed to get switches: {e}")
            return []
    
    def get_links(self) -> List[Dict]:
        """
        Get all links between switches
        
        Returns:
            List of link dictionaries
            Example: [{
                "src": {"dpid": "0000000000000001", "port_no": 1},
                "dst": {"dpid": "0000000000000002", "port_no": 1}
            }, ...]
        """
        try:
            data = self._get("/v1.0/topology/links")
            return data
        except Exception as e:
            logger.error(f"Failed to get links: {e}")
            return []
    
    def get_hosts(self) -> List[Dict]:
        """
        Get all discovered hosts
        
        Returns:
            List of host dictionaries
            Example: [{
                "mac": "00:00:00:00:00:01",
                "ipv4": ["10.0.0.1"],
                "port": {"dpid": "0000000000000001", "port_no": 1}
            }, ...]
        """
        try:
            data = self._get("/v1.0/topology/hosts")
            return data
        except Exception as e:
            logger.error(f"Failed to get hosts: {e}")
            return []
    
    def get_flow_stats(self, dpid: str) -> List[Dict]:
        """
        Get flow table entries for a switch
        
        Args:
            dpid: Switch DPID (as hex string or int)
            
        Returns:
            List of flow entries
        """
        try:
            # Convert dpid to int if needed
            if isinstance(dpid, str) and not dpid.isdigit():
                dpid = int(dpid, 16)
            
            data = self._get(f"/stats/flow/{dpid}")
            return data.get(str(dpid), [])
        except Exception as e:
            logger.error(f"Failed to get flow stats for {dpid}: {e}")
            return []
    
    def get_port_stats(self, dpid: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Get port statistics for switch(es)
        
        Args:
            dpid: Specific switch DPID, or None for all switches
            
        Returns:
            Dictionary mapping DPID to list of port stats
            Example: {
                "1": [{
                    "port_no": 1,
                    "rx_packets": 100,
                    "tx_packets": 100,
                    "rx_bytes": 10000,
                    "tx_bytes": 10000
                }, ...]
            }
        """
        try:
            if dpid:
                # Convert dpid to int if needed
                if isinstance(dpid, str) and not dpid.isdigit():
                    dpid = int(dpid, 16)
                endpoint = f"/stats/port/{dpid}"
            else:
                # Get all switches
                switches = self.get_switches()
                if not switches:
                    return {}
                
                # Get port stats for first switch (for simplicity)
                dpid = switches[0]['dpid_int']
                endpoint = f"/stats/port/{dpid}"
            
            data = self._get(endpoint)
            return data
        except Exception as e:
            logger.error(f"Failed to get port stats: {e}")
            return {}
    
    def get_aggregate_flow_stats(self, dpid: str) -> Dict:
        """
        Get aggregate flow statistics for a switch
        
        Args:
            dpid: Switch DPID
            
        Returns:
            Aggregate statistics (packet count, byte count, flow count)
        """
        try:
            if isinstance(dpid, str) and not dpid.isdigit():
                dpid = int(dpid, 16)
            
            data = self._get(f"/stats/aggregateflow/{dpid}")
            return data.get(str(dpid), [{}])[0]
        except Exception as e:
            logger.error(f"Failed to get aggregate stats for {dpid}: {e}")
            return {}
    
    def add_flow(self, dpid: str, flow: Dict) -> bool:
        """
        Add a flow entry to a switch
        
        Args:
            dpid: Switch DPID
            flow: Flow entry dictionary
            
        Returns:
            True if successful
        """
        try:
            if isinstance(dpid, str) and not dpid.isdigit():
                dpid = int(dpid, 16)
            
            endpoint = f"/stats/flowentry/add"
            data = {"dpid": dpid, **flow}
            self._post(endpoint, data)
            logger.info(f"Added flow to switch {dpid}")
            return True
        except Exception as e:
            logger.error(f"Failed to add flow to {dpid}: {e}")
            return False
    
    def delete_flow(self, dpid: str, flow: Dict) -> bool:
        """
        Delete a flow entry from a switch
        
        Args:
            dpid: Switch DPID
            flow: Flow match criteria
            
        Returns:
            True if successful
        """
        try:
            if isinstance(dpid, str) and not dpid.isdigit():
                dpid = int(dpid, 16)
            
            endpoint = f"/stats/flowentry/delete"
            data = {"dpid": dpid, **flow}
            self._post(endpoint, data)
            logger.info(f"Deleted flow from switch {dpid}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete flow from {dpid}: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if Ryu controller is reachable
        
        Returns:
            True if Ryu is responding
        """
        try:
            self._get("/v1.0/topology/switches")
            return True
        except:
            return False
    
    def get_controller_info(self) -> Dict:
        """
        Get controller information and statistics
        
        Returns:
            Dictionary with controller stats
        """
        try:
            switches = self.get_switches()
            links = self.get_links()
            hosts = self.get_hosts()
            
            return {
                "connected": True,
                "switch_count": len(switches),
                "link_count": len(links),
                "host_count": len(hosts),
                "base_url": self.base_url
            }
        except Exception as e:
            logger.error(f"Failed to get controller info: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
