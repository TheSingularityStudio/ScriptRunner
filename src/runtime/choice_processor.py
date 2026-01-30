"""
ScriptRunner 的选择处理器。
处理玩家选择处理和导航。
"""

from typing import Optional, Dict, Any, List
from ..logging.logger import get_logger

logger = get_logger(__name__)


class ChoiceProcessor:
    """处理玩家选择处理和场景导航。"""

    def __init__(self, parser, state_manager, command_executor):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor

    def process_choice(self, choice_index: int) -> Optional[str]:
        """处理玩家的选择并返回下一个场景 ID。"""
        logger.debug(f"Processing choice index: {choice_index}")

        current_scene = self.parser.get_scene(self.state.get_current_scene())
        choices = current_scene.get('choices', [])

        if 0 <= choice_index < len(choices):
            choice = choices[choice_index]

            # 执行与所选项相关的命令
            self.command_executor.execute_commands(choice.get('commands', []))

            next_scene = choice.get('next')
            if next_scene:
                logger.debug(f"Navigating to scene: {next_scene}")
                return next_scene
            else:
                logger.debug("Choice processed but no next scene specified")
        else:
            logger.warning(f"Invalid choice index: {choice_index}, available choices: {len(choices)}")

        return None

    def get_available_choices(self) -> List[Dict[str, Any]]:
        """获取当前可用选择列表。"""
        current_scene = self.parser.get_scene(self.state.get_current_scene())
        return current_scene.get('choices', [])
