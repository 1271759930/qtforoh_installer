"""
Configuration module - Data schemas and configuration management
"""

from .schema import InstallConfig, ToolConfig
from .loader import ConfigManager
from .defaults import get_qt_version_config, QT_VERSION_CONFIGS

__all__ = [
    "InstallConfig",
    "ToolConfig",
    "ConfigManager",
    "get_qt_version_config",
    "QT_VERSION_CONFIGS",
]