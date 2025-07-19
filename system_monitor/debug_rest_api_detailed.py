#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import os
import signal
from threading import Thread
from tracklab.system_monitor import SystemMonitor

def test_rest_api():
    print("Starting system monitor with REST API...")
    
    # Start the system monitor with REST API
    monitor = SystemMonitor(
        node_id="test-node",
        rest_port=8900,
        enable_grpc=True,
        verbose=True,
        auto_start=True
    )
    
    # Start in a separate thread to avoid blocking
    monitor_thread = Thread(target=monitor.run)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Wait for service to start
    print("Waiting for service to start...")
    time.sleep(3)
    
    # Test REST API endpoints
    base_url = "http://localhost:8900"
    
    endpoints = [
        "/api/health",
        "/api/system/info", 
        "/api/system/metrics"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\nTesting {url}...")
            
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Response text: {response.text}")
            else:
                print(f"Error response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    
    # Stop the monitor
    monitor.stop()
    print("\nMonitor stopped.")

if __name__ == "__main__":
    test_rest_api()