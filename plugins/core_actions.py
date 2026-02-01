"""
ScriptRunner 的核心动作插件。
提供基本的游戏状态操作动作。
"""

import ast
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
            'set': self._execute_parse_and_set,
            'set_flag': self._execute_set_flag,
            'clear_flag': self._execute_clear_flag,
            'apply_effect': self._execute_apply_effect,
            'remove_effect': self._execute_remove_effect,
            'goto': self._execute_goto,
            'if': self._execute_if,
            'spawn_object': self._execute_spawn_object,
            'show_message': self._execute_show_message,
        }

    def _execute_set_variable(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行设置变量命令。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        # 这个方法可能不直接使用，因为脚本使用 parse_and_set
        command_value = target if isinstance(target, dict) else {'name': target, 'value': None}
        name = command_value.get('name')
        value = command_value.get('value')
        if name is not None and value is not None:
            state.set_variable(name, value)
            logger.debug(f"Set variable {name} = {value}")
        return {'success': True, 'message': '', 'actions': []}

    def _execute_parse_and_set(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行解析并设置命令，如 'has_key = true' 或 'health = 100'。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        expression = target
        if '=' not in expression:
            logger.warning(f"Invalid set expression: {expression}")
            return {'success': False, 'message': f'无效的设置表达式: {expression}', 'actions': []}

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
            # 尝试解析为列表或其他Python字面量
            try:
                value = ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                value = value_str

        state.set_variable(key, value)
        logger.debug(f"Set variable {key} = {value}")
        return {'success': True, 'message': '', 'actions': []}

    def _execute_set_flag(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """设置标志。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        flag_name = target
        state.set_flag(flag_name)
        return {'success': True, 'message': '', 'actions': []}

    def _execute_clear_flag(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """清除标志。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        flag_name = target
        state.clear_flag(flag_name)
        return {'success': True, 'message': '', 'actions': []}

    def _execute_apply_effect(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """应用效果。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        effect_name = target
        effect = parser.get_effect(effect_name)
        if not effect:
            logger.warning(f"Effect not found: {effect_name}")
            return {'success': False, 'message': f'效果未找到: {effect_name}', 'actions': []}

        state.apply_effect(effect_name, effect)
        logger.debug(f"Applied effect: {effect_name}")
        return {'success': True, 'message': '', 'actions': []}

    def _execute_remove_effect(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """移除效果。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        effect_name = target
        state.remove_effect(effect_name)
        return {'success': True, 'message': '', 'actions': []}

    def _execute_goto(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """跳转到场景。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        scene_id = target
        state.set_current_scene(scene_id)
        return {'success': True, 'message': '', 'actions': []}

    def _execute_if(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件命令并返回消息。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        # target 应该是条件，但 if 命令可能更复杂
        # 这里简化处理
        condition = target
        # Note: This needs access to the command executor to execute commands
        # For now, just log
        logger.debug(f"Would execute if condition: {condition}")
        return {'success': True, 'message': '', 'actions': []}

    def _execute_spawn_object(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成对象。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')

        object_name = target
        # 这里需要实现生成对象的逻辑
        # 目前只是记录日志，实际实现需要根据游戏逻辑
        logger.debug(f"Spawning object: {object_name}")
        return {'success': True, 'message': '', 'actions': []}

    def _execute_show_message(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """显示消息。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')

        message = target
        logger.debug(f"Showing message: {message}")
        return {'success': True, 'message': message, 'actions': []}
