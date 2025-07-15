#!/bin/bash

# TrackLab Dependencies Setup Script
# This script sets up all necessary dependencies for TrackLab testing

echo "================================================================"
echo "TrackLab Dependencies Setup"
echo "================================================================"
echo ""

# Function to check if a command was successful
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 - SUCCESS"
    else
        echo "❌ $1 - FAILED"
        exit 1
    fi
}

# Activate tracklab environment
echo "Activating tracklab conda environment..."
source ~/miniconda/bin/activate tracklab
check_success "Conda environment activation"

# Check if cloudpickle is installed
echo ""
echo "Checking cloudpickle installation..."
python -c "import cloudpickle; print('cloudpickle version:', cloudpickle.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ cloudpickle - ALREADY INSTALLED"
else
    echo "Installing cloudpickle..."
    pip install cloudpickle
    check_success "cloudpickle installation"
fi

# Check if torch is installed
echo ""
echo "Checking PyTorch installation..."
python -c "import torch; print('PyTorch version:', torch.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ PyTorch - ALREADY INSTALLED"
else
    echo "Installing PyTorch CPU version..."
    echo "This may take several minutes..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    check_success "PyTorch installation"
fi

# Verify installations
echo ""
echo "================================================================"
echo "Verifying installations..."
echo "================================================================"

echo "Testing cloudpickle..."
python -c "import cloudpickle; print('✅ cloudpickle:', cloudpickle.__version__)"
check_success "cloudpickle verification"

echo "Testing PyTorch..."
python -c "import torch; print('✅ PyTorch:', torch.__version__)"
check_success "PyTorch verification"

echo ""
echo "================================================================"
echo "Running TrackLab tests..."
echo "================================================================"

# Test basic TrackLab functionality
echo "Testing TrackLab import..."
python -c "import tracklab; print('✅ TrackLab import successful')"
check_success "TrackLab import test"

# Run a subset of tests to verify everything is working
echo ""
echo "Running core utility tests..."
pytest tests/unit_tests/test_util.py -k "not (app_url or launch_browser)" -v --tb=short -q
check_success "Core utility tests"

echo ""
echo "================================================================"
echo "🎉 TrackLab Dependencies Setup Complete!"
echo "================================================================"
echo ""
echo "Summary of installed dependencies:"
echo "- ✅ cloudpickle (for model serialization)"
echo "- ✅ PyTorch CPU (for machine learning functionality)"
echo "- ✅ TrackLab core modules (all working)"
echo ""
echo "You can now run the full test suite with:"
echo "pytest tests/unit_tests/test_artifacts/test_saved_model.py -v"
echo ""
echo "Or test the complete utility module:"
echo "pytest tests/unit_tests/test_util.py -v"