#!/usr/bin/env python3
"""
Test bundled tools detection and environment setup
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

console = Console()


def test_bundled_tools_constants():
    """Test that bundled tools constants are defined correctly"""
    console.print("\n[bold cyan]Testing bundled tools constants...[/bold cyan]")

    from src.tools.downloader import (
        BUNDLED_TOOLS_DIR,
        BUNDLED_LLVM_MINGW_DIR,
        BUNDLED_PERL_DIR,
    )
    from src.builder.env_setup import (
        BUNDLED_TOOLS_DIR as ENV_BUNDLED_TOOLS_DIR,
        BUNDLED_LLVM_MINGW_DIR as ENV_BUNDLED_LLVM_MINGW_DIR,
        BUNDLED_PERL_DIR as ENV_BUNDLED_PERL_DIR,
    )
    from src.utils import (
        BUNDLED_TOOLS_DIR as UTIL_BUNDLED_TOOLS_DIR,
        BUNDLED_LLVM_MINGW_DIR as UTIL_BUNDLED_LLVM_MINGW_DIR,
        BUNDLED_PERL_DIR as UTIL_BUNDLED_PERL_DIR,
    )

    project_root = Path(__file__).parent.parent
    expected_tools_dir = project_root / "tools"

    # Check all constants point to same location
    if BUNDLED_TOOLS_DIR == expected_tools_dir:
        console.print(f"[green]✓ downloader BUNDLED_TOOLS_DIR: {BUNDLED_TOOLS_DIR}[/green]")
    else:
        console.print(f"[red]✗ downloader BUNDLED_TOOLS_DIR mismatch[/red]")
        return False

    if ENV_BUNDLED_TOOLS_DIR == expected_tools_dir:
        console.print(f"[green]✓ env_setup BUNDLED_TOOLS_DIR: {ENV_BUNDLED_TOOLS_DIR}[/green]")
    else:
        console.print(f"[red]✗ env_setup BUNDLED_TOOLS_DIR mismatch[/red]")
        return False

    if UTIL_BUNDLED_TOOLS_DIR == expected_tools_dir:
        console.print(f"[green]✓ utils BUNDLED_TOOLS_DIR: {UTIL_BUNDLED_TOOLS_DIR}[/green]")
    else:
        console.print(f"[red]✗ utils BUNDLED_TOOLS_DIR mismatch[/red]")
        return False

    return True


def test_downloader_bundled_detection():
    """Test ToolDownloader bundled tools detection"""
    console.print("\n[bold cyan]Testing ToolDownloader bundled detection...[/bold cyan]")

    from src.config import ToolConfig
    from src.tools import ToolDownloader
    from src.utils import is_windows

    tools_dir = Path("tools")
    config = ToolConfig()
    downloader = ToolDownloader(tools_dir, config)

    # Check bundled paths are set
    if downloader.bundled_mingw_bin.exists():
        console.print(f"[green]✓ bundled_mingw_bin exists: {downloader.bundled_mingw_bin}[/green]")
    else:
        console.print(f"[yellow]⚠ bundled_mingw_bin not found (tools not downloaded yet)[/yellow]")

    if downloader.bundled_perl_bin.exists():
        console.print(f"[green]✓ bundled_perl_bin exists: {downloader.bundled_perl_bin}[/green]")
    else:
        console.print(f"[yellow]⚠ bundled_perl_bin not found (tools not downloaded yet)[/yellow]")

    # Test get methods
    make_cmd = downloader.get_make_command()
    perl_cmd = downloader.get_perl_command()

    console.print(f"  make command: {make_cmd or 'Not available'}")
    console.print(f"  perl command: {perl_cmd or 'Not available'}")

    # Test bundled path getters
    mingw_path = downloader.get_bundled_mingw_path()
    perl_path = downloader.get_bundled_perl_path()

    console.print(f"  bundled mingw path: {mingw_path or 'Not available'}")
    console.print(f"  bundled perl path: {perl_path or 'Not available'}")

    console.print("[green]✓ ToolDownloader bundled detection methods work[/green]")
    return True


def test_utils_check_functions():
    """Test utils check_llvm_mingw and check_perl functions"""
    console.print("\n[bold cyan]Testing utils check functions...[/bold cyan]")

    from src.utils import check_llvm_mingw, check_perl

    # These functions should return proper tuples
    mingw_valid, mingw_msg, mingw_hint = check_llvm_mingw()
    perl_valid, perl_msg, perl_hint = check_perl()

    console.print(f"  llvm-mingw: valid={mingw_valid}, msg='{mingw_msg}'")
    console.print(f"  perl: valid={perl_valid}, msg='{perl_msg}'")

    # Check hints suggest download_tools.py when tools not found
    if not mingw_valid:
        if "download_tools.py" in mingw_hint or "scripts/download_tools.py" in mingw_hint:
            console.print("[green]✓ llvm-mingw hint suggests download_tools.py[/green]")
        else:
            console.print(f"[yellow]⚠ llvm-mingw hint: {mingw_hint}[/yellow]")

    if not perl_valid:
        if "download_tools.py" in perl_hint or "scripts/download_tools.py" in perl_hint:
            console.print("[green]✓ perl hint suggests download_tools.py[/green]")
        else:
            console.print(f"[yellow]⚠ perl hint: {perl_hint}[/yellow]")

    console.print("[green]✓ utils check functions work[/green]")
    return True


def test_env_setup_bundled_paths():
    """Test EnvironmentManager bundled paths initialization"""
    console.print("\n[bold cyan]Testing EnvironmentManager bundled paths...[/bold cyan]")

    from src.config import InstallConfig
    from src.builder.env_setup import EnvironmentManager

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

    env_manager = EnvironmentManager(config)

    # Check bundled paths are set
    console.print(f"  bundled_mingw_bin: {env_manager.bundled_mingw_bin}")
    console.print(f"  bundled_perl_bin: {env_manager.bundled_perl_bin}")
    console.print(f"  bundled_perl_bin_alt: {env_manager.bundled_perl_bin_alt}")

    console.print("[green]✓ EnvironmentManager bundled paths initialized[/green]")
    return True


def test_download_tools_script_exists():
    """Test that download_tools.py script exists"""
    console.print("\n[bold cyan]Testing download_tools.py script...[/bold cyan]")

    script_path = Path(__file__).parent.parent / "scripts" / "download_tools.py"

    if script_path.exists():
        console.print(f"[green]✓ download_tools.py exists: {script_path}[/green]")

        # Check script has required functions
        import importlib.util
        spec = importlib.util.spec_from_file_location("download_tools", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        required_funcs = ['extract_zip', 'download_file', 'extract_llvm_mingw', 'extract_perl', 'verify_tools', 'main']
        for func in required_funcs:
            if hasattr(module, func):
                console.print(f"[green]  ✓ {func} defined[/green]")
            else:
                console.print(f"[red]  ✗ {func} missing[/red]")
                return False

        return True
    else:
        console.print(f"[red]✗ download_tools.py not found[/red]")
        return False


def main():
    """Run all tests"""
    console.print("=" * 60)
    console.print("[bold cyan]Bundled Tools Integration Tests[/bold cyan]")
    console.print("=" * 60)

    tests = [
        ("Bundled tools constants", test_bundled_tools_constants),
        ("ToolDownloader bundled detection", test_downloader_bundled_detection),
        ("Utils check functions", test_utils_check_functions),
        ("EnvironmentManager bundled paths", test_env_setup_bundled_paths),
        ("download_tools.py script", test_download_tools_script_exists),
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