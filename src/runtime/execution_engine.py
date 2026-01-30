from typing import Dict, Any, List, Optional
from .scene_executor import SceneExecutor
from .command_executor import CommandExecutor
from .condition_evaluator import ConditionEvaluator
from .choice_processor import ChoiceProcessor
from .input_handler import InputHandler
from ..logging.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine:
    def __init__(self, parser, state_manager):
        self.parser = parser
        self.state = state_manager

        # 初始化子组件
        self.condition_evaluator = ConditionEvaluator(state_manager)
        self.command_executor = CommandExecutor(parser, state_manager, self.condition_evaluator)
        self.scene_executor = SceneExecutor(parser, state_manager, self.command_executor, self.condition_evaluator)
        self.choice_processor = ChoiceProcessor(parser, state_manager, self.command_executor)
        self.input_handler = InputHandler(parser, state_manager, self.command_executor)

        logger.info("ExecutionEngine initialized with modular components")

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        return self.scene_executor.execute_scene(scene_id)



    def process_choice(self, choice_index: int) -> Optional[str]:
        """处理玩家选择并返回下一个场景。"""
        return self.choice_processor.process_choice(choice_index)

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入。"""
        return self.input_handler.process_player_input(input_text)
