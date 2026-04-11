"""
Default configurations and version-specific settings
"""

from typing import List, Dict, Any


# Qt module descriptions (Chinese)
QT_MODULE_DESCRIPTIONS: Dict[str, str] = {
    "qt3d": "3D图形和场景管理",
    "qtactiveqt": "ActiveX/COM控件支持(Windows)",
    "qtandroidextras": "Android平台扩展API",
    "qtcanvas3d": "Canvas 3D WebGL渲染",
    "qtconnectivity": "蓝牙/NFC连接功能",
    "qtdatavis3d": "3D数据可视化图表",
    "qtdoc": "Qt文档和示例",
    "qtdocgallery": "文档库和图片查看",
    "qtfeedback": "触觉反馈和振动控制",
    "qtgamepad": "游戏手柄/控制器支持",
    "qtgraphicaleffects": "图形特效组件",
    "qtlocation": "地理定位和地图服务",
    "qtmacextras": "macOS平台扩展API",
    "qtnetworkauth": "网络认证和OAuth",
    "qtpim": "个人信息管理(联系人/日历)",
    "qtpurchasing": "应用内购买功能",
    "qtqa": "Qt质量保证测试工具",
    "qtremoteobjects": "远程对象通信",
    "qtrepotools": "仓库管理工具",
    "qtscript": "JavaScript脚本引擎(已废弃)",
    "qtscxml": "状态机和SCXML支持",
    "qtsensors": "设备传感器接口",
    "qtserialbus": "串行总线协议(CAN/Modbus)",
    "qtserialport": "串口通信",
    "qtspeech": "语音合成和识别",
    "qtsystems": "系统信息和服务",
    "qttools": "开发工具和IDE组件",
    "qttranslations": "Qt界面翻译文件",
    "qtvirtualkeyboard": "虚拟输入键盘",
    "qtwayland": "Wayland显示协议",
    "qtwebchannel": "Web与Qt通信桥梁",
    "qtwebengine": "Chromium Web引擎",
    "qtwebglplugin": "WebGL流媒体插件",
    "qtwebsockets": "WebSocket协议",
    "qtwebview": "Web视图组件",
    "qtwinextras": "Windows平台扩展API",
    "qtx11extras": "X11平台扩展API",
    "qtopcua": "OPC UA工业通信协议",
    "qtknx": "KNX智能家居协议",
    "doc": "文档构建工具",
}


def get_module_description(module: str) -> str:
    """
    Get Chinese description for a Qt module.

    Args:
        module: Module name (e.g., "qt3d", "qtwebengine")

    Returns:
        Chinese description string
    """
    return QT_MODULE_DESCRIPTIONS.get(module, "未定义模块")


# All available Qt modules that can be skipped
ALL_AVAILABLE_MODULES: List[str] = [
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