# Security Policy

## Reporting a Vulnerability

Please report all vulnerabilities by creating an issue on our GitHub repository at https://github.com/tracklab/tracklab/issues or contact the maintainers directly.

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Considerations

TrackLab is designed for local use only and does not transmit data to external servers. However, please be aware of the following:

- The local web interface runs on localhost and should not be exposed to external networks
- Experiment data is stored locally in SQLite databases
- File artifacts are stored in the local filesystem
- No authentication is required for the local interface by design
