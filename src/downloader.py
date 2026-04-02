"""
Tool downloader module
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

from .config import ToolConfig
from .utils import is_windows, run_command, ensure_directory, format_size


class ToolDownloader:
    """Download and setup required tools"""

    def __init__(self, tools_dir: Path, tool_config: ToolConfig,
                 make_path: Optional[Path] = None, perl_path: Optional[Path] = None):
        self.tools_dir = tools_dir
        self.tool_config = tool_config
        self.console = Console()
        self.make_path = tools_dir / "make"
        self.perl_path = tools_dir / "perl"

        # Store configured tool paths
        # make_path should point to mingw32-make which is part of MinGW toolchain
        self.configured_make_path = make_path
        self.configured_perl_path = perl_path

        ensure_directory(self.tools_dir)
        ensure_directory(self.make_path)
        ensure_directory(self.perl_path)

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

    def _check_make(self) -> bool:
        """Check if make is available"""
        # First check configured path
        if self.configured_make_path and self.configured_make_path.exists():
            self.console.print(f"[green]✓ Using configured make: {self.configured_make_path}[/green]")
            return True

        # Check if make is in PATH
        if shutil.which("make"):
            return True

        # Check if mingw32-make is in PATH (Windows)
        if is_windows() and shutil.which("mingw32-make"):
            return True

        # Check if make is in tools directory
        make_exe = self.make_path / "make.exe" if is_windows() else self.make_path / "make"
        if make_exe.exists():
            return True

        return False

    def _check_perl(self) -> bool:
        """Check if perl is available"""
        # First check configured path
        if self.configured_perl_path and self.configured_perl_path.exists():
            self.console.print(f"[green]✓ Using configured perl: {self.configured_perl_path}[/green]")
            return True

        # Check if perl is in PATH
        if shutil.which("perl"):
            return True

        # Check if perl is in tools directory
        if is_windows():
            perl_exe = self.perl_path / "perl" / "bin" / "perl.exe"
        else:
            perl_exe = self.perl_path / "perl" / "bin" / "perl"

        if perl_exe.exists():
            return True

        return False

    def _check_mingw(self) -> bool:
        """Check if MinGW (gcc) is available"""
        # Check if gcc is in PATH
        if shutil.which("gcc"):
            return True

        # Check if mingw32-make is in PATH (indicates MinGW installation)
        if is_windows() and shutil.which("mingw32-make"):
            # If mingw32-make is in PATH, gcc should also be available
            return True

        # Check configured make path - if user set make path, gcc should be in same directory
        if self.configured_make_path and self.configured_make_path.exists():
            make_path = Path(self.configured_make_path)
            if make_path.is_file():
                bin_dir = make_path.parent
            elif make_path.name.lower() == "bin":
                bin_dir = make_path
            else:
                bin_dir = make_path / "bin"

            gcc_exe = bin_dir / "gcc.exe" if is_windows() else bin_dir / "gcc"
            if gcc_exe.exists():
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

    def download_mingw(self) -> bool:
        """
        Provide download instructions for MinGW (doesn't auto-download)

        Returns:
            False - MinGW requires manual installation
        """
        self.console.print("\n[bold cyan]MinGW Toolchain Setup[/bold cyan]")

        if is_windows():
            # Try winget first
            if shutil.which("winget"):
                self.console.print("\n[cyan]Installing MinGW-w64 via winget...[/cyan]")
                try:
                    result = subprocess.run(
                        ["winget", "install", "MSYS2.MSYS2", "--accept-source-agreements"],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.returncode == 0:
                        self.console.print("[green]✓ MSYS2 installed successfully via winget[/green]")
                        self.console.print(
                            "[yellow]Note: Run 'pacman -S mingw-w64-x86_64-gcc' in MSYS2 to install GCC[/yellow]"
                        )
                        return True
                except Exception as e:
                    self.console.print(f"[yellow]Winget installation failed: {e}[/yellow]")

            # Try chocolatey
            if shutil.which("choco"):
                self.console.print("\n[cyan]Installing MinGW via chocolatey...[/cyan]")
                try:
                    result = subprocess.run(
                        ["choco", "install", "mingw", "-y"],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.returncode == 0:
                        self.console.print("[green]✓ MinGW installed successfully via chocolatey[/green]")
                        return True
                except Exception as e:
                    self.console.print(f"[yellow]Chocolatey installation failed: {e}[/yellow]")

            # Manual download instructions with mirror URLs
            self.console.print("\n[yellow]Please install MinGW manually:[/yellow]")
            self.console.print("  Option 1: winget install MSYS2.MSYS2")
            self.console.print("  Option 2: choco install mingw")
            self.console.print("  Option 3: Download from https://www.mingw-w64.org/downloads/")
            self.console.print("  Mirror 1: https://sourceforge.net/projects/mingw-w64/files/")
            self.console.print("  Mirror 2: https://github.com/niXman/mingw-builds-binaries/releases")
        else:
            self.console.print(
                "[yellow]MinGW should be available via package manager on Linux/macOS[/yellow]"
            )
            self.console.print("Please install gcc using:")
            self.console.print("  Ubuntu/Debian: sudo apt-get install gcc g++ make")
            self.console.print("  macOS: xcode-select --install")

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
                    # Extract version from output
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

        # Check gcc
        gcc_cmd = shutil.which("gcc")
        if not gcc_cmd and is_windows():
            # Try to find gcc in the same directory as configured make
            if self.configured_make_path and self.configured_make_path.exists():
                make_path = Path(self.configured_make_path)
                if make_path.is_file():
                    bin_dir = make_path.parent
                elif make_path.name.lower() == "bin":
                    bin_dir = make_path
                else:
                    bin_dir = make_path / "bin"

                gcc_exe = bin_dir / "gcc.exe"
                if gcc_exe.exists():
                    gcc_cmd = str(gcc_exe)

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
                self.console.print("[green]✓ MinGW toolchain is available[/green]")
            return True, mingw_ok

        self.console.print("\n[yellow]Some tools are missing. Downloading...[/yellow]")

        if not make_ok:
            make_ok = self.download_make()

        if not perl_ok:
            perl_ok = self.download_perl()

        if not mingw_ok:
            mingw_ok = self.download_mingw()

        all_tools_ok = make_ok and perl_ok
        return all_tools_ok, mingw_ok
    
    def get_make_command(self) -> Optional[str]:
        """Get the make command to use"""
        if shutil.which("make"):
            return "make"
        
        if is_windows() and shutil.which("mingw32-make"):
            return "mingw32-make"
        
        # Check tools directory
        make_exe = self.make_path / "make.exe" if is_windows() else self.make_path / "make"
        if make_exe.exists():
            return str(make_exe)
        
        return None
    
    def get_perl_command(self) -> Optional[str]:
        """Get the perl command to use"""
        if shutil.which("perl"):
            return "perl"
        
        # Check tools directory
        if is_windows():
            perl_exe = self.perl_path / "perl" / "bin" / "perl.exe"
        else:
            perl_exe = self.perl_path / "perl" / "bin" / "perl"
        
        if perl_exe.exists():
            return str(perl_exe)
        
        return None