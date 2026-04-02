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
:: 配置参数 - 请根据实际路径修改
:: ==============================================

:: Qt源码路径
set "QT_DIR=D:\code\tqtc-qt5"

:: HarmonyOS SDK路径 (指向native目录的父目录)
set "OHOS_SDK_PATH=D:\DevEco\sdk\default\openharmony"

:: 目标架构 (arm64-v8a, armeabi-v7a, x86_64)
set "OHOS_ARCH=arm64-v8a"

:: MinGW路径 (包含mingw32-make.exe, gcc.exe, g++.exe的bin目录)
set "MINGW_BIN=C:\mingw64\bin"

:: Perl路径 (Strawberry Perl的bin目录)
set "PERL_BIN=C:\StrawberryPerl\perl\bin"

:: 构建目录
set "BUILD_DIR=D:\code\build_%OHOS_ARCH%"

:: 安装目录
set "INSTALL_DIR=D:\code\Qt_%OHOS_ARCH%_bin"

:: 并行编译任务数 (建议设置为CPU核心数)
set "JOBS=8"

:: ==============================================
:: 验证路径
:: ==============================================

echo.
echo !CYAN![验证路径]!NC!

if not exist "%QT_DIR%\configure.bat" (
    echo !RED![错误] Qt源码路径无效: %QT_DIR%!NC!
    echo 请检查 QT_DIR 设置
    exit /b 1
)
echo !GREEN![√] Qt源码: %QT_DIR%!NC!

if not exist "%OHOS_SDK_PATH%\native\llvm" (
    echo !RED![错误] HarmonyOS SDK路径无效: %OHOS_SDK_PATH%!NC!
    echo 请检查 OHOS_SDK_PATH 设置
    exit /b 1
)
echo !GREEN![√] HarmonyOS SDK: %OHOS_SDK_PATH%!NC!

if not exist "%MINGW_BIN%\mingw32-make.exe" (
    echo !RED![错误] MinGW路径无效: %MINGW_BIN%!NC!
    echo !YELLOW![提示] 请安装MinGW-w64或配置正确的 MINGW_BIN 路径!NC!
    echo    下载地址: https://sourceforge.net/projects/mingw-w64/
    exit /b 1
)
echo !GREEN![√] MinGW: %MINGW_BIN%!NC!

if not exist "%PERL_BIN%\perl.exe" (
    echo !RED![错误] Perl路径无效: %PERL_BIN%!NC!
    echo !YELLOW![提示] 请安装Strawberry Perl或配置正确的 PERL_BIN 路径!NC!
    echo    下载地址: https://strawberryperl.com/
    exit /b 1
)
echo !GREEN![√] Perl: %PERL_BIN%!NC!

:: ==============================================
:: 关键步骤: 重置PATH避免MSVC污染
:: 参考项目 config.py 第131-133行
:: ==============================================

echo.
echo !CYAN![设置环境变量]!NC!

:: 重置PATH为最小值 (参考项目做法)
set "PATH=C:\Windows\System32;C:\Windows;%MINGW_BIN%;%PERL_BIN%"

:: 添加 LLVM 到 PATH
set "LLVM_BIN=%OHOS_SDK_PATH%\native\llvm\bin"
if exist "%LLVM_BIN%" (
    set "PATH=%PATH%;%LLVM_BIN%"
    echo !GREEN![√] LLVM: %LLVM_BIN%!NC!
) else (
    echo !YELLOW![警告] LLVM bin 目录不存在!NC!
)

:: 设置 SDK 相关环境变量
set "NATIVE_OHOS_SDK=%OHOS_SDK_PATH%\native"
set "OHOS_SDK_SYSROOT=%OHOS_SDK_PATH%\native\sysroot"
set "LLVM_INSTALL_DIR=%OHOS_SDK_PATH%\native\llvm"
set "OHOS_SDK_ROOT=%OHOS_SDK_PATH%"
set "HOS_SDK_HOME=%OHOS_SDK_PATH%"

:: 关键: 设置目标架构环境变量 (qmake.conf 第50行需要)
set "OHOS_TARGET_ARCH=%OHOS_ARCH%"

:: Qt相关环境变量
set "QT5_ROOT_DIR=%QT_DIR%"
set "QT_INSTALL_PATH=%INSTALL_DIR%"
set "QT_ARCH=%OHOS_ARCH%"
set "QT_BUILD_TYPE=release"

:: 设置 QMAKESPEC (宿主平台)
set "QMAKESPEC=win32-g++"

echo !GREEN![√] NATIVE_OHOS_SDK: %NATIVE_OHOS_SDK%!NC!
echo !GREEN![√] OHOS_SDK_SYSROOT: %OHOS_SDK_SYSROOT%!NC!
echo !GREEN![√] LLVM_INSTALL_DIR: %LLVM_INSTALL_DIR%!NC!
echo !GREEN![√] OHOS_TARGET_ARCH: %OHOS_TARGET_ARCH%!NC!
echo !GREEN![√] QMAKESPEC: %QMAKESPEC%!NC!

:: ==============================================
:: 编译器检测
:: ==============================================

echo.
echo !CYAN![编译器检测]!NC!

:: 检查 cl.exe (MSVC) - 不应该找到
where cl.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo !RED![×] MSVC cl.exe 在PATH中 - 这会导致问题!NC!
    for /f "tokens=*" %%i in ('where cl.exe') do echo     位置: %%i
    echo !YELLOW![警告] 请确保 PATH 不包含 MSVC 路径!NC!
) else (
    echo !GREEN![√] MSVC cl.exe 未找到 (正确)!NC!
)

:: 检查 gcc.exe
"%MINGW_BIN%\gcc.exe" --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%i in ('"%MINGW_BIN%\gcc.exe" --version 2^>nul') do (
        echo !GREEN![√] GCC: %MINGW_BIN%\gcc.exe!NC!
        goto :gcc_done
    )
) else (
    echo !RED![×] GCC 未找到或无法运行!NC!
)
:gcc_done

:: 检查 clang.exe
"%LLVM_BIN%\clang.exe" --version >nul 2>&1
if %errorlevel% equ 0 (
    echo !GREEN![√] Clang: %LLVM_BIN%\clang.exe!NC!
) else (
    echo !YELLOW![!] Clang 未找到或无法运行!NC!
)

:: 检查 mingw32-make.exe
"%MINGW_BIN%\mingw32-make.exe" --version >nul 2>&1
if %errorlevel% equ 0 (
    echo !GREEN![√] Make: %MINGW_BIN%\mingw32-make.exe!NC!
) else (
    echo !RED![×] mingw32-make 未找到!NC!
)

:: 检查 perl.exe
"%PERL_BIN%\perl.exe" -e "print $^V" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('"%PERL_BIN%\perl.exe" -e "print $^V" 2^>nul') do (
        echo !GREEN![√] Perl: %PERL_BIN%\perl.exe (v%%i)!NC!
    )
) else (
    echo !RED![×] Perl 未找到或无法运行!NC!
)

:: ==============================================
:: 准备构建目录
:: ==============================================

echo.
echo !CYAN![准备构建目录]!NC!

:: 清理旧的构建目录
if exist "%BUILD_DIR%" (
    echo !YELLOW![清理] 删除旧构建目录: %BUILD_DIR%!NC!
    rd /s /q "%BUILD_DIR%" 2>nul
)

:: 清理 config.tests 目录 (可能导致缓存问题)
if exist "D:\code\config.tests" (
    echo !YELLOW![清理] 删除 config.tests 目录!NC!
    rd /s /q "D:\code\config.tests" 2>nul
)

:: 创建构建目录
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

:: 使用 qtbase/configure.bat -top-level (参考项目推荐方式)
set "CONFIGURE_SCRIPT=%QT_DIR%\qtbase\configure.bat"

if not exist "%CONFIGURE_SCRIPT%" (
    set "CONFIGURE_SCRIPT=%QT_DIR%\configure.bat"
)

echo !CYAN![Configure 脚本] %CONFIGURE_SCRIPT%!NC!
echo.

:: 显示完整的 configure 命令
echo !CYAN![Configure 命令]!NC!
echo call "%CONFIGURE_SCRIPT%" -top-level ^
    -v ^
    -platform win32-g++ ^
    -xplatform ohos-clang ^
    -device-option OHOS_ARCH=%OHOS_ARCH% ^
    -opensource -confirm-license ^
    -no-use-gold-linker -no-gcc-sysroot ^
    -opengl es2 -opengles3 ^
    -c++std c++14 ^
    -nomake examples -nomake tests ^
    -release ^
    -prefix "/data/storage/el1/bundle/libs/%OHOS_ARCH%" ^
    -extprefix "%INSTALL_DIR%" ^
    -no-dbus ^
    -make-tool "mingw32-make -j%JOBS%" ^
    -recheck-all

echo.
echo !YELLOW![提示] Configure 可能需要几分钟时间...!NC!
echo.

:: 执行 configure
call "%CONFIGURE_SCRIPT%" -top-level ^
    -v ^
    -platform win32-g++ ^
    -xplatform ohos-clang ^
    -device-option OHOS_ARCH=%OHOS_ARCH% ^
    -opensource -confirm-license ^
    -no-use-gold-linker -no-gcc-sysroot ^
    -opengl es2 -opengles3 ^
    -c++std c++14 ^
    -nomake examples -nomake tests ^
    -release ^
    -prefix "/data/storage/el1/bundle/libs/%OHOS_ARCH%" ^
    -extprefix "%INSTALL_DIR%" ^
    -no-dbus ^
    -make-tool "mingw32-make -j%JOBS%" ^
    -recheck-all

if %errorlevel% neq 0 (
    echo.
    echo !RED![============================================]!NC!
    echo !RED![错误] Configure 失败，错误码: %errorlevel%!NC!
    echo !RED![============================================]!NC!
    popd
    exit /b %errorlevel%
)

echo.
echo !GREEN![============================================]!NC!
echo !GREEN![√] Configure 成功!NC!
echo !GREEN![============================================]!NC!

:: ==============================================
:: 编译 Qt
:: ==============================================

echo.
echo !CYAN![============================================]!NC!
echo !CYAN![开始编译 Qt]!NC!
echo !CYAN![============================================]!NC!
echo.

echo !CYAN![使用线程数] %JOBS%!NC!
echo !YELLOW![提示] 编译可能需要很长时间，请耐心等待...!NC!
echo.

mingw32-make -j%JOBS%

if %errorlevel% neq 0 (
    echo.
    echo !RED![============================================]!NC!
    echo !RED![错误] 编译失败，错误码: %errorlevel%!NC!
    echo !RED![============================================]!NC!
    popd
    exit /b %errorlevel%
)

echo.
echo !GREEN![============================================]!NC!
echo !GREEN![√] 编译成功!NC!
echo !GREEN![============================================]!NC!

:: ==============================================
:: 安装 Qt
:: ==============================================

echo.
echo !CYAN![============================================]!NC!
echo !CYAN![开始安装 Qt]!NC!
echo !CYAN![============================================]!NC!
echo.

mingw32-make install

if %errorlevel% neq 0 (
    echo.
    echo !RED![错误] 安装失败，错误码: %errorlevel%!NC!
    popd
    exit /b %errorlevel%
)

popd

:: ==============================================
:: 复制运行时依赖 DLL
:: ==============================================

echo.
echo !CYAN![复制运行时依赖]!NC!

for %%d in (libstdc++-6.dll libgcc_s_seh-1.dll libwinpthread-1.dll) do (
    if exist "%MINGW_BIN%\%%d" (
        copy /y "%MINGW_BIN%\%%d" "%INSTALL_DIR%\bin\" >nul
        echo !GREEN![√] 已复制: %%d!NC!
    ) else (
        echo !YELLOW![!] 未找到: %%d!NC!
    )
)

:: ==============================================
:: 验证安装
:: ==============================================

echo.
echo !GREEN![============================================]!NC!
echo !GREEN![√] 全部完成!]!NC!
echo !GREEN![============================================]!NC!
echo.

if exist "%INSTALL_DIR%\bin\qmake.exe" (
    echo !GREEN![√] qmake.exe 已生成!NC!
    echo.
    echo Qt 安装路径: %INSTALL_DIR%
    echo.
    echo 验证 Qt 版本:
    "%INSTALL_DIR%\bin\qmake.exe" -query QT_VERSION
) else (
    echo !YELLOW![!] qmake.exe 未找到，安装可能不完整!NC!
)

echo.
echo 完成！

exit /b 0