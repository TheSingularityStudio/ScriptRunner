"""
ScriptRunner 核心命令执行器。
处理基础命令，如变量设置。
"""

from typing import Dict, Any, List
from .interfaces import ICommandExecutor
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class CoreCommandExecutor(ICommandExecutor):
    """核心命令执行器，处理基础命令。"""

    def __init__(self, state_manager):
        self.state = state_manager

    def execute_commands(self, commands: List[Dict[str, Any]]) -> None:
        """执行命令列表。"""
        for command in commands:
            self.execute_command(command)

    def execute_command(self, command: Dict[str, Any]) -> None:
        """执行单个命令，使用新的统一YAML结构。"""
        if not command:
            return

        command_type = list(command.keys())[0]
        command_params = command[command_type]

        logger.debug(f"Executing core command: {command_type} with params: {command_params}")

        try:
            if command_type == 'print':
                self._execute_print_command(command_params)
            elif command_type == 'set_variable':
                self._execute_set_variable_command(command_params)
            elif command_type == 'call_action':
                self._execute_call_action_command(command_params)
            elif command_type == 'condition':
                self._execute_condition_command(command_params)
            else:
                logger.warning(f"Unknown core command type: {command_type}")
        except Exception as e:
            logger.error(f"Error executing core command {command}: {e}")
            raise

    def _execute_print_command(self, params: Dict[str, Any]) -> None:
        """执行 print 命令。"""
        message = params.get('message', '')
        # 这里可以扩展为实际的输出处理
        logger.info(f"Script output: {message}")

    def _execute_set_variable_command(self, params: Dict[str, Any]) -> None:
        """执行 set_variable 命令。"""
        name = params.get('name')
        value = params.get('value')
        if name is None:
            logger.error("set_variable command missing 'name' parameter")
            return
        self.state.set_variable(name, value)

    def _execute_call_action_command(self, params: Dict[str, Any]) -> None:
        """执行 call_action 命令。"""
        action = params.get('action')
        if action is None:
            logger.error("call_action command missing 'action' parameter")
            return
        # 这里需要通过脚本对象调用动作，暂时记录
        logger.debug(f"Call action: {action}")

    def _execute_condition_command(self, params: Dict[str, Any]) -> None:
        """执行 condition 命令。"""
        expression = params.get('expression')
        then_commands = params.get('then', [])
        else_commands = params.get('else', [])

        # 这里需要评估表达式，暂时假设为真
        condition_result = True  # 占位符

        if condition_result:
            for cmd in then_commands:
                self.execute_command(cmd)
        else:
            for cmd in else_commands:
                self.execute_command(cmd)

    def _execute_set_command(self, command_value: str):
        """执行 set 命令，如 'health = 100' 或 'health += 25'。"""
        import re

        match = re.match(r'^\s*(\w+)\s*(\+=|=)\s*(.+)\s*$', command_value)
        if not match:
            logger.error(f"Invalid set command: {command_value}")
            return

        var_name, operator, value_str = match.groups()

        try:
            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                value = int(value_str)
            elif value_str.replace('.', '').isdigit() or (value_str.startswith('-') and value_str[1:].replace('.', '').isdigit()):
                value = float(value_str)
            elif value_str.lower() == 'true':
                value = True
            elif value_str.lower() == 'false':
                value = False
            elif value_str.startswith('"') and value_str.endswith('"'):
                value = value_str[1:-1]
            elif value_str.startswith("'") and value_str.endswith("'"):
                value = value_str[1:-1]
            else:
                value = self._get_nested_variable(value_str)
                if value is None:
                    value = value_str
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

    def _get_nested_variable(self, var_path: str) -> Any:
        """获取嵌套变量的值，支持点号访问。"""
        parts = var_path.split('.')
        root_var = parts[0]

        if root_var == 'player':
            value = self.state.get_variable('player', {})
        elif root_var == 'inventory':
            value = self.state.get_variable('inventory', [])
        elif root_var == 'flags':
            value = self.state.get_variable('flags', [])
        else:
            value = self.state.get_variable(root_var, None)

        if len(parts) == 1:
            return value

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
