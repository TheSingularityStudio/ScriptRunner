"""
ScriptRunner 脚本驱动的命令执行器。
支持在YAML脚本中定义命令行为，而不是硬编码。
"""

from typing import Dict, Any, List, Callable
from .interfaces import ICommandExecutor
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptCommandExecutor(ICommandExecutor):
    """脚本驱动的命令执行器，支持动态注册命令处理器。"""

    def __init__(self, parser, state_manager, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.command_handlers: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {}

        # 注册内置命令处理器
        self._register_builtin_handlers()

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
            # 首先尝试使用脚本定义的命令
            script_command = self.parser.get_command(command_type)
            if script_command:
                messages.extend(self._execute_script_command(script_command, command_value))
            else:
                # 回退到注册的处理器
                handler = self.command_handlers.get(command_type)
                if handler:
                    messages.extend(handler(command_value))
                else:
                    logger.warning(f"Unknown command type: {command_type}")
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
        return messages

    def register_command_handler(self, command_name: str, handler: Callable[[Dict[str, Any]], List[str]]):
        """注册自定义命令处理器。"""
        self.command_handlers[command_name] = handler
        logger.info(f"Registered command handler: {command_name}")

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
                if action == 'roll_table':
                    table_name = command_def.get('table', command_value)
                    messages.extend(self._execute_roll_table(table_name))
                elif action == 'set_variable':
                    var_name = command_def.get('variable', command_value)
                    var_value = command_def.get('value', command_value)
                    self._execute_set_variable({var_name: var_value})
                elif action == 'message':
                    msg = command_def.get('message', '')
                    messages.append(msg)
                else:
                    logger.warning(f"Unknown script action: {action}")

        return messages

    def _register_builtin_handlers(self):
        """注册内置命令处理器。"""
        self.command_handlers.update({
            'set': self._execute_set,
            'set_variable': self._execute_set_variable,
            'set_flag': lambda value: self._execute_set_flag(value),
            'clear_flag': lambda value: self._execute_clear_flag(value),
            'roll_table': self._execute_roll_table,
            'apply_effect': self._execute_apply_effect,
            'remove_effect': lambda value: self._execute_remove_effect(value),
            'goto': lambda value: self._execute_goto(value),
            'if': self._execute_if,
            'attack': self._execute_attack,
            'search': self._execute_search,
        })

    def _execute_set(self, expression: str) -> List[str]:
        """执行设置命令，如 'has_key = true' 或 'health = 100'。"""
        if '=' not in expression:
            logger.warning(f"Invalid set expression: {expression}")
            return []

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
        return []

    def _execute_set_variable(self, command_value: Dict[str, Any]) -> List[str]:
        """执行设置变量命令。"""
        name = command_value.get('name')
        value = command_value.get('value')
        if name is not None and value is not None:
            self.state.set_variable(name, value)
            logger.debug(f"Set variable {name} = {value}")
        return []

    def _execute_set_flag(self, flag_name: str) -> List[str]:
        """设置标志。"""
        self.state.set_flag(flag_name)
        return []

    def _execute_clear_flag(self, flag_name: str) -> List[str]:
        """清除标志。"""
        self.state.clear_flag(flag_name)
        return []

    def _execute_roll_table(self, table_name: str) -> List[str]:
        """执行随机表滚动并返回消息。"""
        messages = []
        table = self.parser.get_random_table(table_name)
        if not table:
            logger.warning(f"Random table not found: {table_name}")
            return messages

        entries = table.get('entries', [])
        if not entries:
            logger.warning(f"Random table {table_name} has no entries")
            return messages

        import random
        # 随机选择条目
        result = random.choice(entries)
        logger.debug(f"Rolled table {table_name}: {result}")

        # 如果结果有消息，添加消息
        if isinstance(result, dict) and 'message' in result:
            messages.append(result['message'])

        # 如果结果有命令，执行它们
        if isinstance(result, dict) and 'commands' in result:
            messages.extend(self.execute_commands(result['commands']))
        return messages

    def _execute_apply_effect(self, effect_name: str) -> List[str]:
        """应用效果。"""
        effect = self.parser.get_effect(effect_name)
        if not effect:
            logger.warning(f"Effect not found: {effect_name}")
            return []

        self.state.apply_effect(effect_name, effect)
        logger.debug(f"Applied effect: {effect_name}")
        return []

    def _execute_remove_effect(self, effect_name: str) -> List[str]:
        """移除效果。"""
        self.state.remove_effect(effect_name)
        return []

    def _execute_goto(self, scene_id: str) -> List[str]:
        """跳转到场景。"""
        self.state.set_current_scene(scene_id)
        return []

    def _execute_if(self, command: Dict[str, Any]) -> List[str]:
        """执行条件命令并返回消息。"""
        messages = []
        condition = command.get('if')
        then_commands = command.get('then', [])
        else_commands = command.get('else', [])

        if self.condition_evaluator.evaluate_condition(condition):
            messages.extend(self.execute_commands(then_commands))
        else:
            messages.extend(self.execute_commands(else_commands))
        return messages

    def _execute_attack(self, target: str) -> List[str]:
        """执行攻击命令并返回消息。"""
        messages = []
        # 获取玩家属性
        player_attrs = {}
        for attr in ['strength', 'agility', 'defense', 'health']:
            player_attrs[attr] = self.state.get_variable(attr, 0)

        # 获取目标对象
        target_obj = self.parser.get_object(target)
        if not target_obj:
            logger.warning(f"Attack target not found: {target}")
            return messages

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

        import random
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
            messages.append(success_msg)
            logger.debug(success_msg)
        else:
            # 失败
            failure_msg = attack_behavior.get('failure', '你没能打中{target}')
            failure_msg = failure_msg.replace('{target}', target)
            messages.append(failure_msg)
            logger.debug(failure_msg)

        # 反击
        counter_msg = attack_behavior.get('counter', '')
        if counter_msg:
            messages.append(counter_msg)
            logger.debug(counter_msg)
            # 反击伤害，从配置中获取，默认5
            counter_damage = attack_behavior.get('counter_damage', 5)
            player_health = self.state.get_variable('health', 100)
            self.state.set_variable('health', max(0, player_health - counter_damage))
            counter_damage_msg = f"你受到了{counter_damage}点反击伤害！"
            messages.append(counter_damage_msg)
            logger.debug(f"Player took {counter_damage} counter damage")
        return messages

    def _execute_search(self, location: str) -> List[str]:
        """执行搜索命令并返回消息。"""
        messages = []
        logger.info(f"Searching {location}...")

        # 尝试滚动森林搜索表（如果适用）
        if location == 'forest_path':
            messages.extend(self._execute_roll_table('forest_path_search'))
        else:
            msg = f"No items found while searching {location}."
            messages.append(msg)
            logger.info(msg)
        return messages

    def _evaluate_expression(self, expression: str, context: dict) -> Any:
        """
        Safely evaluate a mathematical or logical expression with limited context.
        """
        # Create a safe context that allows dictionary access via dot notation
        class DotDict(dict):
            """Dictionary subclass that allows attribute-style access for dot notation."""
            def __getattr__(self, key):
                return self[key]

        def is_safe_value(v):
            """Check if a value is safe to include in the evaluation context."""
            if isinstance(v, (int, float, bool)):
                return True
            elif isinstance(v, dict):
                # Ensure all nested values are also safe
                return all(isinstance(sub_v, (int, float, bool)) for sub_v in v.values())
            return False

        safe_context = {}
        for k, v in context.items():
            if isinstance(v, dict):
                # Wrap dictionaries to support dot notation (e.g., player.health)
                safe_context[k] = DotDict(v)
            elif is_safe_value(v):
                safe_context[k] = v

        # Add random function for dice rolls and similar mechanics
        import random
        safe_context['random'] = random.randint

        # Evaluate the expression in the restricted environment
        try:
            return eval(expression, {"__builtins__": {}}, safe_context)
        except (NameError, TypeError, SyntaxError, ZeroDivisionError) as e:
            # Log expected evaluation errors (invalid syntax, undefined variables, etc.)
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return 0
        except Exception as e:
            # Catch any unexpected errors during evaluation
            logger.error(f"Unexpected error evaluating expression '{expression}': {e}")
            return 0
