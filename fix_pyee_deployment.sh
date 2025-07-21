#!/bin/bash
# Script to fix pyee package installation issues for deployment

echo "=== Fixing pyee package for deployment ==="

# Step 1: Clear pip cache to avoid corrupted RECORD issues
echo "1. Clearing pip cache..."
pip cache purge

# Step 2: Force uninstall pyee (ignore errors if not installed)
echo "2. Force uninstalling pyee..."
pip uninstall pyee -y 2>/dev/null || echo "pyee not installed, continuing..."

# Step 3: Force reinstall pyee without dependencies and without cache
echo "3. Reinstalling pyee with force reinstall..."
pip install --force-reinstall --no-deps --no-cache-dir pyee==12.1.1

# Step 4: Verify installation
echo "4. Verifying pyee installation..."
python -c "
try:
    import pyee
    print('✓ pyee installed successfully')
    print(f'  Version: {getattr(pyee, \"__version__\", \"version attribute not available\")}')
except ImportError as e:
    print(f'✗ pyee import failed: {e}')
    exit(1)
except Exception as e:
    print(f'✓ pyee imported with warning: {e}')
"

echo "=== pyee fix completed ==="