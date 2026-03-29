#!/usr/bin/env python3
"""
Quick start script for Qt HarmonyOS Installer
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the CLI tool"""
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Run the CLI module
    cmd = [sys.executable, "-m", "src.cli"] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)

if __name__ == "__main__":
    main()