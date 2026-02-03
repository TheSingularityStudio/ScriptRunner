"""
ScriptRunner 脚本对象基类。
支持面向对象的脚本执行。
"""

from typing import Dict, Any, Callable
from .interfaces import IScriptObject
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptObject(IScriptObject):
    """脚本对象基类，支持面向对象的脚本执行。"""

    def __init__(self, variables: Dict[str, Any] = None, actions: Dict[str, Callable] = None, events: Dict[str, Callable] = None):
        self.variables = variables or {}
        self.actions = actions or {}
        self.events = events or {}

    def get_variable(self, name: str) -> Any:
        """获取脚本变量。"""
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """设置脚本变量。"""
        self.variables[name] = value
        logger.debug(f"Set variable {name} = {value}")

    def execute_action(self, action_name: str, **kwargs) -> Any:
        """执行脚本动作。"""
        if action_name in self.actions:
            logger.debug(f"Executing action {action_name} with kwargs {kwargs}")
            return self.actions[action_name](self, **kwargs)
        logger.warning(f"Unknown action: {action_name}")
        return None

    def trigger_event(self, event_name: str, **kwargs) -> Any:
        """触发脚本事件。"""
        if event_name in self.events:
            logger.debug(f"Triggering event {event_name} with kwargs {kwargs}")
            return self.events[event_name](self, **kwargs)
        logger.warning(f"Unknown event: {event_name}")
        return None
