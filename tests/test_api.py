"""
Integration tests for Flask API
Run with: python3 -m pytest tests/test_api.py

Note: Requires Ryu to be running on localhost:8080
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
import requests
import time


BASE_URL = "http://localhost:5000"
RYU_URL = "http://localhost:8080"


class TestFlaskAPI:
    """Test suite for Flask REST API"""
    
    @pytest.fixture(scope="class", autouse=True)
    def check_services(self):
        """Check if required services are running"""
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
        except requests.RequestException:
            pytest.skip("Flask backend not running")
        
        try:
            requests.get(f"{RYU_URL}/v1.0/topology/switches", timeout=2)
        except requests.RequestException:
            pytest.skip("Ryu controller not running")
    
    def teardown_method(self):
        """Cleanup after each test"""
        try:
            requests.post(f"{BASE_URL}/api/topology/stop", timeout=5)
            time.sleep(2)
        except:
            pass
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'ryu_connected' in data
        assert 'network_active' in data
    
    def test_create_topology_star(self):
        """Test creating star topology"""
        payload = {"type": "star", "size": 3}
        response = requests.post(
            f"{BASE_URL}/api/topology/create",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'Created star topology' in data['message']
    
    def test_create_topology_invalid_type(self):
        """Test creating topology with invalid type"""
        payload = {"type": "invalid", "size": 3}
        response = requests.post(
            f"{BASE_URL}/api/topology/create",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'Invalid topology type' in data['error']
    
    def test_create_topology_invalid_size(self):
        """Test creating topology with invalid size"""
        payload = {"type": "star", "size": 100}
        response = requests.post(
            f"{BASE_URL}/api/topology/create",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'Size must be between' in data['error']
    
    def test_get_topology_data(self):
        """Test getting topology data"""
        # Create topology first
        requests.post(
            f"{BASE_URL}/api/topology/create",
            json={"type": "star", "size": 3}
        )
        time.sleep(4)  # Wait for switches to connect
        
        # Get topology data
        response = requests.get(f"{BASE_URL}/api/topology/data")
        
        assert response.status_code == 200
        data = response.json()
        assert 'nodes' in data
        assert 'edges' in data
        assert len(data['nodes']) > 0  # Should have at least switch and hosts
    
    def test_stop_topology(self):
        """Test stopping topology"""
        # Create topology first
        requests.post(
            f"{BASE_URL}/api/topology/create",
            json={"type": "star", "size": 3}
        )
        time.sleep(2)
        
        # Stop topology
        response = requests.post(f"{BASE_URL}/api/topology/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    def test_pingall(self):
        """Test pingall functionality"""
        # Create topology
        requests.post(
            f"{BASE_URL}/api/topology/create",
            json={"type": "star", "size": 3}
        )
        time.sleep(4)  # Wait for switches to connect
        
        # Run pingall
        response = requests.post(f"{BASE_URL}/api/topology/pingall")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'packet_loss' in data
    
    def test_controller_info(self):
        """Test getting controller info"""
        response = requests.get(f"{BASE_URL}/api/controller/info")
        
        assert response.status_code == 200
        data = response.json()
        assert 'connected' in data
        assert data['connected'] is True


class TestRyuAPI:
    """Test suite for Ryu REST API (direct)"""
    
    @pytest.fixture(scope="class", autouse=True)
    def check_ryu(self):
        """Check if Ryu is running"""
        try:
            requests.get(f"{RYU_URL}/v1.0/topology/switches", timeout=2)
        except requests.RequestException:
            pytest.skip("Ryu controller not running")
    
    def test_get_switches(self):
        """Test Ryu switches endpoint"""
        response = requests.get(f"{RYU_URL}/v1.0/topology/switches")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_links(self):
        """Test Ryu links endpoint"""
        response = requests.get(f"{RYU_URL}/v1.0/topology/links")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_hosts(self):
        """Test Ryu hosts endpoint"""
        response = requests.get(f"{RYU_URL}/v1.0/topology/hosts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
