#!/usr/bin/env python
"""Test UI backend WebSocket real-time updates.

---
id: 0.ui_backend.03-websocket-updates
tag:
  platforms:
    - linux
    - mac
    - win
plugin:
  - wandb
depend:
  requirements:
    - fastapi
    - uvicorn
    - httpx
    - websockets
assert:
  - :wandb:runs_len: 1
  - :wandb:runs[0][config][test_type]: websocket
  - :wandb:runs[0][summary][websocket_test]: passed
  - :wandb:runs[0][summary][messages_received]: 5
  - :wandb:runs[0][exitcode]: 0
"""

import asyncio
import time
import threading
import json
import tracklab
import websockets
from tracklab.ui.server import TrackLabUIServer


def start_server(server):
    """Start the UI server in a separate thread."""
    import uvicorn
    uvicorn.run(server.app, host=server.host, port=server.port, log_level="error")


async def test_websocket_updates():
    """Test WebSocket real-time updates."""
    # Initialize a run
    run = tracklab.init(
        project="ui-websocket-test",
        config={
            "test_type": "websocket",
            "real_time": True
        }
    )
    
    project_name = run.project
    run_id = run.id
    
    # Create and start UI server
    server = TrackLabUIServer(port=8002, host="localhost")
    server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    messages_received = []
    
    try:
        # Connect to WebSocket
        async with websockets.connect("ws://localhost:8002/ws") as websocket:
            print("Connected to WebSocket")
            
            # Start a task to receive messages
            async def receive_messages():
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        messages_received.append(data)
                        print(f"Received: {data['type']}")
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            receive_task = asyncio.create_task(receive_messages())
            
            # Log metrics in a separate thread to trigger updates
            def log_metrics():
                for i in range(5):
                    time.sleep(0.5)
                    tracklab.log({
                        "metric_value": i * 100,
                        "timestamp": time.time()
                    }, step=i)
                    print(f"Logged metric {i}")
            
            log_thread = threading.Thread(target=log_metrics)
            log_thread.start()
            
            # Wait for metrics to be logged and updates received
            await asyncio.sleep(5)
            
            # Cancel receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            log_thread.join()
        
        # Verify we received some messages
        print(f"Received {len(messages_received)} WebSocket messages")
        
        # Check message types
        message_types = [msg.get("type") for msg in messages_received]
        
        # We should receive metric updates or run updates
        valid_types = {"run_update", "metric_update", "system_metrics"}
        received_valid_messages = any(t in valid_types for t in message_types)
        
        if received_valid_messages:
            tracklab.log({
                "websocket_test": "passed",
                "messages_received": len(messages_received)
            })
            print("WebSocket test passed!")
        else:
            tracklab.log({
                "websocket_test": "failed",
                "messages_received": len(messages_received),
                "message_types": message_types
            })
            raise AssertionError(f"No valid WebSocket messages received. Got types: {message_types}")
            
    except Exception as e:
        tracklab.log({
            "websocket_test": "failed",
            "error": str(e)
        })
        raise
    finally:
        tracklab.finish()


def main():
    """Run the async test."""
    asyncio.run(test_websocket_updates())


if __name__ == "__main__":
    main()