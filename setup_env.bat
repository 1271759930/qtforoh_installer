@echo off
REM Qt for HarmonyOS Environment Setup

SET NATIVE_OHOS_SDK=D:\DevEco\sdk\default\openharmony\native
SET OHOS_SDK_SYSROOT=D:\DevEco\sdk\default\openharmony\native\sysroot
SET LLVM_INSTALL_DIR=D:\DevEco\sdk\default\openharmony\native\llvm
SET OHOS_SDK_ROOT=D:\DevEco\sdk\default\openharmony
SET HOS_SDK_HOME=D:\DevEco\sdk\default\openharmony
SET QT5_ROOT_DIR=D:\code\tqtc-qt5
SET QT_INSTALL_PATH=D:\code\qt_install
SET QT_ARCH=arm64-v8a
SET QT_BUILD_TYPE=release
SET PATH=D:\DevEco\sdk\default\openharmony\native\llvm\bin;D:\Tools\llvm-mingw-20260324-ucrt-x86_64\bin;D:\Tools\llvm-mingw-20260324-ucrt-x86_64;C:\Strawberry\perl\bin;C:\Strawberry\perl\site\bin;C:\Strawberry\c\bin;C:\Windows\System32;C:\Windows;C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64
SET MINGW_ROOT=D:\Tools\llvm-mingw-20260324-ucrt-x86_64\bin
SET PERL_ROOT=C:\Strawberry\perl\bin

echo Environment variables set successfully.
echo Run this script before building Qt.
