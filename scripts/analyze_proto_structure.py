#!/usr/bin/env python3
"""
Analyze the structure of tracklab_internal.proto and create a splitting strategy.
"""

import re
import pathlib
from typing import List, Dict, Set, Tuple


def extract_messages_and_services(proto_file: pathlib.Path) -> Dict[str, List[str]]:
    """Extract all messages and services from a proto file."""
    with open(proto_file, 'r') as f:
        content = f.read()
    
    # Find all message definitions
    message_pattern = r'^message\s+(\w+)\s*\{'
    messages = re.findall(message_pattern, content, re.MULTILINE)
    
    # Find all service definitions
    service_pattern = r'^service\s+(\w+)\s*\{'
    services = re.findall(service_pattern, content, re.MULTILINE)
    
    # Find all enum definitions
    enum_pattern = r'^enum\s+(\w+)\s*\{'
    enums = re.findall(enum_pattern, content, re.MULTILINE)
    
    return {
        'messages': messages,
        'services': services,
        'enums': enums
    }


def categorize_messages(messages: List[str]) -> Dict[str, List[str]]:
    """Categorize messages by their functional domain."""
    categories = {
        'core': [],           # Core record types and control structures
        'run_management': [], # Run lifecycle management
        'data_logging': [],   # Data, metrics, history logging
        'artifacts': [],      # Artifact management
        'config': [],         # Configuration management
        'communication': [],  # Request/response communication
        'files': [],          # File management
        'system': [],         # System and environment info
        'alerts': [],         # Alerts and notifications
        'misc': []            # Miscellaneous
    }
    
    # Core system messages
    core_keywords = ['Record', 'Result', 'Control', 'Final', 'Header', 'Footer', 'Info']
    
    # Run management
    run_keywords = ['Run', 'Exit', 'Preempting', 'Version', 'Branch']
    
    # Data logging
    data_keywords = ['History', 'Summary', 'Output', 'Metric', 'Stats', 'TB']
    
    # Artifacts
    artifact_keywords = ['Artifact', 'Model', 'Link', 'Use']
    
    # Configuration
    config_keywords = ['Config', 'Settings', 'Environment']
    
    # Communication
    comm_keywords = ['Request', 'Response', 'Server', 'Client']
    
    # Files
    file_keywords = ['Files', 'FilesRecord', 'FilePusher']
    
    # System
    system_keywords = ['System', 'Git', 'Repo', 'Platform', 'Machine']
    
    # Alerts
    alert_keywords = ['Alert', 'Notification']
    
    for message in messages:
        categorized = False
        
        # Check each category
        for keyword in core_keywords:
            if keyword in message:
                categories['core'].append(message)
                categorized = True
                break
        
        if not categorized:
            for keyword in run_keywords:
                if keyword in message:
                    categories['run_management'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in data_keywords:
                if keyword in message:
                    categories['data_logging'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in artifact_keywords:
                if keyword in message:
                    categories['artifacts'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in config_keywords:
                if keyword in message:
                    categories['config'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in comm_keywords:
                if keyword in message:
                    categories['communication'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in file_keywords:
                if keyword in message:
                    categories['files'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in system_keywords:
                if keyword in message:
                    categories['system'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in alert_keywords:
                if keyword in message:
                    categories['alerts'].append(message)
                    categorized = True
                    break
        
        if not categorized:
            categories['misc'].append(message)
    
    return categories


def main():
    """Main function to analyze proto structure."""
    proto_file = pathlib.Path("/home/wzh/tracklab/tracklab/proto/tracklab_internal.proto")
    
    print("=== TrackLab Internal Proto Analysis ===")
    print()
    
    # Extract all definitions
    definitions = extract_messages_and_services(proto_file)
    
    print(f"Total messages: {len(definitions['messages'])}")
    print(f"Total services: {len(definitions['services'])}")
    print(f"Total enums: {len(definitions['enums'])}")
    print()
    
    # Categorize messages
    categories = categorize_messages(definitions['messages'])
    
    print("=== Message Categorization ===")
    for category, messages in categories.items():
        if messages:
            print(f"\n{category.upper()} ({len(messages)} messages):")
            for msg in sorted(messages):
                print(f"  - {msg}")
    
    print()
    print("=== Splitting Strategy ===")
    
    # Suggest file splits
    file_splits = {
        'tracklab_core.proto': ['core'],
        'tracklab_run.proto': ['run_management'],
        'tracklab_data.proto': ['data_logging'],
        'tracklab_artifacts.proto': ['artifacts'],
        'tracklab_config.proto': ['config'],
        'tracklab_communication.proto': ['communication'],
        'tracklab_files.proto': ['files'],
        'tracklab_system.proto': ['system', 'alerts', 'misc']
    }
    
    for filename, cats in file_splits.items():
        total_messages = sum(len(categories[cat]) for cat in cats)
        print(f"\n{filename}: {total_messages} messages")
        for cat in cats:
            if categories[cat]:
                print(f"  - {cat}: {len(categories[cat])} messages")
    
    print()
    print("=== Services and Enums ===")
    if definitions['services']:
        print(f"Services: {', '.join(definitions['services'])}")
    if definitions['enums']:
        print(f"Enums: {', '.join(definitions['enums'])}")


if __name__ == "__main__":
    main()