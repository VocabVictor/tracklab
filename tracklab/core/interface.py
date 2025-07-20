"""Interface layer to replace protobuf-based communication."""

import json
import queue
import threading
import socket
import time
from typing import Dict, Any, Optional, Callable, List, Union
from collections import defaultdict
import logging

from .core_records import Record
from .request_response import Request, Response
from .base_models import Control
from .storage import DataStore, get_data_store

logger = logging.getLogger(__name__)


class MessageQueue:
    """Simple message queue for inter-component communication."""
    
    def __init__(self, maxsize: int = 0):
        self.queue = queue.Queue(maxsize=maxsize)
        self.closed = False
    
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        """Put item in queue."""
        if self.closed:
            raise RuntimeError("Queue is closed")
        
        if isinstance(item, Record):
            # Serialize record for transport
            data = {"type": "record", "data": item.to_dict()}
        elif isinstance(item, Request):
            data = {"type": "request", "data": item.to_dict()}
        elif isinstance(item, Response):
            data = {"type": "response", "data": item.to_dict()}
        else:
            data = {"type": "raw", "data": item}
        
        self.queue.put(json.dumps(data), block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue."""
        data_str = self.queue.get(block=block, timeout=timeout)
        data = json.loads(data_str)
        
        # Deserialize based on type
        if data["type"] == "record":
            return Record.from_dict(data["data"])
        elif data["type"] == "request":
            return Request.from_dict(data["data"])
        elif data["type"] == "response":
            return Response.from_dict(data["data"])
        else:
            return data["data"]
    
    def close(self):
        """Close the queue."""
        self.closed = True
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()
    
    def qsize(self) -> int:
        """Get queue size."""
        return self.queue.qsize()


class Interface:
    """Main interface for sending/receiving records."""
    
    def __init__(self):
        self.record_q = MessageQueue(maxsize=10000)
        self.result_q = MessageQueue(maxsize=1000)
        self.pending_responses: Dict[str, MessageQueue] = {}
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        self._closed = False
        
        # Start processing thread
        self._process_thread = threading.Thread(target=self._process_records)
        self._process_thread.daemon = True
        self._process_thread.start()
    
    def send_record(self, record: Record):
        """Send a record through the interface."""
        if self._closed:
            raise RuntimeError("Interface is closed")
        
        # Handle request-response pattern
        if record.control and record.control.req_resp:
            # Create response queue
            response_q = MessageQueue(maxsize=1)
            self.pending_responses[record.uuid] = response_q
            
            # Send record
            self.record_q.put(record)
            
            # Wait for response
            try:
                response = response_q.get(timeout=5.0)
                return response
            except queue.Empty:
                raise TimeoutError("Request timeout")
            finally:
                del self.pending_responses[record.uuid]
        else:
            # Fire and forget
            self.record_q.put(record)
    
    def send_request(self, request: Request) -> Response:
        """Send a request and wait for response."""
        # Create a record wrapper for the request
        record = Record(
            control=Control(req_resp=True),
            # Store request data in the record
        )
        
        response = self.send_record(record)
        return response
    
    def register_handler(self, record_type: str, handler: Callable):
        """Register a handler for a record type."""
        self.handlers[record_type].append(handler)
    
    def _process_records(self):
        """Process records from the queue."""
        while not self._closed:
            try:
                record = self.record_q.get(timeout=0.1)
                
                # Handle based on record type
                if record.control and record.control.req_resp:
                    # This is a request, process and send response
                    response = self._handle_request(record)
                    
                    # Send response to waiting queue
                    if record.uuid in self.pending_responses:
                        self.pending_responses[record.uuid].put(response)
                else:
                    # Regular record, call handlers
                    for handler in self.handlers.get(str(record.record_type), []):
                        try:
                            handler(record)
                        except Exception as e:
                            logger.error(f"Error in handler: {e}")
                            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing record: {e}")
    
    def _handle_request(self, record: Record) -> Any:
        """Handle a request record."""
        # This would be implemented based on specific request types
        return Response(response_type="success", data={"status": "ok"})
    
    def close(self):
        """Close the interface."""
        self._closed = True
        self.record_q.close()
        self.result_q.close()
        self._process_thread.join()


class MessageBus:
    """Global message bus for pub/sub communication."""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def publish(self, topic: str, message: Any):
        """Publish a message to a topic."""
        with self._lock:
            handlers = self.subscribers[topic].copy()
        
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
    
    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a topic."""
        with self._lock:
            self.subscribers[topic].append(handler)
    
    def unsubscribe(self, topic: str, handler: Callable):
        """Unsubscribe from a topic."""
        with self._lock:
            if handler in self.subscribers[topic]:
                self.subscribers[topic].remove(handler)


# Global instances
_global_message_bus = MessageBus()


def get_message_bus() -> MessageBus:
    """Get global message bus instance."""
    return _global_message_bus


# Socket-based interface for cross-process communication
class SocketInterface(Interface):
    """Socket-based interface for IPC."""
    
    def __init__(self, address: tuple = ("localhost", 0)):
        super().__init__()
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(address)
        self.server_socket.listen(5)
        self.address = self.server_socket.getsockname()
        
        # Start accept thread
        self._accept_thread = threading.Thread(target=self._accept_connections)
        self._accept_thread.daemon = True
        self._accept_thread.start()
        
        self.clients = []
    
    def _accept_connections(self):
        """Accept client connections."""
        while not self._closed:
            try:
                client_socket, addr = self.server_socket.accept()
                self.clients.append(client_socket)
                
                # Start client handler thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if not self._closed:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection."""
        try:
            while not self._closed:
                # Read message length
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                
                length = int.from_bytes(length_data, 'big')
                
                # Read message
                data = b""
                while len(data) < length:
                    chunk = client_socket.recv(min(length - len(data), 4096))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) == length:
                    # Parse and handle message
                    message = json.loads(data.decode())
                    
                    if message["type"] == "record":
                        record = Record.from_dict(message["data"])
                        self.record_q.put(record)
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)
    
    def send_to_clients(self, record: Record):
        """Send record to all connected clients."""
        message = {"type": "record", "data": record.to_dict()}
        data = json.dumps(message).encode()
        length = len(data).to_bytes(4, 'big')
        
        for client in self.clients[:]:  # Copy list to avoid modification during iteration
            try:
                client.sendall(length + data)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                client.close()
                self.clients.remove(client)