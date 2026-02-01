"""
ScriptRunner 脚本驱动的命令执行器。
支持在YAML脚本中定义命令行为，通过插件提供动作函数。
"""

from typing import Dict, Any, List, Callable
from .interfaces import ICommandExecutor
from ...infrastructure.logger import get_logger
from ...infrastructure.plugin_manager import PluginManager
from ...infrastructure.plugin_interface import ActionPlugin

logger = get_logger(__name__)


class ScriptCommandExecutor(ICommandExecutor):
    """脚本驱动的命令执行器，所有命令行为都在脚本中定义。"""

    def __init__(self, parser, state_manager, condition_evaluator, plugin_manager: PluginManager):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.plugin_manager = plugin_manager
        self.actions = self._load_actions()

    def _load_actions(self) -> Dict[str, Callable]:
        """从插件加载动作函数。"""
        actions = {}
        for plugin in self.plugin_manager.get_plugins_by_type(ActionPlugin):
            plugin_actions = plugin.get_actions()
            actions.update(plugin_actions)
        return actions

    def execute_commands(self, commands: List[Dict[str, Any]]) -> List[str]:
        """执行命令列表并返回所有消息。"""
        messages = []
        for command in commands:
            messages.extend(self.execute_command(command))
        return messages

    def execute_command(self, command: Dict[str, Any]) -> List[str]:
        """执行单个命令并返回消息列表。"""
        messages = []
        if not command:
            return messages

        # 获取命令类型
        command_type = list(command.keys())[0]
        command_value = command[command_type]

        logger.debug(f"Executing command: {command_type} = {command_value}")

        try:
            # 使用脚本定义的命令
            script_command = self.parser.get_command(command_type)
            if script_command:
                messages.extend(self._execute_script_command(script_command, command_value))
            else:
                logger.warning(f"Unknown command type: {command_type}")
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
        return messages

    def _execute_script_command(self, command_def: Dict[str, Any], command_value: Any) -> List[str]:
        """执行脚本定义的命令。"""
        messages = []

        # 获取命令的执行逻辑
        actions = command_def.get('actions', [])

        for action in actions:
            if isinstance(action, dict):
                # 执行子命令
                messages.extend(self.execute_command(action))
            elif isinstance(action, str):
                # 执行简单动作
                if action == 'message':
                    msg = command_def.get('message', '')
                    messages.append(msg)
                elif action in self.actions:
                    # 从插件执行动作
                    messages.extend(self.actions[action](self.parser, self.state, self.condition_evaluator, command_value))
                else:
                    logger.warning(f"Unknown script action: {action}")

        return messages
