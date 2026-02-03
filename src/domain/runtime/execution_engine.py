"""
ScriptRunner 执行引擎模块。
协调各个运行时组件以执行游戏逻辑。
"""

from typing import Dict, Any, List, Optional
from .interfaces import (IExecutionEngine, ISceneExecutor, ICommandExecutor, IConditionEvaluator,
                         IChoiceProcessor, IInputHandler)
from .core_command_executor import CoreCommandExecutor
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine(IExecutionEngine):
    def __init__(self, parser, state_manager, scene_executor: ISceneExecutor,
                 script_object_executor: ICommandExecutor, condition_evaluator: IConditionEvaluator,
                 choice_processor: IChoiceProcessor, input_handler: IInputHandler, script_object=None):
        self.parser = parser
        self.state = state_manager
        self.scene_executor = scene_executor
        self.script_object_executor = script_object_executor
        self.core_command_executor = CoreCommandExecutor(state_manager)
        self.condition_evaluator = condition_evaluator
        self.choice_processor = choice_processor

        # 将 condition_evaluator 传递给 input_handler
        input_handler.condition_evaluator = self.condition_evaluator
        self.input_handler = input_handler

        # 设置脚本对象到执行器
        self.script_object = script_object
        if hasattr(self.script_object_executor, 'set_current_script_object'):
            self.script_object_executor.set_current_script_object(self.script_object)
        if hasattr(self.scene_executor, 'set_script_object'):
            self.scene_executor.set_script_object(self.script_object)

        logger.info("ExecutionEngine initialized with core components")

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        return self.scene_executor.execute_scene(scene_id)

    def process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理玩家选择并返回下一个场景和消息。"""
        return self.choice_processor.process_choice(choice_index)

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入。"""
        return self.input_handler.process_player_input(input_text)
