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

        # 注册执行引擎（依赖解析器和状态管理器）
        self.container.register_factory('execution_engine', self._create_execution_engine)

    def _create_execution_engine(self):
        """创建执行引擎的工厂函数。"""
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        return ExecutionEngine(parser, state_manager)

    def _register_ui_backends(self):
        """注册UI后端。"""
        self.ui_manager.register_backend('console', ConsoleRenderer)
        self.ui_manager.set_backend('console')

    def _load_plugins(self):
        """加载插件。"""
        self.plugin_manager.load_plugins()


# 移除全局初始化器实例，由调用方创建和管理
