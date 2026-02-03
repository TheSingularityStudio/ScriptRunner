"""
ScriptRunner 脚本对象执行器。
通过脚本对象方法执行命令，移除插件依赖。
"""

from typing import Dict, Any, List
from .interfaces import ICommandExecutor, IScriptObject
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptObjectExecutor(ICommandExecutor):
    """脚本对象执行器，通过脚本对象方法执行命令。"""

    def __init__(self, parser, state_manager, condition_evaluator, script_factory, config=None):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.script_factory = script_factory
        self.config = config

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
            # 使用脚本对象执行命令
            script_object = self.script_factory.create_script_from_yaml(command)
            if script_object:
                result = script_object.execute_action(command_type, value=command_value)
                if isinstance(result, list):
                    messages.extend(result)
                elif isinstance(result, str):
                    messages.append(result)
            else:
                logger.warning(f"Unknown command type: {command_type}")
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
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
