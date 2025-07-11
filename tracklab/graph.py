"""
Graph data type for TrackLab
"""

import json
from typing import Any, Dict, List, Optional, Union, Tuple

from .base import WBValue, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("graph")
class Graph(WBValue):
    """
    Graph data type for logging network structures
    
    Supports nodes, edges, and graph visualizations
    """
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: Optional[str] = None,
        directed: bool = False,
        node_symbol: str = "circle",
        edge_symbol: str = "line"
    ):
        """
        Initialize graph
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            title: Graph title
            directed: Whether graph is directed
            node_symbol: Symbol for nodes
            edge_symbol: Symbol for edges
        """
        super().__init__()
        
        self.title = title
        self.directed = directed
        self.node_symbol = node_symbol
        self.edge_symbol = edge_symbol
        
        # Process nodes and edges
        self._process_nodes(nodes)
        self._process_edges(edges)
        
        # Generate ID
        self._id = self._generate_id(
            json.dumps({"nodes": self.nodes, "edges": self.edges}, sort_keys=True).encode()
        )
    
    def _process_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Process node data"""
        self.nodes = []
        
        for i, node in enumerate(nodes):
            processed_node = {
                "id": node.get("id", i),
                "label": node.get("label", f"Node {i}"),
                "x": node.get("x", 0),
                "y": node.get("y", 0),
                "size": node.get("size", 10),
                "color": node.get("color", "blue"),
                "shape": node.get("shape", self.node_symbol)
            }
            
            # Add any additional properties
            for key, value in node.items():
                if key not in processed_node:
                    processed_node[key] = value
            
            self.nodes.append(processed_node)
    
    def _process_edges(self, edges: List[Dict[str, Any]]) -> None:
        """Process edge data"""
        self.edges = []
        
        for i, edge in enumerate(edges):
            processed_edge = {
                "id": edge.get("id", i),
                "source": edge.get("source", edge.get("from")),
                "target": edge.get("target", edge.get("to")),
                "label": edge.get("label", ""),
                "weight": edge.get("weight", 1.0),
                "color": edge.get("color", "gray"),
                "width": edge.get("width", 1)
            }
            
            # Validate source and target
            if processed_edge["source"] is None or processed_edge["target"] is None:
                raise ValueError(f"Edge {i} missing source or target")
            
            # Add any additional properties
            for key, value in edge.items():
                if key not in processed_edge:
                    processed_edge[key] = value
            
            self.edges.append(processed_edge)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "graph",
            "id": self._id,
            "title": self.title,
            "directed": self.directed,
            "node_symbol": self.node_symbol,
            "edge_symbol": self.edge_symbol,
            "nodes": self.nodes,
            "edges": self.edges,
            "stats": self._get_stats()
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()
    
    def _get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "density": self._calculate_density(),
            "avg_degree": self._calculate_avg_degree()
        }
    
    def _calculate_density(self) -> float:
        """Calculate graph density"""
        n = len(self.nodes)
        if n < 2:
            return 0.0
        
        max_edges = n * (n - 1)
        if not self.directed:
            max_edges //= 2
        
        return len(self.edges) / max_edges if max_edges > 0 else 0.0
    
    def _calculate_avg_degree(self) -> float:
        """Calculate average degree"""
        if not self.nodes:
            return 0.0
        
        # Count degrees
        degree_count = {}
        for node in self.nodes:
            degree_count[node["id"]] = 0
        
        for edge in self.edges:
            degree_count[edge["source"]] += 1
            if not self.directed:
                degree_count[edge["target"]] += 1
        
        total_degree = sum(degree_count.values())
        return total_degree / len(self.nodes) if self.nodes else 0.0
    
    def add_node(self, node: Dict[str, Any]) -> None:
        """Add a node to the graph"""
        self._process_nodes([node])
        self.nodes.extend(self._processed_nodes)
    
    def add_edge(self, edge: Dict[str, Any]) -> None:
        """Add an edge to the graph"""
        self._process_edges([edge])
        self.edges.extend(self._processed_edges)
    
    def get_node(self, node_id: Any) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        return None
    
    def get_edge(self, source: Any, target: Any) -> Optional[Dict[str, Any]]:
        """Get edge by source and target"""
        for edge in self.edges:
            if edge["source"] == source and edge["target"] == target:
                return edge
            if not self.directed and edge["source"] == target and edge["target"] == source:
                return edge
        return None
    
    def get_neighbors(self, node_id: Any) -> List[Any]:
        """Get neighbors of a node"""
        neighbors = []
        
        for edge in self.edges:
            if edge["source"] == node_id:
                neighbors.append(edge["target"])
            elif not self.directed and edge["target"] == node_id:
                neighbors.append(edge["source"])
        
        return neighbors
    
    def get_degree(self, node_id: Any) -> int:
        """Get degree of a node"""
        degree = 0
        
        for edge in self.edges:
            if edge["source"] == node_id:
                degree += 1
            elif not self.directed and edge["target"] == node_id:
                degree += 1
        
        return degree
    
    def to_networkx(self) -> Any:
        """Convert to NetworkX graph"""
        try:
            import networkx as nx
            
            # Create graph
            if self.directed:
                G = nx.DiGraph()
            else:
                G = nx.Graph()
            
            # Add nodes
            for node in self.nodes:
                G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
            
            # Add edges
            for edge in self.edges:
                G.add_edge(edge["source"], edge["target"], 
                          **{k: v for k, v in edge.items() if k not in ["source", "target"]})
            
            return G
            
        except ImportError:
            raise ImportError("NetworkX required for graph conversion")
    
    def to_plotly(self) -> Dict[str, Any]:
        """Convert to Plotly format"""
        # Node trace
        node_trace = {
            "type": "scatter",
            "x": [node["x"] for node in self.nodes],
            "y": [node["y"] for node in self.nodes],
            "mode": "markers+text",
            "text": [node["label"] for node in self.nodes],
            "textposition": "middle center",
            "marker": {
                "size": [node["size"] for node in self.nodes],
                "color": [node["color"] for node in self.nodes]
            },
            "name": "Nodes"
        }
        
        # Edge traces
        edge_traces = []
        for edge in self.edges:
            # Find source and target positions
            source_node = self.get_node(edge["source"])
            target_node = self.get_node(edge["target"])
            
            if source_node and target_node:
                edge_trace = {
                    "type": "scatter",
                    "x": [source_node["x"], target_node["x"], None],
                    "y": [source_node["y"], target_node["y"], None],
                    "mode": "lines",
                    "line": {
                        "width": edge["width"],
                        "color": edge["color"]
                    },
                    "showlegend": False
                }
                edge_traces.append(edge_trace)
        
        return {
            "data": [node_trace] + edge_traces,
            "layout": {
                "title": self.title or "Graph",
                "showlegend": True,
                "hovermode": "closest",
                "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False}
            }
        }
    
    @classmethod
    def from_networkx(cls, G: Any, title: Optional[str] = None) -> "Graph":
        """Create Graph from NetworkX graph"""
        try:
            import networkx as nx
            
            # Extract nodes
            nodes = []
            pos = nx.spring_layout(G)  # Get positions
            
            for node_id, data in G.nodes(data=True):
                node = {
                    "id": node_id,
                    "label": str(node_id),
                    "x": pos[node_id][0],
                    "y": pos[node_id][1],
                    **data
                }
                nodes.append(node)
            
            # Extract edges
            edges = []
            for source, target, data in G.edges(data=True):
                edge = {
                    "source": source,
                    "target": target,
                    **data
                }
                edges.append(edge)
            
            return cls(
                nodes=nodes,
                edges=edges,
                title=title,
                directed=G.is_directed()
            )
            
        except ImportError:
            raise ImportError("NetworkX required for graph conversion")
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Graph":
        """Create Graph from JSON"""
        return cls(
            nodes=data["nodes"],
            edges=data["edges"],
            title=data.get("title"),
            directed=data.get("directed", False),
            node_symbol=data.get("node_symbol", "circle"),
            edge_symbol=data.get("edge_symbol", "line")
        )