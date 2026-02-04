"""
游戏运行器插件。
提供游戏特定的执行逻辑，包括场景执行、选择处理和用户输入。
"""

from typing import Dict, Any, Optional, List
from src.infrastructure.plugin_interface import EventPlugin, CommandPlugin
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)


class GameRunnerPlugin(EventPlugin, CommandPlugin):
    """游戏运行器插件，实现游戏特定的执行逻辑。"""

    @property
    def name(self) -> str:
        return "game_runner"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件。"""
        self.container = context.get('container')
        self.parser = None
        self.state_manager = None
        self.execution_engine = None
        logger.info("GameRunner plugin initialized")
        return True

    def shutdown(self) -> None:
        """关闭插件。"""
        logger.info("GameRunner plugin shutdown")

    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        """返回此插件提供的自定义命令。"""
        return {
            'execute_scene': {
                'description': '执行游戏场景',
                'parameters': {
                    'scene_id': {'type': 'str', 'required': True, 'description': '场景ID'}
                }
            },
            'process_choice': {
                'description': '处理玩家选择',
                'parameters': {
                    'choice_index': {'type': 'int', 'required': True, 'description': '选择索引'}
                }
            },
            'process_input': {
                'description': '处理玩家输入',
                'parameters': {
                    'input_text': {'type': 'str', 'required': True, 'description': '输入文本'}
                }
            }
        }

    def execute_command(self, command_name: str, args: Dict[str, Any]) -> Any:
        """执行自定义命令。"""
        if command_name == 'execute_scene':
            return self._execute_scene(args['scene_id'])
        elif command_name == 'process_choice':
            return self._process_choice(args['choice_index'])
        elif command_name == 'process_input':
            return self._process_input(args['input_text'])
        else:
            raise ValueError(f"Unknown command: {command_name}")

    def on_script_section_start(self, section_id: str, context: Dict[str, Any]) -> None:
        """脚本段开始时调用。"""
        logger.info(f"Script section started: {section_id}")
        # 可以在这里添加游戏特定的脚本段开始逻辑

    def on_script_section_end(self, section_id: str, context: Dict[str, Any]) -> None:
        """脚本段结束时调用。"""
        logger.info(f"Script section ended: {section_id}")
        # 可以在这里添加游戏特定的脚本段结束逻辑

    def on_option_selected(self, option_index: int, context: Dict[str, Any]) -> None:
        """选择选项时调用。"""
        logger.info(f"Option selected: {option_index}")
        # 可以在这里添加游戏特定的选择逻辑

    def on_execution_start(self, context: Dict[str, Any]) -> None:
        """执行开始时调用。"""
        logger.info("Execution started")
        # 初始化执行状态
        if self.container:
            self.parser = self.container.get('parser')
            self.state_manager = self.container.get('state_manager')
            self.execution_engine = self.container.get('execution_engine')

    def on_execution_end(self, context: Dict[str, Any]) -> None:
        """执行结束时调用。"""
        logger.info("Execution ended")
        # 清理执行状态

    def _execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景。"""
        if not self.execution_engine:
            raise RuntimeError("Execution engine not available")

        return self.execution_engine.execute_script_section(scene_id)

    def _process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理选择。"""
        if not self.execution_engine:
            raise RuntimeError("Execution engine not available")

        return self.execution_engine.process_option(choice_index)

    def _process_input(self, input_text: str) -> Dict[str, Any]:
        """处理用户输入。"""
        if not self.execution_engine:
            raise RuntimeError("Execution engine not available")

        return self.execution_engine.process_user_input(input_text)
