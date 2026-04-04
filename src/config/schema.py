"""
Configuration data schemas - Pure data classes without business logic
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class InstallConfig:
    """Installation configuration - Pure data container"""
    qt_source_path: Path
    harmony_sdk_path: Path
    install_path: Path
    architecture: str = "arm64-v8a"
    qt_version: str = "5.15.16"
    build_type: str = "release"
    parallel_jobs: int = 8
    skip_modules: List[str] = field(default_factory=list)
    # Tool paths (optional)
    make_path: Optional[Path] = None
    perl_path: Optional[Path] = None
    # Version detection source
    version_source: str = "default"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
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
            "version_source": self.version_source,
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
            version_source=data.get("version_source", "default"),
        )


@dataclass
class ToolConfig:
    """Tool download configuration"""
    make_url: str = "https://sourceforge.net/projects/mingw/files/MinGW/make/make-3.82.90/make-3.82.90-2-mingw32-bin.tar.lzma/download"
    perl_url: str = "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_54002_64bit/strawberry-perl-5.40.0.2-64bit.msi"
    make_version: str = "3.82.90"
    perl_version: str = "5.40.0.2"