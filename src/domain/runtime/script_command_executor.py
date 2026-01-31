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
                if action == 'roll_table':
                    table_name = command_def.get('table', command_value)
                    messages.extend(self._execute_roll_table(table_name))
                elif action == 'set_variable':
                    self._execute_set_variable(command_value)
                elif action == 'parse_and_set':
                    expression = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_set(expression))
                elif action == 'set_flag':
                    flag_name = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_set_flag(flag_name))
                elif action == 'clear_flag':
                    flag_name = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_clear_flag(flag_name))
                elif action == 'apply_effect':
                    effect_name = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_apply_effect(effect_name))
                elif action == 'remove_effect':
                    effect_name = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_remove_effect(effect_name))
                elif action == 'goto':
                    scene_id = command_value if isinstance(command_value, str) else str(command_value)
                    messages.extend(self._execute_goto(scene_id))
                elif action == 'if':
                    messages.extend(self._execute_if(command_value))
                elif action == 'message':
                    msg = command_def.get('message', '')
                    messages.append(msg)
                elif action in self.actions:
                    # 从插件执行动作
                    messages.extend(self.actions[action](self.parser, self.state, self.condition_evaluator, command_value))
                else:
                    logger.warning(f"Unknown script action: {action}")

        return messages

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
