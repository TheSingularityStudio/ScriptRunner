"""
ScriptRunner 的输入处理器。
处理玩家的自然语言输入。
"""

from typing import Dict, Any
from ..logging.logger import get_logger

logger = get_logger(__name__)


class InputHandler:
    """处理玩家的自然语言输入。"""

    def __init__(self, parser, state_manager, command_executor):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入并返回结果。"""
        logger.debug(f"Processing player input: {input_text}")

        # 解析输入
        parsed_command = self.parser.parse_player_command(input_text)

        action = parsed_command.get('action', 'unknown')
        target = parsed_command.get('target')

        logger.info(f"Parsed action: {action}, target: {target}")

        # 根据动作执行相应逻辑
        if action == 'unknown':
            return {
                'success': False,
                'message': f"我不理解 '{input_text}'。",
                'action': action
            }

        # 这里可以扩展更多动作处理
        # 目前返回解析结果
        return {
            'success': True,
            'action': action,
            'target': target,
            'message': f"执行动作: {action}" + (f" 针对 {target}" if target else ""),
            'original_input': input_text
        }
