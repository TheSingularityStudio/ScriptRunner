"""
ScriptRunner 应用程序初始化器。
负责应用程序的启动和组件注册。
"""

from src.di.container import Container
from src.logging.logger import setup_logging
from src.ui.ui_interface import UIManager
from src.plugins.plugin_manager import PluginManager
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.runtime.scene_executor import SceneExecutor
from src.runtime.command_executor import CommandExecutor
from src.runtime.condition_evaluator import ConditionEvaluator
from src.runtime.choice_processor import ChoiceProcessor
from src.runtime.input_handler import InputHandler
from src.ui.renderer import ConsoleRenderer


class ApplicationInitializer:
    """应用程序初始化器，负责设置和注册所有组件。"""

    def __init__(self, container: Container, ui_manager: UIManager, plugin_manager: PluginManager):
        self.container = container
        self.ui_manager = ui_manager
        self.plugin_manager = plugin_manager
        self._initialized = False

    def initialize(self):
        """初始化整个应用程序。"""
        if self._initialized:
            return

        self._setup_logging()
        self._register_core_services()
        self._register_ui_backends()
        self._load_plugins()

        self._initialized = True

    def _setup_logging(self):
        """设置日志系统。"""
        setup_logging()

    def _register_core_services(self):
        """注册核心服务到DI容器。"""
        # 注册解析器
        self.container.register('parser', ScriptParser())

        # 注册状态管理器
        self.container.register('state_manager', StateManager())

        # 注册条件评估器
        self.container.register_factory('condition_evaluator', self._create_condition_evaluator)

        # 注册命令执行器
        self.container.register_factory('command_executor', self._create_command_executor)

        # 注册场景执行器
        self.container.register_factory('scene_executor', self._create_scene_executor)

        # 注册选择处理器
        self.container.register_factory('choice_processor', self._create_choice_processor)

        # 注册输入处理器
        self.container.register_factory('input_handler', self._create_input_handler)

        # 注册执行引擎
        self.container.register_factory('execution_engine', self._create_execution_engine)

    def _create_condition_evaluator(self):
        """创建条件评估器的工厂函数。"""
        state_manager = self.container.get('state_manager')
        return ConditionEvaluator(state_manager)

    def _create_command_executor(self):
        """创建命令执行器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        condition_evaluator = self.container.get('condition_evaluator')
        return CommandExecutor(parser, state_manager, condition_evaluator)

    def _create_scene_executor(self):
        """创建场景执行器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        condition_evaluator = self.container.get('condition_evaluator')
        return SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

    def _create_choice_processor(self):
        """创建选择处理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        return ChoiceProcessor(parser, state_manager, command_executor)

    def _create_input_handler(self):
        """创建输入处理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        return InputHandler(parser, state_manager, command_executor)

    def _create_execution_engine(self):
        """创建执行引擎的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        scene_executor = self.container.get('scene_executor')
        command_executor = self.container.get('command_executor')
        condition_evaluator = self.container.get('condition_evaluator')
        choice_processor = self.container.get('choice_processor')
        input_handler = self.container.get('input_handler')
        return ExecutionEngine(parser, state_manager, scene_executor, command_executor, condition_evaluator, choice_processor, input_handler)

    def _register_ui_backends(self):
        """注册UI后端。"""
        self.ui_manager.register_backend('console', ConsoleRenderer)
        self.ui_manager.set_backend('console')

    def _load_plugins(self):
        """加载插件。"""
        self.plugin_manager.load_plugins()


# 移除全局初始化器实例，由调用方创建和管理
