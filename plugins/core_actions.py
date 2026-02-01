"""
ScriptRunner 的核心动作插件。
提供基本的游戏状态操作动作。
"""

from typing import Dict, Any, List, Callable
from src.infrastructure.plugin_interface import ActionPlugin
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)


class CoreActionsPlugin(ActionPlugin):
    """提供核心游戏动作的基础插件。"""

    @property
    def name(self) -> str:
        return "CoreActions"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件。"""
        logger.info("CoreActions plugin initialized")
        return True

    def shutdown(self) -> None:
        """关闭插件。"""
        logger.info("CoreActions plugin shutdown")

    def get_actions(self) -> Dict[str, Callable]:
        """返回此插件提供的动作。"""
        return {
            'set_variable': self._execute_set_variable,
            'parse_and_set': self._execute_parse_and_set,
            'set_flag': self._execute_set_flag,
            'clear_flag': self._execute_clear_flag,
            'apply_effect': self._execute_apply_effect,
            'remove_effect': self._execute_remove_effect,
            'goto': self._execute_goto,
            'if': self._execute_if,
            'spawn_object': self._execute_spawn_object,
        }

    def _execute_set_variable(self, parser, state, condition_evaluator, command_value: Dict[str, Any]) -> List[str]:
        """执行设置变量命令。"""
        name = command_value.get('name')
        value = command_value.get('value')
        if name is not None and value is not None:
            state.set_variable(name, value)
            logger.debug(f"Set variable {name} = {value}")
        return []

    def _execute_parse_and_set(self, parser, state, condition_evaluator, expression: str) -> List[str]:
        """执行解析并设置命令，如 'has_key = true' 或 'health = 100'。"""
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

        state.set_variable(key, value)
        logger.debug(f"Set variable {key} = {value}")
        return []

    def _execute_set_flag(self, parser, state, condition_evaluator, flag_name: str) -> List[str]:
        """设置标志。"""
        state.set_flag(flag_name)
        return []

    def _execute_clear_flag(self, parser, state, condition_evaluator, flag_name: str) -> List[str]:
        """清除标志。"""
        state.clear_flag(flag_name)
        return []

    def _execute_apply_effect(self, parser, state, condition_evaluator, effect_name: str) -> List[str]:
        """应用效果。"""
        effect = parser.get_effect(effect_name)
        if not effect:
            logger.warning(f"Effect not found: {effect_name}")
            return []

        state.apply_effect(effect_name, effect)
        logger.debug(f"Applied effect: {effect_name}")
        return []

    def _execute_remove_effect(self, parser, state, condition_evaluator, effect_name: str) -> List[str]:
        """移除效果。"""
        state.remove_effect(effect_name)
        return []

    def _execute_goto(self, parser, state, condition_evaluator, scene_id: str) -> List[str]:
        """跳转到场景。"""
        state.set_current_scene(scene_id)
        return []

    def _execute_if(self, parser, state, condition_evaluator, command: Dict[str, Any]) -> List[str]:
        """执行条件命令并返回消息。"""
        messages = []
        condition = command.get('if')
        then_commands = command.get('then', [])
        else_commands = command.get('else', [])

        if condition_evaluator.evaluate_condition(condition):
            # Note: This needs access to the command executor to execute commands
            # For now, just log
            logger.debug(f"Would execute then commands: {then_commands}")
        else:
            logger.debug(f"Would execute else commands: {else_commands}")
        return messages

    def _execute_spawn_object(self, parser, state, condition_evaluator, object_name: str) -> List[str]:
        """生成对象。"""
        # 这里需要实现生成对象的逻辑
        # 目前只是记录日志，实际实现需要根据游戏逻辑
        logger.debug(f"Spawning object: {object_name}")
        return []