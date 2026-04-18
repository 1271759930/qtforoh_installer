#!/usr/bin/env python3
"""
Pre-download tools for Qt HarmonyOS Installer

This script downloads and extracts llvm-mingw and Strawberry Perl
into the tools directory, so users don't need to download them separately.

Usage:
    python scripts/download_tools.py

After running this script, the tools will be available in:
    tools/llvm-mingw/bin/mingw32-make.exe
    tools/perl/bin/perl.exe
"""

import sys
import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from typing import Optional

# Fix encoding for Windows
if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "tqdm", "-q"])
    import requests
    from tqdm import tqdm


PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
LLVM_MINGW_DIR = TOOLS_DIR / "llvm-mingw"
PERL_DIR = TOOLS_DIR / "perl"

# Tool versions and URLs
LLVM_MINGW_VERSION = "20240917"  # Use stable version
LLVM_MINGW_URL = (
    f"https://github.com/mstorsjo/llvm-mingw/releases/download/"
    f"{LLVM_MINGW_VERSION}/llvm-mingw-{LLVM_MINGW_VERSION}-ucrt-x86_64.zip"
)

PERL_VERSION = "5.42.2.1"
PERL_URL = (
    "https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/"
    f"SP_54221_64bit/strawberry-perl-{PERL_VERSION}-64bit-portable.zip"
)


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def download_file(url: str, target_path: Path, description: str) -> bool:
    """Download a file with progress bar"""
    print(f"\n{description}")
    print(f"  URL: {url}")
    print(f"  Target: {target_path}")

    try:
        response = requests.get(url, stream=True, allow_redirects=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        if total_size > 0:
            print(f"  Size: {format_size(total_size)}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=target_path.name
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"  Download completed: {target_path}")
        return True

    except requests.RequestException as e:
        print(f"  Download failed: {e}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def extract_zip(zip_path: Path, target_dir: Path, description: str) -> bool:
    """Extract a zip file"""
    print(f"\n{description}")
    print(f"  Source: {zip_path}")
    print(f"  Target: {target_dir}")

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            members = zf.namelist()

            # Find the root folder in the zip (often the archive contains a single folder)
            root_folder = None
            for name in members:
                if '/' in name:
                    potential_root = name.split('/')[0]
                    if all(m.startswith(potential_root + '/') or m == potential_root for m in members):
                        root_folder = potential_root
                        break

            with tqdm(total=len(members), unit="files", desc="Extracting") as pbar:
                for member in members:
                    # Skip the root folder if found
                    if root_folder:
                        if member == root_folder:
                            pbar.update(1)
                            continue
                        if member.startswith(root_folder + '/'):
                            member = member[len(root_folder) + 1:]
                        elif member.startswith(root_folder):
                            member = member[len(root_folder):]

                    if not member:
                        pbar.update(1)
                        continue

                    target_path = target_dir / member

                    if member.endswith('/'):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(zip_path.name if root_folder else member) as src:
                            # Get actual member path in zip
                            actual_member = root_folder + '/' + member if root_folder else member
                            try:
                                with zf.open(actual_member) as src:
                                    with open(target_path, 'wb') as dst:
                                        dst.write(src.read())
                            except KeyError:
                                # Try original member name
                                with zf.open(member) as src:
                                    with open(target_path, 'wb') as dst:
                                        dst.write(src.read())

                    pbar.update(1)

        print(f"  Extraction completed: {target_dir}")
        return True

    except zipfile.BadZipFile as e:
        print(f"  Bad zip file: {e}")
        return False
    except Exception as e:
        print(f"  Extraction error: {e}")
        return False


def download_llvm_mingw() -> bool:
    """Download and extract llvm-mingw"""
    print("=" * 60)
    print("Downloading llvm-mingw (UCRT version)")
    print("=" * 60)

    zip_path = TOOLS_DIR / f"llvm-mingw-{LLVM_MINGW_VERSION}-ucrt-x86_64.zip"

    if LLVM_MINGW_DIR.exists() and (LLVM_MINGW_DIR / "bin" / "mingw32-make.exe").exists():
        print(f"\n[SKIP] llvm-mingw already exists at {LLVM_MINGW_DIR}")
        return True

    if not download_file(LLVM_MINGW_URL, zip_path, "Downloading llvm-mingw"):
        return False

    if not extract_zip(zip_path, LLVM_MINGW_DIR, "Extracting llvm-mingw"):
        return False

    # Clean up zip file
    zip_path.unlink()
    print(f"  Cleaned up: {zip_path}")

    # Verify extraction
    make_exe = LLVM_MINGW_DIR / "bin" / "mingw32-make.exe"
    gcc_exe = LLVM_MINGW_DIR / "bin" / "gcc.exe"

    if make_exe.exists():
        print(f"  [OK] mingw32-make.exe: {make_exe}")
    else:
        print(f"  [ERROR] mingw32-make.exe not found")
        return False

    if gcc_exe.exists():
        print(f"  [OK] gcc.exe: {gcc_exe}")
    else:
        print(f"  [ERROR] gcc.exe not found")
        return False

    return True


def download_perl() -> bool:
    """Download and extract Strawberry Perl (portable edition)"""
    print("=" * 60)
    print("Downloading Strawberry Perl (Portable)")
    print("=" * 60)

    zip_path = TOOLS_DIR / f"strawberry-perl-{PERL_VERSION}-64bit-portable.zip"

    perl_exe = PERL_DIR / "perl" / "bin" / "perl.exe"
    if PERL_DIR.exists() and perl_exe.exists():
        print(f"\n[SKIP] Perl already exists at {PERL_DIR}")
        return True

    if not download_file(PERL_URL, zip_path, "Downloading Strawberry Perl"):
        return False

    if not extract_zip(zip_path, PERL_DIR, "Extracting Strawberry Perl"):
        return False

    # Clean up zip file
    zip_path.unlink()
    print(f"  Cleaned up: {zip_path}")

    # Verify extraction
    if perl_exe.exists():
        print(f"  [OK] perl.exe: {perl_exe}")
    else:
        # Try alternative structure
        alt_perl_exe = PERL_DIR / "bin" / "perl.exe"
        if alt_perl_exe.exists():
            print(f"  [OK] perl.exe: {alt_perl_exe}")
        else:
            print(f"  [ERROR] perl.exe not found")
            return False

    return True


def verify_tools() -> bool:
    """Verify all tools are properly installed"""
    print("\n" + "=" * 60)
    print("Verifying Tools")
    print("=" * 60)

    errors = []

    # Check llvm-mingw
    make_exe = LLVM_MINGW_DIR / "bin" / "mingw32-make.exe"
    gcc_exe = LLVM_MINGW_DIR / "bin" / "gcc.exe"
    gxx_exe = LLVM_MINGW_DIR / "bin" / "g++.exe"

    if make_exe.exists():
        print(f"  [OK] mingw32-make: {make_exe}")
    else:
        errors.append("mingw32-make.exe not found")

    if gcc_exe.exists():
        print(f"  [OK] gcc: {gcc_exe}")
    else:
        errors.append("gcc.exe not found")

    if gxx_exe.exists():
        print(f"  [OK] g++: {gxx_exe}")
    else:
        errors.append("g++.exe not found")

    # Check Perl
    perl_exe = PERL_DIR / "perl" / "bin" / "perl.exe"
    alt_perl_exe = PERL_DIR / "bin" / "perl.exe"

    if perl_exe.exists():
        print(f"  [OK] perl: {perl_exe}")
    elif alt_perl_exe.exists():
        print(f"  [OK] perl: {alt_perl_exe}")
    else:
        errors.append("perl.exe not found")

    if errors:
        print(f"\n[ERROR] Verification failed: {', '.join(errors)}")
        return False

    print("\n[SUCCESS] All tools verified successfully!")
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("Qt HarmonyOS Installer - Tools Downloader")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Tools directory: {TOOLS_DIR}")

    # Create directories
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    LLVM_MINGW_DIR.mkdir(parents=True, exist_ok=True)
    PERL_DIR.mkdir(parents=True, exist_ok=True)

    all_ok = True

    if not download_llvm_mingw():
        all_ok = False

    if not download_perl():
        all_ok = False

    if not verify_tools():
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("[SUCCESS] All tools downloaded and verified!")
        print("=" * 60)
        print("\nTools are now available at:")
        print(f"  llvm-mingw: {LLVM_MINGW_DIR}")
        print(f"  Perl: {PERL_DIR}")
        print("\nUsers can now run the installer without separate tool downloads.")
    else:
        print("[FAILED] Some tools failed to download or verify")
        print("=" * 60)
        print("\nPlease check your network connection and try again.")
        print("Alternatively, download manually:")
        print(f"  llvm-mingw: {LLVM_MINGW_URL}")
        print(f"  Perl: {PERL_URL}")

    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)