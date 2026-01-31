"""
ScriptRunner 的 UI 接口。
定义 UI 后端需要实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class UIBackend(ABC):
    """UI 后端的抽象基类。"""

    @abstractmethod
    def render_scene(self, scene_data: Dict[str, Any]):
        """渲染场景。"""
        pass

    @abstractmethod
    def get_player_choice(self) -> int:
        """获取玩家的选择输入。如果未做出选择则返回 -1。"""
        pass

    @abstractmethod
    def show_message(self, message: str):
        """向玩家显示消息。"""
        pass

    @abstractmethod
    def clear_screen(self):
        """清除屏幕/显示。"""
        pass

    @abstractmethod
    def render_status(self, status_data: Dict[str, Any]):
        """渲染玩家状态信息。"""
        pass


class UIEvent:
    """表示 UI 事件。"""

    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.data = data or {}


class UIManager:
    """Manages UI backends and provides a unified interface."""

    def __init__(self):
        self._backends: Dict[str, UIBackend] = {}
        self._current_backend: Optional[UIBackend] = None

    def register_backend(self, name: str, backend: UIBackend):
        """Register a UI backend."""
        self._backends[name] = backend

    def set_backend(self, name: str):
        """Set the current UI backend."""
        if name in self._backends:
            self._current_backend = self._backends[name]
        else:
            raise ValueError(f"UI backend '{name}' not registered")

    def get_current_backend(self) -> Optional[UIBackend]:
        """Get the current UI backend."""
        return self._current_backend

    def render_scene(self, scene_data: Dict[str, Any]):
        """Render scene using current backend."""
        if self._current_backend:
            self._current_backend.render_scene(scene_data)

    def get_player_choice(self) -> int:
        """Get player choice using current backend."""
        if self._current_backend:
            return self._current_backend.get_player_choice()
        return -1

    def show_message(self, message: str):
        """Show message using current backend."""
        if self._current_backend:
            self._current_backend.show_message(message)

    def clear_screen(self):
        """Clear screen using current backend."""
        if self._current_backend:
            self._current_backend.clear_screen()

    def render_status(self, status_data: Dict[str, Any]):
        """Render status using current backend."""
        if self._current_backend:
            self._current_backend.render_status(status_data)


# 移除全局UI管理器实例，由调用方创建和管理
