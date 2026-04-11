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


def is_macos() -> bool:
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux"""
    return platform.system() == "Linux"


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 12:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires >= 3.12)"


def check_llvm_mingw() -> Tuple[bool, str, str]:
    """
    Check if llvm-mingw make tool is available.

    Returns:
        Tuple of (is_valid, status_message, download_hint)
    """
    import re

    # Check make command
    make_path = shutil.which("make")
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
            "请下载 llvm-mingw: https://github.com/mstorsjo/llvm-mingw/releases"


def check_perl() -> Tuple[bool, str, str]:
    """
    Check if Perl is available.

    Returns:
        Tuple of (is_valid, status_message, download_hint)
    """
    perl_path = shutil.which("perl")
    if perl_path:
        return True, f"Perl found: {perl_path}", ""
    else:
        return False, "Perl 未安装", \
            "请下载 Strawberry Perl: https://strawberryperl.com/"


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None


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


def clean_directory(path: Path) -> bool:
    """Clean a directory (remove all contents)"""
    try:
        if path.exists():
            shutil.rmtree(path)
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


def get_qt_version_config(version: str) -> dict:
    """
    Get version-specific configuration for Qt HarmonyOS build.

    Different Qt versions may have different:
    - Skip module lists
    - Configure parameters
    - Required tool versions

    Args:
        version: Qt version string (e.g., "5.12.12", "5.15.16")

    Returns:
        Dictionary with version-specific configuration
    """
    # Parse major.minor version
    parts = version.split(".")
    major = int(parts[0]) if parts else 5
    minor = int(parts[1]) if len(parts) > 1 else 15

    # Common skip modules for all versions (only modules that exist in Qt 5.12-5.15)
    common_skip = [
        "qt3d", "qtactiveqt", "qtandroidextras", "qtcanvas3d",
        "qtconnectivity", "qtdatavis3d", "qtdoc", "qtdocgallery",
        "qtfeedback", "qtgamepad", "qtgraphicaleffects", "qtlocation",
        "qtmacextras", "qtnetworkauth", "qtpim", "qtpurchasing",
        "qtqa", "qtremoteobjects", "qtrepotools", "qtscript",
        "qtscxml", "qtsensors", "qtserialbus", "qtserialport",
        "qtspeech", "qtsystems", "qttools", "qttranslations",
        "qtvirtualkeyboard", "qtwayland", "qtwebchannel", "qtwebengine",
        "qtwebglplugin", "qtwebsockets", "qtwebview", "qtwinextras",
        "qtx11extras", "doc",
    ]

    # Version-specific configurations
    if major == 5 and minor == 12:
        # Qt 5.12 specific
        return {
            "skip_modules": common_skip,
            "c++std": "c++14",
            "opengl": ["es2", "opengles3"],
            "extra_configure_options": ["-no-dbus"],
            "notes": "Qt 5.12 LTS - uses -ohos-arch parameter, dbus disabled for HarmonyOS"
        }
    elif major == 5 and minor == 15:
        # Qt 5.15 specific - use recommended skip list for HarmonyOS
        qt15_skip = [
            "qt3d", "qtactiveqt", "qtandroidextras", "qtcanvas3d",
            "qtconnectivity", "qtdatavis3d", "qtdoc", "qtdocgallery",
            "qtfeedback", "qtgamepad", "qtgraphicaleffects", "qtlocation",
            "qtmacextras", "qtnetworkauth", "qtpim", "qtpurchasing",
            "qtqa", "qtremoteobjects", "qtrepotools", "qtscript",
            "qtscxml", "qtsensors", "qtserialbus", "qtserialport",
            "qtspeech", "qtsystems", "qttools", "qttranslations",
            "qtvirtualkeyboard", "qtwayland", "qtwebchannel", "qtwebengine",
            "qtwebglplugin", "qtwebsockets", "qtwebview", "qtwinextras",
            "qtx11extras", "qtopcua", "qtknx", "doc",
        ]
        return {
            "skip_modules": qt15_skip,
            "c++std": "c++14",
            "opengl": ["es2", "opengles3"],
            "extra_configure_options": ["-no-dbus"],
            "notes": "Qt 5.15 LTS - recommended skip modules for HarmonyOS, dbus disabled"
        }
    else:
        # Default configuration for unknown versions
        return {
            "skip_modules": common_skip,
            "c++std": "c++14",
            "opengl": ["es2", "opengles3"],
            "extra_configure_options": ["-no-dbus"],
            "notes": f"Unknown Qt version {version}, using default config, dbus disabled"
        }
