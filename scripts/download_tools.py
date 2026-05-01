#!/usr/bin/env python3
"""
Tool extractor/downloader for Qt HarmonyOS Installer

This script:
1. First checks for zip archives in tools/archives/ and extracts them
2. If archives not found, downloads them from the internet

Usage:
    python scripts/download_tools.py

After running this script, the tools will be available in:
    tools/llvm-mingw/bin/mingw32-make.exe
    tools/perl/perl/bin/perl.exe
"""

import sys
import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
ARCHIVES_DIR = TOOLS_DIR / "archives"
LLVM_MINGW_DIR = TOOLS_DIR / "llvm-mingw"
PERL_DIR = TOOLS_DIR / "perl"

LLVM_MINGW_ARCHIVE = ARCHIVES_DIR / "llvm-mingw-20260421-ucrt-x86_64.zip"
PERL_ARCHIVE = ARCHIVES_DIR / "strawberry-perl-5.42.2.1-64bit-portable.zip"

# GitCode release URLs (https://gitcode.com/PERMISSION-DENIED/qtforoh_installer/releases/resource)
LLVM_MINGW_URL = "https://gitcode.com/PERMISSION-DENIED/qtforoh_installer/releases/download/resource/llvm-mingw-20260421-ucrt-x86_64.zip"
PERL_URL = "https://gitcode.com/PERMISSION-DENIED/qtforoh_installer/releases/download/resource/strawberry-perl-5.42.2.1-64bit-portable.zip"


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def is_lfs_pointer(file_path: Path) -> bool:
    """Check if file is a Git LFS pointer (not actual content)"""
    if not file_path.exists():
        return False
    try:
        with open(file_path, 'rb') as f:
            content = f.read(200)
            return b'version https://git-lfs.github.com/spec/v1' in content
    except:
        return False


def extract_zip(zip_path: Path, target_dir: Path, tool_name: str) -> bool:
    """Extract a zip file"""
    print(f"\n解压 {tool_name} / Extracting {tool_name}")
    print(f"  源文件 / Source: {zip_path}")
    print(f"  目标目录 / Target: {target_dir}")

    if not zip_path.exists():
        print(f"  [错误] 压缩包不存在 / [ERROR] Archive not found")
        return False

    # Check for LFS pointer
    if is_lfs_pointer(zip_path):
        print(f"  [错误] 文件是 Git LFS 指针，非实际内容 / [ERROR] File is LFS pointer, not actual content")
        print(f"  请删除该文件重新下载 / Please delete and re-download")
        return False

    zip_size = zip_path.stat().st_size
    print(f"  压缩包大小 / Archive size: {format_size(zip_size)}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = zf.namelist()
            print(f"  文件数量 / Files: {len(members)}")

            root_folder = None
            for name in members[:10]:
                if '/' in name:
                    potential_root = name.split('/')[0]
                    if all(m.startswith(potential_root + '/') or m == potential_root for m in members[:100]):
                        root_folder = potential_root
                        break

            target_dir.mkdir(parents=True, exist_ok=True)

            print(f"  正在解压... / Extracting...")
            for member in members:
                if root_folder:
                    if member == root_folder:
                        continue
                    if member.startswith(root_folder + '/'):
                        member = member[len(root_folder) + 1:]
                    elif member.startswith(root_folder):
                        member = member[len(root_folder):]

                if not member:
                    continue

                target_path = target_dir / member

                if member.endswith('/'):
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    actual_member = root_folder + '/' + member if root_folder else member
                    try:
                        with zf.open(actual_member) as src:
                            with open(target_path, 'wb') as dst:
                                dst.write(src.read())
                    except KeyError:
                        with zf.open(member) as src:
                            with open(target_path, 'wb') as dst:
                                dst.write(src.read())

        print(f"  [成功] 解压完成 / [OK] Extraction completed")
        return True

    except zipfile.BadZipFile as e:
        print(f"  [错误] 压缩包损坏 / [ERROR] Bad zip: {e}")
        return False
    except Exception as e:
        print(f"  [错误] 解压失败 / [ERROR] Extraction failed: {e}")
        return False


def download_file(url: str, target_path: Path, description: str) -> bool:
    """Download a file with progress bar"""
    print(f"\n下载 {description} / Downloading {description}")
    print(f"  URL: {url}")
    print(f"  目标 / Target: {target_path}")

    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        print("  安装依赖... / Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests", "tqdm", "-q"])
        import requests
        from tqdm import tqdm

    try:
        response = requests.get(url, stream=True, allow_redirects=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        if total_size > 0:
            print(f"  文件大小 / Size: {format_size(total_size)}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024, desc=target_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"  [成功] 下载完成 / [OK] Download completed")
        return True

    except Exception as e:
        print(f"  [错误] 下载失败 / [ERROR] Download failed: {e}")
        return False


def extract_llvm_mingw() -> bool:
    """Extract or download llvm-mingw"""
    print("=" * 60)
    print("llvm-mingw (UCRT)")
    print("=" * 60)

    make_exe = LLVM_MINGW_DIR / "bin" / "mingw32-make.exe"
    if make_exe.exists():
        print(f"\n[跳过] llvm-mingw 已存在 / [SKIP] Already exists: {LLVM_MINGW_DIR}")
        return True

    # Check if archive is LFS pointer - delete and re-download
    if LLVM_MINGW_ARCHIVE.exists() and is_lfs_pointer(LLVM_MINGW_ARCHIVE):
        print(f"\n[警告] 检测到 LFS 指针文件，删除并重新下载 / [WARN] LFS pointer detected, deleting")
        LLVM_MINGW_ARCHIVE.unlink()

    if LLVM_MINGW_ARCHIVE.exists() and not is_lfs_pointer(LLVM_MINGW_ARCHIVE):
        print(f"\n从本地压缩包解压 / Extracting from local archive")
        return extract_zip(LLVM_MINGW_ARCHIVE, LLVM_MINGW_DIR, "llvm-mingw")

    print(f"\n本地压缩包不存在，从网络下载 / Local archive not found, downloading")
    if download_file(LLVM_MINGW_URL, LLVM_MINGW_ARCHIVE, "llvm-mingw"):
        return extract_zip(LLVM_MINGW_ARCHIVE, LLVM_MINGW_DIR, "llvm-mingw")

    return False


def extract_perl() -> bool:
    """Extract or download Perl"""
    print("=" * 60)
    print("Strawberry Perl (Portable)")
    print("=" * 60)

    perl_exe = PERL_DIR / "perl" / "bin" / "perl.exe"
    if perl_exe.exists():
        print(f"\n[跳过] Perl 已存在 / [SKIP] Already exists: {PERL_DIR}")
        return True

    # Check if archive is LFS pointer - delete and re-download
    if PERL_ARCHIVE.exists() and is_lfs_pointer(PERL_ARCHIVE):
        print(f"\n[警告] 检测到 LFS 指针文件，删除并重新下载 / [WARN] LFS pointer detected, deleting")
        PERL_ARCHIVE.unlink()

    if PERL_ARCHIVE.exists() and not is_lfs_pointer(PERL_ARCHIVE):
        print(f"\n从本地压缩包解压 / Extracting from local archive")
        return extract_zip(PERL_ARCHIVE, PERL_DIR, "Perl")

    print(f"\n本地压缩包不存在，从网络下载 / Local archive not found, downloading")
    if download_file(PERL_URL, PERL_ARCHIVE, "Perl"):
        return extract_zip(PERL_ARCHIVE, PERL_DIR, "Perl")

    return False


def verify_tools() -> bool:
    """Verify all tools are properly installed"""
    print("\n" + "=" * 60)
    print("验证工具 / Verifying Tools")
    print("=" * 60)

    errors = []

    make_exe = LLVM_MINGW_DIR / "bin" / "mingw32-make.exe"
    gcc_exe = LLVM_MINGW_DIR / "bin" / "gcc.exe"
    perl_exe = PERL_DIR / "perl" / "bin" / "perl.exe"

    if make_exe.exists():
        print(f"  [OK] mingw32-make: {make_exe}")
    else:
        errors.append("mingw32-make.exe 未找到")

    if gcc_exe.exists():
        print(f"  [OK] gcc: {gcc_exe}")
    else:
        errors.append("gcc.exe 未找到")

    if perl_exe.exists():
        print(f"  [OK] perl: {perl_exe}")
    else:
        alt_perl = PERL_DIR / "bin" / "perl.exe"
        if alt_perl.exists():
            print(f"  [OK] perl: {alt_perl}")
        else:
            errors.append("perl.exe 未找到")

    if errors:
        print(f"\n[错误] 验证失败: {', '.join(errors)}")
        return False

    print("\n[成功] 所有工具验证通过!")
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("Qt HarmonyOS Installer - 工具准备")
    print("Qt HarmonyOS Installer - Tools Setup")
    print("=" * 60)
    print(f"项目根目录 / Project root: {PROJECT_ROOT}")
    print(f"工具目录 / Tools directory: {TOOLS_DIR}")
    print(f"压缩包目录 / Archives directory: {ARCHIVES_DIR}")

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)

    all_ok = True

    if not extract_llvm_mingw():
        all_ok = False

    if not extract_perl():
        all_ok = False

    if not verify_tools():
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("[成功] 所有工具已准备就绪!")
        print("[SUCCESS] All tools ready!")
        print("=" * 60)
        print("\n工具位置 / Tools location:")
        print(f"  llvm-mingw: {LLVM_MINGW_DIR}")
        print(f"  Perl: {PERL_DIR}")
        print("\n现在可以运行安装器 / You can now run the installer:")
        print("  python run.py install")
    else:
        print("[失败] 工具准备失败")
        print("[FAILED] Tools setup failed")
        print("=" * 60)

    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)