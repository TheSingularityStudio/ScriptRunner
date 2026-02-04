"""
ScriptRunner 执行引擎模块。
协调各个运行时组件以执行脚本逻辑。
"""

from typing import Dict, Any, List, Optional
from .interfaces import (IExecutionEngine, IScriptSectionExecutor, ICommandExecutor, IConditionEvaluator,
                         IOptionProcessor, IInputHandler)
from .core_command_executor import CoreCommandExecutor
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ExecutionEngine(IExecutionEngine):
    def __init__(self, parser, state_manager, scene_executor: IScriptSectionExecutor,
                 script_object_executor: ICommandExecutor, condition_evaluator: IConditionEvaluator,
                 choice_processor: IOptionProcessor, input_handler: IInputHandler, script_object=None, plugin_manager=None):
        self.parser = parser
        self.state = state_manager
        self.script_section_executor = scene_executor
        self.script_object_executor = script_object_executor
        self.core_command_executor = CoreCommandExecutor(state_manager)
        self.condition_evaluator = condition_evaluator
        self.option_processor = choice_processor

        # 将 condition_evaluator 传递给 input_handler
        input_handler.condition_evaluator = self.condition_evaluator
        self.input_handler = input_handler

        # 设置脚本对象到执行器
        self.script_object = script_object
        if hasattr(self.script_object_executor, 'set_current_script_object'):
            self.script_object_executor.set_current_script_object(self.script_object)
        if hasattr(self.script_section_executor, 'set_script_object'):
            self.script_section_executor.set_script_object(self.script_object)

        # 设置插件管理器
        self.plugin_manager = plugin_manager

        logger.info("ExecutionEngine initialized with core components")

    def execute_script_section(self, section_id: str) -> Dict[str, Any]:
        """执行脚本段并返回结果。"""
        # 首先尝试通过插件执行
        if self.plugin_manager:
            game_plugin = self.plugin_manager.get_plugin('game_runner')
            if game_plugin and hasattr(game_plugin, 'execute_command'):
                try:
                    return game_plugin.execute_command('execute_scene', {'scene_id': section_id})
                except Exception as e:
                    logger.warning(f"Plugin execution failed, falling back to direct execution: {e}")

        # 回退到直接执行
        if self.script_section_executor:
            return self.script_section_executor.execute_script_section(section_id)
        else:
            logger.warning(f"No scene executor available, cannot execute section: {section_id}")
            return {}

    def process_option(self, option_index: int) -> tuple[Optional[str], List[str]]:
        """处理选项并返回下一个脚本段和消息。"""
        # 首先尝试通过插件处理
        if self.plugin_manager:
            game_plugin = self.plugin_manager.get_plugin('game_runner')
            if game_plugin and hasattr(game_plugin, 'execute_command'):
                try:
                    return game_plugin.execute_command('process_choice', {'choice_index': option_index})
                except Exception as e:
                    logger.warning(f"Plugin execution failed, falling back to direct execution: {e}")

        # 回退到直接处理
        return self.option_processor.process_option(option_index)

    def process_user_input(self, input_text: str) -> Dict[str, Any]:
        """处理用户的自然语言输入。"""
        # 首先尝试通过插件处理
        if self.plugin_manager:
            game_plugin = self.plugin_manager.get_plugin('game_runner')
            if game_plugin and hasattr(game_plugin, 'execute_command'):
                try:
                    return game_plugin.execute_command('process_input', {'input_text': input_text})
                except Exception as e:
                    logger.warning(f"Plugin execution failed, falling back to direct execution: {e}")

        # 回退到直接处理
        return self.input_handler.process_user_input(input_text)
