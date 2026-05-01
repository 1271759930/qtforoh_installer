@echo off
REM Qt for HarmonyOS Environment Setup

SET NATIVE_OHOS_SDK=D:\DevEco\sdk\default\openharmony\native
SET OHOS_SDK_SYSROOT=D:\DevEco\sdk\default\openharmony\native\sysroot
SET LLVM_INSTALL_DIR=D:\DevEco\sdk\default\openharmony\native\llvm
SET OHOS_SDK_ROOT=D:\DevEco\sdk\default\openharmony
SET HOS_SDK_HOME=D:\DevEco\sdk\default\openharmony
SET QT5_ROOT_DIR=D:\code\tqtc-qt5
SET QT_INSTALL_PATH=D:\code\qt_install\Qt5.12.12-arm64-v8a\Qt5.12.12-arm64-v8a
SET QT_ARCH=arm64-v8a
SET QT_BUILD_TYPE=release
SET OHOS_TARGET_ARCH=arm64-v8a
SET PATH=D:\DevEco\sdk\default\openharmony\native\llvm\bin;D:\code\qtohos_installer\tools\perl\perl\bin;D:\code\qtohos_installer\tools\llvm-mingw\bin;C:\Windows\System32;C:\Windows;C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64
SET MINGW_ROOT=D:\code\qtohos_installer\tools\llvm-mingw\bin
SET PERL_ROOT=D:\code\qtohos_installer\tools\perl
SET PYTHON_ROOT=C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64

echo Environment variables set successfully.
echo Run this script before building Qt.
