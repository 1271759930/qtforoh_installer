"""
Shared constants for Qt for HarmonyOS Installer
集中定义常量，避免重复定义
"""

from pathlib import Path

# Bundled tools directory (relative to project root)
BUNDLED_TOOLS_DIR = Path(__file__).parent.parent / "tools"

# Bundled llvm-mingw paths
BUNDLED_LLVM_MINGW_DIR = BUNDLED_TOOLS_DIR / "llvm-mingw"
BUNDLED_LLVM_MINGW_BIN = BUNDLED_LLVM_MINGW_DIR / "bin"
BUNDLED_LLVM_MINGW_MAKE = BUNDLED_LLVM_MINGW_BIN / "mingw32-make.exe"
BUNDLED_LLVM_MINGW_GCC = BUNDLED_LLVM_MINGW_BIN / "gcc.exe"

# Bundled Perl paths
BUNDLED_PERL_DIR = BUNDLED_TOOLS_DIR / "perl"
BUNDLED_PERL_BIN = BUNDLED_PERL_DIR / "perl" / "bin"
BUNDLED_PERL_BIN_ALT = BUNDLED_PERL_DIR / "bin"
BUNDLED_PERL_EXE = BUNDLED_PERL_BIN / "perl.exe"
BUNDLED_PERL_LIB = BUNDLED_PERL_DIR / "perl" / "lib"

# Archives directory
BUNDLED_ARCHIVES_DIR = BUNDLED_TOOLS_DIR / "archives"

# GitCode Release URLs for bundled tools
GITCODE_RELEASE_BASE = "https://gitcode.com/PERMISSION-DENIED/qtforoh_installer/releases/download/resource"
LLVM_MINGW_ARCHIVE_NAME = "llvm-mingw-20260421-ucrt-x86_64.zip"
PERL_ARCHIVE_NAME = "strawberry-perl-5.42.2.1-64bit-portable.zip"
LLVM_MINGW_URL = f"{GITCODE_RELEASE_BASE}/{LLVM_MINGW_ARCHIVE_NAME}"
PERL_URL = f"{GITCODE_RELEASE_BASE}/{PERL_ARCHIVE_NAME}"