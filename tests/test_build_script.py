#!/usr/bin/env python3
"""Test batch script generation"""
import sys
sys.path.insert(0, "scripts")
from pathlib import Path
import build_qt_ohos as b

data = b.load_config(Path("temp/test_gles_config.yaml"))
config = b.config_from_dict(data)
build_dir = Path("temp/test_build")
build_dir.mkdir(parents=True, exist_ok=True)

script = b._generate_bat(config, build_dir)
print("Batch script generated: {}".format(script))
print("Size: {} bytes".format(script.stat().st_size))

content = script.read_text(encoding="utf-8")
env_vars = [line for line in content.split("\n") if line.strip().startswith('set "') and "=" in line]
print("\nEnvironment variables set in batch script ({}):".format(len(env_vars)))
for v in env_vars:
    print("  " + v.strip())

print("\n--- Checking NO non-Qt variables are set ---")
non_qt_vars = ["QT5_ROOT_DIR", "QT_INSTALL_PATH", "QT_ARCH", "QT_BUILD_TYPE",
               "HOS_SDK_HOME", "PYTHON_ROOT", "PYTHON_PATH", "PYTHON_BIN"]
found_bad = False
for var in non_qt_vars:
    if var in content:
        print("  [FAIL] Found non-Qt variable: " + var)
        found_bad = True

if not found_bad:
    print("  [PASS] No non-Qt variables found in batch script")

print("\n--- Checking Qt compilation variables are present ---")
required_vars = ["NATIVE_OHOS_SDK", "OHOS_SDK_SYSROOT", "LLVM_INSTALL_DIR",
                 "OHOS_SDK_ROOT", "OHOS_TARGET_ARCH", "PERL5LIB"]
all_found = True
for var in required_vars:
    if var in content:
        print("  [PASS] " + var)
    else:
        print("  [FAIL] Missing: " + var)
        all_found = False

print("\n--- Checking cleared variables ---")
cleared_vars = ["QMAKESPEC", "XQMAKESPEC", "QMAKEPATH", "QMAKEFEATURES",
                "MAKEFLAGS", "MFLAGS"]
for var in cleared_vars:
    pattern = 'set "' + var + '="'
    if pattern in content:
        print("  [PASS] " + var + " cleared")
    else:
        print("  [FAIL] " + var + " not cleared")
