#!/bin/bash
# Quick setup script for Linux/macOS

echo "========================================"
echo "Qt for HarmonyOS Installer Setup"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed"
    echo "Please install Python 3.12 or later"
    exit 1
fi

echo "[OK] Python found"
python3 --version

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 is not available"
    echo "Please ensure pip is installed with Python"
    exit 1
fi

echo "[OK] pip found"
pip3 --version

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo "[OK] Dependencies installed"

# Install the tool
echo ""
echo "Installing qtohos-installer..."
pip3 install -e .

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install qtohos-installer"
    exit 1
fi

echo "[OK] qtohos-installer installed"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "You can now run:"
echo "  qtohos-installer install    - Start interactive installation"
echo "  qtohos-installer check      - Check prerequisites"
echo "  qtohos-installer guide      - Show installation guide"
echo "  qtohos-installer --help     - Show all commands"
echo ""