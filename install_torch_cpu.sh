#!/bin/bash

# Install PyTorch CPU version for TrackLab
# This script installs PyTorch CPU version in the background to avoid blocking the terminal

echo "Starting PyTorch CPU installation in the background..."
echo "This may take several minutes depending on your internet connection."

# Activate the tracklab conda environment and install torch CPU version
{
    source ~/miniconda/bin/activate tracklab
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo "PyTorch CPU installation completed successfully!"
    echo "Installation finished at: $(date)"
} > /tmp/torch_install.log 2>&1 &

# Get the process ID
INSTALL_PID=$!

echo "Installation running in background with PID: $INSTALL_PID"
echo "You can monitor progress with: tail -f /tmp/torch_install.log"
echo "To check if installation is complete: ps -p $INSTALL_PID"
echo ""
echo "Once installation is complete, you can test with:"
echo "source ~/miniconda/bin/activate tracklab && python -c 'import torch; print(\"PyTorch version:\", torch.__version__)'"