"""
ScriptRunner 的动作执行器。
提供统一的动作执行逻辑，避免代码重复。
"""

from typing import Dict, Any, Optional
from ..infrastructure.logger import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """统一的动作执行器，处理常见的DSL动作。"""

    def __init__(self, state_manager, command_executor):
        self.state = state_manager
        self.command_executor = command_executor

    def execute_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute a single DSL action string.

        This method parses and executes various types of actions defined in the game's
        Domain Specific Language (DSL). Actions are colon-separated commands that
        modify game state, trigger events, or perform logging operations.

        Args:
            action: The action string to execute, using format "command:parameter"
            context: Optional dictionary for additional context (used for logging/effects)

        Raises:
            Exception: Re-raises any execution errors after logging them

        Supported action formats:
            - "set:variable=value": Set a game variable (delegates to command executor)
            - "add_flag:flag_name": Set a boolean flag to true
            - "remove_flag:flag_name" or "clear_flag:flag_name": Clear a flag
            - "broadcast:message": Log an informational broadcast message
            - "log:message": Log a custom message

        Note:
            - String parameters can be enclosed in quotes (single or double)
            - Unknown actions are logged as warnings but don't raise errors
            - All execution errors are logged and re-raised to maintain error visibility
        """
        if context is None:
            context = {}

        try:
            if action.startswith('set:'):
                # Variable assignment action: set:variable=expression
                var_expr = action[4:].strip()
                self.command_executor.execute_command({'set': var_expr})
                logger.debug(f"Executed set action: {var_expr}")

            elif action.startswith('add_flag:'):
                # Flag setting action: add_flag:flag_name
                flag = action[9:].strip()
                self.state.set_flag(flag)
                logger.debug(f"Executed add_flag action: {flag}")

            elif action.startswith('remove_flag:') or action.startswith('clear_flag:'):
                # Flag clearing action: remove_flag:flag_name or clear_flag:flag_name
                flag = action[12:].strip() if action.startswith('remove_flag:') else action[9:].strip()
                self.state.clear_flag(flag)
                logger.debug(f"Executed remove_flag action: {flag}")

            elif action.startswith('broadcast:'):
                # Message broadcasting action: broadcast:message
                message = action[10:].strip('"\'' )
                logger.info(f"Action broadcast: {message}")
                # TODO: Add to game message queue for UI display

            elif action.startswith('log:'):
                # Custom logging action: log:message
                message = action[4:].strip('"\'' )
                logger.info(f"Action log: {message}")

            else:
                # Unknown action type - log warning but don't fail
                logger.warning(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            raise

    def execute_actions(self, actions: list, context: Optional[Dict[str, Any]] = None) -> None:
        """执行多个动作。

        Args:
            actions: 动作字符串列表
            context: 可选的上下文信息
        """
        for action in actions:
            self.execute_action(action, context)
