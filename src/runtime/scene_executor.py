"""
ScriptRunner 的场景执行器。
处理场景执行和处理。
"""

from typing import Dict, Any, Optional
from .interfaces import ISceneExecutor
from ..logging.logger import get_logger

logger = get_logger(__name__)


class SceneExecutor(ISceneExecutor):
    """处理场景执行和处理。"""

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行一个场景并返回处理结果。"""
        logger.debug(f"Executing scene: {scene_id}")

        scene = self.parser.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene '{scene_id}' not found")

        self.state.set_current_scene(scene_id)

        # 执行场景命令
        self.command_executor.execute_commands(scene.get('commands', []))

        # 处理具有变量替换和条件过滤的场景
        processed_scene = self._process_scene(scene)

        # 替换文本中的变量
        if 'text' in processed_scene:
            processed_scene['text'] = self._replace_variables(processed_scene['text'])

        # 确保存在“text”字段（与传统格式兼容）
        if 'description' in processed_scene and 'text' not in processed_scene:
            processed_scene['text'] = self._replace_variables(processed_scene['description'])

        logger.debug(f"Scene execution completed for: {scene_id}")
        return processed_scene

    def _process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """处理场景内容，根据条件过滤选择。"""
        processed = scene.copy()

        # 根据条件筛选选项
        choices = scene.get('choices', [])
        processed_choices = []

        for choice in choices:
            if self.condition_evaluator.evaluate_condition(choice.get('condition')):
                processed_choices.append(choice)

        processed['choices'] = processed_choices
        return processed

    def _replace_variables(self, text: str) -> str:
        """替换文本中的 DSL 变量。"""
        # Get all variables from state manager
        variables = self.state.get_all_variables()

        for var_name, var_value in variables.items():
            if var_value is not None:
                text = text.replace(f"{{{var_name}}}", str(var_value))

        return text
