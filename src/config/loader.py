"""
Configuration loader and saver
"""

from pathlib import Path
from typing import Optional
import yaml

from .schema import InstallConfig, ToolConfig
from .defaults import get_default_skip_modules


class ConfigManager:
    """Configuration file manager"""

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

                # Initialize skip_modules if empty
                if not self.install_config.skip_modules:
                    self.install_config.skip_modules = get_default_skip_modules(
                        self.install_config.qt_version
                    )

                if "tools" in data:
                    self.tool_config.make_url = data["tools"].get(
                        "make_url", self.tool_config.make_url
                    )
                    self.tool_config.perl_url = data["tools"].get(
                        "perl_url", self.tool_config.perl_url
                    )
                return True
        except Exception as e:
            print(f"Failed to load config: {e}")

        return False

    def create_config(
        self,
        qt_source_path: Path,
        harmony_sdk_path: Path,
        install_path: Path,
        architecture: str = "arm64-v8a",
        qt_version: str = "5.15.16",
        build_type: str = "release",
        parallel_jobs: int = 8,
        make_path: Optional[Path] = None,
        perl_path: Optional[Path] = None,
        python_path: Optional[Path] = None,
        version_source: str = "default",
    ) -> InstallConfig:
        """Create a new configuration with defaults"""
        skip_modules = get_default_skip_modules(qt_version)

        self.install_config = InstallConfig(
            qt_source_path=qt_source_path,
            harmony_sdk_path=harmony_sdk_path,
            install_path=install_path,
            architecture=architecture,
            qt_version=qt_version,
            build_type=build_type,
            parallel_jobs=parallel_jobs,
            skip_modules=skip_modules,
            make_path=make_path,
            perl_path=perl_path,
            python_path=python_path,
            version_source=version_source,
        )

        return self.install_config