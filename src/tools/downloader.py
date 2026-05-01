"""
Tool downloader module - Supports bundled tools and system tools
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import requests
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..config import ToolConfig
from ..utils import is_windows, run_command, ensure_directory, format_size
from ..constants import (
    BUNDLED_LLVM_MINGW_DIR,
    BUNDLED_LLVM_MINGW_BIN,
    BUNDLED_PERL_DIR,
    BUNDLED_PERL_BIN,
    BUNDLED_PERL_BIN_ALT,
    BUNDLED_ARCHIVES_DIR,
    LLVM_MINGW_URL,
    PERL_URL,
    LLVM_MINGW_ARCHIVE_NAME,
    PERL_ARCHIVE_NAME,
)


class ToolDownloader:
    """Download and setup required tools - Uses bundled tools"""

    def __init__(self, tools_dir: Path, tool_config: ToolConfig):
        self.tools_dir = tools_dir
        self.tool_config = tool_config
        self.console = Console()

        # Bundled tools paths (from constants)
        self.bundled_mingw_bin = BUNDLED_LLVM_MINGW_BIN
        self.bundled_perl_bin = BUNDLED_PERL_BIN
        self.bundled_perl_bin_alt = BUNDLED_PERL_BIN_ALT

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
        """Check if perl is available - Bundled tools first with完整性验证"""
        # Check bundled Perl tools
        if is_windows():
            bundled_perl = self.bundled_perl_bin / "perl.exe"
            bundled_perl_alt = self.bundled_perl_bin_alt / "perl.exe"
            if bundled_perl.exists():
                # Verify Perl completeness (check lib directory)
                perl_lib = BUNDLED_PERL_DIR / "perl" / "lib"
                if not perl_lib.exists():
                    self.console.print("[yellow]⚠ Perl 目录不完整，缺少 lib 目录[/yellow]")
                    self.console.print("[yellow]  需要重新下载完整工具[/yellow]")
                    return False

                # Check for File/Basename.pm (critical module)
                basename_pm = perl_lib / "File" / "Basename.pm"
                if not basename_pm.exists():
                    self.console.print("[yellow]⚠ Perl 目录不完整，缺少核心模块[/yellow]")
                    self.console.print("[yellow]  需要重新下载完整工具[/yellow]")
                    return False

                self.console.print(f"[green]✓ Using bundled perl: {bundled_perl}[/green]")
                return True
            if bundled_perl_alt.exists():
                # Verify alternative Perl location
                perl_lib_alt = BUNDLED_PERL_DIR / "lib"
                if perl_lib_alt.exists():
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

    def download_bundled_tools(self, console=None) -> Tuple[bool, bool]:
        """
        Download bundled tools (llvm-mingw and Perl) from GitCode release.

        Args:
            console: Rich console for output (optional)

        Returns:
            Tuple of (llvm_mingw_ok, perl_ok)
        """
        if console is None:
            console = self.console

        console.print("\n[bold cyan]============================================[/bold cyan]")
        console.print("[bold cyan]下载构建工具 / Downloading Build Tools[/bold cyan]")
        console.print("[bold cyan]============================================[/bold cyan]")

        # Ensure archives directory exists
        BUNDLED_ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

        llvm_ok = self._download_and_extract_llvm_mingw(console)
        perl_ok = self._download_and_extract_perl(console)

        console.print("\n[bold cyan]============================================[/bold cyan]")
        if llvm_ok and perl_ok:
            console.print("[bold green]✓ 所有工具下载完成 / All tools downloaded successfully[/bold green]")
        else:
            console.print("[bold red]✗ 工具下载失败 / Tool download failed[/bold red]")
        console.print("[bold cyan]============================================[/bold cyan]")

        return llvm_ok, perl_ok

    def _download_and_extract_llvm_mingw(self, console) -> bool:
        """Download and extract llvm-mingw from GitCode release"""
        console.print("\n[cyan]步骤 1/2: llvm-mingw (MinGW 工具链)[/cyan]")
        console.print(f"  目标: {BUNDLED_LLVM_MINGW_DIR}")

        # Check if already extracted AND complete (stub headers created automatically)
        mingw32_make = BUNDLED_LLVM_MINGW_DIR / "bin" / "mingw32-make.exe"

        if mingw32_make.exists():
            console.print("[green]  ✓ llvm-mingw 已存在，跳过下载[/green]")
            return True

        # If directory exists but incomplete, delete it
        if BUNDLED_LLVM_MINGW_DIR.exists():
            console.print("[yellow]  llvm-mingw 目录不完整，删除并重新下载...[/yellow]")
            import shutil
            try:
                shutil.rmtree(BUNDLED_LLVM_MINGW_DIR)
            except Exception as e:
                console.print(f"[red]  删除失败: {e}[/red]")
                return False

        archive_path = BUNDLED_ARCHIVES_DIR / LLVM_MINGW_ARCHIVE_NAME

        # Download if archive doesn't exist or is LFS pointer
        if not archive_path.exists() or self._is_lfs_pointer(archive_path):
            if archive_path.exists():
                console.print("[yellow]  检测到 LFS 指针文件，删除并重新下载...[/yellow]")
                archive_path.unlink()

            console.print(f"[cyan]  下载 llvm-mingw (~70MB)...[/cyan]")
            if not self.download_file(LLVM_MINGW_URL, archive_path, "llvm-mingw"):
                return False

        # Extract
        console.print("[cyan]  解压 llvm-mingw...[/cyan]")
        if not self._extract_archive(archive_path, BUNDLED_LLVM_MINGW_DIR, "llvm-mingw", console):
            return False

        # Verify after extraction
        if mingw32_make.exists():
            console.print("[green]  ✓ llvm-mingw 安装完成[/green]")
            return True
        else:
            console.print("[red]  ✗ llvm-mingw 安装失败: mingw32-make.exe 未找到[/red]")
            return False

    def _download_and_extract_perl(self, console) -> bool:
        """Download and extract Perl from GitCode release"""
        console.print("\n[cyan]步骤 2/2: Strawberry Perl[/cyan]")
        console.print(f"  目标: {BUNDLED_PERL_DIR}")

        # Check if already extracted AND complete
        perl_exe = BUNDLED_PERL_DIR / "perl" / "bin" / "perl.exe"
        perl_lib = BUNDLED_PERL_DIR / "perl" / "lib"
        basename_pm = perl_lib / "File" / "Basename.pm"

        if perl_exe.exists() and perl_lib.exists() and basename_pm.exists():
            console.print("[green]  ✓ Perl 已存在且完整，跳过下载[/green]")
            return True

        # If directory exists but incomplete, delete it
        if BUNDLED_PERL_DIR.exists():
            console.print("[yellow]  Perl 目录不完整，删除并重新下载...[/yellow]")
            import shutil
            try:
                shutil.rmtree(BUNDLED_PERL_DIR)
            except Exception as e:
                console.print(f"[red]  删除失败: {e}[/red]")
                return False

        archive_path = BUNDLED_ARCHIVES_DIR / PERL_ARCHIVE_NAME

        # Download if archive doesn't exist or is LFS pointer
        if not archive_path.exists() or self._is_lfs_pointer(archive_path):
            if archive_path.exists():
                console.print("[yellow]  检测到 LFS 指针文件，删除并重新下载...[/yellow]")
                archive_path.unlink()

            console.print(f"[cyan]  下载 Strawberry Perl (~290MB)...[/cyan]")
            if not self.download_file(PERL_URL, archive_path, "Perl"):
                return False

        # Extract
        console.print("[cyan]  解压 Perl (这可能需要一些时间)...[/cyan]")
        if not self._extract_archive(archive_path, BUNDLED_PERL_DIR, "Perl", console):
            return False

        # Verify
        if perl_exe.exists():
            console.print("[green]  ✓ Perl 安装完成[/green]")
            return True
        else:
            console.print("[red]  ✗ Perl 安装失败: perl.exe 未找到[/red]")
            return False

    def _is_lfs_pointer(self, file_path: Path) -> bool:
        """Check if file is a Git LFS pointer"""
        if not file_path.exists():
            return False
        try:
            with open(file_path, 'rb') as f:
                content = f.read(200)
                return b'version https://git-lfs.github.com/spec/v1' in content
        except Exception:
            return False

    def _extract_archive(self, archive_path: Path, target_dir: Path, tool_name: str, console) -> bool:
        """Extract a zip archive with tqdm progress bar"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                members = zf.namelist()
                total_files = len(members)

                # Detect root folder by checking first few entries
                root_folder = None
                for name in members[:20]:
                    if '/' in name:
                        candidate = name.split('/')[0]
                        # Check if most entries start with this folder
                        count = sum(1 for m in members[:100] if m.startswith(candidate + '/') or m == candidate)
                        if count >= min(50, len(members[:100])):
                            root_folder = candidate
                            console.print(f"  [cyan]检测到根目录: {root_folder}，跳过[/cyan]")
                            break

                # Clean target directory if it has nested structure from previous failed extraction
                if target_dir.exists():
                    nested = target_dir / (root_folder if root_folder else "")
                    if nested.exists() and nested.is_dir():
                        console.print(f"  [yellow]检测到嵌套目录，清理后重新解压[/yellow]")
                        import shutil
                        try:
                            shutil.rmtree(target_dir)
                        except Exception:
                            pass

                target_dir.mkdir(parents=True, exist_ok=True)

                # Extract with tqdm progress bar
                with tqdm(
                    total=total_files,
                    unit="files",
                    unit_scale=False,
                    desc=f"Extracting {tool_name}",
                    ncols=80
                ) as pbar:
                    for member in members:
                        # Skip root folder entry
                        if root_folder:
                            if member == root_folder or member == root_folder + '/':
                                pbar.update(1)
                                continue
                            if member.startswith(root_folder + '/'):
                                relative_path = member[len(root_folder) + 1:]
                            else:
                                relative_path = member
                        else:
                            relative_path = member

                        if not relative_path:
                            pbar.update(1)
                            continue

                        target_path = target_dir / relative_path

                        # Create directories or extract files
                        if relative_path.endswith('/'):
                            target_path.mkdir(parents=True, exist_ok=True)
                        else:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            # Use original member name for extraction
                            try:
                                with zf.open(member) as src:
                                    with open(target_path, 'wb') as dst:
                                        dst.write(src.read())
                            except KeyError:
                                # Fallback for different path format
                                pass

                        pbar.update(1)

                console.print(f"[green]  ✓ 解压完成: {total_files} 文件[/green]")

                # Create missing intrinsics stub headers for llvm-mingw
                if "llvm-mingw" in tool_name or "mingw" in tool_name.lower():
                    self._create_intrinsics_stubs(target_dir, console)

                return True

        except zipfile.BadZipFile as e:
            console.print(f"[red]  ✗ 压缩包损坏: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]  ✗ 解压失败: {e}[/red]")
            return False

    def _create_intrinsics_stubs(self, target_dir: Path, console) -> None:
        """Create stub headers for missing intrinsics files (mm_malloc.h, x86intrin.h, etc.)"""
        include_dir = target_dir / "include"
        if not include_dir.exists():
            return

        # mm_malloc.h - aligned memory allocation
        mm_malloc_h = include_dir / "mm_malloc.h"
        if not mm_malloc_h.exists():
            mm_malloc_h.write_text("""/**
 * mm_malloc.h - Aligned memory allocation stub for SIMD operations
 */
#ifndef _MM_MALLOC_H_INCLUDED
#define _MM_MALLOC_H_INCLUDED

#include <stdlib.h>

#if defined(_WIN32) || defined(_WIN64)
#include <malloc.h>
#define _mm_malloc(size, alignment) _aligned_malloc(size, alignment)
#define _mm_free(ptr) _aligned_free(ptr)
#else
static inline void* _mm_malloc(size_t size, size_t alignment) {
    void* ptr = NULL;
    if (alignment < sizeof(void*)) alignment = sizeof(void*);
    posix_memalign(&ptr, alignment, size);
    return ptr;
}
static inline void _mm_free(void* ptr) { free(ptr); }
#endif

#endif
""")
            console.print("[cyan]  创建 mm_malloc.h stub[/cyan]")

        # x86intrin.h - x86 SIMD intrinsics stub
        x86intrin_h = include_dir / "x86intrin.h"
        if not x86intrin_h.exists():
            x86intrin_h.write_text("""/**
 * x86intrin.h - x86 SIMD intrinsics stub
 * Actual intrinsics are compiler builtins in clang.
 */
#ifndef _X86INTRIN_H_INCLUDED
#define _X86INTRIN_H_INCLUDED

#include <mm_malloc.h>

#endif
""")
            console.print("[cyan]  创建 x86intrin.h stub[/cyan]")

        # emmintrin.h - SSE2 intrinsics stub
        emmintrin_h = include_dir / "emmintrin.h"
        if not emmintrin_h.exists():
            emmintrin_h.write_text("""/**
 * emmintrin.h - SSE2 intrinsics stub
 * Actual intrinsics are compiler builtins in clang.
 */
#ifndef _EMMINTRIN_H_INCLUDED
#define _EMMINTRIN_H_INCLUDED

/* SSE2 intrinsics are built into clang compiler */
#endif
""")
            console.print("[cyan]  创建 emmintrin.h stub[/cyan]")