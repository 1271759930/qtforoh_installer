"""
Utility functions
"""

import os
import sys
import platform
import subprocess
import shutil
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
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            return result.returncode, result.stdout, result.stderr
        else:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True
            )
            
            stdout_lines = []
            for line in process.stdout:
                stdout_lines.append(line)
                if logger:
                    logger.info(line.rstrip())
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