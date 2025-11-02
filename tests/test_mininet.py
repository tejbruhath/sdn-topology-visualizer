"""
Unit tests for Mininet Manager
Run with: python3 -m pytest tests/test_mininet.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from mininet_manager import MininetManager
import config


class TestMininetManager:
    """Test suite for MininetManager"""
    
    def setup_method(self):
        """Setup before each test"""
        self.manager = MininetManager()
    
    def teardown_method(self):
        """Cleanup after each test"""
        if self.manager.net is not None:
            self.manager.stop()
    
    def test_initialization(self):
        """Test manager initializes correctly"""
        assert self.manager.net is None
        assert self.manager.topology_type is None
        assert self.manager.topology_size == 0
    
    def test_invalid_topology_type(self):
        """Test invalid topology type raises error"""
        with pytest.raises(ValueError):
            self.manager.create("invalid_type", 4)
    
    def test_invalid_size_too_small(self):
        """Test size below minimum raises error"""
        with pytest.raises(ValueError):
            self.manager.create("star", config.MIN_SIZE - 1)
    
    def test_invalid_size_too_large(self):
        """Test size above maximum raises error"""
        with pytest.raises(ValueError):
            self.manager.create("star", config.MAX_SIZE + 1)
    
    def test_get_network_info_no_network(self):
        """Test getting info when no network exists"""
        info = self.manager.get_network_info()
        assert info['active'] is False
        assert 'No network running' in info['message']
    
    # Note: The following tests require Mininet and sudo privileges
    # They are marked with pytest.mark.skipif for CI environments
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Requires Mininet and sudo")
    def test_create_star_topology(self):
        """Test creating star topology"""
        result = self.manager.create("star", 3)
        
        assert result['success'] is True
        assert result['topology_type'] == "star"
        assert result['size'] == 3
        assert result['switches'] == 1
        assert result['hosts'] == 3
        assert result['links'] == 3
        
        # Verify network exists
        assert self.manager.net is not None
        assert len(self.manager.net.switches) == 1
        assert len(self.manager.net.hosts) == 3
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Requires Mininet and sudo")
    def test_create_linear_topology(self):
        """Test creating linear topology"""
        result = self.manager.create("linear", 3)
        
        assert result['success'] is True
        assert result['switches'] == 3
        assert result['hosts'] == 3
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Requires Mininet and sudo")
    def test_stop_network(self):
        """Test stopping network"""
        self.manager.create("star", 3)
        result = self.manager.stop()
        
        assert result['success'] is True
        assert self.manager.net is None
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Requires Mininet and sudo")
    def test_pingall(self):
        """Test pingall functionality"""
        self.manager.create("star", 3)
        
        # Wait for switches to connect
        import time
        time.sleep(3)
        
        result = self.manager.pingall()
        
        assert result['success'] is True
        assert 'packet_loss' in result
        # Note: May not be 0% if Ryu not running
    
    @pytest.mark.skipif(os.getenv('CI') == 'true', reason="Requires Mininet and sudo")
    def test_get_network_info_with_network(self):
        """Test getting info when network exists"""
        self.manager.create("star", 3)
        info = self.manager.get_network_info()
        
        assert info['active'] is True
        assert info['topology_type'] == "star"
        assert info['size'] == 3
        assert len(info['switches']) == 1
        assert len(info['hosts']) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
