#!/usr/bin/env python3
"""
Test script to verify interactive input works correctly
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

import questionary
from questionary import Style

# Custom style
custom_style = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
    ("separator", "fg:gray"),
    ("instruction", "fg:gray"),
    ("text", "fg:white"),
])

def test_text_input():
    """Test text input"""
    print("\n=== Testing Text Input ===")
    response = questionary.text(
        "Enter a test path:",
        default="",
        style=custom_style
    ).ask()
    
    if response:
        print(f"You entered: {response}")
        return True
    else:
        print("Input cancelled or empty")
        return False

def test_select_input():
    """Test select input"""
    print("\n=== Testing Select Input ===")
    choice = questionary.select(
        "Select an option:",
        choices=[
            "Option A",
            "Option B",
            "Option C",
        ],
        style=custom_style
    ).ask()
    
    if choice:
        print(f"You selected: {choice}")
        return True
    else:
        print("Selection cancelled")
        return False

def test_confirm_input():
    """Test confirm input"""
    print("\n=== Testing Confirm Input ===")
    confirm = questionary.confirm(
        "Do you want to continue?",
        default=True,
        style=custom_style
    ).ask()
    
    if confirm is not None:
        print(f"Your answer: {confirm}")
        return True
    else:
        print("Confirmation cancelled")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Interactive Input Test")
    print("=" * 60)
    
    try:
        # Test text input
        if not test_text_input():
            print("\nText input test failed or cancelled")
            return
        
        # Test select input
        if not test_select_input():
            print("\nSelect input test failed or cancelled")
            return
        
        # Test confirm input
        if not test_confirm_input():
            print("\nConfirm input test failed or cancelled")
            return
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()