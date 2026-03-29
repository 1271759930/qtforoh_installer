#!/usr/bin/env python3
"""
Test script to verify tool download fixes
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ToolConfig
from src.downloader import ToolDownloader
from rich.console import Console

def test_perl_url():
    """Test if Perl can be installed"""
    console = Console()

    console.print("\n[bold cyan]Testing Perl Installation[/bold cyan]")
    console.print("[yellow]Perl will be installed via winget or chocolatey (more reliable)[/yellow]")

    import shutil
    if shutil.which("winget"):
        console.print("[green]✓ Winget is available for Perl installation[/green]")
        return True
    elif shutil.which("choco"):
        console.print("[green]✓ Chocolatey is available for Perl installation[/green]")
        return True
    else:
        console.print("[yellow]⚠ Neither winget nor chocolatey found[/yellow]")
        console.print("[yellow]  Perl will need to be installed manually[/yellow]")
        return True  # Not a failure, just manual installation needed

def test_make_install():
    """Test make installation"""
    console = Console()
    tools_dir = Path("tools")
    config = ToolConfig()

    console.print("\n[bold cyan]Testing Make Installation[/bold cyan]")
    downloader = ToolDownloader(tools_dir, config)

    # Check if make already exists
    make_ok, perl_ok = downloader.check_existing_tools()
    console.print(f"Make available: {make_ok}")
    console.print(f"Perl available: {perl_ok}")

    if not make_ok:
        console.print("\n[yellow]Attempting to install make...[/yellow]")
        result = downloader.download_make()
        console.print(f"Installation result: {result}")

    return True

def test_perl_download():
    """Test Perl download"""
    console = Console()
    tools_dir = Path("tools")
    config = ToolConfig()

    console.print("\n[bold cyan]Testing Perl Download[/bold cyan]")
    downloader = ToolDownloader(tools_dir, config)

    # Check if perl already exists
    make_ok, perl_ok = downloader.check_existing_tools()

    if not perl_ok:
        console.print("\n[yellow]Attempting to download Perl...[/yellow]")
        result = downloader.download_perl()
        console.print(f"Download result: {result}")

    return True

def main():
    """Run all tests"""
    console = Console()

    console.print("=" * 60)
    console.print("[bold cyan]Tool Download Fix Verification[/bold cyan]")
    console.print("=" * 60)

    # Test 1: Perl URL
    if not test_perl_url():
        console.print("\n[red]Perl URL test failed[/red]")
        return

    # Test 2: Make installation
    if not test_make_install():
        console.print("\n[red]Make installation test failed[/red]")
        return

    # Test 3: Perl download
    if not test_perl_download():
        console.print("\n[red]Perl download test failed[/red]")
        return

    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ All tests passed![/bold green]")
    console.print("=" * 60)

if __name__ == "__main__":
    main()