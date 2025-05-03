#!/usr/bin/env python
"""
Run the fix_row2 script with Flask app context.
"""

from main import app
from fix_row2 import direct_import_row2

if __name__ == "__main__":
    print("Running row 2 import fix...")
    with app.app_context():
        if direct_import_row2():
            print("SUCCESS: Row 2 import fix completed!")
        else:
            print("ERROR: Row 2 import fix failed!")