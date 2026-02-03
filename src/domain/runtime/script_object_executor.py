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

    def __init__(self, parser, state_manager, condition_evaluator, script_factory, core_command_executor, config=None):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.script_factory = script_factory
        self.core_command_executor = core_command_executor
        self.config = config
        self.current_script_object = None

    def set_current_script_object(self, script_object: IScriptObject):
        """设置当前脚本对象。"""
        self.current_script_object = script_object

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
            if command_type == 'action' and self.current_script_object:
                # 执行脚本动作
                action_name = command_value['action']
                kwargs = {k: v for k, v in command_value.items() if k != 'action'}
                action_commands = self.current_script_object.execute_action(action_name, **kwargs)
                for cmd in action_commands:
                    substituted_cmd = self._substitute_command(cmd, command_value.get('value'))
                    messages.extend(self.execute_command(substituted_cmd))
            elif command_type == 'event' and self.current_script_object:
                # 触发脚本事件
                event_commands = self.current_script_object.trigger_event(command_value)
                for cmd in event_commands:
                    substituted_cmd = self._substitute_command(cmd, None)
                    messages.extend(self.execute_command(substituted_cmd))
            elif command_type == 'set':
                # 执行 set 命令
                self.core_command_executor.execute_command(command)
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

    def _execute_set_command(self, command_value: str):
        """执行 set 命令，如 'health = 100' 或 'health += 25'。"""
        import re

        # 解析命令，支持 = 和 +=
        match = re.match(r'^\s*(\w+)\s*(\+=|=)\s*(.+)\s*$', command_value)
        if not match:
            logger.error(f"Invalid set command: {command_value}")
            return

        var_name, operator, value_str = match.groups()

        # 解析值，支持数字、字符串、布尔值、变量
        try:
            # 如果是数字
            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                value = int(value_str)
            elif value_str.replace('.', '').isdigit() or (value_str.startswith('-') and value_str[1:].replace('.', '').isdigit()):
                value = float(value_str)
            elif value_str.lower() == 'true':
                value = True
            elif value_str.lower() == 'false':
                value = False
            elif value_str.startswith('"') and value_str.endswith('"'):
                value = value_str[1:-1]  # 移除引号
            elif value_str.startswith("'") and value_str.endswith("'"):
                value = value_str[1:-1]  # 移除引号
            else:
                # 可能是变量或表达式
                value = self._get_nested_variable(value_str)
                if value is None:
                    value = value_str  # 如果不是变量，保持原样
        except Exception as e:
            logger.error(f"Failed to parse value in set command: {value_str}, error: {e}")
            return

        if operator == '=':
            self.state.set_variable(var_name, value)
        elif operator == '+=':
            current_value = self.state.get_variable(var_name, 0)
            if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                self.state.set_variable(var_name, current_value + value)
            else:
                logger.error(f"Cannot add non-numeric values: {current_value} + {value}")

    def _substitute_command(self, command: Dict[str, Any], command_value: Any) -> Dict[str, Any]:
        """替换命令字典中的变量占位符。"""
        substituted = {}
        for key, value in command.items():
            if isinstance(value, str):
                substituted[key] = self._substitute_variables(value, command_value)
            elif isinstance(value, dict):
                substituted[key] = self._substitute_command(value, command_value)
            else:
                substituted[key] = value
        return substituted
