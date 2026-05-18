"""
Utility functions
"""

import os
import sys
import platform
import subprocess
import shutil
import locale
from pathlib import Path
from typing import Optional, List, Tuple
import logging
from datetime import datetime

from .constants import (
    BUNDLED_LLVM_MINGW_DIR,
    BUNDLED_LLVM_MINGW_BIN,
    BUNDLED_LLVM_MINGW_MAKE,
    BUNDLED_LLVM_MINGW_GCC,
    BUNDLED_PERL_DIR,
    BUNDLED_PERL_EXE,
    BUNDLED_PERL_BIN_ALT,
)


def setup_logging(log_dir: Path) -> logging.Logger:
    """Setup logging configuration"""
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"install_{timestamp}.log"

    logger = logging.getLogger("qtohos-installer")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def is_windows() -> bool:
    """Check if running on Windows"""
    return platform.system() == "Windows"


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires >= 3.10)"


def check_llvm_mingw() -> Tuple[bool, str, str]:
    """
    Check if llvm-mingw make tool is available - Bundled tools first.

    Returns:
        Tuple of (is_valid, status_message, download_hint)
    """
    import re

    # Check bundled llvm-mingw first (use constants)
    if is_windows():
        if BUNDLED_LLVM_MINGW_MAKE.exists() and BUNDLED_LLVM_MINGW_GCC.exists():
            return True, f"Bundled llvm-mingw found: {BUNDLED_LLVM_MINGW_DIR}", ""

    # Check make command (try both 'make' and 'mingw32-make' on Windows)
    make_path = shutil.which("make")

    # On Windows, also check for mingw32-make
    if not make_path and is_windows():
        make_path = shutil.which("mingw32-make")

    if make_path:
        # Check if it's from llvm-mingw (path contains "llvm-mingw")
        make_path_lower = make_path.lower()
        if "llvm-mingw" in make_path_lower:
            # Extract version info if possible (e.g., llvm-mingw-20260407-ucrt)
            match = re.search(r'llvm-mingw-(\d{8})', make_path)
            if match:
                version_date = match.group(1)
                return True, f"llvm-mingw make found (version: {version_date})", ""
            return True, "llvm-mingw make found", ""
        else:
            # Found make but not llvm-mingw version
            return False, f"Make found but not llvm-mingw version: {make_path}", \
                "请安装 llvm-mingw: https://github.com/mstorsjo/llvm-mingw/releases"
    else:
        # No make found
        return False, "Make 未安装", \
            "请运行 python scripts/download_tools.py 下载预打包工具"


def check_perl() -> Tuple[bool, str, str]:
    """
    Check if Perl is available - Bundled tools first.

    Returns:
        Tuple of (is_valid, status_message, download_hint)
    """
    # Check bundled Perl first (use constants)
    if is_windows():
        if BUNDLED_PERL_EXE.exists():
            return True, f"Bundled Perl found: {BUNDLED_PERL_EXE}", ""
        bundled_perl_alt = BUNDLED_PERL_BIN_ALT / "perl.exe"
        if bundled_perl_alt.exists():
            return True, f"Bundled Perl found: {bundled_perl_alt}", ""

    perl_path = shutil.which("perl")
    if perl_path:
        return True, f"Perl found: {perl_path}", ""
    else:
        return False, "Perl 未安装", \
            "请运行 python scripts/download_tools.py 下载预打包工具"


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    capture_output: bool = False,
    logger: Optional[logging.Logger] = None
) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, stderr
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        env: Environment variables
        capture_output: Whether to capture output
        logger: Logger instance
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if logger:
        logger.info(f"Running command: {' '.join(cmd)}")
        if cwd:
            logger.debug(f"Working directory: {cwd}")
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=False
            )
            stdout_text = _decode_process_output(result.stdout)
            stderr_text = _decode_process_output(result.stderr)
            return result.returncode, stdout_text, stderr_text
        else:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=False
            )
            
            stdout_lines = []
            for raw_line in iter(process.stdout.readline, b""):
                line = _decode_process_output(raw_line)
                stdout_lines.append(line)
                if logger:
                    # Logger with StreamHandler will print to console
                    logger.info(line.rstrip())
                else:
                    # No logger - print directly
                    print(line, end="")

            process.wait()
            return process.returncode, "".join(stdout_lines), ""
    
    except FileNotFoundError as e:
        error_msg = f"Command not found: {cmd[0]}"
        if logger:
            logger.error(error_msg)
        return -1, "", error_msg
    except Exception as e:
        error_msg = f"Error running command: {e}"
        if logger:
            logger.error(error_msg)
        return -1, "", error_msg


def _decode_process_output(data: bytes) -> str:
    """Decode subprocess output with Windows-friendly fallbacks."""
    if data is None:
        return ""

    if isinstance(data, str):
        return data

    encodings = ["utf-8"]
    if is_windows():
        preferred = locale.getpreferredencoding(False)
        if preferred:
            encodings.append(preferred)
        encodings.extend(["gbk", "cp936"])
    else:
        preferred = locale.getpreferredencoding(False)
        if preferred:
            encodings.append(preferred)

    seen = set()
    ordered_encodings = []
    for enc in encodings:
        key = enc.lower()
        if key not in seen:
            seen.add(key)
            ordered_encodings.append(enc)

    for enc in ordered_encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue

    return data.decode("utf-8", errors="replace")


def validate_path(path: Path, must_exist: bool = True, create: bool = False) -> Tuple[bool, str]:
    """
    Validate a path
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        create: Whether to create the path if it doesn't exist
    
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        path = path.resolve()
        
        if must_exist and not path.exists():
            if create:
                path.mkdir(parents=True, exist_ok=True)
                return True, f"Created: {path}"
            return False, f"Path does not exist: {path}"
        
        return True, f"Valid path: {path}"
    
    except Exception as e:
        return False, f"Invalid path: {e}"


def get_directory_size(path: Path) -> int:
    """Get total size of a directory in bytes"""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def ensure_directory(path: Path) -> bool:
    """Ensure a directory exists, create if necessary"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_git_branch(repo_path: Path) -> Optional[str]:
    """
    Get the current Git branch name for a repository.

    Args:
        repo_path: Path to the Git repository

    Returns:
        Branch name or None if not a Git repo or on detached HEAD
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # "HEAD" means detached HEAD state
            if branch and branch != "HEAD":
                return branch
        return None
    except Exception:
        return None


def parse_qt_version_from_branch(branch_name: str) -> Optional[str]:
    """
    Parse Qt version from a HarmonyOS branch name.

    Branch name formats:
        - tqtc/harmonyos-X.XX.XX (e.g., tqtc/harmonyos-5.15.16)
        - tqtc/lts-X.XX.XX-harmonyos (e.g., tqtc/lts-5.12.12-harmonyos)
        - harmonyos-X.XX.XX

    Args:
        branch_name: Git branch name

    Returns:
        Qt version string or None if not parseable
    """
    import re

    # Match pattern: harmonyos-X.XX.XX
    match = re.search(r'harmonyos-(\d+\.\d+(?:\.\d+)?)', branch_name)
    if match:
        return match.group(1)

    # Match pattern: lts-X.XX.XX-harmonyos
    match = re.search(r'lts-(\d+\.\d+(?:\.\d+)?)-harmonyos', branch_name)
    if match:
        return match.group(1)

    return None


def detect_qt_version(qt_source_path: Path) -> Tuple[str, str]:
    """
    Detect Qt version from source directory.

    First tries to parse from Git branch name, then falls back to
    checking qtbase/.qmake.conf or defaults to 5.15.16.

    Args:
        qt_source_path: Path to Qt source directory

    Returns:
        Tuple of (version_string, detection_method)
    """
    # Method 1: Try Git branch
    branch = get_git_branch(qt_source_path)
    if branch:
        version = parse_qt_version_from_branch(branch)
        if version:
            return version, f"Git branch: {branch}"

    # Method 2: Try qtbase/.qmake.conf
    qmake_conf = qt_source_path / "qtbase" / ".qmake.conf"
    if qmake_conf.exists():
        try:
            content = qmake_conf.read_text(encoding="utf-8")
            import re
            match = re.search(r'MODULE_VERSION\s*=\s*(\S+)', content)
            if match:
                return match.group(1), "qtbase/.qmake.conf"
        except Exception:
            pass

    # Method 3: Default
    return "5.15.16", "default (no version detected)"


def add_to_user_path(path_str: str) -> Tuple[bool, str]:
    """
    Add a path to user's PATH environment variable on Windows.
    将路径添加到Windows用户PATH环境变量。

    Args:
        path_str: Path to add

    Returns:
        Tuple of (success, message)
    """
    if not is_windows():
        return False, "仅支持Windows系统 / Only supported on Windows"

    try:
        import winreg

        path_str = str(Path(path_str).resolve())

        # Open user environment key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        )

        try:
            # Get current PATH value
            current_path, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            current_path = ""

        # Check if path already exists
        path_lower = path_str.lower()
        existing_paths = [p.strip().lower() for p in current_path.split(";") if p.strip()]

        if path_lower in existing_paths:
            winreg.CloseKey(key)
            return True, f"路径已存在 / Path already in PATH: {path_str}"

        # Add new path
        if current_path:
            new_path = path_str + ";" + current_path
        else:
            new_path = path_str

        # Set new PATH value
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)

        # Notify system of environment change
        try:
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_long()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(result)
            )
        except Exception:
            pass

        return True, f"已添加到用户PATH / Added to user PATH: {path_str}"

    except PermissionError:
        return False, "权限不足，无法修改环境变量 / Insufficient permissions"
    except Exception as e:
        return False, f"添加失败 / Failed to add: {e}"
