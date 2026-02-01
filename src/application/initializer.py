"""
ScriptRunner 应用程序初始化器。
负责应用程序的启动和组件注册。
"""

from src.infrastructure.container import Container
from src.infrastructure.logger import setup_logging
from src.presentation.ui.ui_interface import UIManager
from src.infrastructure.plugin_manager import PluginManager
from src.infrastructure.config import Config
from src.domain.parser.parser import ScriptParser
from src.infrastructure.state_manager import StateManager
from src.domain.runtime.execution_engine import ExecutionEngine
from src.domain.runtime.scene_executor import SceneExecutor
from src.domain.runtime.script_command_executor import ScriptCommandExecutor
from src.domain.runtime.condition_evaluator import ConditionEvaluator
from src.domain.runtime.choice_processor import ChoiceProcessor
from src.domain.runtime.input_handler import InputHandler
from src.domain.runtime.event_manager import EventManager
from src.domain.runtime.effects_manager import EffectsManager
from src.domain.runtime.state_machine_manager import StateMachineManager
from src.domain.runtime.meta_manager import MetaManager
from src.domain.runtime.random_manager import RandomManager
from src.presentation.ui.renderer import ConsoleRenderer


class ApplicationInitializer:
    """应用程序初始化器，负责设置和注册所有组件。"""

    def __init__(self, container: Container):
        self.container = container
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
        # 从配置系统获取日志设置，但避免循环依赖
        # 这里使用默认配置，稍后可以通过配置系统覆盖
        setup_logging()

    def _register_core_services(self):
        """注册核心服务到DI容器。"""
        # 创建并注册配置、UI管理器和插件管理器
        self.config = Config()
        self.ui_manager = UIManager()
        self.plugin_manager = PluginManager()
        self.container.register('config', self.config)
        self.container.register('ui_manager', self.ui_manager)
        self.container.register('plugin_manager', self.plugin_manager)

        # 注册解析器
        self.container.register('parser', ScriptParser())

        # 注册状态管理器
        self.container.register('state_manager', StateManager())

        # 注册条件评估器
        self.container.register_factory('condition_evaluator', self._create_condition_evaluator)

        # 注册命令执行器
        self.container.register_factory('command_executor', self._create_command_executor)

        # 注册动作执行器
        self.container.register_factory('action_executor', self._create_action_executor)

        # 注册场景执行器
        self.container.register_factory('scene_executor', self._create_scene_executor)

        # 注册选择处理器
        self.container.register_factory('choice_processor', self._create_choice_processor)

        # 注册输入处理器
        self.container.register_factory('input_handler', self._create_input_handler)

        # 注册事件管理器
        self.container.register_factory('event_manager', self._create_event_manager)

        # 注册效果管理器
        self.container.register_factory('effects_manager', self._create_effects_manager)

        # 注册状态机管理器
        self.container.register_factory('state_machine_manager', self._create_state_machine_manager)

        # 注册元管理器
        self.container.register_factory('meta_manager', self._create_meta_manager)

        # 注册随机管理器
        self.container.register_factory('random_manager', self._create_random_manager)

        # 注册互动管理器
        self.container.register_factory('interaction_manager', self._create_interaction_manager)

        # 注册执行引擎
        self.container.register_factory('execution_engine', self._create_execution_engine)

        # 注册渲染器
        self.container.register_factory('renderer', self._create_renderer)

    def _create_condition_evaluator(self):
        """创建条件评估器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        return ConditionEvaluator(state_manager, parser)

    def _create_command_executor(self):
        """创建命令执行器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        condition_evaluator = self.container.get('condition_evaluator')
        plugin_manager = self.container.get('plugin_manager')
        return ScriptCommandExecutor(parser, state_manager, condition_evaluator, plugin_manager)

    def _create_action_executor(self):
        """创建动作执行器的工厂函数。"""
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        from src.domain.runtime.action_executor import ActionExecutor
        return ActionExecutor(state_manager, command_executor)

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
        return InputHandler(self.container, self.config)

    def _create_event_manager(self):
        """创建事件管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        condition_evaluator = self.container.get('condition_evaluator')
        return EventManager(parser, state_manager, command_executor, condition_evaluator)

    def _create_effects_manager(self):
        """创建效果管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        return EffectsManager(parser, state_manager, command_executor)

    def _create_state_machine_manager(self):
        """创建状态机管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        command_executor = self.container.get('command_executor')
        condition_evaluator = self.container.get('condition_evaluator')
        return StateMachineManager(parser, state_manager, command_executor, condition_evaluator)

    def _create_meta_manager(self):
        """创建元管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        condition_evaluator = self.container.get('condition_evaluator')
        return MetaManager(parser, state_manager, condition_evaluator)

    def _create_random_manager(self):
        """创建随机管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        return RandomManager(parser, state_manager)

    def _create_interaction_manager(self):
        """创建互动管理器的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        condition_evaluator = self.container.get('condition_evaluator')
        return __import__('src.domain.runtime.interaction_manager', fromlist=['InteractionManager']).InteractionManager(parser, state_manager, condition_evaluator)

    def _create_execution_engine(self):
        """创建执行引擎的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        scene_executor = self.container.get('scene_executor')
        command_executor = self.container.get('command_executor')
        condition_evaluator = self.container.get('condition_evaluator')
        choice_processor = self.container.get('choice_processor')
        input_handler = self.container.get('input_handler')
        event_manager = self.container.get('event_manager')
        effects_manager = self.container.get('effects_manager')
        state_machine_manager = self.container.get('state_machine_manager')
        meta_manager = self.container.get('meta_manager')
        random_manager = self.container.get('random_manager')
        interaction_manager = self.container.get('interaction_manager')
        execution_engine = ExecutionEngine(parser, state_manager, scene_executor, command_executor, condition_evaluator, choice_processor, input_handler, event_manager, effects_manager, state_machine_manager, meta_manager, random_manager, interaction_manager)

        # 设置输入处理器的事件管理器引用
        input_handler.event_manager = execution_engine.event_manager
        input_handler.condition_evaluator = execution_engine.condition_evaluator
        input_handler.interaction_manager = execution_engine.interaction_manager

        return execution_engine

    def _create_renderer(self):
        """创建渲染器的工厂函数。"""
        execution_engine = self.container.get('execution_engine')
        return ConsoleRenderer(execution_engine)

    def _register_ui_backends(self):
        """注册UI后端。"""
        self.ui_manager.register_backend('console', ConsoleRenderer)
        self.ui_manager.set_backend('console')

    def _load_plugins(self):
        """加载插件。"""
        self.plugin_manager.load_plugins()


# 移除全局初始化器实例，由调用方创建和管理
