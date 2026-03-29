"""
Configuration management module
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml
import json


@dataclass
class InstallConfig:
    """Installation configuration"""
    qt_source_path: Path
    harmony_sdk_path: Path
    install_path: Path
    architecture: str = "arm64-v8a"
    qt_version: str = "5.15.16"
    build_type: str = "release"
    parallel_jobs: int = 8
    skip_modules: list = field(default_factory=lambda: [
        "qt3d", "qtactiveqt", "qtandroidextras", "qtcanvas3d",
        "qtconnectivity", "qtdatavis3d", "qtdoc", "qtdocgallery",
        "qtfeedback", "qtgamepad", "qtgraphicaleffects", "qtlocation",
        "qtmacextras", "qtnetworkauth", "qtpim", "qtpurchasing",
        "qtqa", "qtremoteobjects", "qtrepotools", "qtscript",
        "qtscxml", "qtsensors", "qtserialbus", "qtserialport",
        "qtspeech", "qtsystems", "qttools", "qttranslations",
        "qtvirtualkeyboard", "qtwayland", "qtwebchannel", "qtwebengine",
        "qtwebglplugin", "qtwebsockets", "qtwebview", "qtwinextras",
        "qtx11extras", "doc"
    ])
    # 工具路径配置（可选）
    make_path: Optional[Path] = None
    perl_path: Optional[Path] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "qt_source_path": str(self.qt_source_path),
            "harmony_sdk_path": str(self.harmony_sdk_path),
            "install_path": str(self.install_path),
            "architecture": self.architecture,
            "qt_version": self.qt_version,
            "build_type": self.build_type,
            "parallel_jobs": self.parallel_jobs,
            "skip_modules": self.skip_modules,
            "make_path": str(self.make_path) if self.make_path else None,
            "perl_path": str(self.perl_path) if self.perl_path else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstallConfig":
        """Create from dictionary"""
        make_path = data.get("make_path")
        perl_path = data.get("perl_path")

        return cls(
            qt_source_path=Path(data["qt_source_path"]),
            harmony_sdk_path=Path(data["harmony_sdk_path"]),
            install_path=Path(data["install_path"]),
            architecture=data.get("architecture", "arm64-v8a"),
            qt_version=data.get("qt_version", "5.15.16"),
            build_type=data.get("build_type", "release"),
            parallel_jobs=data.get("parallel_jobs", 8),
            skip_modules=data.get("skip_modules", []),
            make_path=Path(make_path) if make_path else None,
            perl_path=Path(perl_path) if perl_path else None,
        )


@dataclass
class ToolConfig:
    """Tool configuration"""
    make_url: str = "https://sourceforge.net/projects/mingw/files/MinGW/make/make-3.82.90/make-3.82.90-2-mingw32-bin.tar.lzma/download"
    # 使用可用的Strawberry Perl版本
    perl_url: str = "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_54002_64bit/strawberry-perl-5.40.0.2-64bit.msi"
    make_version: str = "3.82.90"
    perl_version: str = "5.40.0.2"


class ConfigManager:
    """Configuration manager"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("config.yaml")
        self.install_config: Optional[InstallConfig] = None
        self.tool_config = ToolConfig()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        if not self.install_config:
            return
        
        data = {
            "install": self.install_config.to_dict(),
            "tools": {
                "make_url": self.tool_config.make_url,
                "perl_url": self.tool_config.perl_url,
                "make_version": self.tool_config.make_version,
                "perl_version": self.tool_config.perl_version,
            }
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        if not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data and "install" in data:
                self.install_config = InstallConfig.from_dict(data["install"])
                if "tools" in data:
                    self.tool_config.make_url = data["tools"].get("make_url", self.tool_config.make_url)
                    self.tool_config.perl_url = data["tools"].get("perl_url", self.tool_config.perl_url)
                return True
        except Exception as e:
            print(f"Failed to load config: {e}")
        
        return False