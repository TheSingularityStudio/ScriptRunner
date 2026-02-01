"""
ScriptRunner 的选择处理器。
处理玩家选择处理和导航。
"""

from typing import Optional, Dict, Any, List
from .interfaces import IChoiceProcessor
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ChoiceProcessor(IChoiceProcessor):
    """处理玩家选择处理和场景导航。"""

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

    def process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理玩家的选择并返回下一个场景和消息列表。"""
        messages = []
        logger.debug(f"Processing choice index: {choice_index}")

        choices = self.get_available_choices()

        if 0 <= choice_index < len(choices):
            choice = choices[choice_index]

            # 执行与所选项相关的命令
            messages.extend(self.command_executor.execute_commands(choice.get('commands', [])))

            next_scene = choice.get('next')
            if next_scene:
                logger.debug(f"Navigating to scene: {next_scene}")
                return next_scene, messages
            else:
                logger.debug("Choice processed but no next scene specified")
        else:
            logger.warning(f"Invalid choice index: {choice_index}, available choices: {len(choices)}")

        return None, messages

    def get_available_choices(self) -> List[Dict[str, Any]]:
        """获取当前可用选择列表。"""
        current_scene = self.parser.get_scene(self.state.get_current_scene())
        choices = current_scene.get('choices', [])
        available_choices = []
        for choice in choices:
            condition = choice.get('condition')
            if condition:
                if self.condition_evaluator.evaluate_condition(condition):
                    available_choices.append(choice)
            else:
                available_choices.append(choice)
        return available_choices
