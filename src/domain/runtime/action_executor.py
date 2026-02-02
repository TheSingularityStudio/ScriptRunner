"""
ScriptRunner 的动作执行器。
提供统一的动作执行逻辑，避免代码重复。
"""

from typing import Dict, Any, Optional
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """统一的动作执行器，处理常见的DSL动作。"""

    def __init__(self, state_manager, command_executor):
        self.state = state_manager
        self.command_executor = command_executor

    def execute_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        执行单个 DSL 动作字符串。

        此方法解析并执行游戏域特定语言（DSL）中定义的各种类型的动作。动作是用冒号分隔的命令，用于修改游戏状态、触发事件或执行日志操作。

        Args:
            action: 要执行的操作字符串，使用格式 "command:parameter"
            context: 可选字典，用于提供附加上下文（用于日志记录/效果）

        Raises:
            Exception: 在记录执行错误后重新引发它们

        Supported action formats:
            - "set:variable=value": 设置一个游戏变量（交给命令执行器处理）
            - "add_flag:flag_name": 将布尔标志设置为真
            - "remove_flag:flag_name" 或 "clear_flag:flag_name": 清除标志
            - "broadcast:message": 记录信息广播消息
            - "log:message": 记录自定义消息

        Note:
            - 字符串参数可以用引号（单引号或双引号）括起来
            - 未知操作会被记录为警告，但不会引发错误
            - 所有执行错误都会被记录并重新引发，以保持错误的可见性
        """
        if context is None:
            context = {}

        try:
            if action.startswith('set:'):
                # 变量赋值动作: set:variable=expression
                var_expr = action[4:].strip()
                self.command_executor.execute_command({'set': var_expr})
                logger.debug(f"Executed set action: {var_expr}")

            elif action.startswith('add_flag:'):
                # 标志设置动作: add_flag:flag_name
                flag = action[9:].strip()
                self.state.set_flag(flag)
                logger.debug(f"Executed add_flag action: {flag}")

            elif action.startswith('remove_flag:') or action.startswith('clear_flag:'):
                # 标志清除动作: remove_flag:flag_name or clear_flag:flag_name
                flag = action[12:].strip() if action.startswith('remove_flag:') else action[9:].strip()
                self.state.clear_flag(flag)
                logger.debug(f"Executed remove_flag action: {flag}")

            elif action.startswith('broadcast:'):
                # 消息广播动作: broadcast:message
                message = action[10:].strip('"\'' )
                logger.info(f"Action broadcast: {message}")
                # 添加到游戏消息队列以供界面显示
                self.state.add_broadcast_message(message)

            elif action.startswith('log:'):
                # 自定义日志动作: log:message
                message = action[4:].strip('"\'' )
                logger.info(f"Action log: {message}")

            else:
                # 未知的操作类型 - 记录警告但不失败
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
