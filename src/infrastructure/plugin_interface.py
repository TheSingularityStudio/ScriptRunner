"""
ScriptRunner 的插件接口。
定义插件必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PluginInterface(ABC):
    """所有插件的基础接口。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本。"""
        pass

    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """使用上下文初始化插件。"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """关闭插件。"""
        pass


class CommandPlugin(PluginInterface):
    """自定义命令插件。"""

    @abstractmethod
    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        """返回此插件提供的自定义命令。"""
        pass

    @abstractmethod
    def execute_command(self, command_name: str, args: Dict[str, Any]) -> Any:
        """执行一个自定义命令。"""
        pass


class UIPlugin(PluginInterface):
    """用于自定义 UI 后端的插件。"""

    @abstractmethod
    def get_ui_backends(self) -> Dict[str, type]:
        """返回此插件提供的 UI 后端类。"""
        pass


class ParserPlugin(PluginInterface):
    """用于扩展解析器功能的插件。"""

    @abstractmethod
    def extend_parser(self, parser) -> None:
        """为解析器扩展额外功能。"""
        pass


class EventPlugin(PluginInterface):
    """用于处理事件的插件。"""

    @abstractmethod
    def on_scene_start(self, scene_id: str, context: Dict[str, Any]) -> None:
        """在场景开始时调用。"""
        pass

    @abstractmethod
    def on_scene_end(self, scene_id: str, context: Dict[str, Any]) -> None:
        """在场景结束时调用。"""
        pass

    @abstractmethod
    def on_choice_selected(self, choice_index: int, context: Dict[str, Any]) -> None:
        """当选择一个选项时调用。"""
        pass

    @abstractmethod
    def on_game_start(self, context: Dict[str, Any]) -> None:
        """在游戏开始时调用。"""
        pass

    @abstractmethod
    def on_game_end(self, context: Dict[str, Any]) -> None:
        """在游戏结束时调用。"""
        pass


class ActionPlugin(PluginInterface):
    """用于提供便利动作函数的插件。"""

    @abstractmethod
    def get_actions(self) -> Dict[str, callable]:
        """返回此插件提供的动作函数。"""
        pass


class StoragePlugin(PluginInterface):
    """用于自定义存储后端的插件。"""

    @abstractmethod
    def save_game(self, game_data: Dict[str, Any]) -> bool:
        """保存游戏数据。"""
        pass

    @abstractmethod
    def load_game(self) -> Optional[Dict[str, Any]]:
        """加载游戏数据。"""
        pass
