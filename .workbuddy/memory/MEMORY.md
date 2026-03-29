# 项目记忆

## 项目概述

**项目名称**: qtohos-installer  
**创建日期**: 2026-03-29  
**项目类型**: CLI工具  
**主要功能**: 鸿蒙版本Qt框架的交互式安装工具

## 项目目标

开发一个CLI工具，用于自动化安装Qt for HarmonyOS：
1. 交互式收集配置信息（Qt源码路径、鸿蒙SDK路径、安装路径）
2. 自动下载所需工具（make、perl）
3. 配置编译环境变量
4. 执行Qt的configure、build、install流程

## 技术栈

- **语言**: Python 3.12+
- **CLI框架**: Click + Questionary
- **UI增强**: Rich（进度显示、彩色输出）
- **依赖管理**: pip + pyproject.toml

## 项目结构

```
qtohos_installer/
├── src/                    # 核心源代码
│   ├── cli.py             # CLI入口（使用Click）
│   ├── interactive.py     # 交互式输入（使用Questionary）
│   ├── downloader.py      # 工具下载模块
│   ├── environment.py     # 环境变量配置
│   ├── builder.py         # Qt编译执行
│   ├── installer.py       # 安装流程控制
│   ├── config.py          # 配置管理
│   └ utils.py             # 工具函数
├── tools/                  # 下载的工具存放目录
├── logs/                   # 日志文件目录
├── pyproject.toml          # Python项目配置
├── requirements.txt        # 依赖列表
├── README.md               # 项目说明
├── USAGE.md                # 详细使用指南
├── config.example.yaml     # 配置示例
├── setup.bat/sh            # 快速安装脚本
└── quick_start.py          # 快速启动脚本
```

## 核心模块设计

### 1. CLI模块 (cli.py)
- 使用Click框架实现命令行接口
- 提供多个子命令：install, config, check, guide, clean
- 支持版本显示和帮助信息

### 2. 交互式输入 (interactive.py)
- 使用Questionary实现友好的交互界面
- 支持路径验证和自动补全
- 提供配置确认和修改功能

### 3. 工具下载 (downloader.py)
- 自动检测make和perl是否已安装
- Windows平台支持通过winget/chocolatey安装
- 提供手动下载指引

### 4. 环境配置 (environment.py)
- 设置所有必要的编译环境变量
- 支持Windows和Unix平台
- 生成环境设置脚本（setup_env.bat/sh）

### 5. Qt编译 (builder.py)
- 生成正确的configure命令
- 执行make编译和安装
- 提供进度显示和错误处理

### 6. 安装流程 (installer.py)
- 协调各模块完成完整安装流程
- 提供进度显示和状态管理
- 生成完成报告和后续步骤指引

## 编译流程参考

基于官方文档 (https://wiki.qt.io/Building_Qt_for_HarmonyOS):

1. **环境变量设置**
   - NATIVE_OHOS_SDK: HarmonyOS Native SDK路径
   - LLVM_INSTALL_DIR: LLVM编译器路径
   - OHOS_SDK_SYSROOT: SDK sysroot路径

2. **Configure命令**
   ```bash
   configure -xplatform ohos-clang \
     -ohos-arch arm64-v8a \
     -prefix /data/storage/el1/bundle/libs/arm64 \
     -extprefix <安装路径> \
     -opensource -confirm-license \
     -release \
     -skip <模块列表> \
     -nomake examples -nomake tests
   ```

3. **编译和安装**
   ```bash
   mingw32-make -j8
   mingw32-make install
   ```

## 关键特性

1. **交互式引导**: 通过问答式界面收集配置，降低使用门槛
2. **自动工具下载**: 自动检测并下载缺失的编译工具
3. **环境自动配置**: 自动设置复杂的环境变量
4. **进度实时显示**: 使用Rich库显示编译进度和状态
5. **完善的日志**: 所有操作记录到日志文件，便于问题排查
6. **配置持久化**: 保存配置文件，支持重复安装和配置修改

## 用户偏好

- 用户希望有详细的中文文档和说明
- 需要清晰的错误提示和故障排除指南
- 希望工具能尽可能自动化，减少手动操作

## 后续优化方向

1. **测试覆盖**: 添加单元测试和集成测试
2. **错误恢复**: 支持从失败的步骤继续安装
3. **多版本支持**: 支持不同Qt版本（5.12.12, 5.15.16等）
4. **图形界面**: 可考虑添加简单的GUI版本
5. **CI/CD集成**: 支持在CI/CD流程中使用
6. **更多平台**: 完善Linux和macOS支持

## 官方资源链接

- Qt for HarmonyOS Wiki: https://wiki.qt.io/Building_Qt_for_HarmonyOS
- Qt源码仓库: https://codereview.qt-project.org/qt/tqtc-qt5
- DevEco Studio: https://developer.huawei.com/consumer/cn/deveco-studio/
- HarmonyOS开发文档: https://developer.huawei.com/consumer/cn/

## 注意事项

1. **编译时间**: Qt编译可能需要1-3小时，需要提醒用户
2. **磁盘空间**: 源码+编译+安装约需10-15GB空间
3. **内存需求**: 建议至少8GB内存，16GB更佳
4. **SDK版本**: 推荐使用HarmonyOS SDK API 17（对应HarmonyOS 5）
5. **Qt分支**: 必须使用tqtc/harmonyos分支，不能使用普通Qt分支