# AGENTS.md

Quick reference for OpenCode sessions working in this repo.

## Entry Points

```
python run.py              # Wrapper: checks Python >= 3.12, auto-installs deps, then runs CLI
python -m src.cli          # Direct module execution (requires deps pre-installed)
python -m src.cli install  # Interactive installation
python -m src.cli check    # Verify prerequisites
python scripts/download_tools.py  # Download bundled tools (llvm-mingw + Perl)
```

## Python Version

**Hard requirement: Python >= 3.10**. Tool will refuse to run on older versions. Check enforced in `run.py:32` and `src/core/installer.py:96`.

## Bundled Tools

Project includes pre-packaged build tools in `tools/` directory:
- `tools/llvm-mingw/bin/` - mingw32-make.exe, gcc.exe, g++.exe (llvm-mingw UCRT)
- `tools/perl/bin/` - perl.exe (Strawberry Perl portable)

**Before first run**, download bundled tools:
```
python scripts/download_tools.py
```

This downloads ~200MB of tools. After that, users don't need to separately install make or perl.

**No tool path configuration required** - bundled tools are automatically detected and used. Only Python path can be optionally configured for QML compilation.

## Windows Build Specifics

Windows builds use generated batch scripts (`build_qt_ohos.bat`) instead of direct subprocess calls. This is critical to:
- Reset PATH to avoid MSVC `cl.exe` polluting the build environment
- Ensure MinGW `gcc/g++` is detected for host tools
- Avoid Python subprocess environment variable inheritance issues

**Never set QMAKESPEC before configure** - it must be unset (see `script_gen.py:144`).

## Configure Key Flags

Generated in `src/builder/qt_builder.py:256` and `script_gen.py`:
- `-platform win32-g++`: MinGW for host tools
- `-xplatform ohos-clang`: Cross-compile to HarmonyOS
- `-ohos-arch <arch>`: Target architecture
- `-prefix` + `-extprefix`: Device prefix vs actual install path

## Tests

No pytest framework. Tests are standalone scripts:
```
python tests/test_ui.py
python tests/test_download.py
```

## Dev Commands

```
pip install -e .                    # Dev install
pip install -r requirements.txt     # Runtime deps only
pip install -e ".[dev]"             # Dev deps (pytest, black, flake8, mypy)
black src/                          # Format (line-length 100)
flake8 src/                         # Lint
```

## Config

User config saved to `config.yaml` (copy from `config.example.yaml`).

## Architecture Summary

```
src/cli.py              -> CLI entry (Click commands)
src/core/installer.py   -> Flow orchestrator
src/core/steps.py       -> Step definitions (modifiable)
src/builder/qt_builder.py -> Qt compile execution
src/builder/script_gen.py -> Windows batch script generator
src/config/defaults.py  -> Version-specific skip modules, configure options
scripts/download_tools.py -> Download bundled llvm-mingw + Perl
```

## Skip Modules

Default skip list in `src/config/defaults.py`. Qt 5.12 and 5.15 have different lists. Essential modules (`qtbase`, `qtdeclarative`) should never be skipped.

## Logs

`logs/install_<timestamp>.log` in workspace directory.