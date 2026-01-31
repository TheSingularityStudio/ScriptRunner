from typing import Dict, Any, List, Optional
from .interfaces import IExecutionEngine, ISceneExecutor, ICommandExecutor, IConditionEvaluator, IChoiceProcessor, IInputHandler
from .event_manager import EventManager
from .effects_manager import EffectsManager
from .state_machine_manager import StateMachineManager
from .meta_manager import MetaManager
from .random_manager import RandomManager
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
        self.event_manager = EventManager(parser, state_manager, command_executor, condition_evaluator)
        self.effects_manager = EffectsManager(parser, state_manager, command_executor)
        self.state_machine_manager = StateMachineManager(parser, state_manager, command_executor, condition_evaluator)
        self.meta_manager = MetaManager(parser, state_manager, condition_evaluator)
        self.random_manager = RandomManager(parser, state_manager)

        # 加载状态机、元数据和随机表
        self.state_machine_manager.load_state_machines()
        self.meta_manager.load_meta_data()
        self.random_manager.load_random_tables()

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
