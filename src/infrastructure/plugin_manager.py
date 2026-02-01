"""
ScriptRunner 插件管理器。
负责加载和管理插件。
"""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Any, Type
from .plugin_interface import PluginInterface
from .logger import get_logger

logger = get_logger(__name__)


class PluginManager:
    """管理 ScriptRunner 应用程序的插件。"""

    def __init__(self, plugin_dir: str = 'plugins'):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginInterface] = {}
        self._loaded = False

    def load_plugins(self):
        """加载所有可用插件。"""
        if self._loaded:
            return

        if not self.plugin_dir.exists():
            logger.info(f"Plugin directory {self.plugin_dir} does not exist, skipping plugin loading")
            self._loaded = True
            return

        logger.info(f"Loading plugins from {self.plugin_dir}")

        # 查找插件文件
        plugin_files = list(self.plugin_dir.glob('*.py'))
        plugin_files.extend(self.plugin_dir.glob('*/__init__.py'))
        logger.debug(f"Found plugin files: {[str(f) for f in plugin_files]}")

        for plugin_file in plugin_files:
            try:
                self._load_plugin_from_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self.plugins)} plugins")

    def _load_plugin_from_file(self, plugin_file: Path):
        """从 Python 文件加载插件。"""
        # 将文件路径转换为模块路径
        rel_path = plugin_file.relative_to(self.plugin_dir.parent)
        module_path = str(rel_path).replace(os.sep, '.').replace('.py', '')

        try:
            # 添加项目根目录到 Python 路径，以便插件可以导入 src 包
            import sys
            project_root = self.plugin_dir.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            module = importlib.import_module(module_path)

            # 在模块中查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                logger.debug(f"Checking attribute {attr_name}: {attr}")
                if (isinstance(attr, type) and
                    issubclass(attr, PluginInterface) and
                    attr != PluginInterface and
                    (not hasattr(attr, '__abstractmethods__') or not attr.__abstractmethods__)):
                    logger.debug(f"Found plugin class: {attr}")
                    plugin_instance = attr()
                    self.register_plugin(plugin_instance.name, plugin_instance)
                    logger.debug(f"Loaded plugin: {plugin_instance.name}")

        except ImportError as e:
            logger.warning(f"Could not import plugin module {module_path}: {e}")

    def register_plugin(self, name: str, plugin: PluginInterface):
        """注册一个插件实例。"""
        if name in self.plugins:
            logger.warning(f"Plugin {name} already registered, overwriting")

        try:
            # 初始化插件
            context = self._get_plugin_context()
            if plugin.initialize(context):
                self.plugins[name] = plugin
                logger.info(f"Registered plugin: {name} (v{plugin.version})")
            else:
                logger.warning(f"Plugin {name} failed to initialize")
        except Exception as e:
            logger.error(f"Failed to register plugin {name}: {e}")

    def unregister_plugin(self, name: str):
        """注销插件。"""
        if name in self.plugins:
            try:
                self.plugins[name].shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {e}")
            del self.plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def get_plugin(self, name: str) -> PluginInterface:
        """通过名称获取已注册的插件。"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """获取所有已注册的插件。"""
        return self.plugins.copy()

    def get_plugins_by_type(self, plugin_type: Type[PluginInterface]) -> List[PluginInterface]:
        """根据类型获取插件列表。"""
        return [plugin for plugin in self.plugins.values() if isinstance(plugin, plugin_type)]

    def _get_plugin_context(self) -> Dict[str, Any]:
        """获取在初始化期间传递给插件的上下文。"""
        # 插件初始化时不需要上下文，延迟到动作执行时提供
        return {}

    def shutdown_all(self):
        """关闭所有插件。"""
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                logger.debug(f"Shutdown plugin: {name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {e}")

        self.plugins.clear()


# 移除全局插件管理器实例，由调用方创建和管理
