#!/bin/bash
# Install fonts for certificate generation
apt-get update && apt-get install -y fonts-dejavu-core fonts-liberation || true

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python db_init.py

# Sync data from Google Sheets
python backend/db_refresh.py
