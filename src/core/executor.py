"""
Step executor - Executes installation steps
"""

import logging
from typing import Optional

from .steps import InstallStep
from ..ui.display import Display


class StepExecutor:
    """Executes installation steps with error handling and logging"""

    def __init__(self, display: Optional[Display] = None):
        self.display = display or Display()
        self.logger: Optional[logging.Logger] = None
        self.current_step = 0
        self.total_steps = 0

    def set_logger(self, logger: logging.Logger) -> None:
        """Set logger for step execution"""
        self.logger = logger

    def execute(self, step: InstallStep, context: Any, step_number: int, total_steps: int) -> bool:
        """
        Execute a single installation step.

        Args:
            step: The step to execute
            context: The installer context (QtHarmonyInstaller instance)
            step_number: Current step number (1-based)
            total_steps: Total number of steps

        Returns:
            True if step succeeded, False otherwise
        """
        self.current_step = step_number
        self.total_steps = total_steps

        # Check skip condition
        if step.should_skip():
            self.display.print(f"\n[yellow]Skipping step: {step.display_name}[/yellow]")
            if self.logger:
                self.logger.info(f"Skipped step: {step.name}")
            return True

        # Display step title
        self.display.show_step_title(step_number, step.display_name)

        # Log step start
        if self.logger:
            self.logger.info(f"Starting step: {step.name}")

        try:
            # Execute the step handler
            result = step.handler(context)

            if result:
                if self.logger:
                    self.logger.info(f"Step completed: {step.name}")
            else:
                self.display.show_error(f"{step.display_name} failed")
                if self.logger:
                    self.logger.error(f"Step failed: {step.name}")

            return result

        except KeyboardInterrupt:
            self.display.print("\n[yellow]Operation cancelled by user[/yellow]")
            if self.logger:
                self.logger.info(f"Step interrupted: {step.name}")
            return False

        except Exception as e:
            self.display.show_error(f"Error in {step.display_name}: {e}")
            if self.logger:
                self.logger.error(f"Step error ({step.name}): {e}")
            return False

    def run_all(self, steps: list, context: Any) -> bool:
        """
        Execute all steps in sequence.

        Args:
            steps: List of InstallStep objects
            context: The installer context

        Returns:
            True if all steps succeeded, False otherwise
        """
        total = len(steps)

        for i, step in enumerate(steps, 1):
            if not self.execute(step, context, i, total):
                return False

        return True