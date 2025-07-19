#!/usr/bin/env python3
"""
Split the large tracklab_internal.proto file into smaller, more manageable modules.
"""

import re
import pathlib
from typing import Dict, List, Set, Tuple


def extract_proto_section(content: str, message_name: str) -> str:
    """Extract a complete message definition from proto content."""
    # Find the message definition
    pattern = rf'^message\s+{re.escape(message_name)}\s*\{{'
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return ""
    
    start_pos = match.start()
    
    # Find the matching closing brace
    brace_count = 0
    pos = match.end() - 1  # Start from the opening brace
    
    while pos < len(content):
        char = content[pos]
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        pos += 1
    
    if brace_count != 0:
        return ""
    
    # Extract the complete message definition
    return content[start_pos:pos+1]


def extract_enum_section(content: str, enum_name: str) -> str:
    """Extract a complete enum definition from proto content."""
    pattern = rf'^enum\s+{re.escape(enum_name)}\s*\{{'
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return ""
    
    start_pos = match.start()
    
    # Find the matching closing brace
    brace_count = 0
    pos = match.end() - 1  # Start from the opening brace
    
    while pos < len(content):
        char = content[pos]
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        pos += 1
    
    if brace_count != 0:
        return ""
    
    return content[start_pos:pos+1]


def create_proto_file(filename: str, package_name: str, messages: List[str], enums: List[str], 
                     original_content: str, proto_dir: pathlib.Path) -> None:
    """Create a new proto file with the specified messages and enums."""
    
    # Start with the basic header
    content = f'''syntax = "proto3";

package {package_name};

import "google/protobuf/empty.proto";
import "google/protobuf/timestamp.proto";
import "tracklab_base.proto";
import "tracklab_telemetry.proto";

option go_package = "core/pkg/service_go_proto";

'''
    
    # Add extracted messages
    for message in messages:
        section = extract_proto_section(original_content, message)
        if section:
            content += section + "\n\n"
    
    # Add extracted enums
    for enum in enums:
        section = extract_enum_section(original_content, enum)
        if section:
            content += section + "\n\n"
    
    # Write to file
    file_path = proto_dir / filename
    with open(file_path, 'w') as f:
        f.write(content.strip() + "\n")
    
    print(f"Created {filename} with {len(messages)} messages and {len(enums)} enums")


def main():
    """Main function to split the proto file."""
    
    # Define the message categories from our analysis
    categories = {
        'core': ['AlertRecord', 'AlertResult', 'AppleInfo', 'ArtifactInfo', 'ArtifactRecord', 
                'ArtifactResult', 'ConfigRecord', 'ConfigResult', 'Control', 'CoreWeaveInfo', 
                'CpuInfo', 'DiskInfo', 'EnvironmentRecord', 'ErrorInfo', 'FileTransferInfoRequest', 
                'FilesRecord', 'FilesResult', 'FinalRecord', 'FooterRecord', 'GitInfo', 
                'GitRepoRecord', 'GpuAmdInfo', 'GpuNvidiaInfo', 'HeaderRecord', 'HistoryRecord', 
                'HistoryResult', 'JobInfoRequest', 'JobInfoResponse', 'LinkArtifactResult', 
                'LocalInfo', 'MemoryInfo', 'MetricControl', 'MetricRecord', 'MetricResult', 
                'OutputRawRecord', 'OutputRawResult', 'OutputRecord', 'OutputResult', 'Record', 
                'Result', 'RunExitRecord', 'RunExitResult', 'RunPreemptingRecord', 'RunPreemptingResult', 
                'RunRecord', 'RunUpdateResult', 'ServerInfoRequest', 'ServerInfoResponse', 
                'SettingsRecord', 'StatsRecord', 'SummaryRecord', 'SummaryRecordRequest', 
                'SummaryResult', 'TBRecord', 'TBResult', 'TPUInfo', 'TelemetryRecordRequest', 
                'TrainiumInfo', 'UseArtifactRecord', 'UseArtifactResult', 'VersionInfo'],
        
        'run_management': ['BranchPoint', 'CheckVersionRequest', 'CheckVersionResponse', 
                          'PollExitRequest', 'PollExitResponse', 'RunFinishWithoutExitRequest', 
                          'RunFinishWithoutExitResponse', 'RunStartRequest', 'RunStartResponse', 
                          'RunStatusRequest', 'RunStatusResponse'],
        
        'data_logging': ['FilePusherStats', 'GetSummaryRequest', 'GetSummaryResponse', 
                        'GetSystemMetricsRequest', 'GetSystemMetricsResponse', 'HistoryAction', 
                        'HistoryItem', 'HistoryStep', 'MetricOptions', 'MetricSummary', 
                        'OperationStats', 'OperationStatsRequest', 'OperationStatsResponse', 
                        'PartialHistoryRequest', 'PartialHistoryResponse', 'SampledHistoryItem', 
                        'SampledHistoryRequest', 'SampledHistoryResponse', 'StatsItem', 
                        'SummaryItem', 'SystemMetricSample', 'SystemMetricsBuffer'],
        
        'artifacts': ['ArtifactManifest', 'ArtifactManifestEntry', 'DownloadArtifactRequest', 
                     'DownloadArtifactResponse', 'LinkArtifactRequest', 'LinkArtifactResponse', 
                     'LogArtifactRequest', 'LogArtifactResponse', 'PartialJobArtifact'],
        
        'config': ['ConfigItem', 'SettingsItem', 'StoragePolicyConfigItem'],
        
        'communication': ['AttachRequest', 'AttachResponse', 'CancelRequest', 'CancelResponse', 
                         'DeferRequest', 'HttpResponse', 'InternalMessagesRequest', 
                         'InternalMessagesResponse', 'JobInputRequest', 'KeepaliveRequest', 
                         'KeepaliveResponse', 'LoginRequest', 'LoginResponse', 'NetworkStatusRequest', 
                         'NetworkStatusResponse', 'PauseRequest', 'PauseResponse', 
                         'PythonPackagesRequest', 'Request', 'Response', 'ResumeRequest', 
                         'ResumeResponse', 'SenderMarkRequest', 'SenderReadRequest', 
                         'ServerFeatureItem', 'ServerFeatureRequest', 'ServerFeatureResponse', 
                         'ServerMessage', 'ServerMessages', 'ShutdownRequest', 'ShutdownResponse', 
                         'StatusReportRequest', 'StatusRequest', 'StatusResponse', 
                         'StopStatusRequest', 'StopStatusResponse', 'SyncFinishRequest', 
                         'SyncResponse', 'TestInjectRequest', 'TestInjectResponse'],
        
        'files': ['FilesItem', 'FilesUploaded'],
        
        'system': ['GitSource', 'ExtraItem', 'FileCounts', 'ImageSource', 'InternalMessages', 
                  'JobInputPath', 'JobInputSource', 'JobSource', 'Operation', 'Source']
    }
    
    # File mapping
    file_mapping = {
        'tracklab_core.proto': ['core'],
        'tracklab_run.proto': ['run_management'],
        'tracklab_data.proto': ['data_logging'],
        'tracklab_artifacts.proto': ['artifacts'],
        'tracklab_config.proto': ['config'],
        'tracklab_communication.proto': ['communication'],
        'tracklab_files.proto': ['files'],
        'tracklab_system.proto': ['system']
    }
    
    # Read the original file
    original_file = pathlib.Path("/home/wzh/tracklab/tracklab/proto/tracklab_internal.proto")
    with open(original_file, 'r') as f:
        original_content = f.read()
    
    # Create proto modules directory
    proto_dir = pathlib.Path("/home/wzh/tracklab/tracklab/proto/modules")
    proto_dir.mkdir(exist_ok=True)
    
    print("=== Creating Modular Proto Files ===")
    
    # Create each file
    for filename, cats in file_mapping.items():
        messages = []
        for cat in cats:
            messages.extend(categories[cat])
        
        # Package name based on filename
        package_name = filename.replace('.proto', '').replace('tracklab_', 'tracklab_')
        
        # Add ServerFeature enum to communication module
        enums = ['ServerFeature'] if 'communication' in cats else []
        
        create_proto_file(filename, package_name, messages, enums, original_content, proto_dir)
    
    print()
    print("=== Summary ===")
    print(f"Split {len(sum(categories.values(), []))} messages into {len(file_mapping)} files")
    print(f"Created files in: {proto_dir}")
    print()
    print("Next steps:")
    print("1. Update the Rust build script to use these new proto files")
    print("2. Update imports in other proto files if needed")
    print("3. Test the new build process")


if __name__ == "__main__":
    main()