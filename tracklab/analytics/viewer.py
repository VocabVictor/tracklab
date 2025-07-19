from __future__ import annotations

__all__ = ("AnalyticsViewer", "AnalyticsReport")

import csv
import io
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .local_analytics import LocalAnalytics


class AnalyticsReport:
    """Container for analytics report data."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.generated_at = datetime.now()
    
    def to_json(self, indent: int = 2) -> str:
        """Export report as JSON."""
        return json.dumps({
            "generated_at": self.generated_at.isoformat(),
            **self.data
        }, indent=indent, default=str)
    
    def to_csv(self) -> str:
        """Export error summary as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write error summary
        if "error_summary" in self.data:
            writer.writerow(["Error Summary"])
            writer.writerow(["Exception Type", "Count"])
            for exc_type, count in self.data["error_summary"].items():
                writer.writerow([exc_type, count])
            writer.writerow([])
        
        # Write recent errors
        if "recent_errors" in self.data:
            writer.writerow(["Recent Errors"])
            writer.writerow(["Timestamp", "Type", "Message", "Handled"])
            for error in self.data["recent_errors"]:
                writer.writerow([
                    datetime.fromtimestamp(error["timestamp"] / 1000).isoformat(),
                    error["data"]["exception_type"],
                    error["data"]["message"][:100],  # Truncate long messages
                    error["data"]["handled"]
                ])
        
        return output.getvalue()
    
    def to_markdown(self) -> str:
        """Export report as Markdown."""
        lines = [
            f"# Analytics Report",
            f"Generated at: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Error summary
        if "error_summary" in self.data:
            lines.extend([
                "## Error Summary",
                "",
                "| Exception Type | Count |",
                "|----------------|-------|"
            ])
            for exc_type, count in self.data["error_summary"].items():
                lines.append(f"| {exc_type} | {count} |")
            lines.append("")
        
        # Statistics
        if "statistics" in self.data:
            stats = self.data["statistics"]
            lines.extend([
                "## Statistics",
                "",
                f"- Total Errors: {stats.get('total_errors', 0)}",
                f"- Error Rate: {stats.get('error_rate', 0):.2f} errors/day",
                f"- Most Common Error: {stats.get('most_common_error', 'N/A')}",
                ""
            ])
        
        # Recent errors
        if "recent_errors" in self.data and self.data["recent_errors"]:
            lines.extend([
                "## Recent Errors (Last 10)",
                "",
                "| Time | Type | Message | Handled |",
                "|------|------|---------|---------|"
            ])
            for error in self.data["recent_errors"][:10]:
                time_str = datetime.fromtimestamp(
                    error["timestamp"] / 1000
                ).strftime("%Y-%m-%d %H:%M")
                msg = error["data"]["message"][:50] + "..." if len(error["data"]["message"]) > 50 else error["data"]["message"]
                lines.append(
                    f"| {time_str} | {error['data']['exception_type']} | {msg} | {error['data']['handled']} |"
                )
        
        return "\n".join(lines)


class AnalyticsViewer:
    """Tool for viewing and analyzing local analytics data."""
    
    def __init__(self, analytics_path: Optional[str] = None):
        self.analytics = LocalAnalytics(base_path=analytics_path)
    
    def get_error_summary(self, days: int = 7) -> Dict[str, int]:
        """Get error summary for the last N days."""
        return self.analytics.get_error_summary(days=days)
    
    def get_error_details(
        self,
        days: int = 7,
        error_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get detailed error information."""
        return self.analytics.query_errors(
            start_date=datetime.now() - timedelta(days=days),
            error_type=error_type,
            limit=limit
        )
    
    def get_error_timeline(self, days: int = 7, bucket_hours: int = 24) -> Dict[str, int]:
        """Get error counts bucketed by time period."""
        errors = self.get_error_details(days=days)
        
        # Create time buckets
        timeline = defaultdict(int)
        bucket_ms = bucket_hours * 60 * 60 * 1000
        
        for error in errors:
            timestamp = error["timestamp"]
            bucket = (timestamp // bucket_ms) * bucket_ms
            bucket_time = datetime.fromtimestamp(bucket / 1000).strftime("%Y-%m-%d")
            timeline[bucket_time] += 1
        
        return dict(sorted(timeline.items()))
    
    def get_error_context_summary(self, days: int = 7) -> Dict[str, Any]:
        """Analyze error contexts to find patterns."""
        errors = self.get_error_details(days=days)
        
        # Analyze contexts
        environments = defaultdict(int)
        handled_vs_unhandled = {"handled": 0, "unhandled": 0}
        
        for error in errors:
            data = error["data"]
            environments[data.get("environment", "unknown")] += 1
            if data.get("handled", False):
                handled_vs_unhandled["handled"] += 1
            else:
                handled_vs_unhandled["unhandled"] += 1
        
        return {
            "environments": dict(environments),
            "handled_breakdown": handled_vs_unhandled
        }
    
    def generate_report(self, days: int = 7) -> AnalyticsReport:
        """Generate a comprehensive analytics report."""
        # Gather all data
        error_summary = self.get_error_summary(days=days)
        recent_errors = self.get_error_details(days=days, limit=50)
        timeline = self.get_error_timeline(days=days)
        context_summary = self.get_error_context_summary(days=days)
        
        # Calculate statistics
        total_errors = sum(error_summary.values())
        error_rate = total_errors / days if days > 0 else 0
        most_common_error = max(error_summary.items(), key=lambda x: x[1])[0] if error_summary else None
        
        # Build report data
        report_data = {
            "period_days": days,
            "error_summary": error_summary,
            "recent_errors": recent_errors,
            "timeline": timeline,
            "context_summary": context_summary,
            "statistics": {
                "total_errors": total_errors,
                "error_rate": error_rate,
                "most_common_error": most_common_error,
                "unique_error_types": len(error_summary)
            }
        }
        
        return AnalyticsReport(report_data)
    
    def export_errors(
        self,
        format: str = "json",
        output_file: Optional[str] = None,
        days: int = 7
    ) -> str:
        """Export error data in various formats."""
        report = self.generate_report(days=days)
        
        # Generate output based on format
        if format == "json":
            output = report.to_json()
        elif format == "csv":
            output = report.to_csv()
        elif format == "markdown":
            output = report.to_markdown()
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Write to file if specified
        if output_file:
            Path(output_file).write_text(output)
        
        return output
    
    def print_summary(self, days: int = 7) -> None:
        """Print a summary to console."""
        report = self.generate_report(days=days)
        stats = report.data["statistics"]
        
        print(f"\nAnalytics Summary (Last {days} days)")
        print("=" * 40)
        print(f"Total Errors: {stats['total_errors']}")
        print(f"Error Rate: {stats['error_rate']:.2f} errors/day")
        print(f"Unique Error Types: {stats['unique_error_types']}")
        
        if stats['most_common_error']:
            print(f"Most Common: {stats['most_common_error']}")
        
        print("\nError Breakdown:")
        for exc_type, count in report.data["error_summary"].items():
            print(f"  {exc_type}: {count}")
        
        print("\nEnvironments:")
        for env, count in report.data["context_summary"]["environments"].items():
            print(f"  {env}: {count}")
        
        handled = report.data["context_summary"]["handled_breakdown"]
        print(f"\nHandled: {handled['handled']}, Unhandled: {handled['unhandled']}")
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old analytics data."""
        return self.analytics.cleanup_old_data(days_to_keep=days_to_keep)