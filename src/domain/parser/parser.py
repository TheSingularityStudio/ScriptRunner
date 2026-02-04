"""
ScriptRunner 脚本解析器，面向对象的脚本执行器。
"""

import yaml
import os
from typing import Dict, Any
from .interfaces import IScriptParser
try:
    from ...infrastructure.logger import get_logger
except ImportError:
    from infrastructure.logger import get_logger

logger = get_logger(__name__)


class ScriptParser(IScriptParser):
    def __init__(self):
        self.script_data = {}

    def load_script(self, file_path: str) -> Dict[str, Any]:
        """加载并解析YAML脚本文件。"""
        logger.info(f"Loading script from file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"Script file not found: {file_path}")
            raise FileNotFoundError(f"Script file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            self.script_data = yaml.safe_load(file)

        logger.debug(f"Script data loaded with {len(self.script_data)} top-level keys")

        # Handle includes
        if 'includes' in self.script_data:
            self._load_includes(file_path)

        self._validate_script()
        logger.info("Script loaded and parsed successfully")
        return self.script_data

    def _load_includes(self, base_file_path: str):
        """加载并合并包含的文件。"""
        includes = self.script_data.pop('includes')  # Remove includes from script_data
        if not isinstance(includes, list):
            includes = [includes]

        base_dir = os.path.dirname(base_file_path)

        for include_path in includes:
            # Resolve relative path
            if not os.path.isabs(include_path):
                include_path = os.path.join(base_dir, include_path)

            if not os.path.exists(include_path):
                logger.error(f"Included script file not found: {include_path}")
                raise FileNotFoundError(f"包含的脚本文件未找到: {include_path}")

            logger.info(f"Loading included script: {include_path}")
            with open(include_path, 'r', encoding='utf-8') as file:
                include_data = yaml.safe_load(file)

            # Merge include_data into script_data, with script_data taking precedence
            self._merge_dicts(self.script_data, include_data)

    def _merge_dicts(self, target: Dict[str, Any], source: Dict[str, Any]):
        """递归合并字典，target优先。"""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dicts(target[key], value)
            # If key exists and both are not dicts, keep target (no overwrite)

    def _validate_script(self):
        """脚本结构的初步验证。"""
        # Basic validation for script object structure
        if not isinstance(self.script_data, dict):
            raise ValueError("Script must be a dictionary")

        # Required keys for all scripts
        required_keys = {'name', 'actions', 'start_action'}
        for key in required_keys:
            if key not in self.script_data:
                raise ValueError(f"Script must contain '{key}' key")

        # Validate actions structure
        actions = self.script_data.get('actions', {})
        if not isinstance(actions, dict):
            raise ValueError("Actions must be a dictionary")

        start_action = self.script_data.get('start_action')
        if start_action not in actions:
            raise ValueError(f"start_action '{start_action}' not found in actions")

        # Validate each action has commands
        for action_name, action_data in actions.items():
            if not isinstance(action_data, dict) or 'commands' not in action_data:
                raise ValueError(f"Action '{action_name}' must be a dict with 'commands' key")
            if not isinstance(action_data['commands'], list):
                raise ValueError(f"Action '{action_name}' commands must be a list")

        # Optional keys validation
        if 'variables' in self.script_data and not isinstance(self.script_data['variables'], dict):
            raise ValueError("Variables must be a dictionary")

        logger.info("Script validation passed")

    def create_script_object(self, script_data: Dict[str, Any]):
        """从脚本数据创建脚本对象实例。"""
        from ..runtime.script_object import ScriptObject
        from ..runtime.script_factory import ScriptFactory

        return ScriptFactory.create_script_from_yaml(script_data)


