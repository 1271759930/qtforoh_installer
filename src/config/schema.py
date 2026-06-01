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
    nomake_targets: List[str] = field(default_factory=lambda: ["doc", "examples", "tests"])
    python_path: Optional[Path] = None
    version_source: str = "default"
    force_opengl_es: bool = False  # Force OpenGL ES with -opengl es2 -opengles3

    @property
    def actual_install_path(self) -> Path:
        """Get actual installation path with Qt version and architecture.
        Includes '-gles' suffix if force_opengl_es is enabled."""
        folder_name = f"Qt{self.qt_version}-{self.architecture}"
        if self.force_opengl_es:
            folder_name += "-gles"
        return self.install_path / folder_name

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
            "nomake_targets": self.nomake_targets,
            "python_path": str(self.python_path) if self.python_path else None,
            "version_source": self.version_source,
            "force_opengl_es": self.force_opengl_es,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstallConfig":
        """Create from dictionary"""
        python_path = data.get("python_path")

        return cls(
            qt_source_path=Path(data["qt_source_path"]),
            harmony_sdk_path=Path(data["harmony_sdk_path"]),
            install_path=Path(data["install_path"]),
            architecture=data.get("architecture", "arm64-v8a"),
            qt_version=data.get("qt_version", "5.15.16"),
            build_type=data.get("build_type", "release"),
            parallel_jobs=data.get("parallel_jobs", 8),
            skip_modules=data.get("skip_modules", []),
            nomake_targets=data.get("nomake_targets", ["doc", "examples", "tests"]),
            python_path=Path(python_path) if python_path else None,
            version_source=data.get("version_source", "default"),
            force_opengl_es=data.get("force_opengl_es", False),
        )


@dataclass
class ToolConfig:
    """Tool download configuration"""
    make_url: str = "https://sourceforge.net/projects/mingw/files/MinGW/make/make-3.82.90/make-3.82.90-2-mingw32-bin.tar.lzma/download"
    perl_url: str = "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/SP_54002_64bit/strawberry-perl-5.40.0.2-64bit.msi"
    make_version: str = "3.82.90"
    perl_version: str = "5.40.0.2"