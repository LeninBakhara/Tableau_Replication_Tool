#!/bin/bash
echo "=================================="
echo " Dashboard Cloning Tool"
echo " by Decision Tree"
echo "=================================="
echo ""

cd "$(dirname "$0")/backend"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Install deps if needed
echo "Checking dependencies..."
pip install -r requirements.txt -q

echo ""
echo "Starting server..."
echo "Open http://localhost:8000 in your browser"
echo ""
echo "Login: lenin.bakhara@decision-tree.com"
echo "Password: Admin@1234"
echo ""
echo "Press Ctrl+C to stop"
echo "----------------------------------"
python3 main.py
