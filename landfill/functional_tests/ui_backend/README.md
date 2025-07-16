# UI Backend Tests

This directory contains functional tests for the TrackLab UI backend that was refactored from SQLite to LevelDB.

## Test Files

1. **t1_ui_backend_complete.py** - Complete test that creates real LevelDB data and tests all UI backend components including:
   - DatastoreReader functionality
   - DatastoreService with caching
   - File watcher service
   - All data reading operations

2. **t2_ui_backend_api.py** - Tests the FastAPI server and all REST API endpoints with real LevelDB data
   - Creates test LevelDB data
   - Starts UI server
   - Tests all API endpoints

3. **t3_ui_backend_websocket.py** - Tests WebSocket connections for real-time updates

4. **t4_ui_backend_file_watcher.py** - Tests the file watcher service that monitors LevelDB changes

5. **t5_ui_backend_integration.py** - Comprehensive integration test of the entire UI backend stack

## Running Tests

These tests follow the landfill test format with `.yea` configuration files. To run individually:

```bash
cd landfill/functional_tests/ui_backend
python t1_ui_backend_simple.py
```

## Test Coverage

The tests cover:
- LevelDB data reading functionality
- FastAPI REST endpoints
- WebSocket real-time updates
- File system monitoring
- Service layer with caching
- Complete integration scenarios

## Notes

- The UI backend was refactored from a single monolithic `server.py` file to a proper layered architecture
- The backend now reads directly from LevelDB files created by the TrackLab SDK
- Tests ensure compatibility between the SDK's data storage and the UI's data reading