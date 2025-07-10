# Legacy Compatibility Module

This module provides backward compatibility with older versions of TrackLab and wandb APIs.

## Purpose

The `old` module contains legacy implementations that help users migrate from older versions while maintaining compatibility with existing code.

## Components

- `core.py` - Legacy run and core functionality
- `settings.py` - Legacy settings management  
- `summary.py` - Legacy summary handling

## Usage

```python
from tracklab.old import LegacyRun, LegacySettings, LegacySummary

# Use legacy components for compatibility
run = LegacyRun("my-run")
settings = LegacySettings(learning_rate=0.001)
summary = LegacySummary()
```

## Migration

This module is intended for transitional use. New projects should use the modern TrackLab APIs found in the main modules.