"""
Tool downloader module - Supports bundled tools and system tools
"""

import os
import sys
import shutil
import zipfile
import tarfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import requests
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..config import ToolConfig
from ..utils import is_windows, run_command, ensure_directory, format_size

# Bundled tools directory (relative to project root)
BUNDLED_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
BUNDLED_LLVM_MINGW_DIR = BUNDLED_TOOLS_DIR / "llvm-mingw"
BUNDLED_PERL_DIR = BUNDLED_TOOLS_DIR / "perl"


class ToolDownloader:
    """Download and setup required tools - Uses bundled tools"""

    def __init__(self, tools_dir: Path, tool_config: ToolConfig):
        self.tools_dir = tools_dir
        self.tool_config = tool_config
        self.console = Console()

        # Bundled tools paths
        self.bundled_mingw_bin = BUNDLED_LLVM_MINGW_DIR / "bin"
        self.bundled_perl_bin = BUNDLED_PERL_DIR / "perl" / "bin"
        self.bundled_perl_bin_alt = BUNDLED_PERL_DIR / "bin"

        ensure_directory(self.tools_dir)

    def check_existing_tools(self) -> Tuple[bool, bool, bool]:
        """
        Check if tools are already available - Bundled tools first

        Priority:
        1. User configured paths
        2. Bundled tools in project tools/ directory
        3. System PATH

        Returns:
            Tuple of (make_available, perl_available, mingw_available)
        """
        make_available = self._check_make()
        perl_available = self._check_perl()
        mingw_available = self._check_mingw()

        return make_available, perl_available, mingw_available

    def _check_make(self) -> bool:
        """Check if make is available - Bundled tools first"""
        # Check bundled llvm-mingw tools
        if is_windows():
            bundled_make = self.bundled_mingw_bin / "mingw32-make.exe"
            if bundled_make.exists():
                self.console.print(f"[green]✓ Using bundled mingw32-make: {bundled_make}[/green]")
                return True

        # Check if mingw32-make is in PATH (Windows)
        if is_windows() and shutil.which("mingw32-make"):
            return True

        # Check if make is in PATH
        if shutil.which("make"):
            return True

        return False

    def _check_perl(self) -> bool:
        """Check if perl is available - Bundled tools first"""
        # Check bundled Perl tools
        if is_windows():
            bundled_perl = self.bundled_perl_bin / "perl.exe"
            bundled_perl_alt = self.bundled_perl_bin_alt / "perl.exe"
            if bundled_perl.exists():
                self.console.print(f"[green]✓ Using bundled perl: {bundled_perl}[/green]")
                return True
            if bundled_perl_alt.exists():
                self.console.print(f"[green]✓ Using bundled perl: {bundled_perl_alt}[/green]")
                return True

        # Check if perl is in PATH
        if shutil.which("perl"):
            return True

        return False

    def _check_mingw(self) -> bool:
        """Check if MinGW (gcc) is available - Bundled tools first"""
        # Check bundled llvm-mingw first
        if is_windows():
            bundled_gcc = self.bundled_mingw_bin / "gcc.exe"
            if bundled_gcc.exists():
                self.console.print(f"[green]✓ Using bundled gcc: {bundled_gcc}[/green]")
                return True

        # Check if gcc is in PATH
        if shutil.which("gcc"):
            return True

        # Check if mingw32-make is in PATH (indicates MinGW installation)
        if is_windows() and shutil.which("mingw32-make"):
            return True

        return False

    def download_file(
        self,
        url: str,
        target_path: Path,
        description: str = "Downloading"
    ) -> bool:
        """
        Download a file with progress bar

        Args:
            url: Download URL
            target_path: Target file path
            description: Description for progress bar

        Returns:
            True if successful, False otherwise
        """
        try:
            self.console.print(f"\n[cyan]{description}...[/cyan]")
            self.console.print(f"  URL: {url}")
            self.console.print(f"  Target: {target_path}")

            # Send request with stream
            response = requests.get(url, stream=True, allow_redirects=True, timeout=30)
            response.raise_for_status()

            # Get file size
            total_size = int(response.headers.get("content-length", 0))
            if total_size > 0:
                self.console.print(f"  Size: {format_size(total_size)}")

            # Download with progress
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with open(target_path, "wb") as f:
                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=target_path.name
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            self.console.print(f"[green]✓ Download completed: {target_path}[/green]")
            return True

        except requests.RequestException as e:
            self.console.print(f"[red]✗ Download failed: {e}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]✗ Error: {e}[/red]")
            return False

    def download_make(self) -> bool:
        """Download and setup make tool"""
        self.console.print("\n[bold cyan]Downloading Make Tool[/bold cyan]")

        if is_windows():
            return self._download_make_windows()
        else:
            self.console.print(
                "[yellow]Make should be available via package manager on Linux/macOS[/yellow]"
            )
            self.console.print("Please install make using:")
            self.console.print("  Ubuntu/Debian: sudo apt-get install make")
            self.console.print("  macOS: xcode-select --install")
            return False

    def _download_make_windows(self) -> bool:
        """Download make for Windows"""
        # Download mingw32-make
        # We'll use a direct download link for make
        make_url = "https://sourceforge.net/projects/mingw/files/MinGW/make/make-3.82.90/make-3.82.90-2-mingw32-bin.tar.lzma/download"

        # Alternative: use chocolatey or download from a reliable source
        # For simplicity, we'll download from a mirror
        self.console.print(
            "[yellow]Note: Downloading make from SourceForge[/yellow]"
        )
        self.console.print(
            "[yellow]Alternative: Install via chocolatey: choco install make[/yellow]"
        )

        # Try to use winget or chocolatey if available
        if shutil.which("winget"):
            self.console.print("\n[cyan]Installing make via winget...[/cyan]")
            try:
                result = subprocess.run(
                    ["winget", "install", "GnuWin32.Make", "--accept-source-agreements"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'  # 忽略无法解码的字符
                )
                if result.returncode == 0:
                    self.console.print("[green]✓ Make installed successfully via winget[/green]")
                    return True
            except Exception as e:
                self.console.print(f"[yellow]Winget installation failed: {e}[/yellow]")

        if shutil.which("choco"):
            self.console.print("\n[cyan]Installing make via chocolatey...[/cyan]")
            try:
                result = subprocess.run(
                    ["choco", "install", "make", "-y"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'  # 忽略无法解码的字符
                )
                if result.returncode == 0:
                    self.console.print("[green]✓ Make installed successfully via chocolatey[/green]")
                    return True
            except Exception as e:
                self.console.print(f"[yellow]Chocolatey installation failed: {e}[/yellow]")

        # Manual download
        self.console.print("\n[yellow]Please install make manually:[/yellow]")
        self.console.print("  Option 1: choco install make")
        self.console.print("  Option 2: winget install GnuWin32.Make")
        self.console.print("  Option 3: Download from https://sourceforge.net/projects/gnuwin32/files/make/")

        return False

    def download_perl(self) -> bool:
        """Download and setup Perl"""
        self.console.print("\n[bold cyan]Downloading Perl[/bold cyan]")

        if is_windows():
            return self._download_perl_windows()
        else:
            self.console.print(
                "[yellow]Perl should be available via package manager on Linux/macOS[/yellow]"
            )
            self.console.print("Please install perl using:")
            self.console.print("  Ubuntu/Debian: sudo apt-get install perl")
            self.console.print("  macOS: brew install perl")
            return False

    def _download_perl_windows(self) -> bool:
        """Download Perl for Windows (Strawberry Perl)"""
        # Try winget first (more reliable)
        if shutil.which("winget"):
            self.console.print("\n[cyan]Installing Strawberry Perl via winget...[/cyan]")
            try:
                result = subprocess.run(
                    ["winget", "install", "StrawberryPerl.StrawberryPerl", "--accept-source-agreements"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if result.returncode == 0:
                    self.console.print("[green]✓ Perl installed successfully via winget[/green]")
                    self.console.print(
                        "[yellow]Note: You may need to restart your terminal for PATH changes to take effect[/yellow]"
                    )
                    return True
            except Exception as e:
                self.console.print(f"[yellow]Winget installation failed: {e}[/yellow]")

        # Try chocolatey
        if shutil.which("choco"):
            self.console.print("\n[cyan]Installing Strawberry Perl via chocolatey...[/cyan]")
            try:
                result = subprocess.run(
                    ["choco", "install", "strawberryperl", "-y"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if result.returncode == 0:
                    self.console.print("[green]✓ Perl installed successfully via chocolatey[/green]")
                    return True
            except Exception as e:
                self.console.print(f"[yellow]Chocolatey installation failed: {e}[/yellow]")

        # Manual download as fallback
        self.console.print("\n[yellow]Please install Perl manually:[/yellow]")
        self.console.print("  Option 1: winget install StrawberryPerl.StrawberryPerl")
        self.console.print("  Option 2: choco install strawberryperl")
        self.console.print("  Option 3: Download from https://strawberryperl.com/")

        return False

    def validate_toolchain(self) -> Tuple[bool, str]:
        """
        Validate that make, perl, and gcc are working

        Returns:
            Tuple of (success, message)
        """
        self.console.print("\n[bold cyan]Validating Toolchain[/bold cyan]")

        errors = []

        # Check make
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
                    version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
                    self.console.print(f"[green]✓ Make: {version_line}[/green]")
                else:
                    errors.append("make --version failed")
            except Exception as e:
                errors.append(f"make validation error: {e}")
        else:
            errors.append("make not found")

        # Check perl
        perl_cmd = self.get_perl_command()
        if perl_cmd:
            try:
                result = subprocess.run(
                    [perl_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version_info = "available"
                    for line in (result.stdout + result.stderr).split('\n')[:5]:
                        if 'version' in line.lower() or 'v' in line.lower():
                            version_info = line.strip()
                            break
                    self.console.print(f"[green]✓ Perl: {version_info}[/green]")
                else:
                    errors.append("perl --version failed")
            except Exception as e:
                errors.append(f"perl validation error: {e}")
        else:
            errors.append("perl not found")

        # Check gcc (from bundled tools or PATH)
        gcc_cmd = None
        if is_windows():
            bundled_gcc = self.bundled_mingw_bin / "gcc.exe"
            if bundled_gcc.exists():
                gcc_cmd = str(bundled_gcc)
        if not gcc_cmd:
            gcc_cmd = shutil.which("gcc")

        if gcc_cmd:
            try:
                result = subprocess.run(
                    [gcc_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
                    self.console.print(f"[green]✓ GCC: {version_line}[/green]")
                else:
                    errors.append("gcc --version failed")
            except Exception as e:
                errors.append(f"gcc validation error: {e}")
        else:
            errors.append("gcc not found")

        if errors:
            error_msg = "; ".join(errors)
            self.console.print(f"\n[red]✗ Toolchain validation failed: {error_msg}[/red]")
            return False, error_msg

        self.console.print("\n[green]✓ All toolchain components validated successfully[/green]")
        return True, "All tools validated"

    def ensure_tools_available(self) -> Tuple[bool, bool]:
        """
        Ensure all required tools are available

        Returns:
            Tuple of (all_tools_ok, mingw_ok)
        """
        make_ok, perl_ok, mingw_ok = self.check_existing_tools()

        if make_ok and perl_ok:
            self.console.print("\n[green]✓ All required tools are available[/green]")
            if mingw_ok:
                self.console.print("[green]✓ MinGW toolchain (gcc/g++) is available[/green]")
            else:
                self.console.print("[yellow]⚠ MinGW gcc not detected - host tools may use MSVC[/yellow]")
                self.console.print("[yellow]  Run 'python scripts/download_tools.py' to download bundled tools[/yellow]")
            return True, mingw_ok

        self.console.print("\n[yellow]Some tools are missing. Downloading...[/yellow]")

        if not make_ok:
            make_ok = self.download_make()

        if not perl_ok:
            perl_ok = self.download_perl()

        # Re-check mingw after tools are set up
        _, _, mingw_ok = self.check_existing_tools()

        all_tools_ok = make_ok and perl_ok
        return all_tools_ok, mingw_ok

    def get_make_command(self) -> Optional[str]:
        """Get the make command to use - Bundled tools first"""
        # Check bundled llvm-mingw first (Windows)
        if is_windows():
            bundled_make = self.bundled_mingw_bin / "mingw32-make.exe"
            if bundled_make.exists():
                return str(bundled_make)

        # Check PATH
        if shutil.which("make"):
            return "make"

        if is_windows() and shutil.which("mingw32-make"):
            return "mingw32-make"

        return None

    def get_perl_command(self) -> Optional[str]:
        """Get the perl command to use - Bundled tools first"""
        # Check bundled Perl first (Windows)
        if is_windows():
            bundled_perl = self.bundled_perl_bin / "perl.exe"
            if bundled_perl.exists():
                return str(bundled_perl)
            bundled_perl_alt = self.bundled_perl_bin_alt / "perl.exe"
            if bundled_perl_alt.exists():
                return str(bundled_perl_alt)

        # Check PATH
        if shutil.which("perl"):
            return "perl"

        return None

    def get_bundled_mingw_path(self) -> Optional[Path]:
        """Get the bundled MinGW bin directory"""
        if self.bundled_mingw_bin.exists():
            return self.bundled_mingw_bin
        return None

    def get_bundled_perl_path(self) -> Optional[Path]:
        """Get the bundled Perl bin directory"""
        if self.bundled_perl_bin.exists():
            return self.bundled_perl_bin
        if self.bundled_perl_bin_alt.exists():
            return self.bundled_perl_bin_alt
        return None