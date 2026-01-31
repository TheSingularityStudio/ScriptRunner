from typing import Dict, Any, List, Optional
from .interfaces import IExecutionEngine, ISceneExecutor, ICommandExecutor, IConditionEvaluator, IChoiceProcessor, IInputHandler
from ..logging.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine(IExecutionEngine):
    def __init__(self, parser, state_manager, scene_executor: ISceneExecutor,
                 command_executor: ICommandExecutor, condition_evaluator: IConditionEvaluator,
                 choice_processor: IChoiceProcessor, input_handler: IInputHandler):
        self.parser = parser
        self.state = state_manager
        self.scene_executor = scene_executor
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator
        self.choice_processor = choice_processor
        self.input_handler = input_handler

        logger.info("ExecutionEngine initialized with dependency injection")

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        return self.scene_executor.execute_scene(scene_id)



    def process_choice(self, choice_index: int) -> Optional[str]:
        """处理玩家选择并返回下一个场景。"""
        return self.choice_processor.process_choice(choice_index)

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入。"""
        return self.input_handler.process_player_input(input_text)
