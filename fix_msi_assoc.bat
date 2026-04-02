@echo off
echo 正在修复 MSI 文件关联...
echo.

:: 需要管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 需要管理员权限运行此脚本
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

:: 修复 MSI 文件关联
assoc .msi=MsiPackage
ftype MsiPackage="%SystemRoot%\System32\msiexec.exe" /i "%1" %*

echo.
echo ✓ MSI 文件关联已修复
echo 你现在可以双击 MSI 文件进行安装了
pause