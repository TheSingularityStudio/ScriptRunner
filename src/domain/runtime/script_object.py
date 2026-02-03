"""
ScriptRunner 脚本对象基类。
支持面向对象的脚本执行。
"""

from typing import Dict, Any, List
from .interfaces import IScriptObject
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptObject(IScriptObject):
    """脚本对象基类，支持面向对象的脚本执行。"""

    def __init__(self, variables: Dict[str, Any] = None, actions: Dict[str, List[Dict[str, Any]]] = None, events: Dict[str, List[Dict[str, Any]]] = None):
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

    def execute_action(self, action_name: str, **kwargs) -> List[Dict[str, Any]]:
        """执行脚本动作，返回命令列表。"""
        if action_name in self.actions:
            logger.debug(f"Executing action {action_name} with kwargs {kwargs}")
            return self.actions[action_name]
        logger.warning(f"Unknown action: {action_name}")
        return []

    def trigger_event(self, event_name: str, **kwargs) -> List[Dict[str, Any]]:
        """触发脚本事件，返回命令列表。"""
        if event_name in self.events:
            logger.debug(f"Triggering event {event_name} with kwargs {kwargs}")
            return self.events[event_name]
        logger.warning(f"Unknown event: {event_name}")
        return []
