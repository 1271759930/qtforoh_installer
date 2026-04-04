"""
Qt for HarmonyOS Installation CLI Tool

A modular CLI tool for installing Qt for HarmonyOS.
"""

__version__ = "1.0.0"
__author__ = "Qt HarmonyOS Installer Team"

# Main entry point
from .cli import main, cli

# Core components
from .core import QtHarmonyInstaller, InstallStep, DEFAULT_STEPS

# Configuration
from .config import InstallConfig, ToolConfig, ConfigManager, get_qt_version_config

# UI components
from .ui import Display, ConfigCollector

# Builder components
from .builder import QtBuilder, EnvironmentManager

# Tools
from .tools import ToolDownloader

__all__ = [
    # Entry point
    "main",
    "cli",
    # Core
    "QtHarmonyInstaller",
    "InstallStep",
    "DEFAULT_STEPS",
    # Config
    "InstallConfig",
    "ToolConfig",
    "ConfigManager",
    "get_qt_version_config",
    # UI
    "Display",
    "ConfigCollector",
    # Builder
    "QtBuilder",
    "EnvironmentManager",
    # Tools
    "ToolDownloader",
]