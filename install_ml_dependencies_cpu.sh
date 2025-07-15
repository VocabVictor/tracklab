#!/bin/bash

# Install TensorFlow and JAX CPU versions for TrackLab
# This script installs ML dependencies in the background to avoid blocking the terminal

echo "================================================================"
echo "Starting ML Dependencies Installation (CPU versions)"
echo "================================================================"
echo ""
echo "This will install:"
echo "- TensorFlow CPU"
echo "- JAX CPU" 
echo "- Additional dependencies"
echo ""
echo "Starting installation in the background..."

# Create log file
LOG_FILE="/tmp/ml_dependencies_install.log"

# Activate the tracklab conda environment and install dependencies
{
    echo "Starting ML dependencies installation at: $(date)"
    echo "================================================================"
    
    # Activate conda environment
    source ~/miniconda/bin/activate tracklab
    
    # Install TensorFlow CPU version
    echo ""
    echo "Installing TensorFlow CPU..."
    echo "----------------------------------------------------------------"
    pip install tensorflow-cpu
    
    # Install JAX CPU version
    echo ""
    echo "Installing JAX CPU..."
    echo "----------------------------------------------------------------"
    # For CPU-only JAX, we need to set the environment variable
    pip install --upgrade "jax[cpu]"
    
    # Verify installations
    echo ""
    echo "================================================================"
    echo "Verifying installations..."
    echo "================================================================"
    
    # Test TensorFlow
    echo "Testing TensorFlow..."
    python -c "import tensorflow as tf; print('✅ TensorFlow version:', tf.__version__)"
    
    # Test JAX
    echo "Testing JAX..."
    python -c "import jax; print('✅ JAX version:', jax.__version__)"
    python -c "import jax.numpy as jnp; print('✅ JAX numpy available')"
    
    echo ""
    echo "================================================================"
    echo "ML Dependencies installation completed successfully!"
    echo "Installation finished at: $(date)"
    echo "================================================================"
    
} > "$LOG_FILE" 2>&1 &

# Get the process ID
INSTALL_PID=$!

echo "Installation running in background with PID: $INSTALL_PID"
echo "Log file: $LOG_FILE"
echo ""
echo "You can monitor progress with: tail -f $LOG_FILE"
echo "To check if installation is complete: ps -p $INSTALL_PID"
echo ""
echo "Once installation is complete, you can test with:"
echo "source ~/miniconda/bin/activate tracklab"
echo "python -c 'import tensorflow as tf; print(\"TensorFlow:\", tf.__version__)'"
echo "python -c 'import jax; print(\"JAX:\", jax.__version__)'"