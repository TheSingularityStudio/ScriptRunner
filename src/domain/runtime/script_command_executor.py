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

    def __init__(self, parser, state_manager, condition_evaluator, plugin_manager: PluginManager, config=None):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.plugin_manager = plugin_manager
        self.config = config
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

        # 替换命令值中的变量占位符
        if isinstance(command_value, str):
            command_value = self._substitute_variables(command_value, None)

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
                if 'message' in action:
                    message = action['message']
                    # 替换变量占位符
                    message = self._substitute_variables(message, command_value)
                    messages.append(message)
                else:
                    # 执行子命令
                    messages.extend(self.execute_command(action))
            elif isinstance(action, str):
                if action == 'message':
                    # 特殊处理：直接添加command_value作为消息
                    messages.append(str(command_value))
                elif ':' in action:
                    # 处理 command:value 格式
                    cmd_type, cmd_val = action.split(':', 1)
                    messages.extend(self._execute_script_command({'actions': [cmd_type]}, cmd_val))
                elif action in self.actions:
                    # 构建 context
                    context = {
                        'parser': self.parser,
                        'state': self.state,
                        'condition_evaluator': self.condition_evaluator,
                        'command_value': command_value,
                        'config': self.config
                    }
                    result = self.actions[action](command_value, context)
                    if isinstance(result, list):
                        messages.extend(result)
                    elif isinstance(result, dict):
                        if 'message' in result:
                            messages.append(result['message'])
                        if 'actions' in result:
                            # 执行附加动作
                            for additional_action in result['actions']:
                                if isinstance(additional_action, dict):
                                    messages.extend(self.execute_command(additional_action))
                                elif isinstance(additional_action, str):
                                    # 递归执行
                                    messages.extend(self._execute_script_command({'actions': [additional_action]}, command_value))
                    else:
                        logger.warning(f"Unexpected result type from action {action}: {type(result)}")
                else:
                    logger.warning(f"Unknown script action: {action}")

        return messages

    def _substitute_variables(self, message: str, command_value: Any) -> str:
        """替换消息中的变量占位符。"""
        import re

        # 替换 {value} 为 command_value
        if '{value}' in message:
            message = message.replace('{value}', str(command_value))

        # 替换其他变量，支持点号访问，如 {player.health}, {inventory.0.name}
        def replace_var(match):
            var_path = match.group(1)
            if var_path == 'value':
                return str(command_value) if command_value is not None else ''
            else:
                try:
                    value = self._get_nested_variable(var_path)
                    return str(value) if value is not None else f'{{{var_path}}}'
                except Exception as e:
                    logger.warning(f"Failed to substitute variable {var_path}: {e}")
                    return f'{{{var_path}}}'

        # 使用正则表达式替换所有 {variable} 或 {variable.property} 格式
        message = re.sub(r'\{([^}]+)\}', replace_var, message)

        return message

    def _get_nested_variable(self, var_path: str) -> Any:
        """获取嵌套变量的值，支持点号访问。"""
        parts = var_path.split('.')
        root_var = parts[0]

        # 特殊处理一些预定义变量
        if root_var == 'player':
            value = self.state.get_variable('player', {})
        elif root_var == 'inventory':
            value = self.state.get_variable('inventory', [])
        elif root_var == 'flags':
            value = self.state.get_variable('flags', [])
        else:
            value = self.state.get_variable(root_var, None)

        # 如果没有更多部分，直接返回
        if len(parts) == 1:
            return value

        # 遍历剩余部分
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                try:
                    index = int(part)
                    value = value[index] if 0 <= index < len(value) else None
                except (ValueError, IndexError):
                    value = None
            else:
                value = None
            if value is None:
                break

        return value
