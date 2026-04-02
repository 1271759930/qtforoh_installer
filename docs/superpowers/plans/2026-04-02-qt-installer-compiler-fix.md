# Qt Installer Compiler Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Qt configure to use MinGW/Clang instead of MSVC compiler by adding -platform parameter and improving PATH management.

**Architecture:** Add `-platform win32-g++` to configure command, reset PATH before build to avoid MSVC pollution, add MinGW toolchain download support.

**Tech Stack:** Python 3.12+, Rich for CLI, PyYAML for config, requests for downloads

---

## File Structure

| File | Purpose | Type |
|------|---------|------|
| `src/builder.py` | Qt build commands, add platform parameter | Modify |
| `src/environment.py` | PATH management, add reset functionality | Modify |
| `src/config.py` | Add mingw_path to config dataclass | Modify |
| `src/downloader.py` | Add MinGW download and toolchain validation | Modify |
| `src/interactive.py` | Add MinGW path prompt | Modify |

---

## Task 1: Fix builder.py - Add -platform Parameter

**Files:**
- Modify: `src/builder.py`

- [ ] **Step 1: Add -platform parameter to generate_configure_command()**

Find line 86-97 in `src/builder.py` and modify the `generate_configure_command()` method:

```python
def generate_configure_command(self) -> List[str]:
    """
    Generate configure command for Qt

    Returns:
        Configure command as list of strings
    """
    self.console.print("\n[bold cyan]Generating configure command...[/bold cyan]")

    # Base configure command
    if is_windows():
        qtbase_configure = self.config.qt_source_path / "qtbase" / "configure.bat"
        root_configure = self.config.qt_source_path / "configure.bat"
        if qtbase_configure.exists():
            configure_script = qtbase_configure
            cmd = [str(configure_script), "-top-level"]
        else:
            configure_script = root_configure
            cmd = [str(configure_script)]
    else:
        configure_script = self.config.qt_source_path / "configure"
        cmd = [str(configure_script)]

    # Add common options
    cmd.extend([
        "-v",  # Verbose output
        "-xplatform", "ohos-clang",  # Target platform
    ])

    # CRITICAL: Specify host platform to use MinGW for building host tools
    if is_windows():
        cmd.extend(["-platform", "win32-g++"])

    cmd.extend([
        "-opensource",
        "-confirm-license",
        "-no-use-gold-linker",
        "-no-gcc-sysroot",
        "-ohos-arch", self.config.architecture,
        "-c++std", "c++14",
        "-nomake", "examples",
        "-nomake", "tests",
    ])

    # Build type
    if self.config.build_type == "debug":
        cmd.append("-debug")
    elif self.config.build_type == "release":
        cmd.append("-release")
    else:  # release-with-debug-info
        cmd.extend(["-release", "-force-debug-info"])

    # Installation prefix
    device_prefix = f"/data/storage/el1/bundle/libs/{self.config.architecture.split('-')[0]}"
    cmd.extend([
        "-prefix", device_prefix,
        "-extprefix", str(self.config.install_path),
    ])

    # Windows-specific options
    if is_windows():
        llvm_dir = self.env_manager.env_vars.get("LLVM_INSTALL_DIR", "")
        if llvm_dir:
            cmd.extend(["-device-option", f"CROSS_COMPILE={llvm_dir}/bin"])

    # Skip modules
    for module in self.config.skip_modules:
        cmd.extend(["-skip", module])

    # No DBus (not available on HarmonyOS)
    cmd.append("-no-dbus")

    # Display command
    self.console.print("\n[bold]Configure command:[/bold]")
    cmd_str = " ".join(cmd)
    self.console.print(Panel(cmd_str, border_style="cyan"))

    return cmd
```

- [ ] **Step 2: Add compiler detection method**

Add this new method to `QtBuilder` class in `src/builder.py` after the `_print_windows_path_check` method:

```python
def _print_compiler_detection(self, env: dict) -> None:
    """
    Print compiler detection info before configure.
    Verify that MinGW gcc is available and MSVC is NOT in PATH.
    """
    self.console.print("\n[bold cyan]Compiler Detection:[/bold cyan]")

    import shutil

    # Check for MSVC (should NOT be found)
    msvc_cl = shutil.which("cl", path=env.get("PATH", ""))
    if msvc_cl:
        self.console.print(f"  [red]⚠ MSVC cl.exe found in PATH: {msvc_cl}[/red]")
        self.console.print("  [yellow]  This may cause build issues![/yellow]")
    else:
        self.console.print("  [green]✓ No MSVC in PATH[/green]")

    # Check for MinGW gcc (SHOULD be found on Windows)
    if is_windows():
        gcc = shutil.which("gcc", path=env.get("PATH", ""))
        if gcc:
            self.console.print(f"  [green]✓ GCC found: {gcc}[/green]")
            # Get version
            try:
                result = run_command([gcc, "--version"], capture_output=True, logger=self.logger)
                if result[0] == 0:
                    version_line = result[1].split('\n')[0]
                    self.console.print(f"    [dim]{version_line}[/dim]")
            except Exception:
                pass
        else:
            self.console.print("  [yellow]⚠ GCC not found in PATH[/yellow]")
            self.console.print("  [yellow]  Host tools may not build correctly[/yellow]")

        gpp = shutil.which("g++", path=env.get("PATH", ""))
        if gpp:
            self.console.print(f"  [green]✓ G++ found: {gpp}[/green]")
        else:
            self.console.print("  [yellow]⚠ G++ not found in PATH[/yellow]")

    # Check for OHOS clang (SHOULD be found)
    clang = shutil.which("clang", path=env.get("PATH", ""))
    if clang:
        self.console.print(f"  [green]✓ Clang found: {clang}[/green]")
    else:
        self.console.print("  [red]✗ Clang not found in PATH[/red]")

    clang_pp = shutil.which("clang++", path=env.get("PATH", ""))
    if clang_pp:
        self.console.print(f"  [green]✓ Clang++ found: {clang_pp}[/green]")
    else:
        self.console.print("  [red]✗ Clang++ not found in PATH[/red]")
```

- [ ] **Step 3: Modify configure_qt to call compiler detection**

Modify the `configure_qt()` method in `src/builder.py` to call the new detection method:

```python
def configure_qt(self) -> Tuple[int, str, str]:
    """
    Run Qt configure

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    self.console.print("\n[bold cyan]Configuring Qt...[/bold cyan]")
    self.logger.info("Starting Qt configuration")

    cmd = self.generate_configure_command()
    env = self.env_manager.get_build_environment()

    # Print compiler detection before configure
    self._print_compiler_detection(env)

    # Print Windows PATH check (existing)
    self._print_windows_path_check(env)

    # Run configure
    exit_code, stdout, stderr = run_command(
        cmd,
        cwd=self.build_dir,
        env=env,
        capture_output=False,
        logger=self.logger
    )

    if exit_code == 0:
        self.console.print("\n[green]✓ Qt configuration completed successfully[/green]")
        self.logger.info("Qt configuration completed successfully")
    else:
        self.console.print(f"\n[red]✗ Qt configuration failed with code: {exit_code}[/red]")
        self.logger.error(f"Qt configuration failed with code: {exit_code}")

    return exit_code, stdout, stderr
```

- [ ] **Step 4: Commit builder.py changes**

```bash
git add src/builder.py
git commit -m "fix: add -platform win32-g++ to configure command and compiler detection

- Add -platform win32-g++ to force MinGW for host tool builds
- Add _print_compiler_detection() to verify compiler setup
- Prevents MSVC from being incorrectly selected"
```

---

## Task 2: Improve environment.py - PATH Reset

**Files:**
- Modify: `src/environment.py`

- [ ] **Step 1: Add import for sys module**

At the top of `src/environment.py`, ensure `sys` is imported:

```python
"""
Environment configuration module
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

from .config import InstallConfig
from .utils import is_windows
```

- [ ] **Step 2: Add reset_path_to_minimum method**

Add this new method to `EnvironmentManager` class after `__init__`:

```python
def reset_path_to_minimum(self) -> None:
    """
    Reset PATH to minimum required paths.
    This prevents system compilers (MSVC) from polluting the build environment.
    """
    if is_windows():
        minimum_paths = [
            "C:\\Windows\\System32",
            "C:\\Windows",
            os.path.dirname(sys.executable)  # Python directory
        ]
        self.env_vars["PATH"] = os.pathsep.join(minimum_paths)
        self.console.print("[cyan]PATH reset to minimum to avoid MSVC pollution[/cyan]")
```

- [ ] **Step 3: Modify _setup_windows_environment to reset PATH first**

Modify the `_setup_windows_environment()` method:

```python
def _setup_windows_environment(self) -> None:
    """Setup Windows-specific environment"""
    # CRITICAL: Reset PATH first to avoid MSVC pollution
    self.reset_path_to_minimum()

    self._set_windows_tool_roots()

    # Build tool paths configured by user (preferred on Windows)
    custom_tool_path = self._build_windows_tool_path()
    if custom_tool_path:
        current_path = self.env_vars.get("PATH", "")
        self.env_vars["PATH"] = f"{custom_tool_path};{current_path}"

    # Add MinGW to PATH if configured
    if self.config.mingw_path:
        mingw_bin = Path(self.config.mingw_path)
        if mingw_bin.is_file():
            mingw_bin = mingw_bin.parent
        if mingw_bin.name.lower() != "bin":
            mingw_bin = mingw_bin / "bin"
        current_path = self.env_vars.get("PATH", "")
        self.env_vars["PATH"] = f"{mingw_bin};{current_path}"
        self.console.print(f"[green]✓ Added MinGW to PATH: {mingw_bin}[/green]")

    # Add LLVM bin to PATH
    llvm_bin = self.config.harmony_sdk_path / "native" / "llvm" / "bin"
    if llvm_bin.exists():
        current_path = self.env_vars.get("PATH", os.environ.get("PATH", ""))
        self.env_vars["PATH"] = f"{llvm_bin};{current_path}"

    # Add Perl to PATH if in tools directory
    perl_bin = Path("tools") / "perl" / "perl" / "bin"
    if perl_bin.exists():
        current_path = self.env_vars.get("PATH", os.environ.get("PATH", ""))
        self.env_vars["PATH"] = f"{perl_bin};{current_path}"
```

- [ ] **Step 4: Commit environment.py changes**

```bash
git add src/environment.py
git commit -m "fix: reset PATH to minimum before build to avoid MSVC pollution

- Add reset_path_to_minimum() method
- Reset PATH before adding tool paths
- Add MinGW path support in _setup_windows_environment"
```

---

## Task 3: Extend config.py - Add MinGW Path

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Add mingw_path field to InstallConfig**

Modify the `InstallConfig` dataclass in `src/config.py`:

```python
@dataclass
class InstallConfig:
    """Installation configuration"""
    qt_source_path: Path
    harmony_sdk_path: Path
    install_path: Path
    architecture: str = "arm64-v8a"
    qt_version: str = "5.15.16"
    build_type: str = "release"
    parallel_jobs: int = 8
    skip_modules: list = field(default_factory=lambda: [
        "qt3d", "qtactiveqt", "qtandroidextras", "qtcanvas3d",
        "qtconnectivity", "qtdatavis3d", "qtdoc", "qtdocgallery",
        "qtfeedback", "qtgamepad", "qtgraphicaleffects", "qtlocation",
        "qtmacextras", "qtnetworkauth", "qtpim", "qtpurchasing",
        "qtqa", "qtremoteobjects", "qtrepotools", "qtscript",
        "qtscxml", "qtsensors", "qtserialbus", "qtserialport",
        "qtspeech", "qtsystems", "qttools", "qttranslations",
        "qtvirtualkeyboard", "qtwayland", "qtwebchannel", "qtwebengine",
        "qtwebglplugin", "qtwebsockets", "qtwebview", "qtwinextras",
        "qtx11extras", "doc"
    ])
    # Tool path configuration (optional)
    make_path: Optional[Path] = None
    perl_path: Optional[Path] = None
    mingw_path: Optional[Path] = None  # NEW: MinGW toolchain path
```

- [ ] **Step 2: Update to_dict method**

Modify `to_dict()` method:

```python
def to_dict(self) -> dict:
    """Convert to dictionary"""
    return {
        "qt_source_path": str(self.qt_source_path),
        "harmony_sdk_path": str(self.harmony_sdk_path),
        "install_path": str(self.install_path),
        "architecture": self.architecture,
        "qt_version": self.qt_version,
        "build_type": self.build_type,
        "parallel_jobs": self.parallel_jobs,
        "skip_modules": self.skip_modules,
        "make_path": str(self.make_path) if self.make_path else None,
        "perl_path": str(self.perl_path) if self.perl_path else None,
        "mingw_path": str(self.mingw_path) if self.mingw_path else None,
    }
```

- [ ] **Step 3: Update from_dict method**

Modify `from_dict()` method:

```python
@classmethod
def from_dict(cls, data: dict) -> "InstallConfig":
    """Create from dictionary"""
    make_path = data.get("make_path")
    perl_path = data.get("perl_path")
    mingw_path = data.get("mingw_path")

    return cls(
        qt_source_path=Path(data["qt_source_path"]),
        harmony_sdk_path=Path(data["harmony_sdk_path"]),
        install_path=Path(data["install_path"]),
        architecture=data.get("architecture", "arm64-v8a"),
        qt_version=data.get("qt_version", "5.15.16"),
        build_type=data.get("build_type", "release"),
        parallel_jobs=data.get("parallel_jobs", 8),
        skip_modules=data.get("skip_modules", []),
        make_path=Path(make_path) if make_path else None,
        perl_path=Path(perl_path) if perl_path else None,
        mingw_path=Path(mingw_path) if mingw_path else None,
    )
```

- [ ] **Step 4: Commit config.py changes**

```bash
git add src/config.py
git commit -m "feat: add mingw_path to InstallConfig

- Add mingw_path field for MinGW toolchain configuration
- Update serialization methods"
```

---

## Task 4: Improve downloader.py - MinGW Download

**Files:**
- Modify: `src/downloader.py`

- [ ] **Step 1: Update ToolDownloader __init__ to accept mingw_path**

Modify `__init__` method:

```python
class ToolDownloader:
    """Download and setup required tools"""

    def __init__(self, tools_dir: Path, tool_config: ToolConfig,
                 make_path: Optional[Path] = None, perl_path: Optional[Path] = None,
                 mingw_path: Optional[Path] = None):
        self.tools_dir = tools_dir
        self.tool_config = tool_config
        self.console = Console()
        self.make_path = tools_dir / "make"
        self.perl_path = tools_dir / "perl"
        self.mingw_path = tools_dir / "mingw"

        # Store configured tool paths
        self.configured_make_path = make_path
        self.configured_perl_path = perl_path
        self.configured_mingw_path = mingw_path

        ensure_directory(self.tools_dir)
        ensure_directory(self.make_path)
        ensure_directory(self.perl_path)
```

- [ ] **Step 2: Add check_mingw method**

Add after `_check_perl` method:

```python
def _check_mingw(self) -> bool:
    """Check if MinGW is available"""
    # First check configured path
    if self.configured_mingw_path and self.configured_mingw_path.exists():
        self.console.print(f"[green]✓ Using configured MinGW: {self.configured_mingw_path}[/green]")
        return True

    # Check if gcc is in PATH
    if shutil.which("gcc"):
        return True

    # Check if mingw32-make is in PATH (indicates MinGW installation)
    if is_windows() and shutil.which("mingw32-make"):
        return True

    # Check if mingw is in tools directory
    if is_windows():
        gcc_exe = self.mingw_path / "bin" / "gcc.exe"
        if gcc_exe.exists():
            return True

    return False
```

- [ ] **Step 3: Add download_mingw method**

Add after `download_perl` method:

```python
def download_mingw(self) -> bool:
    """Download and setup MinGW toolchain"""
    self.console.print("\n[bold cyan]Downloading MinGW Toolchain[/bold cyan]")

    if not is_windows():
        self.console.print(
            "[yellow]MinGW should be available via package manager on Linux/macOS[/yellow]"
        )
        self.console.print("Please install mingw using:")
        self.console.print("  Ubuntu/Debian: sudo apt-get install mingw-w64")
        self.console.print("  macOS: brew install mingw-w64")
        return False

    # MinGW download URL from reference project
    mingw_url = "https://gitcode.com/Li-Yaosong/prebuilt/releases/download/1.0.0/mingw64-x86_64-8.1.0-release-posix-seh-rt_v6-rev0.7z"

    # Try winget first
    if shutil.which("winget"):
        self.console.print("\n[cyan]Checking for MinGW via winget...[/cyan]")
        # Note: winget may not have a direct MinGW package, try MSYS2
        self.console.print("[yellow]winget does not have direct MinGW package[/yellow]")

    # Manual download
    self.console.print("\n[yellow]MinGW download requires manual installation:[/yellow]")
    self.console.print("  Option 1: Download from https://sourceforge.net/projects/mingw-w64/")
    self.console.print("  Option 2: Install MSYS2 which includes MinGW: https://www.msys2.org/")
    self.console.print("  Option 3: Download from reference project mirror:")
    self.console.print(f"    {mingw_url}")

    return False
```

- [ ] **Step 4: Add validate_toolchain method**

Add after `download_mingw` method:

```python
def validate_toolchain(self) -> bool:
    """
    Validate that the complete toolchain is available and working.

    Returns:
        True if all tools are valid, False otherwise
    """
    self.console.print("\n[bold cyan]Validating toolchain...[/bold cyan]")

    all_valid = True

    # Validate make
    make_cmd = self.get_make_command()
    if make_cmd:
        try:
            result = subprocess.run(
                [make_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                self.console.print(f"[green]✓ Make: {version}[/green]")
            else:
                self.console.print("[red]✗ Make found but not working[/red]")
                all_valid = False
        except Exception as e:
            self.console.print(f"[red]✗ Make validation failed: {e}[/red]")
            all_valid = False
    else:
        self.console.print("[red]✗ Make not found[/red]")
        all_valid = False

    # Validate perl
    perl_cmd = self.get_perl_command()
    if perl_cmd:
        try:
            result = subprocess.run(
                [perl_cmd, "-e", "print $^V"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.console.print(f"[green]✓ Perl: {result.stdout.strip()}[/green]")
            else:
                self.console.print("[red]✗ Perl found but not working[/red]")
                all_valid = False
        except Exception as e:
            self.console.print(f"[red]✗ Perl validation failed: {e}[/red]")
            all_valid = False
    else:
        self.console.print("[red]✗ Perl not found[/red]")
        all_valid = False

    # Validate MinGW gcc (Windows only)
    if is_windows():
        gcc = shutil.which("gcc")
        if gcc:
            try:
                result = subprocess.run(
                    [gcc, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0]
                    self.console.print(f"[green]✓ GCC: {version}[/green]")
                else:
                    self.console.print("[yellow]⚠ GCC found but not working[/yellow]")
            except Exception as e:
                self.console.print(f"[yellow]⚠ GCC validation failed: {e}[/yellow]")
        else:
            self.console.print("[yellow]⚠ GCC not found - host tools may not build[/yellow]")

    return all_valid
```

- [ ] **Step 5: Update check_existing_tools to include mingw**

Modify `check_existing_tools` method:

```python
def check_existing_tools(self) -> Tuple[bool, bool, bool]:
    """
    Check if tools are already available

    Returns:
        Tuple of (make_available, perl_available, mingw_available)
    """
    make_available = self._check_make()
    perl_available = self._check_perl()
    mingw_available = self._check_mingw()

    return make_available, perl_available, mingw_available
```

- [ ] **Step 6: Update ensure_tools_available**

Modify `ensure_tools_available` method:

```python
def ensure_tools_available(self) -> Tuple[bool, bool]:
    """
    Ensure all required tools are available

    Returns:
        Tuple of (all_tools_available, mingw_available)
    """
    make_ok, perl_ok, mingw_ok = self.check_existing_tools()

    if make_ok and perl_ok:
        self.console.print("\n[green]✓ All required tools are available[/green]")
        if mingw_ok:
            self.console.print("[green]✓ MinGW toolchain is available[/green]")
        else:
            self.console.print("[yellow]⚠ MinGW not available - host tools may use MSVC[/yellow]")
        return True, mingw_ok

    self.console.print("\n[yellow]Some tools are missing. Downloading...[/yellow]")

    if not make_ok:
        make_ok = self.download_make()

    if not perl_ok:
        perl_ok = self.download_perl()

    if not mingw_ok:
        mingw_ok = self.download_mingw()

    return make_ok and perl_ok, mingw_ok
```

- [ ] **Step 7: Commit downloader.py changes**

```bash
git add src/downloader.py
git commit -m "feat: add MinGW toolchain download and validation support

- Add _check_mingw() method
- Add download_mingw() method with mirror URLs
- Add validate_toolchain() for complete validation
- Update ensure_tools_available() to include MinGW check"
```

---

## Task 5: Improve interactive.py - MinGW Path Prompt

**Files:**
- Modify: `src/interactive.py`

- [ ] **Step 1: Modify prompt_tool_paths to include MinGW**

Modify the `prompt_tool_paths()` method:

```python
def prompt_tool_paths(self) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
    """Prompt for tool paths if already installed"""
    self.console.print("\n[bold cyan]Step 7: Build Tools Configuration[/bold cyan]")
    self.console.print(
        "[yellow]Note: make, perl, and mingw are required for building Qt[/yellow]"
    )

    make_path = None
    perl_path = None
    mingw_path = None

    # Ask about make
    has_make = Confirm.ask(
        "\n[bold]Have you already installed make?[/bold]",
        default=False
    )

    if has_make:
        self.console.print("\n[bold]Please specify make path[/bold]")
        self.console.print("[yellow]You can provide either make executable path or tool root directory[/yellow]")
        self.console.print("[yellow]Example 1: D:\\Tools\\llvm-mingw-xxxx\\bin\\mingw32-make.exe[/yellow]")
        self.console.print("[yellow]Example 2: D:\\Tools\\llvm-mingw-xxxx[/yellow]")

        while True:
            response = Prompt.ask(
                "\n[bold green]Make executable path[/bold green] (or press Enter to skip)"
            )

            if not response.strip():
                self.console.print("[yellow]Skipping make path configuration[/yellow]")
                break

            path = Path(response.strip())
            if path.exists():
                make_path = path
                self.console.print(f"[green]✓ Make path set: {make_path}[/green]")
                break
            else:
                self.console.print(f"[red]✗ Path not found: {path}[/red]")
                retry = Confirm.ask("[bold]Try again?[/bold]", default=True)
                if not retry:
                    break

    # Ask about perl
    has_perl = Confirm.ask(
        "\n[bold]Have you already installed perl?[/bold]",
        default=False
    )

    if has_perl:
        self.console.print("\n[bold]Please specify perl path[/bold]")
        self.console.print("[yellow]You can provide either perl executable path or perl bin directory[/yellow]")
        self.console.print("[yellow]Example 1: C:\\Strawberry\\perl\\bin\\perl.exe[/yellow]")
        self.console.print("[yellow]Example 2: C:\\Strawberry\\perl\\bin[/yellow]")

        while True:
            response = Prompt.ask(
                "\n[bold green]Perl executable path[/bold green] (or press Enter to skip)"
            )

            if not response.strip():
                self.console.print("[yellow]Skipping perl path configuration[/yellow]")
                break

            path = Path(response.strip())
            if path.exists():
                perl_path = path
                self.console.print(f"[green]✓ Perl path set: {perl_path}[/green]")
                break
            else:
                self.console.print(f"[red]✗ Path not found: {path}[/red]")
                retry = Confirm.ask("[bold]Try again?[/bold]", default=True)
                if not retry:
                    break

    # Ask about MinGW
    has_mingw = Confirm.ask(
        "\n[bold]Have you already installed MinGW (GCC for Windows)?[/bold]",
        default=False
    )

    if has_mingw:
        self.console.print("\n[bold]Please specify MinGW path[/bold]")
        self.console.print("[yellow]You can provide either the MinGW root directory or bin directory[/yellow]")
        self.console.print("[yellow]Example 1: D:\\Tools\\mingw64\\bin\\gcc.exe[/yellow]")
        self.console.print("[yellow]Example 2: D:\\Tools\\mingw64[/yellow]")

        while True:
            response = Prompt.ask(
                "\n[bold green]MinGW path[/bold green] (or press Enter to skip)"
            )

            if not response.strip():
                self.console.print("[yellow]Skipping MinGW path configuration[/yellow]")
                break

            path = Path(response.strip())
            if path.exists():
                mingw_path = path
                self.console.print(f"[green]✓ MinGW path set: {mingw_path}[/green]")
                break
            else:
                self.console.print(f"[red]✗ Path not found: {path}[/red]")
                retry = Confirm.ask("[bold]Try again?[/bold]", default=True)
                if not retry:
                    break

    return make_path, perl_path, mingw_path
```

- [ ] **Step 2: Update confirm_configuration to show mingw_path**

Modify the `confirm_configuration()` method to display mingw_path:

```python
def confirm_configuration(self, config: InstallConfig) -> bool:
    """Display configuration and ask for confirmation"""
    self.console.print("\n" + "=" * 60)
    self.console.print("[bold cyan]Configuration Summary[/bold cyan]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Qt Source Path", str(config.qt_source_path))
    table.add_row("HarmonyOS SDK Path", str(config.harmony_sdk_path))
    table.add_row("Install Path", str(config.install_path))
    table.add_row("Architecture", config.architecture)
    table.add_row("Qt Version", config.qt_version)
    table.add_row("Build Type", config.build_type)
    table.add_row("Parallel Jobs", str(config.parallel_jobs))

    # Show tool paths if configured
    if config.make_path:
        table.add_row("Make Path", str(config.make_path))
    if config.perl_path:
        table.add_row("Perl Path", str(config.perl_path))
    if config.mingw_path:
        table.add_row("MinGW Path", str(config.mingw_path))

    self.console.print(table)

    # Use Rich Confirm
    confirm = Confirm.ask(
        "\n[bold]Proceed with installation?[/bold]",
        default=True
    )

    return confirm
```

- [ ] **Step 3: Update collect_configuration to handle mingw_path**

Modify the `collect_configuration()` method:

```python
def collect_configuration(self) -> InstallConfig:
    """Collect all configuration from user"""
    self.show_welcome()

    # Prompt for paths
    qt_source_path = self.prompt_qt_source_path()
    harmony_sdk_path = self.prompt_harmony_sdk_path()
    install_path = self.prompt_install_path()

    # Prompt for build options
    architecture = self.prompt_architecture()
    build_type = self.prompt_build_type()
    parallel_jobs = self.prompt_parallel_jobs()

    # Prompt for tool paths (now returns 3 values)
    make_path, perl_path, mingw_path = self.prompt_tool_paths()

    # Create configuration
    config = InstallConfig(
        qt_source_path=qt_source_path,
        harmony_sdk_path=harmony_sdk_path,
        install_path=install_path,
        architecture=architecture,
        build_type=build_type,
        parallel_jobs=parallel_jobs,
        make_path=make_path,
        perl_path=perl_path,
        mingw_path=mingw_path
    )

    # Confirm configuration
    if self.confirm_configuration(config):
        return config
    else:
        raise KeyboardInterrupt("Installation cancelled by user")
```

- [ ] **Step 4: Commit interactive.py changes**

```bash
git add src/interactive.py
git commit -m "feat: add MinGW path configuration to interactive prompts

- Update prompt_tool_paths() to include MinGW
- Update confirm_configuration() to display MinGW path
- Update collect_configuration() for 3-value return"
```

---

## Task 6: Update installer.py - Pass MinGW Path

**Files:**
- Modify: `src/installer.py`

- [ ] **Step 1: Update setup_tools to pass mingw_path**

Modify the `setup_tools()` method:

```python
def setup_tools(self) -> bool:
    """
    Setup required tools (make, perl, mingw)

    Returns:
        True if tools setup successful, False otherwise
    """
    self.console.print("\n[bold cyan]Setting up build tools...[/bold cyan]")

    tools_dir = self.workspace / "tools"
    config = self.config_manager.install_config

    # Pass configured tool paths to downloader (now including mingw_path)
    self.downloader = ToolDownloader(
        tools_dir,
        self.config_manager.tool_config,
        make_path=config.make_path if config else None,
        perl_path=config.perl_path if config else None,
        mingw_path=config.mingw_path if config else None
    )

    tools_ok, mingw_ok = self.downloader.ensure_tools_available()

    if tools_ok:
        self.console.print("[green]✓ All tools are ready[/green]")
        if not mingw_ok:
            self.console.print("[yellow]⚠ MinGW not available - configure may use MSVC[/yellow]")
            self.console.print("[yellow]  This may cause build failures![/yellow]")
        return True
    else:
        self.console.print("[red]✗ Some tools are missing[/red]")

        if not mingw_ok:
            self.console.print("  [yellow]MinGW is recommended for building host tools[/yellow]")

        return False
```

- [ ] **Step 2: Commit installer.py changes**

```bash
git add src/installer.py
git commit -m "fix: pass mingw_path to ToolDownloader and handle availability

- Update setup_tools() to pass mingw_path
- Add warning when MinGW is not available"
```

---

## Verification

After all tasks are complete, verify the fix:

1. Run `python -m src.cli check` to validate toolchain
2. Run `python -m src.cli install` and observe configure output
3. Check that configure shows "Platform: win32-g++"
4. Check that configure shows "Xplatform: ohos-clang"
5. Verify Makefile uses clang, not MSVC

---

## Summary

This plan fixes the Qt configure compiler selection issue by:

1. **Adding `-platform win32-g++`** to force MinGW for host tool compilation
2. **Resetting PATH** to avoid MSVC pollution
3. **Adding MinGW support** to the toolchain management
4. **Improving compiler detection** to warn about potential issues

The most critical fix is Task 1 (adding -platform parameter), which directly solves the MSVC selection problem.