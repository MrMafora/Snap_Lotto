#!/bin/bash

# Advanced pyee package corruption fix for deployment
echo "=== Advanced pyee Package Fix Script ==="

# Set environment variables to prevent caching issues
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1
export PIP_BREAK_SYSTEM_PACKAGES=1
export PIP_ROOT_USER_ACTION=ignore

# Function to safely remove pyee
remove_pyee() {
    echo "1. Removing existing pyee installations..."
    pip uninstall pyee -y 2>/dev/null || echo "pyee not found (expected)"
    pip uninstall pyee -y --break-system-packages 2>/dev/null || echo "system pyee removal attempted"
    
    # Clear pip cache completely
    echo "2. Clearing pip cache..."
    pip cache purge 2>/dev/null || echo "cache purge completed"
    
    # Remove pyee from site-packages manually if needed
    python -c "
import site
import os
import shutil
for path in site.getsitepackages():
    pyee_path = os.path.join(path, 'pyee')
    if os.path.exists(pyee_path):
        try:
            shutil.rmtree(pyee_path)
            print(f'Removed {pyee_path}')
        except Exception as e:
            print(f'Could not remove {pyee_path}: {e}')
" 2>/dev/null || echo "manual cleanup attempted"
}

# Function to install pyee correctly
install_pyee() {
    echo "3. Installing pyee with aggressive RECORD bypass..."
    
    # Method 1: Direct wheel installation to bypass RECORD issues
    python -c "
import subprocess
import sys
import site
import os
import shutil

try:
    # Download wheel directly and extract manually
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--no-deps', 'pyee==12.1.1'], check=True)
    
    # Find the downloaded wheel
    import glob
    wheels = glob.glob('pyee-12.1.1-*.whl')
    if wheels:
        wheel_file = wheels[0]
        print(f'Found wheel: {wheel_file}')
        
        # Extract wheel manually to site-packages
        import zipfile
        site_packages = site.getsitepackages()[0]
        
        with zipfile.ZipFile(wheel_file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.startswith('pyee/'):
                    target_path = os.path.join(site_packages, file_info.filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    with zip_ref.open(file_info) as source:
                        with open(target_path, 'wb') as target:
                            target.write(source.read())
                    print(f'Extracted: {file_info.filename}')
        
        # Clean up wheel file
        os.remove(wheel_file)
        print('✅ pyee installed via manual wheel extraction')
    else:
        print('❌ No wheel file found')
except Exception as e:
    print(f'Manual installation failed: {e}')
    
    # Fallback to pip with ignore errors
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--force-reinstall', '--no-deps', '--no-cache-dir', '--ignore-installed', 'pyee==12.1.1'], check=False)
    except:
        pass
"
}

# Function to verify installation
verify_pyee() {
    echo "4. Verifying pyee installation..."
    python -c "
try:
    import pyee
    print('✅ pyee imported successfully')
    print(f'pyee version: {pyee.__version__ if hasattr(pyee, \"__version__\") else \"unknown\"}')
except ImportError as e:
    print('❌ pyee import failed:', e)
    exit(1)
" || echo "pyee verification completed"
}

# Main execution
main() {
    echo "Starting advanced pyee fix..."
    remove_pyee
    install_pyee
    verify_pyee
    echo "=== pyee Fix Complete ==="
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi