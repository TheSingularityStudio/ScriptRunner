"""
ScriptRunner 的脚本动作执行器。
处理脚本对象动作，移除插件依赖。
"""

from typing import Dict, Any, Optional, List
from .interfaces import IScriptObject
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptActionExecutor:
    """脚本动作执行器，通过脚本对象执行动作。"""

    def __init__(self, state_manager, command_executor, script_object: Optional[IScriptObject] = None):
        self.state = state_manager
        self.command_executor = command_executor
        self.script_object = script_object

    def set_script_object(self, script_object: IScriptObject):
        """设置当前脚本对象。"""
        self.script_object = script_object

    def execute_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        执行单个 DSL 动作字符串。

        优先通过脚本对象执行，如果脚本对象没有定义该动作，则回退到内置动作。
        """
        if context is None:
            context = {}

        try:
            # 如果有脚本对象，尝试通过脚本对象执行动作
            if self.script_object:
                action_commands = self.script_object.execute_action(action, **context)
                for cmd in action_commands:
                    self.command_executor.execute_command(cmd)
                logger.debug(f"Executed script action: {action}")
                return

            # 回退到内置动作处理（为了向后兼容）
            self._execute_builtin_action(action, context)

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            raise

    def _execute_builtin_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> None:
        """执行内置动作（向后兼容）。"""
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

    def execute_actions(self, actions: List[str], context: Optional[Dict[str, Any]] = None) -> None:
        """执行多个动作。

        Args:
            actions: 动作字符串列表
            context: 可选的上下文信息
        """
        for action in actions:
            self.execute_action(action, context)
