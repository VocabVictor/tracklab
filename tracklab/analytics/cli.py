#!/usr/bin/env python
"""Command-line interface for TrackLab Analytics.

This tool provides commands to view, analyze, and manage local analytics data.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .viewer import AnalyticsViewer


def cmd_summary(args):
    """Show analytics summary."""
    viewer = AnalyticsViewer(args.path)
    viewer.print_summary(days=args.days)


def cmd_errors(args):
    """List recent errors."""
    viewer = AnalyticsViewer(args.path)
    errors = viewer.get_error_details(
        days=args.days,
        error_type=args.type,
        limit=args.limit
    )
    
    if not errors:
        print("No errors found.")
        return
    
    print(f"\nShowing {len(errors)} errors (most recent first):")
    print("=" * 80)
    
    for error in reversed(errors[-args.limit:]):
        timestamp = datetime.fromtimestamp(error["timestamp"] / 1000)
        data = error["data"]
        
        print(f"\n[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {data['exception_type']}")
        print(f"Message: {data['message']}")
        print(f"Handled: {data['handled']}")
        print(f"Environment: {data['environment']}")
        
        if args.verbose and data.get("traceback"):
            print("\nTraceback:")
            print(data["traceback"])
        
        print("-" * 80)


def cmd_export(args):
    """Export analytics data."""
    viewer = AnalyticsViewer(args.path)
    output = viewer.export_errors(
        format=args.format,
        output_file=args.output,
        days=args.days
    )
    
    if not args.output:
        print(output)
    else:
        print(f"Analytics data exported to: {args.output}")


def cmd_cleanup(args):
    """Clean up old analytics data."""
    viewer = AnalyticsViewer(args.path)
    
    if not args.yes:
        response = input(f"Delete analytics data older than {args.keep_days} days? [y/N] ")
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return
    
    removed = viewer.cleanup_old_data(days_to_keep=args.keep_days)
    print(f"Removed {removed} old analytics files.")


def cmd_timeline(args):
    """Show error timeline."""
    viewer = AnalyticsViewer(args.path)
    timeline = viewer.get_error_timeline(days=args.days, bucket_hours=args.bucket_hours)
    
    if not timeline:
        print("No errors found.")
        return
    
    print(f"\nError Timeline (Last {args.days} days):")
    print("=" * 40)
    
    max_count = max(timeline.values()) if timeline else 1
    
    for date, count in sorted(timeline.items()):
        bar_length = int((count / max_count) * 30)
        bar = "#" * bar_length
        print(f"{date}: {bar} {count}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="TrackLab Analytics CLI - View and manage local analytics data"
    )
    parser.add_argument(
        "--path",
        help="Path to analytics directory (default: ~/.tracklab/analytics)",
        default=None
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show analytics summary")
    summary_parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days to analyze (default: 7)"
    )
    
    # Errors command
    errors_parser = subparsers.add_parser("errors", help="List recent errors")
    errors_parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days to look back (default: 7)"
    )
    errors_parser.add_argument(
        "--type", help="Filter by error type"
    )
    errors_parser.add_argument(
        "--limit", type=int, default=10,
        help="Maximum number of errors to show (default: 10)"
    )
    errors_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show full tracebacks"
    )
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export analytics data")
    export_parser.add_argument(
        "--format", choices=["json", "csv", "markdown"], default="json",
        help="Export format (default: json)"
    )
    export_parser.add_argument(
        "--output", "-o", help="Output file (default: stdout)"
    )
    export_parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days to export (default: 7)"
    )
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old analytics data")
    cleanup_parser.add_argument(
        "--keep-days", type=int, default=30,
        help="Number of days to keep (default: 30)"
    )
    cleanup_parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt"
    )
    
    # Timeline command
    timeline_parser = subparsers.add_parser("timeline", help="Show error timeline")
    timeline_parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days to analyze (default: 7)"
    )
    timeline_parser.add_argument(
        "--bucket-hours", type=int, default=24,
        help="Hours per timeline bucket (default: 24)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    commands = {
        "summary": cmd_summary,
        "errors": cmd_errors,
        "export": cmd_export,
        "cleanup": cmd_cleanup,
        "timeline": cmd_timeline
    }
    
    try:
        commands[args.command](args)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())