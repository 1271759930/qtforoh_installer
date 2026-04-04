"""
Installation steps definition - Configurable step system
"""

from dataclasses import dataclass
from typing import Callable, Optional, List, Any


@dataclass
class InstallStep:
    """Definition of an installation step"""
    name: str                      # Internal name (e.g., "init", "check")
    display_name: str              # Display name (e.g., "初始化", "检查前置条件")
    handler: Callable              # Step handler function
    required: bool = True          # Whether this step is required
    skip_condition: Optional[Callable[[], bool]] = None  # Condition to skip

    def should_skip(self) -> bool:
        """Check if this step should be skipped"""
        return self.skip_condition is not None and self.skip_condition()


# Step handler functions (will be called with context)
# These are placeholder functions that will be replaced by actual handlers

def initialize_step(context: Any) -> bool:
    """Initialize installer"""
    return context.initialize()


def check_prerequisites_step(context: Any) -> bool:
    """Check prerequisites"""
    return context.check_prerequisites()


def collect_config_step(context: Any) -> bool:
    """Collect configuration"""
    return context.load_or_prompt_config() is not None


def setup_tools_step(context: Any) -> bool:
    """Setup tools"""
    return context.setup_tools()


def setup_environment_step(context: Any) -> bool:
    """Setup environment"""
    return context.setup_environment()


def build_qt_step(context: Any) -> bool:
    """Build Qt"""
    return context.build_qt()


# Default installation steps
DEFAULT_STEPS: List[InstallStep] = [
    InstallStep("init", "初始化", initialize_step),
    InstallStep("check", "检查前置条件", check_prerequisites_step),
    InstallStep("config", "收集配置", collect_config_step),
    InstallStep("tools", "设置工具", setup_tools_step),
    InstallStep("env", "设置环境", setup_environment_step),
    InstallStep("build", "编译 Qt", build_qt_step),
]


def create_custom_steps(additional_steps: Optional[List[InstallStep]] = None,
                        skip_steps: Optional[List[str]] = None) -> List[InstallStep]:
    """
    Create a custom step list.

    Args:
        additional_steps: Steps to add to the default list
        skip_steps: Names of steps to skip

    Returns:
        Customized list of installation steps
    """
    steps = DEFAULT_STEPS.copy()

    if skip_steps:
        steps = [s for s in steps if s.name not in skip_steps]

    if additional_steps:
        steps.extend(additional_steps)

    return steps