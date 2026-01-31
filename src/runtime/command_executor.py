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
            elif command_type == 'search':
                self._execute_search(command_value)
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

    def _evaluate_expression(self, expression: str, context: dict) -> Any:
        """简单表达式评估器。"""
        # 创建安全的上下文，允许字典以支持点号访问
        class DotDict(dict):
            def __getattr__(self, key):
                return self[key]

        def is_safe_value(v):
            if isinstance(v, (int, float, bool)):
                return True
            elif isinstance(v, dict):
                return all(isinstance(sub_v, (int, float, bool)) for sub_v in v.values())
            return False

        safe_context = {}
        for k, v in context.items():
            if isinstance(v, dict):
                safe_context[k] = DotDict(v)
            elif is_safe_value(v):
                safe_context[k] = v

        safe_context['random'] = random.randint

        # 评估表达式
        try:
            return eval(expression, {"__builtins__": {}}, safe_context)
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return 0

    def _execute_attack(self, target: str) -> None:
        """执行攻击命令。"""
        # 获取玩家属性
        player_attrs = {}
        for attr in ['strength', 'agility', 'defense', 'health']:
            player_attrs[attr] = self.state.get_variable(attr, 0)

        # 获取目标对象
        target_obj = self.parser.get_object(target)
        if not target_obj:
            logger.warning(f"Attack target not found: {target}")
            return

        target_attrs = target_obj.get('attributes', {})
        behaviors = target_obj.get('behaviors', {})
        attack_behavior = behaviors.get('attack', {})

        # 计算命中率
        hit_chance_expr = attack_behavior.get('hit_chance', '0.5')
        context = {**player_attrs, **target_attrs}
        # 添加 player. 前缀的变量
        context.update({f'player.{k}': v for k, v in player_attrs.items()})
        # 添加 player 和 target 字典以支持点号访问
        context['player'] = player_attrs
        context['target'] = target_attrs
        hit_chance = self._evaluate_expression(hit_chance_expr, context)

        if random.random() < hit_chance:
            # 命中
            damage_expr = attack_behavior.get('damage', '10')
            damage = self._evaluate_expression(damage_expr, context)

            # 应用伤害到目标
            states = target_obj.get('states', [])
            for state in states:
                if state['name'] == 'health':
                    state['value'] = max(0, state['value'] - damage)
                    break

            # 成功消息
            success_msg = attack_behavior.get('success', '你击中了{target}，造成{damage}点伤害！')
            success_msg = success_msg.replace('{target}', target).replace('{damage}', str(damage))
            print(success_msg)
            logger.info(success_msg)
        else:
            # 失败
            failure_msg = attack_behavior.get('failure', '你没能打中{target}')
            failure_msg = failure_msg.replace('{target}', target)
            print(failure_msg)
            logger.info(failure_msg)

        # 反击
        counter_msg = attack_behavior.get('counter', '')
        if counter_msg:
            print(counter_msg)
            logger.info(counter_msg)
            # 反击伤害，暂时固定为5
            player_health = self.state.get_variable('health', 100)
            self.state.set_variable('health', max(0, player_health - 5))
            print(f"你受到了5点反击伤害！")
            logger.info("Player took 5 counter damage")

    def _execute_search(self, location: str) -> None:
        """执行搜索命令。"""
        logger.info(f"Searching {location}...")

        # 尝试滚动森林战利品表（如果适用）
        if location == 'forest_path':
            self._execute_roll_table('forest_loot')
        else:
            logger.info(f"No items found while searching {location}.")
