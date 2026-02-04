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

        # Check for expected top-level keys for script objects
        expected_keys = {'variables', 'actions', 'events'}
        has_expected = any(key in self.script_data for key in expected_keys)

        if not has_expected:
            logger.warning("Script does not contain expected keys (variables, actions, events). This may not be a valid script object.")

    def create_script_object(self, script_data: Dict[str, Any]):
        """从脚本数据创建脚本对象实例。"""
        from ..runtime.script_object import ScriptObject
        from ..runtime.script_factory import ScriptFactory

        return ScriptFactory.create_script_from_yaml(script_data)


