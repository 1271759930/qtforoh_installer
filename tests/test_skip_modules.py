#!/usr/bin/env python3
"""
Test script for skip module configuration refactoring.
Tests the separation of SKIP_MODULES (Qt modules) from SKIP_MAKE_TARGETS (configure flags).

Key tests:
1. "doc" is NOT in skip module lists (it's a make target)
2. "doc" IS in SKIP_MAKE_TARGETS
3. "qtqa" and "qtrepotools" are in QT512_AVAILABLE_MODULES
4. Module counts are consistent when entering/exiting modification page
5. InstallConfig has nomake_targets field
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

from rich.console import Console

console = Console()


def test_doc_not_in_skip_modules():
    """Test that 'doc' is NOT in skip module lists (it's a make target)"""
    console.print("\n[bold cyan]Test: 'doc' NOT in skip module lists[/bold cyan]")
    
    from src.config.defaults import QT512_SKIP_MODULES, QT515_SKIP_MODULES
    
    # 'doc' should NOT be in either skip module list
    if "doc" in QT512_SKIP_MODULES:
        console.print("[red]✗ FAILED: 'doc' is in QT512_SKIP_MODULES (should be in make targets only)[/red]")
        return False
    
    if "doc" in QT515_SKIP_MODULES:
        console.print("[red]✗ FAILED: 'doc' is in QT515_SKIP_MODULES (should be in make targets only)[/red]")
        return False
    
    console.print("[green]✓ PASSED: 'doc' is NOT in skip module lists[/green]")
    return True


def test_doc_in_make_targets():
    """Test that 'doc' IS in SKIP_MAKE_TARGETS"""
    console.print("\n[bold cyan]Test: 'doc' in SKIP_MAKE_TARGETS[/bold cyan]")
    
    from src.config.defaults import SKIP_MAKE_TARGETS
    
    if "doc" not in SKIP_MAKE_TARGETS:
        console.print("[red]✗ FAILED: 'doc' is NOT in SKIP_MAKE_TARGETS[/red]")
        return False
    
    console.print(f"[green]✓ PASSED: 'doc' is in SKIP_MAKE_TARGETS = {SKIP_MAKE_TARGETS}[/green]")
    return True


def test_qtqa_qtrepotools_in_qt512():
    """Test that 'qtqa' and 'qtrepotools' are in QT512_AVAILABLE_MODULES"""
    console.print("\n[bold cyan]Test: 'qtqa' and 'qtrepotools' in QT512_AVAILABLE_MODULES[/bold cyan]")
    
    from src.config.defaults import QT512_AVAILABLE_MODULES
    
    missing = []
    if "qtqa" not in QT512_AVAILABLE_MODULES:
        missing.append("qtqa")
    if "qtrepotools" not in QT512_AVAILABLE_MODULES:
        missing.append("qtrepotools")
    
    if missing:
        console.print(f"[red]✗ FAILED: {missing} are NOT in QT512_AVAILABLE_MODULES[/red]")
        return False
    
    console.print("[green]✓ PASSED: 'qtqa' and 'qtrepotools' are in QT512_AVAILABLE_MODULES[/green]")
    return True


def test_skip_module_counts():
    """Test skip module counts match expected values"""
    console.print("\n[bold cyan]Test: Skip module counts[/bold cyan]")
    
    from src.config.defaults import QT512_SKIP_MODULES, QT515_SKIP_MODULES
    
    # Expected counts (after removing 'doc')
    qt512_expected = 36  # 37 - 1 (doc removed)
    qt515_expected = 26  # 27 - 1 (doc removed)
    
    qt512_actual = len(QT512_SKIP_MODULES)
    qt515_actual = len(QT515_SKIP_MODULES)
    
    console.print(f"  QT512_SKIP_MODULES: {qt512_actual} modules (expected: {qt512_expected})")
    console.print(f"  QT515_SKIP_MODULES: {qt515_actual} modules (expected: {qt515_expected})")
    
    if qt512_actual != qt512_expected:
        console.print(f"[red]✗ FAILED: QT512 count mismatch[/red]")
        return False
    
    if qt515_actual != qt515_expected:
        console.print(f"[red]✗ FAILED: QT515 count mismatch[/red]")
        return False
    
    console.print("[green]✓ PASSED: Skip module counts are correct[/green]")
    return True


def test_nomake_targets_field():
    """Test InstallConfig has nomake_targets field"""
    console.print("\n[bold cyan]Test: InstallConfig nomake_targets field[/bold cyan]")
    
    from src.config.schema import InstallConfig
    
    # Check if nomake_targets is a valid field
    config = InstallConfig(
        qt_source_path=Path("/tmp/qt"),
        harmony_sdk_path=Path("/tmp/sdk"),
        install_path=Path("/tmp/install"),
    )
    
    if not hasattr(config, 'nomake_targets'):
        console.print("[red]✗ FAILED: InstallConfig missing 'nomake_targets' field[/red]")
        return False
    
    # Check default value
    default_nomake = config.nomake_targets
    if "doc" not in default_nomake:
        console.print(f"[red]✗ FAILED: Default nomake_targets doesn't contain 'doc': {default_nomake}[/red]")
        return False
    
    console.print(f"[green]✓ PASSED: InstallConfig has nomake_targets = {default_nomake}[/green]")
    return True


def test_config_serialization():
    """Test InstallConfig serialization with nomake_targets"""
    console.print("\n[bold cyan]Test: InstallConfig serialization[/bold cyan]")
    
    from src.config.schema import InstallConfig
    
    config = InstallConfig(
        qt_source_path=Path("/tmp/qt"),
        harmony_sdk_path=Path("/tmp/sdk"),
        install_path=Path("/tmp/install"),
        skip_modules=["qt3d", "qtwebengine"],
        nomake_targets=["doc", "examples"],
    )
    
    # Test to_dict
    data = config.to_dict()
    if "nomake_targets" not in data:
        console.print("[red]✗ FAILED: to_dict() missing 'nomake_targets'[/red]")
        return False
    
    if data["nomake_targets"] != ["doc", "examples"]:
        console.print(f"[red]✗ FAILED: to_dict() nomake_targets mismatch: {data['nomake_targets']}[/red]")
        return False
    
    # Test from_dict
    config2 = InstallConfig.from_dict(data)
    if config2.nomake_targets != ["doc", "examples"]:
        console.print(f"[red]✗ FAILED: from_dict() nomake_targets mismatch: {config2.nomake_targets}[/red]")
        return False
    
    console.print("[green]✓ PASSED: InstallConfig serialization works correctly[/green]")
    return True


def test_get_default_nomake_targets():
    """Test get_default_nomake_targets() function"""
    console.print("\n[bold cyan]Test: get_default_nomake_targets() function[/bold cyan]")
    
    from src.config.defaults import get_default_nomake_targets
    
    # Test for both Qt versions
    qt512_targets = get_default_nomake_targets("5.12.12")
    qt515_targets = get_default_nomake_targets("5.15.16")
    
    # Both should include 'doc'
    if "doc" not in qt512_targets:
        console.print(f"[red]✗ FAILED: Qt 5.12 targets missing 'doc': {qt512_targets}[/red]")
        return False
    
    if "doc" not in qt515_targets:
        console.print(f"[red]✗ FAILED: Qt 5.15 targets missing 'doc': {qt515_targets}[/red]")
        return False
    
    console.print(f"[green]✓ PASSED: get_default_nomake_targets() works[/green]")
    console.print(f"  Qt 5.12: {qt512_targets}")
    console.print(f"  Qt 5.15: {qt515_targets}")
    return True


def test_skip_modules_only_contain_modules():
    """Test that skip module lists only contain actual Qt modules (no make targets)"""
    console.print("\n[bold cyan]Test: Skip modules only contain Qt modules[/bold cyan]")
    
    from src.config.defaults import (
        QT512_SKIP_MODULES, 
        QT515_SKIP_MODULES,
        SKIP_MAKE_TARGETS,
        QT512_AVAILABLE_MODULES,
        QT515_AVAILABLE_MODULES,
    )
    
    # All skip modules should be in available modules
    qt512_invalid = [m for m in QT512_SKIP_MODULES if m not in QT512_AVAILABLE_MODULES]
    qt515_invalid = [m for m in QT515_SKIP_MODULES if m not in QT515_AVAILABLE_MODULES]
    
    # Make targets should NOT be in skip modules
    qt512_make_targets = [m for m in QT512_SKIP_MODULES if m in SKIP_MAKE_TARGETS]
    qt515_make_targets = [m for m in QT515_SKIP_MODULES if m in SKIP_MAKE_TARGETS]
    
    issues = []
    if qt512_invalid:
        issues.append(f"Qt 5.12 has non-module items: {qt512_invalid}")
    if qt515_invalid:
        issues.append(f"Qt 5.15 has non-module items: {qt515_invalid}")
    if qt512_make_targets:
        issues.append(f"Qt 5.12 contains make targets: {qt512_make_targets}")
    if qt515_make_targets:
        issues.append(f"Qt 5.15 contains make targets: {qt515_make_targets}")
    
    if issues:
        for issue in issues:
            console.print(f"[red]  {issue}[/red]")
        console.print("[red]✗ FAILED: Skip modules contain invalid items[/red]")
        return False
    
    console.print("[green]✓ PASSED: Skip modules only contain actual Qt modules[/green]")
    return True


def test_consistency_after_ui_entry():
    """
    Test that module counts remain consistent after entering/exiting modification page.
    This simulates the original bug scenario.
    """
    console.print("\n[bold cyan]Test: Consistency after UI entry (bug fix verification)[/bold cyan]")
    
    from src.config.defaults import (
        QT512_SKIP_MODULES,
        QT515_SKIP_MODULES,
        SKIP_MAKE_TARGETS,
        QT512_AVAILABLE_MODULES,
        QT515_AVAILABLE_MODULES,
        get_default_skip_modules,
        get_default_nomake_targets,
    )
    
    # Scenario: User selects Qt 5.12 version
    version = "5.12.12"
    initial_skip = get_default_skip_modules(version)
    initial_nomake = get_default_nomake_targets(version)
    
    console.print(f"  Initial skip_modules: {len(initial_skip)} modules")
    console.print(f"  Initial nomake_targets: {initial_nomake}")
    
    # Simulate "entering modification page" - filter by available modules
    # (This is what collect_skip_modules() does)
    available_modules = QT512_AVAILABLE_MODULES
    
    # Filter skip_modules by available (as UI would do)
    filtered_skip = [m for m in initial_skip if m in available_modules]
    
    console.print(f"  After UI filtering: {len(filtered_skip)} modules")
    
    # The count should remain the same because all skip modules are in available modules
    if len(filtered_skip) != len(initial_skip):
        console.print(f"[red]✗ FAILED: Module count changed from {len(initial_skip)} to {len(filtered_skip)}[/red]")
        console.print(f"[red]  Lost modules: {[m for m in initial_skip if m not in available_modules]}[/red]")
        return False
    
    # Verify that nomake_targets are separate and not affected
    if "doc" in filtered_skip:
        console.print("[red]✗ FAILED: 'doc' leaked into skip_modules[/red]")
        return False
    
    if "doc" not in initial_nomake:
        console.print("[red]✗ FAILED: 'doc' missing from nomake_targets[/red]")
        return False
    
    console.print("[green]✓ PASSED: Module counts remain consistent[/green]")
    console.print("[green]  Bug fix verified: 'doc' is handled separately as make target[/green]")
    return True


def main():
    """Run all tests"""
    console.print("=" * 60)
    console.print("[bold cyan]Skip Module Configuration Tests[/bold cyan]")
    console.print("=" * 60)
    
    tests = [
        ("'doc' NOT in skip modules", test_doc_not_in_skip_modules),
        ("'doc' in make targets", test_doc_in_make_targets),
        ("qtqa/qtrepotools in QT512 modules", test_qtqa_qtrepotools_in_qt512),
        ("Skip module counts", test_skip_module_counts),
        ("InstallConfig nomake_targets field", test_nomake_targets_field),
        ("Config serialization", test_config_serialization),
        ("get_default_nomake_targets()", test_get_default_nomake_targets),
        ("Skip modules only contain modules", test_skip_modules_only_contain_modules),
        ("Bug fix verification", test_consistency_after_ui_entry),
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
    
    if failed == 0:
        console.print("\n[bold green]All tests passed! Bug fix verified.[/bold green]")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)