@echo off
REM Qt for HarmonyOS Environment Setup

SET NATIVE_OHOS_SDK=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\native
SET OHOS_SDK_SYSROOT=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\native\sysroot
SET LLVM_INSTALL_DIR=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\native\llvm
SET OHOS_SDK_ROOT=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony
SET HOS_SDK_HOME=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony
SET QT5_ROOT_DIR=c:\code\tqtc-qt5
SET QT_INSTALL_PATH=C:\Qt\QtSDKs
SET QT_ARCH=arm64-v8a
SET QT_BUILD_TYPE=debug
SET OHOS_TARGET_ARCH=arm64-v8a
SET PATH=C:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\native\llvm\bin;C:\code\qtforoh_installer\tools\perl\perl\bin;C:\code\qtforoh_installer\tools\llvm-mingw\bin;tools\llvm-mingw\bin;tools\llvm-mingw;tools\perl\bin;tools\perl\site\bin;tools\c\bin;C:\Windows\System32;C:\Windows;C:\Users\lzh\AppData\Local\Programs\Python\Python314
SET MINGW_ROOT=C:\code\qtforoh_installer\tools\llvm-mingw\bin
SET PERL_ROOT=C:\code\qtforoh_installer\tools\perl
SET PYTHON_ROOT=C:\Users\lzh\AppData\Local\Programs\Python\Python314

echo Environment variables set successfully.
echo Run this script before building Qt.
