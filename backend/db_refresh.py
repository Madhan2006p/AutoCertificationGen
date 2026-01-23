# db_refresh.py - Compatibility wrapper for Render build
# Calls the new sync module

from backend.sync import sync_data

def refresh():
    sync_data()

if __name__ == "__main__":
    refresh()
