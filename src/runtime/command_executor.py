"""
ScriptRunner 的命令执行器。
处理游戏脚本中的命令执行。
"""

from typing import Dict, Any, List
import random
from .interfaces import ICommandExecutor
from ..logging.logger import get_logger

logger = get_logger(__name__)


class CommandExecutor(ICommandExecutor):
    """执行游戏脚本中的命令。"""

    def __init__(self, parser, state_manager, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator

    def execute_commands(self, commands: List[Dict[str, Any]]) -> None:
        """执行命令列表。"""
        for command in commands:
            self.execute_command(command)

    def execute_command(self, command: Dict[str, Any]) -> None:
        """执行单个命令。"""
        if not command:
            return

        # 获取命令类型
        command_type = list(command.keys())[0]
        command_value = command[command_type]

        logger.debug(f"Executing command: {command_type} = {command_value}")

        try:
            if command_type == 'set':
                self._execute_set(command_value)
            elif command_type == 'set_variable':
                self._execute_set_variable(command_value)
            elif command_type == 'set_flag' or command_type == 'add_flag':
                self.state.set_flag(command_value)
            elif command_type == 'clear_flag':
                self.state.clear_flag(command_value)
            elif command_type == 'roll_table':
                self._execute_roll_table(command_value)
            elif command_type == 'apply_effect':
                self._execute_apply_effect(command_value)
            elif command_type == 'remove_effect':
                self.state.remove_effect(command_value)
            elif command_type == 'goto':
                self.state.set_current_scene(command_value)
            elif command_type == 'if':
                self._execute_if(command)
            elif command_type == 'attack':
                self._execute_attack(command_value)
            else:
                logger.warning(f"Unknown command type: {command_type}")
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")

    def _execute_set(self, expression: str) -> None:
        """执行设置命令，如 'has_key = true' 或 'health = 100'。"""
        if '=' not in expression:
            logger.warning(f"Invalid set expression: {expression}")
            return

        key, value_str = expression.split('=', 1)
        key = key.strip()
        value_str = value_str.strip()

        # 解析值
        if value_str.lower() == 'true':
            value = True
        elif value_str.lower() == 'false':
            value = False
        elif value_str.isdigit():
            value = int(value_str)
        elif value_str.replace('.', '').isdigit():
            value = float(value_str)
        elif value_str.startswith('"') and value_str.endswith('"'):
            value = value_str[1:-1]
        else:
            value = value_str

        self.state.set_variable(key, value)
        logger.debug(f"Set variable {key} = {value}")

    def _execute_roll_table(self, table_name: str) -> None:
        """执行随机表滚动。"""
        table = self.parser.get_random_table(table_name)
        if not table:
            logger.warning(f"Random table not found: {table_name}")
            return

        entries = table.get('entries', [])
        if not entries:
            logger.warning(f"Random table {table_name} has no entries")
            return

        # 随机选择条目
        result = random.choice(entries)
        logger.info(f"Rolled table {table_name}: {result}")

        # 如果结果有命令，执行它们
        if isinstance(result, dict) and 'commands' in result:
            self.execute_commands(result['commands'])

    def _execute_apply_effect(self, effect_name: str) -> None:
        """应用效果。"""
        effect = self.parser.get_effect(effect_name)
        if not effect:
            logger.warning(f"Effect not found: {effect_name}")
            return

        self.state.apply_effect(effect_name, effect)
        logger.debug(f"Applied effect: {effect_name}")

    def _execute_set_variable(self, command_value: Dict[str, Any]) -> None:
        """执行设置变量命令。"""
        name = command_value.get('name')
        value = command_value.get('value')
        if name is not None and value is not None:
            self.state.set_variable(name, value)
            logger.debug(f"Set variable {name} = {value}")

    def _execute_if(self, command: Dict[str, Any]) -> None:
        """执行条件命令。"""
        condition = command.get('if')
        then_commands = command.get('then', [])
        else_commands = command.get('else', [])

        if self.condition_evaluator.evaluate_condition(condition):
            self.execute_commands(then_commands)
        else:
            self.execute_commands(else_commands)

    def _execute_attack(self, target: str) -> None:
        """执行攻击命令。"""
        # 获取目标对象
        target_obj = self.parser.get_object(target)
        if not target_obj:
            logger.warning(f"Attack target not found: {target}")
            return

        # 找到 health 状态（states 是列表）
        states = target_obj.get('states', [])
        health_state = None
        for state in states:
            if state.get('name') == 'health':
                health_state = state
                break

        if not health_state:
            logger.warning(f"Target {target} has no health state")
            return

        # 获取当前生命值
        current_health = health_state.get('value', 0)
        damage = 10  # 固定伤害值，可以根据玩家属性计算
        new_health = max(0, current_health - damage)

        # 更新生命值
        health_state['value'] = new_health
        logger.info(f"Attacked {target}, dealt {damage} damage. Health: {new_health}")

        # 如果目标死亡，可以添加更多逻辑
        if new_health <= 0:
            logger.info(f"{target} has been defeated!")
            # 可以触发死亡事件或移除对象
