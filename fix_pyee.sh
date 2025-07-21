#!/bin/bash
# Script to fix the pyee package installation issue with enhanced error handling

echo "=== PYEE Package Fix Script ==="
echo "Applying comprehensive pyee package corruption fix..."

# Step 1: Clear pip cache to prevent corruption issues
echo "1. Clearing pip cache..."
pip cache purge || true

# Step 2: Remove corrupted pyee installation completely
echo "2. Removing corrupted pyee installation..."
pip uninstall pyee -y 2>/dev/null || true

# Step 3: Force clean reinstall with no cache and no dependencies
echo "3. Installing clean pyee==12.1.1..."
pip install --force-reinstall --no-deps --no-cache-dir pyee==12.1.1

# Step 4: Verify installation
echo "4. Verifying pyee installation..."
python -c "
import sys
try:
    import pyee
    print(f'✅ pyee successfully installed - version: {pyee.__version__}')
    print(f'✅ pyee module location: {pyee.__file__}')
except ImportError as e:
    print(f'❌ pyee import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ pyee verification error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ pyee package fix completed successfully!"
else
    echo "❌ pyee package fix failed. Trying alternative approach..."
    pip install --force-reinstall --no-cache-dir --ignore-installed pyee==12.1.1
    python -c "import pyee; print(f'pyee version: {pyee.__version__}')" && echo "✅ Alternative fix successful" || echo "❌ All fix attempts failed"
fi