# Progress 动态刷新问题修复

## 问题描述

用户反馈在输入时：
- 没有回显
- 没有光标位置显示
- 界面显示 "⠏ Collecting configuration..." 动态刷新

## 问题原因

在 `installer.py` 的 `run()` 方法中，使用了 Rich 的 `Progress` 上下文管理器：

```python
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=self.console
) as progress:
    task = progress.add_task("Initializing...", total=None)

    # ...

    progress.update(task, description="Collecting configuration...")

    # Step 3: Get configuration
    config = self.load_or_prompt_config()  # 这里调用交互式输入
```

**问题**：
- Progress 会持续动态刷新显示
- 在调用 `load_or_prompt_config()` 进行交互式输入时，Progress 仍在运行
- 动态刷新会干扰正常的输入显示，导致回显和光标位置不正常

## 解决方案

移除 Progress 动态刷新，改用简单的状态提示：

```python
def run(self) -> bool:
    try:
        # Step 1: Initialize
        self.console.print("\n[bold cyan]Step 1: Initializing...[/bold cyan]")
        if not self.initialize():
            return False

        # Step 2: Check prerequisites
        self.console.print("\n[bold cyan]Step 2: Checking prerequisites...[/bold cyan]")
        if not self.check_prerequisites():
            self.console.print(
                "\n[yellow]Please install missing prerequisites and try again[/yellow]"
            )
            return False

        # Step 3: Get configuration
        self.console.print("\n[bold cyan]Step 3: Collecting configuration...[/bold cyan]")
        config = self.load_or_prompt_config()
        if not config:
            return False

        # ... 其他步骤
```

## 修改内容

### 文件：`src/installer.py`

1. **移除导入**：
   ```python
   # 移除
   from rich.progress import Progress, SpinnerColumn, TextColumn
   ```

2. **重写 run() 方法**：
   - 移除 Progress 上下文管理器
   - 使用简单的 console.print() 显示步骤
   - 每个步骤有清晰的标题和编号

## 效果对比

### 修改前

```
Step 1: Qt Source Code Path
Please specify the path to Qt source code (tqtc-qt5).
This should contain the Qt source files for HarmonyOS.

╭──────────────────────╮
│ Qt source code path: │
╰──────────────────────╯
⠏ Collecting configuration...  ← 动态刷新，干扰输入
```

### 修改后

```
Step 3: Collecting configuration...

Step 1: Qt Source Code Path
Please specify the path to Qt source code (tqtc-qt5).
This should contain the Qt source files for HarmonyOS.

╭──────────────────────╮
│ Qt source code path: │
╰──────────────────────╯

Enter path: D:\code\tqtc-qt5_  ← 正常显示，有光标
```

## 优势

1. **清晰的步骤显示** - 每个步骤都有编号和标题
2. **无干扰输入** - 输入时没有动态刷新干扰
3. **正常的光标显示** - 可以看到输入位置
4. **正常的回显** - 输入内容正常显示

## 测试

运行以下命令测试修复效果：

```bash
python -m src.cli install
```

现在应该可以看到：
- ✅ 清晰的步骤提示
- ✅ 正常的输入框
- ✅ 可见的光标位置
- ✅ 正常的输入回显

## 注意事项

- 所有步骤都使用简单的文本提示
- 不再使用动态刷新的进度指示器
- 长时间操作（如编译）会在 builder.py 中显示进度
- 交互式输入不受任何干扰