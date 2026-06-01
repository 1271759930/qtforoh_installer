@echo off
REM Qt for HarmonyOS Environment Setup - Example Template
REM Copy this file to setup_env.bat and modify paths for your environment

REM ========================================
REM HarmonyOS SDK Paths
REM ========================================
REM Update these paths to match your DevEco Studio installation

SET NATIVE_OHOS_SDK=<YOUR_SDK_PATH>\native
SET OHOS_SDK_SYSROOT=<YOUR_SDK_PATH>\native\sysroot
SET LLVM_INSTALL_DIR=<YOUR_SDK_PATH>\native\llvm
SET OHOS_SDK_ROOT=<YOUR_SDK_PATH>
SET HOS_SDK_HOME=<YOUR_SDK_PATH>

REM Example (adjust for your system):
REM SET NATIVE_OHOS_SDK=D:\DevEco\sdk\default\openharmony\native
REM SET OHOS_SDK_SYSROOT=D:\DevEco\sdk\default\openharmony\native\sysroot
REM SET LLVM_INSTALL_DIR=D:\DevEco\sdk\default\openharmony\native\llvm
REM SET OHOS_SDK_ROOT=D:\DevEco\sdk\default\openharmony
REM SET HOS_SDK_HOME=D:\DevEco\sdk\default\openharmony

REM ========================================
REM Qt Source and Installation Paths
REM ========================================

SET QT5_ROOT_DIR=<YOUR_QT_SOURCE_PATH>
SET QT_INSTALL_PATH=<YOUR_INSTALL_PATH>

REM Example:
REM SET QT5_ROOT_DIR=D:\code\tqtc-qt5
REM SET QT_INSTALL_PATH=D:\code\qt_install

REM ========================================
REM Build Configuration
REM ========================================

SET QT_ARCH=arm64-v8a
SET QT_BUILD_TYPE=release
SET OHOS_TARGET_ARCH=arm64-v8a

REM ========================================
REM Tool Paths (Required for Windows Build)
REM ========================================
REM LLVM-MinGW for host tools compilation
REM Strawberry Perl for Qt build scripts

SET MINGW_ROOT=<YOUR_MINGW_PATH>
SET PERL_ROOT=<YOUR_PERL_PATH>

REM Example:
REM SET MINGW_ROOT=D:\Tools\llvm-mingw-20260324-ucrt-x86_64\bin
REM SET PERL_ROOT=C:\Strawberry\perl\bin

REM ========================================
REM PATH Updates
REM ========================================
REM Add HOST-TOOL directories to PATH (mingw make, perl).
REM
REM WARNING: Do NOT add %LLVM_INSTALL_DIR%\bin to PATH!
REM That folder contains OHOS cross-compilers (arm64/x86_64 clang/clang++)
REM that cannot run on Windows. qmake resolves them via the NATIVE_OHOS_SDK
REM environment variable in the ohos-clang mkspec. If that folder is in
REM PATH, qmake will mistakenly try to run the cross-compilers directly
REM and fail with "Cannot run target compiler '...clang++'".

SET PATH=%MINGW_ROOT%;%PERL_ROOT%;%PATH%

echo Environment variables configured.
echo.
echo Current settings:
echo   NATIVE_OHOS_SDK:  %NATIVE_OHOS_SDK%
echo   QT5_ROOT_DIR:     %QT5_ROOT_DIR%
echo   QT_INSTALL_PATH:  %QT_INSTALL_PATH%
echo   QT_ARCH:          %QT_ARCH%
echo.
echo Run this script before building Qt:
echo   call setup_env.bat
echo   python -m src.cli install