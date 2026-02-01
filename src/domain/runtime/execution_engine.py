"""
ScriptRunner 执行引擎模块。
协调各个运行时组件以执行游戏逻辑。
"""

from typing import Dict, Any, List, Optional
from .interfaces import (IExecutionEngine, ISceneExecutor, ICommandExecutor, IConditionEvaluator,
                         IChoiceProcessor, IInputHandler, IEventManager, IEffectsManager,
                         IStateMachineManager, IMetaManager, IRandomManager)
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine(IExecutionEngine):
    def __init__(self, parser, state_manager, scene_executor: ISceneExecutor,
                 command_executor: ICommandExecutor, condition_evaluator: IConditionEvaluator,
                 choice_processor: IChoiceProcessor, input_handler: IInputHandler,
                 event_manager: IEventManager, effects_manager: IEffectsManager,
                 state_machine_manager: IStateMachineManager, meta_manager: IMetaManager,
                 random_manager: IRandomManager, interaction_manager=None):
        self.parser = parser
        self.state = state_manager
        self.scene_executor = scene_executor
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator
        self.choice_processor = choice_processor
        self.event_manager = event_manager
        self.effects_manager = effects_manager
        self.state_machine_manager = state_machine_manager
        self.meta_manager = meta_manager
        self.random_manager = random_manager
        self.interaction_manager = interaction_manager

        # Pass event_manager and condition_evaluator to input_handler
        input_handler.event_manager = self.event_manager
        input_handler.condition_evaluator = self.condition_evaluator
        self.input_handler = input_handler

        logger.info("ExecutionEngine initialized with dependency injection")

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        return self.scene_executor.execute_scene(scene_id)



    def process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理玩家选择并返回下一个场景和消息。"""
        return self.choice_processor.process_choice(choice_index)

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入。"""
        return self.input_handler.process_player_input(input_text)
