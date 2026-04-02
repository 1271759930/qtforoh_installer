@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ==============================================
:: Qt for HarmonyOS Configure and Build Script
:: Based on: https://gitcode.com/qtforohos/Build
:: ==============================================

:: 颜色输出
for /f "tokens=* usebackq" %%f in (`echo prompt $E^| cmd`) do @set "ESC=%%f"
set "RED=!ESC![91m"
set "GREEN=!ESC![92m"
set "YELLOW=!ESC![93m"
set "CYAN=!ESC![96m"
set "NC=!ESC![0m"

:: ==============================================
:: 默认配置参数
:: ==============================================

:: Qt源码路径
set "QT_DIR=D:\code\tqtc-qt5"

:: HarmonyOS SDK路径
set "OHOS_SDK_PATH=D:\DevEco\sdk\default\openharmony"

:: 目标架构
set "OHOS_ARCH=arm64-v8a"

:: 构建目录
set "BUILD_DIR=D:\code\build_%OHOS_ARCH%"

:: 安装目录
set "INSTALL_DIR=D:\code\Qt_%OHOS_ARCH%_bin"

:: 并行编译任务数
set "JOBS=8"

:: 配置文件路径
set "CONFIG_FILE=%~dp0build-config.cfg"

:: ==============================================
:: 主菜单
:: ==============================================

:MAIN_MENU
cls
echo.
echo !CYAN!==============================================!NC!
echo !CYAN!  Qt for HarmonyOS 构建脚本!NC!
echo !CYAN!==============================================!NC!
echo.
echo 当前配置:
echo.
echo   [1] Qt源码路径:     !GREEN!%QT_DIR%!NC!
echo   [2] HarmonyOS SDK:   !GREEN!%OHOS_SDK_PATH%!NC!
echo   [3] 目标架构:        !GREEN!%OHOS_ARCH%!NC!
echo   [4] MinGW路径:       !GREEN!%MINGW_BIN%!NC!
echo   [5] Perl路径:        !GREEN!%PERL_BIN%!NC!
echo   [6] 并行任务数:      !GREEN!%JOBS%!NC!
echo   [7] 构建目录:        %BUILD_DIR%
echo   [8] 安装目录:        %INSTALL_DIR%
echo.
echo !CYAN!----------------------------------------------!NC!
echo.
echo   [C] 配置路径 (设置MinGW/Perl等)
echo   [D] 检测已安装工具
echo   [S] 保存配置到文件
echo   [L] 加载已保存配置
echo.
echo   [R] 运行构建
echo   [Q] 退出
echo.
set /p "CHOICE=请选择: "

if /i "%CHOICE%"=="1" goto SET_QT_DIR
if /i "%CHOICE%"=="2" goto SET_SDK_PATH
if /i "%CHOICE%"=="3" goto SET_ARCH
if /i "%CHOICE%"=="4" goto SET_MINGW
if /i "%CHOICE%"=="5" goto SET_PERL
if /i "%CHOICE%"=="6" goto SET_JOBS
if /i "%CHOICE%"=="7" goto SET_BUILD_DIR
if /i "%CHOICE%"=="8" goto SET_INSTALL_DIR
if /i "%CHOICE%"=="C" goto CONFIG_ALL
if /i "%CHOICE%"=="D" goto DETECT_TOOLS
if /i "%CHOICE%"=="S" goto SAVE_CONFIG
if /i "%CHOICE%"=="L" goto LOAD_CONFIG
if /i "%CHOICE%"=="R" goto RUN_BUILD
if /i "%CHOICE%"=="Q" exit /b 0
goto MAIN_MENU

:: ==============================================
:: 配置各路径
:: ==============================================

:SET_QT_DIR
set /p "QT_DIR=请输入Qt源码路径: "
goto MAIN_MENU

:SET_SDK_PATH
set /p "OHOS_SDK_PATH=请输入HarmonyOS SDK路径: "
goto MAIN_MENU

:SET_ARCH
echo.
echo 可选架构:
echo   1. arm64-v8a    (64位ARM，推荐)
echo   2. armeabi-v7a  (32位ARM)
echo   3. x86_64       (64位x86模拟器)
echo.
set /p "ARCH_CHOICE=请选择 (1/2/3): "
if "%ARCH_CHOICE%"=="1" set "OHOS_ARCH=arm64-v8a"
if "%ARCH_CHOICE%"=="2" set "OHOS_ARCH=armeabi-v7a"
if "%ARCH_CHOICE%"=="3" set "OHOS_ARCH=x86_64"
set "BUILD_DIR=D:\code\build_%OHOS_ARCH%"
set "INSTALL_DIR=D:\code\Qt_%OHOS_ARCH%_bin"
goto MAIN_MENU

:SET_MINGW
echo.
echo 当前MinGW路径: %MINGW_BIN%
echo.
set /p "MINGW_BIN=请输入MinGW bin目录路径 (包含mingw32-make.exe): "
if exist "%MINGW_BIN%\mingw32-make.exe" (
    echo !GREEN![√] mingw32-make.exe 找到!NC!
) else (
    echo !RED![×] mingw32-make.exe 未找到，请检查路径!NC!
)
goto MAIN_MENU

:SET_PERL
echo.
echo 当前Perl路径: %PERL_BIN%
echo.
set /p "PERL_BIN=请输入Perl bin目录路径 (包含perl.exe): "
if exist "%PERL_BIN%\perl.exe" (
    echo !GREEN![√] perl.exe 找到!NC!
    "%PERL_BIN%\perl.exe" -e "print 'Perl版本: ' . $^V"
    echo.
) else (
    echo !RED![×] perl.exe 未找到，请检查路径!NC!
)
goto MAIN_MENU

:SET_JOBS
set /p "JOBS=请输入并行编译任务数 (建议为CPU核心数): "
goto MAIN_MENU

:SET_BUILD_DIR
set /p "BUILD_DIR=请输入构建目录路径: "
goto MAIN_MENU

:SET_INSTALL_DIR
set /p "INSTALL_DIR=请输入安装目录路径: "
goto MAIN_MENU

:: ==============================================
:: 批量配置
:: ==============================================

:CONFIG_ALL
call :CONFIG_MINGW
call :CONFIG_PERL
goto MAIN_MENU

:CONFIG_MINGW
echo.
echo !CYAN![配置 MinGW]!NC!
echo.

:: 自动检测常见路径
for %%p in (
    "C:\mingw64\bin"
    "C:\mingw\bin"
    "D:\mingw64\bin"
    "D:\mingw\bin"
    "%USERPROFILE%\mingw64\bin"
    "C:\Program Files\mingw64\bin"
) do (
    if exist %%p\mingw32-make.exe (
        echo !GREEN!检测到 MinGW: %%p!NC!
        set "DETECTED_MINGW=%%p"
        goto :mingw_detected
    )
)

:mingw_detected
if defined DETECTED_MINGW (
    echo.
    set /p "USE_DETECTED=使用检测到的路径? [Y/n]: "
    if /i "!USE_DETECTED!"=="n" (
        set /p "MINGW_BIN=请输入MinGW bin目录路径: "
    ) else (
        set "MINGW_BIN=!DETECTED_MINGW!"
    )
) else (
    echo !YELLOW!未自动检测到MinGW，请手动输入路径!NC!
    echo 常见安装位置:
    echo   - C:\mingw64\bin
    echo   - 从 https://sourceforge.net/projects/mingw-w64/ 下载
    echo.
    set /p "MINGW_BIN=请输入MinGW bin目录路径: "
)

if exist "%MINGW_BIN%\mingw32-make.exe" (
    echo !GREEN![√] MinGW配置成功: %MINGW_BIN%!NC!
    "%MINGW_BIN%\gcc.exe" --version 2>nul | findstr "gcc"
) else (
    echo !RED![×] mingw32-make.exe 未找到!NC!
)
exit /b 0

:CONFIG_PERL
echo.
echo !CYAN![配置 Perl]!NC!
echo.

:: 自动检测常见路径
for %%p in (
    "C:\StrawberryPerl\perl\bin"
    "C:\Strawberry\perl\bin"
    "D:\StrawberryPerl\perl\bin"
    "C:\Perl\bin"
    "%USERPROFILE%\scoop\apps\strawberryperl\current\perl\bin"
) do (
    if exist %%p\perl.exe (
        echo !GREEN!检测到 Perl: %%p!NC!
        set "DETECTED_PERL=%%p"
        goto :perl_detected
    )
)

:perl_detected
if defined DETECTED_PERL (
    echo.
    set /p "USE_DETECTED=使用检测到的路径? [Y/n]: "
    if /i "!USE_DETECTED!"=="n" (
        set /p "PERL_BIN=请输入Perl bin目录路径: "
    ) else (
        set "PERL_BIN=!DETECTED_PERL!"
    )
) else (
    echo !YELLOW!未自动检测到Perl，请手动输入路径!NC!
    echo 常见安装位置:
    echo   - C:\StrawberryPerl\perl\bin
    echo   - 从 https://strawberryperl.com/ 下载
    echo.
    set /p "PERL_BIN=请输入Perl bin目录路径: "
)

if exist "%PERL_BIN%\perl.exe" (
    echo !GREEN![√] Perl配置成功: %PERL_BIN%!NC!
    "%PERL_BIN%\perl.exe" -e "print 'Perl版本: ' . $^V"
    echo.
) else (
    echo !RED![×] perl.exe 未找到!NC!
)
exit /b 0

:: ==============================================
:: 检测已安装工具
:: ==============================================

:DETECT_TOOLS
echo.
echo !CYAN![检测已安装工具]!NC!
echo.

:: 检测 MinGW
echo 检测 MinGW...
set "MINGW_FOUND=0"
for %%p in (
    "C:\mingw64\bin"
    "C:\mingw\bin"
    "D:\mingw64\bin"
    "D:\mingw\bin"
    "%USERPROFILE%\mingw64\bin"
) do (
    if exist %%p\mingw32-make.exe (
        echo   !GREEN![√] MinGW: %%p!NC!
        set "MINGW_FOUND=1"
    )
)
if "%MINGW_FOUND%"=="0" echo   !RED![×] MinGW 未找到!NC!

:: 检测 Perl
echo.
echo 检测 Perl...
set "PERL_FOUND=0"
for %%p in (
    "C:\StrawberryPerl\perl\bin"
    "C:\Strawberry\perl\bin"
    "D:\StrawberryPerl\perl\bin"
    "C:\Perl\bin"
) do (
    if exist %%p\perl.exe (
        echo   !GREEN![√] Perl: %%p!NC!
        set "PERL_FOUND=1"
    )
)
if "%PERL_FOUND%"=="0" echo   !RED![×] Perl 未找到!NC!

:: 检测 LLVM
echo.
echo 检测 LLVM (HarmonyOS SDK)...
if exist "%OHOS_SDK_PATH%\native\llvm\bin\clang.exe" (
    echo   !GREEN![√] LLVM: %OHOS_SDK_PATH%\native\llvm\bin!NC!
) else (
    echo   !RED![×] LLVM 未找到!NC!
)

echo.
pause
goto MAIN_MENU

:: ==============================================
:: 保存/加载配置
:: ==============================================

:SAVE_CONFIG
echo.
echo 保存配置到: %CONFIG_FILE%
(
    echo QT_DIR=%QT_DIR%
    echo OHOS_SDK_PATH=%OHOS_SDK_PATH%
    echo OHOS_ARCH=%OHOS_ARCH%
    echo MINGW_BIN=%MINGW_BIN%
    echo PERL_BIN=%PERL_BIN%
    echo JOBS=%JOBS%
    echo BUILD_DIR=%BUILD_DIR%
    echo INSTALL_DIR=%INSTALL_DIR%
) > "%CONFIG_FILE%"
echo !GREEN![√] 配置已保存!NC!
pause
goto MAIN_MENU

:LOAD_CONFIG
if exist "%CONFIG_FILE%" (
    echo 加载配置: %CONFIG_FILE%
    for /f "usebackq tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        set "%%a=%%b"
    )
    echo !GREEN![√] 配置已加载!NC!
) else (
    echo !YELLOW![!] 配置文件不存在: %CONFIG_FILE%!NC!
)
pause
goto MAIN_MENU

:: ==============================================
:: 运行构建
:: ==============================================

:RUN_BUILD
echo.
echo !CYAN![============================================]!NC!
echo !CYAN![开始构建]!NC!
echo !CYAN![============================================]!NC!
echo.

:: 验证必要路径
if not exist "%QT_DIR%\configure.bat" (
    echo !RED![错误] Qt源码路径无效: %QT_DIR%!NC!
    pause
    goto MAIN_MENU
)

if not exist "%OHOS_SDK_PATH%\native\llvm" (
    echo !RED![错误] HarmonyOS SDK路径无效: %OHOS_SDK_PATH%!NC!
    pause
    goto MAIN_MENU
)

if not defined MINGW_BIN (
    echo !RED![错误] MinGW路径未配置!NC!
    echo 请先选择 [C] 配置路径 或 [4] 设置MinGW路径
    pause
    goto MAIN_MENU
)

if not exist "%MINGW_BIN%\mingw32-make.exe" (
    echo !RED![错误] MinGW路径无效: %MINGW_BIN%!NC!
    pause
    goto MAIN_MENU
)

if not defined PERL_BIN (
    echo !RED![错误] Perl路径未配置!NC!
    echo 请先选择 [C] 配置路径 或 [5] 设置Perl路径
    pause
    goto MAIN_MENU
)

if not exist "%PERL_BIN%\perl.exe" (
    echo !RED![错误] Perl路径无效: %PERL_BIN%!NC!
    pause
    goto MAIN_MENU
)

:: ==============================================
:: 设置环境变量
:: ==============================================

echo.
echo !CYAN![设置环境变量]!NC!

:: 重置PATH
set "PATH=C:\Windows\System32;C:\Windows;%MINGW_BIN%;%PERL_BIN%"

:: 添加 LLVM
set "LLVM_BIN=%OHOS_SDK_PATH%\native\llvm\bin"
if exist "%LLVM_BIN%" (
    set "PATH=%PATH%;%LLVM_BIN%"
)

:: 设置环境变量
set "NATIVE_OHOS_SDK=%OHOS_SDK_PATH%\native"
set "OHOS_SDK_SYSROOT=%OHOS_SDK_PATH%\native\sysroot"
set "LLVM_INSTALL_DIR=%OHOS_SDK_PATH%\native\llvm"
set "OHOS_SDK_ROOT=%OHOS_SDK_PATH%"
set "HOS_SDK_HOME=%OHOS_SDK_PATH%"
set "OHOS_TARGET_ARCH=%OHOS_ARCH%"
set "QMAKESPEC=win32-g++"

echo !GREEN![√] 环境变量已设置!NC!
echo   NATIVE_OHOS_SDK: %NATIVE_OHOS_SDK%
echo   OHOS_TARGET_ARCH: %OHOS_TARGET_ARCH%
echo   QMAKESPEC: %QMAKESPEC%

:: ==============================================
:: 编译器检测
:: ==============================================

echo.
echo !CYAN![编译器检测]!NC!

where cl.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo !RED![×] MSVC cl.exe 在PATH中 - 可能导致问题!NC!
) else (
    echo !GREEN![√] MSVC cl.exe 未找到 (正确)!NC!
)

if exist "%MINGW_BIN%\gcc.exe" (
    echo !GREEN![√] GCC: %MINGW_BIN%\gcc.exe!NC!
) else (
    echo !RED![×] GCC 未找到!NC!
)

if exist "%LLVM_BIN%\clang.exe" (
    echo !GREEN![√] Clang: %LLVM_BIN%\clang.exe!NC!
) else (
    echo !YELLOW![!] Clang 未找到!NC!
)

:: ==============================================
:: 准备构建目录
:: ==============================================

echo.
echo !CYAN![准备构建目录]!NC!

if exist "%BUILD_DIR%" (
    echo !YELLOW![清理] 删除旧构建目录!NC!
    rd /s /q "%BUILD_DIR%" 2>nul
)

if exist "D:\code\config.tests" (
    rd /s /q "D:\code\config.tests" 2>nul
)

mkdir "%BUILD_DIR%"
echo !GREEN![√] 构建目录: %BUILD_DIR%!NC!

:: ==============================================
:: 运行 Configure
:: ==============================================

echo.
echo !CYAN![============================================]!NC!
echo !CYAN![开始 Configure]!NC!
echo !CYAN![============================================]!NC!
echo.

pushd "%BUILD_DIR%"

set "CONFIGURE_SCRIPT=%QT_DIR%\qtbase\configure.bat"
if not exist "%CONFIGURE_SCRIPT%" (
    set "CONFIGURE_SCRIPT=%QT_DIR%\configure.bat"
)

echo !CYAN![Configure命令]!NC!
echo call "%CONFIGURE_SCRIPT%" -top-level -v -platform win32-g++ -xplatform ohos-clang -device-option OHOS_ARCH=%OHOS_ARCH% ...

echo.
echo !YELLOW![提示] Configure可能需要几分钟...!NC!
echo.

call "%CONFIGURE_SCRIPT%" -top-level -v -platform win32-g++ -xplatform ohos-clang -device-option OHOS_ARCH=%OHOS_ARCH% -opensource -confirm-license -no-use-gold-linker -no-gcc-sysroot -opengl es2 -opengles3 -c++std c++14 -nomake examples -nomake tests -release -prefix "/data/storage/el1/bundle/libs/%OHOS_ARCH%" -extprefix "%INSTALL_DIR%" -no-dbus -make-tool "mingw32-make -j%JOBS%" -recheck-all

if %errorlevel% neq 0 (
    echo.
    echo !RED![错误] Configure失败!NC!
    popd
    pause
    goto MAIN_MENU
)

echo.
echo !GREEN![√] Configure成功!NC!

:: ==============================================
:: 编译
:: ==============================================

echo.
echo !CYAN![============================================]!NC!
echo !CYAN![开始编译]!NC!
echo !CYAN![============================================]!NC!
echo.

mingw32-make -j%JOBS%

if %errorlevel% neq 0 (
    echo.
    echo !RED![错误] 编译失败!NC!
    popd
    pause
    goto MAIN_MENU
)

echo.
echo !GREEN![√] 编译成功!NC!

:: ==============================================
:: 安装
:: ==============================================

echo.
echo !CYAN![开始安装]!NC!

mingw32-make install

if %errorlevel% neq 0 (
    echo !RED![错误] 安装失败!NC!
    popd
    pause
    goto MAIN_MENU
)

popd

:: 复制DLL
for %%d in (libstdc++-6.dll libgcc_s_seh-1.dll libwinpthread-1.dll) do (
    if exist "%MINGW_BIN%\%%d" (
        copy /y "%MINGW_BIN%\%%d" "%INSTALL_DIR%\bin\" >nul
        echo !GREEN![√] 已复制: %%d!NC!
    )
)

echo.
echo !GREEN![============================================]!NC!
echo !GREEN![√] 全部完成!]!NC!
echo !GREEN![============================================]!NC!
echo.
echo Qt安装路径: %INSTALL_DIR%
echo.

if exist "%INSTALL_DIR%\bin\qmake.exe" (
    "%INSTALL_DIR%\bin\qmake.exe" -query QT_VERSION
)

echo.
pause
goto MAIN_MENU