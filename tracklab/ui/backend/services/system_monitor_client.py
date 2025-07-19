"""
System Monitor Client for TrackLab Backend

This module provides a client interface to communicate with the Rust-based
system_monitor service via REST API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemMonitorClient:
    """Client for interacting with the system_monitor REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the system monitor client.
        
        Args:
            base_url: Base URL of the system_monitor REST API
        """
        self.base_url = base_url.rstrip('/')
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def health_check(self) -> bool:
        """
        Check if the system monitor service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
            
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """
        Get static system information.
        
        Returns:
            System information dict or None if failed
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/system/info") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get system info: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None
            
    async def get_metrics(self, node_id: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get real-time system metrics.
        
        Args:
            node_id: Optional node ID for distributed environments
            
        Returns:
            List of metrics or None if failed
        """
        try:
            session = await self._get_session()
            params = {}
            if node_id:
                params["node_id"] = node_id
                
            async with session.get(
                f"{self.base_url}/api/system/metrics",
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get metrics: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return None
            
    async def get_formatted_metrics(self, node_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get metrics formatted for frontend consumption.
        
        Args:
            node_id: Optional node ID for distributed environments
            
        Returns:
            Formatted metrics dict or None if failed
        """
        metrics_list = await self.get_metrics(node_id)
        if not metrics_list:
            return None
            
        # Assuming single node for now, take first entry
        if metrics_list:
            return metrics_list[0]
        return None
        
    async def stream_metrics(
        self,
        callback,
        interval: float = 1.0,
        node_id: Optional[str] = None
    ):
        """
        Stream metrics at regular intervals.
        
        Args:
            callback: Async function to call with metrics
            interval: Update interval in seconds
            node_id: Optional node ID for distributed environments
        """
        while True:
            try:
                metrics = await self.get_formatted_metrics(node_id)
                if metrics:
                    await callback(metrics)
            except Exception as e:
                logger.error(f"Error streaming metrics: {e}")
                
            await asyncio.sleep(interval)


# Example usage
async def example_usage():
    """Example of how to use the SystemMonitorClient."""
    async with SystemMonitorClient() as client:
        # Check health
        if await client.health_check():
            print("System monitor is healthy")
            
        # Get system info
        info = await client.get_system_info()
        if info:
            print(f"System: {info['platform']} {info['architecture']}")
            print(f"CPU: {info['cpu_model']} ({info['cpu_cores']} cores)")
            print(f"Memory: {info['memory_total'] / (1024**3):.1f} GB")
            
        # Get metrics
        metrics = await client.get_formatted_metrics()
        if metrics:
            print(f"\nCurrent metrics at {datetime.fromtimestamp(metrics['timestamp']/1000)}")
            print(f"CPU Usage: {metrics['cpu']['overall']:.1f}%")
            print(f"Memory Usage: {metrics['memory']['usage']:.1f}%")
            print(f"Network: {metrics['network']['bytesIn']/1024:.1f} KB/s in, "
                  f"{metrics['network']['bytesOut']/1024:.1f} KB/s out")
            
            # Print GPU info if available
            if metrics['accelerators']:
                print("\nGPUs:")
                for gpu in metrics['accelerators']:
                    print(f"  {gpu['name']}: {gpu['utilization']:.1f}% utilization, "
                          f"{gpu['memory']['percentage']:.1f}% memory")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())