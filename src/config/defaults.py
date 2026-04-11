"""
Default configurations and version-specific settings
"""

from typing import List, Dict, Any, Optional
from pathlib import Path


# Qt module status types
QT_MODULE_STATUS = {
    "essential": "核心模块(不建议跳过)",
    "addon": "扩展模块",
    "deprecated": "已废弃模块",
    "ignore": "忽略模块",
    "preview": "预览模块",
}

# Qt module descriptions (Chinese) - Complete list based on .gitmodules
QT_MODULE_DESCRIPTIONS: Dict[str, str] = {
    # Core modules (essential) - 不建议跳过
    "qtbase": "Qt核心模块(基础类库)",
    "qtdeclarative": "QML/Qt Quick核心",
    "qtmultimedia": "多媒体框架",
    "qttools": "开发工具和IDE组件",
    "qttranslations": "Qt界面翻译文件",
    "qtdoc": "Qt文档和示例",
    "qtgraphicaleffects": "图形特效组件",
    "qtquickcontrols2": "Qt Quick Controls 2",
    # Addon modules - 可选择性跳过
    "qtsvg": "SVG图形支持",
    "qtactiveqt": "ActiveX/COM控件(Windows)",
    "qtscript": "JavaScript脚本引擎(已废弃)",
    "qtxmlpatterns": "XML模式和XPath",
    "qtlocation": "地理定位和地图",
    "qtsensors": "设备传感器接口",
    "qtconnectivity": "蓝牙/NFC连接",
    "qtwayland": "Wayland显示协议",
    "qt3d": "3D图形和场景",
    "qtimageformats": "扩展图片格式",
    "qtquickcontrols": "Qt Quick Controls 1",
    "qtserialbus": "串行总线(CAN/Modbus)",
    "qtserialport": "串口通信",
    "qtx11extras": "X11扩展API",
    "qtmacextras": "macOS扩展API",
    "qtwinextras": "Windows扩展API",
    "qtandroidextras": "Android扩展API",
    "qtwebsockets": "WebSocket协议",
    "qtwebchannel": "Web与Qt通信",
    "qtwebengine": "Chromium Web引擎",
    "qtwebview": "Web视图组件",
    "qtpurchasing": "应用内购买",
    "qtcharts": "图表组件",
    "qtdatavis3d": "3D数据可视化",
    "qtvirtualkeyboard": "虚拟键盘",
    "qtgamepad": "游戏手柄支持",
    "qtscxml": "状态机SCXML",
    "qtspeech": "语音合成识别",
    "qtnetworkauth": "网络认证OAuth",
    "qtremoteobjects": "远程对象通信",
    "qtwebglplugin": "WebGL流媒体",
    "qtlottie": "Lottie动画支持",
    "qtquicktimeline": "Quick时间线动画",
    "qtquick3d": "Qt Quick 3D",
    "qtknx": "KNX智能家居协议",
    "qtmqtt": "MQTT协议",
    "qtopcua": "OPC UA工业协议",
    "qtcoap": "CoAP协议",
    "qtohosextras": "HarmonyOS扩展API",
    # Ignore/Deprecated modules - 建议跳过
    "qtsystems": "系统信息(已废弃)",
    "qtfeedback": "触觉反馈(已废弃)",
    "qtpim": "个人信息管理(已废弃)",
    "qtcanvas3d": "Canvas 3D(已废弃)",
    "qtrepotools": "仓库管理工具",
    "qtqa": "Qt质量保证测试",
    "qtdocgallery": "文档库查看(已废弃)",
}

# Module status mapping (based on .gitmodules status field)
QT_MODULE_STATUS_MAP: Dict[str, str] = {
    # Essential - 核心模块，不建议跳过
    "qtbase": "essential",
    "qtdeclarative": "essential",
    "qtmultimedia": "essential",
    "qttools": "essential",
    "qttranslations": "essential",
    "qtdoc": "essential",
    "qtgraphicaleffects": "essential",
    "qtquickcontrols2": "essential",
    # Addon - 扩展模块
    "qtsvg": "addon",
    "qtactiveqt": "addon",
    "qtscript": "deprecated",
    "qtxmlpatterns": "deprecated",
    "qtlocation": "addon",
    "qtsensors": "addon",
    "qtconnectivity": "addon",
    "qtwayland": "addon",
    "qt3d": "addon",
    "qtimageformats": "addon",
    "qtquickcontrols": "addon",
    "qtserialbus": "addon",
    "qtserialport": "addon",
    "qtx11extras": "addon",
    "qtmacextras": "addon",
    "qtwinextras": "addon",
    "qtandroidextras": "addon",
    "qtwebsockets": "addon",
    "qtwebchannel": "addon",
    "qtwebengine": "addon",
    "qtwebview": "addon",
    "qtpurchasing": "addon",
    "qtcharts": "addon",
    "qtdatavis3d": "addon",
    "qtvirtualkeyboard": "addon",
    "qtgamepad": "addon",
    "qtscxml": "addon",
    "qtspeech": "addon",
    "qtnetworkauth": "addon",
    "qtremoteobjects": "addon",
    "qtwebglplugin": "addon",
    "qtlottie": "addon",
    "qtquicktimeline": "addon",
    "qtquick3d": "addon",
    "qtknx": "addon",
    "qtmqtt": "addon",
    "qtopcua": "preview",
    "qtcoap": "addon",
    "qtohosextras": "addon",
    # Ignore - 忽略/已废弃
    "qtsystems": "ignore",
    "qtfeedback": "ignore",
    "qtpim": "ignore",
    "qtcanvas3d": "ignore",
    "qtrepotools": "essential",  # 构建工具，不参与编译
    "qtqa": "essential",  # QA工具，不参与编译
    "qtdocgallery": "ignore",
}

# Modules available for Qt 5.12 HarmonyOS
QT512_AVAILABLE_MODULES: List[str] = [
    # Core
    "qtbase", "qtdeclarative", "qtmultimedia", "qttools", "qttranslations",
    "qtdoc", "qtgraphicaleffects", "qtquickcontrols2",
    # Addon
    "qtsvg", "qtactiveqt", "qtscript", "qtxmlpatterns",
    "qtlocation", "qtsensors", "qtconnectivity", "qtwayland",
    "qt3d", "qtimageformats", "qtquickcontrols",
    "qtserialbus", "qtserialport",
    "qtx11extras", "qtmacextras", "qtwinextras", "qtandroidextras",
    "qtwebsockets", "qtwebchannel", "qtwebengine", "qtwebview",
    "qtpurchasing", "qtcharts", "qtdatavis3d",
    "qtvirtualkeyboard", "qtgamepad", "qtscxml", "qtspeech",
    "qtnetworkauth", "qtremoteobjects", "qtwebglplugin",
    # HarmonyOS specific
    "qtohosextras",
    # Ignore (should be skipped)
    "qtsystems", "qtfeedback", "qtpim", "qtcanvas3d", "qtdocgallery",
]

# Modules available for Qt 5.15 HarmonyOS (includes more modules)
QT515_AVAILABLE_MODULES: List[str] = [
    # Core
    "qtbase", "qtdeclarative", "qtmultimedia", "qttools", "qttranslations",
    "qtdoc", "qtgraphicaleffects", "qtquickcontrols2",
    # Addon
    "qtsvg", "qtactiveqt", "qtscript", "qtxmlpatterns",
    "qtlocation", "qtsensors", "qtconnectivity", "qtwayland",
    "qt3d", "qtimageformats", "qtquickcontrols",
    "qtserialbus", "qtserialport",
    "qtx11extras", "qtmacextras", "qtwinextras", "qtandroidextras",
    "qtwebsockets", "qtwebchannel", "qtwebengine", "qtwebview",
    "qtpurchasing", "qtcharts", "qtdatavis3d",
    "qtvirtualkeyboard", "qtgamepad", "qtscxml", "qtspeech",
    "qtnetworkauth", "qtremoteobjects", "qtwebglplugin",
    "qtlottie", "qtquicktimeline", "qtquick3d",
    "qtknx", "qtmqtt", "qtopcua", "qtcoap",
    # HarmonyOS specific
    "qtohosextras",
    # Ignore (should be skipped)
    "qtsystems", "qtfeedback", "qtpim", "qtcanvas3d", "qtdocgallery",
]

# Modules that should NEVER be skipped (essential for HarmonyOS)
ESSENTIAL_MODULES: List[str] = [
    "qtbase",  # Qt核心
    "qtdeclarative",  # QML/Quick核心
]


def get_module_description(module: str) -> str:
    """
    Get Chinese description for a Qt module.

    Args:
        module: Module name (e.g., "qt3d", "qtwebengine")

    Returns:
        Chinese description string
    """
    return QT_MODULE_DESCRIPTIONS.get(module, "未定义模块")


def get_module_status(module: str) -> str:
    """
    Get module status type.

    Args:
        module: Module name

    Returns:
        Status string: essential, addon, deprecated, ignore, preview
    """
    return QT_MODULE_STATUS_MAP.get(module, "addon")


def is_module_essential(module: str) -> bool:
    """
    Check if a module is essential and should not be skipped.

    Args:
        module: Module name

    Returns:
        True if essential, False otherwise
    """
    return module in ESSENTIAL_MODULES


def get_available_modules(version: str, qt_source_path: Optional[Path] = None) -> List[str]:
    """
    Get available modules for a Qt version.
    Optionally filter by modules actually present in source tree.

    Args:
        version: Qt version string (e.g., "5.12.12", "5.15.16")
        qt_source_path: Optional path to Qt source to filter existing modules

    Returns:
        List of available module names
    """
    # Determine base module list based on version
    parts = version.split(".")
    if len(parts) >= 2:
        major = int(parts[0]) if parts[0].isdigit() else 5
        minor = int(parts[1]) if parts[1].isdigit() else 15

        if major == 5 and minor >= 15:
            base_modules = QT515_AVAILABLE_MODULES.copy()
        elif major == 5 and minor >= 12:
            base_modules = QT512_AVAILABLE_MODULES.copy()
        else:
            base_modules = QT515_AVAILABLE_MODULES.copy()
    else:
        base_modules = QT515_AVAILABLE_MODULES.copy()

    # Filter by actual source modules if path provided
    if qt_source_path and qt_source_path.exists():
        existing_modules = []
        for module in base_modules:
            module_path = qt_source_path / module
            if module_path.exists() and module_path.is_dir():
                existing_modules.append(module)
        return existing_modules

    return base_modules


# Common skip modules for Qt 5.12 HarmonyOS build
COMMON_SKIP_MODULES: List[str] = [
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

# Qt 5.15 recommended skip modules for HarmonyOS
QT15_SKIP_MODULES: List[str] = [
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


# Version-specific configurations
QT_VERSION_CONFIGS: Dict[str, Dict[str, Any]] = {
    "5.12.12": {
        "skip_modules": COMMON_SKIP_MODULES,
        "c++std": "c++14",
        "opengl": ["es2", "opengles3"],
        "extra_configure_options": ["-no-dbus"],
        "notes": "Qt 5.12 LTS - uses -ohos-arch parameter, dbus disabled for HarmonyOS"
    },
    "5.15.16": {
        "skip_modules": QT15_SKIP_MODULES,
        "c++std": "c++14",
        "opengl": ["es2", "opengles3"],
        "extra_configure_options": ["-no-dbus"],
        "notes": "Qt 5.15 LTS - recommended skip modules for HarmonyOS, dbus disabled"
    },
}

# Default configuration for unknown versions
DEFAULT_CONFIG: Dict[str, Any] = {
    "skip_modules": COMMON_SKIP_MODULES,
    "c++std": "c++14",
    "opengl": ["es2", "opengles3"],
    "extra_configure_options": ["-no-dbus"],
    "notes": "Using default configuration, dbus disabled for HarmonyOS"
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