"""
Histogram data type for TrackLab
"""

import json
from typing import Any, Dict, List, Optional, Union, Tuple
import numpy as np

from .base import WBValue, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("histogram")
class Histogram(WBValue):
    """
    Histogram data type for logging distributions
    
    Supports numpy arrays, lists, and other data that can be histogrammed
    """
    
    def __init__(
        self,
        values: Union[List[float], np.ndarray, Any],
        bins: Optional[Union[int, List[float], np.ndarray]] = None,
        num_bins: int = 64,
        title: Optional[str] = None,
        labels: Optional[List[str]] = None
    ):
        """
        Initialize histogram
        
        Args:
            values: Values to histogram
            bins: Bin edges or number of bins
            num_bins: Number of bins (if bins not specified)
            title: Histogram title
            labels: Labels for bins
        """
        super().__init__()
        
        self.title = title
        self.labels = labels
        self.num_bins = num_bins
        
        # Process values and bins
        self._process_data(values, bins)
    
    def _process_data(self, values: Any, bins: Optional[Union[int, List[float], np.ndarray]]) -> None:
        """Process values and create histogram"""
        
        # Convert values to numpy array
        if isinstance(values, list):
            values = np.array(values)
        elif hasattr(values, 'numpy'):  # PyTorch tensor
            values = values.detach().cpu().numpy()
        elif hasattr(values, 'eval'):  # TensorFlow tensor
            values = values.numpy()
        elif not isinstance(values, np.ndarray):
            try:
                values = np.array(values)
            except Exception:
                raise ValueError(f"Cannot convert values to array: {type(values)}")
        
        # Flatten if multidimensional
        if values.ndim > 1:
            values = values.flatten()
        
        # Remove NaN values
        values = values[~np.isnan(values)]
        
        if len(values) == 0:
            raise ValueError("No valid values for histogram")
        
        # Determine bins
        if bins is None:
            bins = self.num_bins
        
        # Create histogram
        try:
            counts, bin_edges = np.histogram(values, bins=bins)
        except Exception as e:
            raise ValueError(f"Failed to create histogram: {e}")
        
        # Store histogram data
        self._counts = counts.tolist()
        self._bin_edges = bin_edges.tolist()
        self._values = values.tolist()
        
        # Calculate statistics
        self._stats = {
            "count": len(values),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75))
        }
        
        # Generate ID
        self._id = self._generate_id(json.dumps(self._counts).encode())
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "histogram",
            "id": self._id,
            "title": self.title,
            "labels": self.labels,
            "counts": self._counts,
            "bin_edges": self._bin_edges,
            "num_bins": len(self._counts),
            "stats": self._stats
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()
    
    def get_bins(self) -> List[Tuple[float, float]]:
        """Get bin ranges"""
        bins = []
        for i in range(len(self._bin_edges) - 1):
            bins.append((self._bin_edges[i], self._bin_edges[i + 1]))
        return bins
    
    def get_bin_centers(self) -> List[float]:
        """Get bin centers"""
        centers = []
        for i in range(len(self._bin_edges) - 1):
            center = (self._bin_edges[i] + self._bin_edges[i + 1]) / 2
            centers.append(center)
        return centers
    
    def get_counts(self) -> List[int]:
        """Get bin counts"""
        return self._counts
    
    def get_frequencies(self) -> List[float]:
        """Get bin frequencies (normalized counts)"""
        total = sum(self._counts)
        if total == 0:
            return [0.0] * len(self._counts)
        return [count / total for count in self._counts]
    
    def get_probabilities(self) -> List[float]:
        """Get bin probabilities (frequencies * bin_width)"""
        frequencies = self.get_frequencies()
        bin_widths = self.get_bin_widths()
        return [freq * width for freq, width in zip(frequencies, bin_widths)]
    
    def get_bin_widths(self) -> List[float]:
        """Get bin widths"""
        widths = []
        for i in range(len(self._bin_edges) - 1):
            width = self._bin_edges[i + 1] - self._bin_edges[i]
            widths.append(width)
        return widths
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistics"""
        return self._stats.copy()
    
    def plot(self, show: bool = True, save_path: Optional[str] = None) -> Any:
        """Plot histogram using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot histogram
            ax.hist(self._values, bins=self._bin_edges, alpha=0.7, edgecolor='black')
            
            # Set labels and title
            ax.set_xlabel('Value')
            ax.set_ylabel('Frequency')
            if self.title:
                ax.set_title(self.title)
            
            # Add statistics as text
            stats_text = f"Mean: {self._stats['mean']:.3f}\nStd: {self._stats['std']:.3f}\nCount: {self._stats['count']}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            if save_path:
                fig.savefig(save_path, dpi=300, bbox_inches='tight')
            
            if show:
                plt.show()
            
            return fig
            
        except ImportError:
            raise ImportError("matplotlib required for plotting")
    
    def to_plotly(self) -> Dict[str, Any]:
        """Convert to Plotly format"""
        return {
            "data": [{
                "type": "histogram",
                "x": self._values,
                "nbinsx": len(self._counts),
                "name": self.title or "Histogram"
            }],
            "layout": {
                "title": self.title or "Histogram",
                "xaxis": {"title": "Value"},
                "yaxis": {"title": "Frequency"},
                "showlegend": False
            }
        }
    
    def merge(self, other: "Histogram") -> "Histogram":
        """Merge with another histogram"""
        if not isinstance(other, Histogram):
            raise ValueError("Can only merge with another Histogram")
        
        # Combine values
        combined_values = self._values + other._values
        
        # Create new histogram
        return Histogram(
            values=combined_values,
            bins=max(self.num_bins, other.num_bins),
            title=f"{self.title or 'Histogram'} + {other.title or 'Histogram'}"
        )
    
    def normalize(self) -> "Histogram":
        """Create normalized histogram"""
        # Create new histogram with same structure
        new_hist = Histogram.__new__(Histogram)
        new_hist.__dict__.update(self.__dict__)
        
        # Normalize counts
        total = sum(self._counts)
        if total > 0:
            new_hist._counts = [count / total for count in self._counts]
        
        # Update stats
        new_hist._stats = self._stats.copy()
        new_hist._stats["normalized"] = True
        
        return new_hist
    
    def cumulative(self) -> "Histogram":
        """Create cumulative histogram"""
        # Create new histogram with same structure
        new_hist = Histogram.__new__(Histogram)
        new_hist.__dict__.update(self.__dict__)
        
        # Calculate cumulative counts
        cumulative_counts = []
        running_sum = 0
        for count in self._counts:
            running_sum += count
            cumulative_counts.append(running_sum)
        
        new_hist._counts = cumulative_counts
        new_hist._stats = self._stats.copy()
        new_hist._stats["cumulative"] = True
        
        return new_hist
    
    def percentile(self, p: float) -> float:
        """Get percentile value"""
        if not 0 <= p <= 100:
            raise ValueError("Percentile must be between 0 and 100")
        
        return float(np.percentile(self._values, p))
    
    def __len__(self) -> int:
        """Get number of bins"""
        return len(self._counts)
    
    def __getitem__(self, index: int) -> Tuple[float, float, int]:
        """Get bin info by index"""
        if not 0 <= index < len(self._counts):
            raise IndexError(f"Bin index {index} out of range")
        
        return (self._bin_edges[index], self._bin_edges[index + 1], self._counts[index])
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Histogram":
        """Create Histogram from JSON"""
        # This is a simplified implementation
        # In practice, would need to reconstruct from stored data
        hist = cls.__new__(cls)
        hist._counts = data["counts"]
        hist._bin_edges = data["bin_edges"]
        hist._stats = data["stats"]
        hist.title = data.get("title")
        hist.labels = data.get("labels")
        hist._id = data.get("id")
        return hist
    
    @classmethod
    def from_sequence(cls, sequence: List[Union[List[float], np.ndarray]], 
                     titles: Optional[List[str]] = None) -> List["Histogram"]:
        """Create multiple histograms from sequence"""
        histograms = []
        
        for i, values in enumerate(sequence):
            title = titles[i] if titles and i < len(titles) else f"Histogram {i+1}"
            hist = cls(values, title=title)
            histograms.append(hist)
        
        return histograms