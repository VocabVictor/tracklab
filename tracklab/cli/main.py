"""
TrackLab CLI interface
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from ..backend.server.manager import ServerManager
from ..util.logging import setup_logging, get_logger
from ..sdk.tracklab_settings import get_settings, update_settings

logger = get_logger(__name__)

def cmd_server(args):
    """Server management commands"""
    
    manager = ServerManager(args.host, args.port)
    
    if args.server_command == "start":
        if manager.start(background=not args.foreground):
            print(f"✅ Server started on {args.host}:{args.port}")
            print(f"🌐 Dashboard: http://{args.host}:{args.port}/dashboard")
            print(f"📚 API Docs: http://{args.host}:{args.port}/api/docs")
            
            if args.foreground:
                try:
                    # Keep running in foreground
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping server...")
                    manager.stop()
        else:
            print("❌ Failed to start server")
            sys.exit(1)
    
    elif args.server_command == "stop":
        if manager.stop():
            print("✅ Server stopped")
        else:
            print("❌ Failed to stop server")
            sys.exit(1)
    
    elif args.server_command == "restart":
        if manager.restart():
            print("✅ Server restarted")
        else:
            print("❌ Failed to restart server")
            sys.exit(1)
    
    elif args.server_command == "status":
        status = manager.get_status()
        print(f"Server status: {'🟢 Running' if status['running'] else '🔴 Stopped'}")
        print(f"Host: {status['host']}")
        print(f"Port: {status['port']}")
        print(f"URL: {status['url']}")
        if status['pid']:
            print(f"PID: {status['pid']}")

def cmd_runs(args):
    """Run management commands"""
    
    from ..apis.public import get_api
    
    api = get_api()
    
    if args.runs_command == "list":
        runs = api.list_runs(args.project, args.entity)
        
        if not runs:
            print("No runs found")
            return
        
        print(f"Found {len(runs)} runs:")
        print()
        
        for run in runs:
            print(f"🏃 {run.name} ({run.id[:8]})")
            print(f"   Project: {run.project}")
            print(f"   State: {run.state}")
            print(f"   Created: {run.created_at}")
            print()
    
    elif args.runs_command == "show":
        if not args.run_id:
            print("❌ Run ID required")
            sys.exit(1)
        
        run = api.get_run(args.run_id)
        
        if not run:
            print("❌ Run not found")
            sys.exit(1)
        
        print(f"🏃 Run: {run.name}")
        print(f"   ID: {run.id}")
        print(f"   Project: {run.project}")
        print(f"   Entity: {run.entity}")
        print(f"   State: {run.state}")
        print(f"   Created: {run.created_at}")
        print(f"   Updated: {run.updated_at}")
        
        if run.notes:
            print(f"   Notes: {run.notes}")
        
        if run.tags:
            print(f"   Tags: {', '.join(run.tags)}")
        
        if run.config:
            print(f"   Config: {len(run.config)} items")
        
        if run.summary:
            print(f"   Summary: {len(run.summary)} items")
        
        # Show metrics
        metrics = run.get_metrics()
        if metrics:
            print(f"   Metrics: {len(metrics)} logged")
        
        # Show files
        files = run.get_files()
        if files:
            print(f"   Files: {len(files)} saved")

def cmd_projects(args):
    """Project management commands"""
    
    from ..apis.public import get_api
    
    api = get_api()
    
    if args.projects_command == "list":
        projects = api.list_projects()
        
        if not projects:
            print("No projects found")
            return
        
        print(f"Found {len(projects)} projects:")
        print()
        
        for project in projects:
            print(f"📁 {project.name}")
            print(f"   Entity: {project.entity}")
            print(f"   Created: {project.created_at}")
            if project.description:
                print(f"   Description: {project.description}")
            print()
    
    elif args.projects_command == "create":
        if not args.name:
            print("❌ Project name required")
            sys.exit(1)
        
        try:
            project = api.create_project(args.name, args.entity, args.description)
            print(f"✅ Created project: {project.name}")
        except Exception as e:
            print(f"❌ Failed to create project: {e}")
            sys.exit(1)

def cmd_config(args):
    """Configuration commands"""
    
    settings = get_settings()
    
    if args.config_command == "show":
        print("🔧 TrackLab Configuration:")
        print(f"   TrackLab Dir: {settings.tracklab_dir}")
        print(f"   Server Host: {settings.server_host}")
        print(f"   Server Port: {settings.server_port}")
        print(f"   Database URL: {settings.database_url}")
        print(f"   Mode: {settings.mode}")
        print(f"   Log Level: {settings.log_level}")
        print(f"   Auto Start: {settings.server_auto_start}")
        print(f"   Save Code: {settings.save_code}")
    
    elif args.config_command == "set":
        if not args.key or not args.value:
            print("❌ Key and value required")
            sys.exit(1)
        
        try:
            update_settings(**{args.key: args.value})
            print(f"✅ Set {args.key} = {args.value}")
        except Exception as e:
            print(f"❌ Failed to set config: {e}")
            sys.exit(1)

def cmd_status(args):
    """Show TrackLab status"""
    
    from ..apis.internal import get_internal_api
    from ..backend.server.manager import ServerManager
    
    print("🚀 TrackLab Status:")
    print()
    
    # Settings
    settings = get_settings()
    print(f"📂 Data Directory: {settings.tracklab_dir}")
    print(f"🔧 Mode: {settings.mode}")
    print()
    
    # Server status
    manager = ServerManager(settings.server_host, settings.server_port)
    server_status = manager.get_status()
    
    print(f"🌐 Server: {'🟢 Running' if server_status['running'] else '🔴 Stopped'}")
    print(f"   URL: {server_status['url']}")
    if server_status['pid']:
        print(f"   PID: {server_status['pid']}")
    print()
    
    # Database status
    try:
        api = get_internal_api()
        health = api.health_check()
        print(f"💾 Database: {'🟢 Connected' if health['status'] == 'healthy' else '🔴 Error'}")
        if health['status'] == 'healthy':
            print(f"   Projects: {health.get('projects', 0)}")
        else:
            print(f"   Error: {health.get('error', 'Unknown')}")
    except Exception as e:
        print(f"💾 Database: 🔴 Error ({e})")
    
    print()

def cmd_init(args):
    """Initialize TrackLab"""
    
    from ..sdk.tracklab_settings import get_settings
    
    settings = get_settings()
    
    print("🚀 Initializing TrackLab...")
    
    # Create directories
    try:
        settings.ensure_directories()
        print(f"✅ Created directories in {settings.tracklab_dir}")
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        sys.exit(1)
    
    # Start server if requested
    if args.server:
        manager = ServerManager(settings.server_host, settings.server_port)
        if manager.start():
            print(f"✅ Server started on {settings.server_host}:{settings.server_port}")
        else:
            print("❌ Failed to start server")
            sys.exit(1)
    
    print("✅ TrackLab initialized successfully!")
    print()
    print("Next steps:")
    print("1. Start the server: tracklab server start")
    print("2. Open the dashboard: http://localhost:8080/dashboard")
    print("3. Start tracking experiments with: import tracklab; tracklab.init()")

def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="TrackLab - Local experiment tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server commands
    server_parser = subparsers.add_parser("server", help="Server management")
    server_parser.add_argument("server_command", choices=["start", "stop", "restart", "status"], 
                              help="Server command")
    server_parser.add_argument("--host", default="localhost", help="Server host")
    server_parser.add_argument("--port", type=int, default=8080, help="Server port")
    server_parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    server_parser.set_defaults(func=cmd_server)
    
    # Run commands
    runs_parser = subparsers.add_parser("runs", help="Run management")
    runs_parser.add_argument("runs_command", choices=["list", "show"], help="Run command")
    runs_parser.add_argument("--project", help="Project name")
    runs_parser.add_argument("--entity", default="default", help="Entity name")
    runs_parser.add_argument("--run-id", help="Run ID")
    runs_parser.set_defaults(func=cmd_runs)
    
    # Project commands
    projects_parser = subparsers.add_parser("projects", help="Project management")
    projects_parser.add_argument("projects_command", choices=["list", "create"], help="Project command")
    projects_parser.add_argument("--name", help="Project name")
    projects_parser.add_argument("--entity", default="default", help="Entity name")
    projects_parser.add_argument("--description", help="Project description")
    projects_parser.set_defaults(func=cmd_projects)
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration")
    config_parser.add_argument("config_command", choices=["show", "set"], help="Config command")
    config_parser.add_argument("--key", help="Configuration key")
    config_parser.add_argument("--value", help="Configuration value")
    config_parser.set_defaults(func=cmd_config)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show TrackLab status")
    status_parser.set_defaults(func=cmd_status)
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize TrackLab")
    init_parser.add_argument("--server", action="store_true", help="Start server after init")
    init_parser.set_defaults(func=cmd_init)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        level="DEBUG" if args.debug else "INFO",
        quiet=args.quiet,
        verbose=args.verbose
    )
    
    # Run command
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n🛑 Interrupted")
            sys.exit(1)
        except Exception as e:
            if args.debug:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()