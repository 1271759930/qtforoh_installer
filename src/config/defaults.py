"""
Default configurations and version-specific settings
"""

from typing import List, Dict, Any


# Common skip modules for all Qt 5.x versions
COMMON_SKIP_MODULES: List[str] = [
    "qt3d", "qtactiveqt", "qtandroidextras",
    "qtconnectivity", "qtdatavis3d", "qtdoc",
    "qtgraphicaleffects", "qtlocation",
    "qtmacextras", "qtnetworkauth",
    "qtremoteobjects", "qtscript",
    "qtscxml", "qtsensors", "qtserialbus", "qtserialport",
    "qtspeech",
    "qttranslations",
    "qtvirtualkeyboard", "qtwayland", "qtwebchannel", "qtwebengine",
    "qtwebglplugin", "qtwebsockets", "qtwebview", "qtwinextras",
    "qtx11extras", "doc",
]

# Qt 5.15 recommended skip modules for HarmonyOS
QT15_SKIP_MODULES: List[str] = [
    "doc", "qtactiveqt", "qtandroidextras", "qtcanvas3d",
    "qtdoc", "qtfeedback", "qtgamepad", "qtlocation",
    "qtmacextras", "qtnetworkauth", "qtpim", "qtpurchasing",
    "qtqa", "qtremoteobjects", "qtrepotools", "qtscript",
    "qtsystems", "qttools", "qtwayland", "qtwebchannel",
    "qtwebengine", "qtwebglplugin", "qtwinextras", "qtx11extras",
    "qtopcua", "qtknx", "qtconnectivity",
]


# Version-specific configurations
QT_VERSION_CONFIGS: Dict[str, Dict[str, Any]] = {
    "5.12.12": {
        "skip_modules": COMMON_SKIP_MODULES,
        "c++std": "c++14",
        "opengl": ["es2", "opengles3"],
        "extra_configure_options": [],
        "notes": "Qt 5.12 LTS - uses -ohos-arch parameter"
    },
    "5.15.16": {
        "skip_modules": QT15_SKIP_MODULES,
        "c++std": "c++14",
        "opengl": ["es2", "opengles3"],
        "extra_configure_options": [],
        "notes": "Qt 5.15 LTS - recommended skip modules for HarmonyOS"
    },
}

# Default configuration for unknown versions
DEFAULT_CONFIG: Dict[str, Any] = {
    "skip_modules": COMMON_SKIP_MODULES,
    "c++std": "c++14",
    "opengl": ["es2", "opengles3"],
    "extra_configure_options": [],
    "notes": "Using default configuration"
}


def get_qt_version_config(version: str) -> Dict[str, Any]:
    """
    Get version-specific configuration for Qt HarmonyOS build.

    Args:
        version: Qt version string (e.g., "5.12.12", "5.15.16")

    Returns:
        Dictionary with version-specific configuration
    """
    # Parse major.minor version
    parts = version.split(".")
    if len(parts) >= 2:
        major = int(parts[0]) if parts[0].isdigit() else 5
        minor = int(parts[1]) if parts[1].isdigit() else 15
        version_key = f"{major}.{minor}.{parts[2] if len(parts) > 2 and parts[2].isdigit() else '0'}"

        # Try exact match first
        if version_key in QT_VERSION_CONFIGS:
            return QT_VERSION_CONFIGS[version_key]

        # Try major.minor match
        major_minor = f"{major}.{minor}"
        for key, config in QT_VERSION_CONFIGS.items():
            if key.startswith(major_minor):
                return config

    return DEFAULT_CONFIG


def get_default_skip_modules(version: str = "5.15.16") -> List[str]:
    """
    Get default skip modules for a Qt version.

    Args:
        version: Qt version string

    Returns:
        List of module names to skip
    """
    config = get_qt_version_config(version)
    return config.get("skip_modules", COMMON_SKIP_MODULES).copy()