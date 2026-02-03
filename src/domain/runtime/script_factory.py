"""
ScriptRunner 脚本工厂。
负责从YAML创建脚本对象实例。
"""

from typing import Dict, Any
from .script_object import ScriptObject
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptFactory:
    """脚本工厂，负责从YAML数据创建脚本对象实例。"""

    @staticmethod
    def create_script_from_yaml(yaml_data: Dict[str, Any]) -> ScriptObject:
        """
        从YAML数据创建脚本对象。

        期望的YAML结构：
        variables: {var_name: value, ...}
        actions: {action_name: [commands], ...}
        events: {event_name: [commands], ...}
        """
        logger.debug("Creating script object from YAML data")

        variables = yaml_data.get('variables', {})
        actions = yaml_data.get('actions', {})
        events = yaml_data.get('events', {})

        script_object = ScriptObject(variables=variables, actions=actions, events=events)
        logger.info("Script object created successfully")
        return script_object
