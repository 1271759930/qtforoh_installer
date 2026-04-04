#!/usr/bin/env python3
"""
Test script for UI module (non-interactive tests)
"""

import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import InstallConfig
from src.ui import Display, ConfigCollector
from rich.console import Console


def test_display():
    """Test Display class"""
    console = Console()
    console.print("\n[bold cyan]Testing Display class...[/bold cyan]")

    display = Display()

    # Test simple output
    display.show_success("Test success message")
    display.show_error("Test error message")
    display.show_warning("Test warning message")
    display.show_info("Test info message")

    console.print("[green]✓ Display output methods work[/green]")
    return True


def test_display_config_summary():
    """Test config summary display"""
    console = Console()
    console.print("\n[bold cyan]Testing config summary display...[/bold cyan]")

    display = Display()
    config = InstallConfig(
        qt_source_path=Path("/tmp/qt"),
        harmony_sdk_path=Path("/tmp/sdk"),
        install_path=Path("/tmp/install"),
        architecture="arm64-v8a",
        qt_version="5.15.16",
        build_type="release",
        parallel_jobs=8,
        version_source="test"
    )

    display.show_config_summary(config)
    console.print("[green]✓ Config summary display works[/green]")
    return True


def test_collector_creation():
    """Test ConfigCollector creation"""
    console = Console()
    console.print("\n[bold cyan]Testing ConfigCollector creation...[/bold cyan]")

    collector = ConfigCollector()

    console.print("[green]✓ ConfigCollector created[/green]")

    # Check methods exist
    methods = ['collect_qt_source_path', 'collect_harmony_sdk_path',
               'collect_install_path', 'collect_architecture', 'collect_build_type',
               'collect_parallel_jobs', 'collect_tool_paths', 'confirm_configuration',
               'collect_all', 'show_welcome', '_modify_config_menu']

    missing = []
    for method in methods:
        if not hasattr(collector, method):
            missing.append(method)

    if missing:
        console.print(f"[red]✗ Missing methods: {missing}[/red]")
        return False

    console.print(f"[green]✓ All {len(methods)} methods present[/green]")
    return True


def test_questionary_style():
    """Test that questionary is properly configured"""
    console = Console()
    console.print("\n[bold cyan]Testing questionary configuration...[/bold cyan]")

    try:
        from src.ui.prompts import CUSTOM_STYLE
        console.print("[green]✓ CUSTOM_STYLE defined[/green]")
        return True
    except ImportError as e:
        console.print(f"[red]✗ Import error: {e}[/red]")
        return False


def main():
    """Run all tests"""
    console = Console()

    console.print("=" * 60)
    console.print("[bold cyan]UI Module Tests[/bold cyan]")
    console.print("=" * 60)

    tests = [
        ("Display output methods", test_display),
        ("Config summary display", test_display_config_summary),
        ("ConfigCollector creation", test_collector_creation),
        ("Questionary style config", test_questionary_style),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                console.print(f"[red]✗ {name} failed[/red]")
        except Exception as e:
            failed += 1
            console.print(f"[red]✗ {name} error: {e}[/red]")

    console.print("\n" + "=" * 60)
    console.print(f"[bold]Results: {passed} passed, {failed} failed[/bold]")
    console.print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)