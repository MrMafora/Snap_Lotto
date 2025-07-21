#!/bin/bash
# Script to fix the pyee package installation issue

echo "Fixing pyee package installation..."

# Uninstall any existing pyee installation
pip uninstall pyee -y 2>/dev/null || true

# Force reinstall without dependencies to avoid RECORD file issues
pip install --force-reinstall --no-deps pyee==12.1.1

# Verify installation
python -c "import pyee; print(f'pyee version: {pyee.__version__}')" || {
    echo "pyee installation failed, trying alternative approach..."
    pip install --force-reinstall --no-cache-dir pyee==12.1.1
}

echo "pyee package fix completed."