# db_refresh.py - Compatibility wrapper for Render build
# Calls the new sync module

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.sync import sync_data

def refresh():
    sync_data()

if __name__ == "__main__":
    refresh()
