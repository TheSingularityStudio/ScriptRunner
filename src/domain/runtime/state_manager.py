"""
ScriptRunner 状态管理器。
负责管理脚本执行过程中的状态和变量。
"""

import json
import os
from typing import Dict, Any, Optional
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """状态管理器，负责管理脚本执行过程中的状态和变量。"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.current_scene: Optional[str] = None
        self.execution_state_file = 'execution_state.json'

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量的值。"""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any):
        """设置变量的值。"""
        self.variables[name] = value
        logger.debug(f"Variable set: {name} = {value}")

    def get_current_scene(self) -> Optional[str]:
        """获取当前场景。"""
        return self.current_scene

    def set_current_scene(self, scene: str):
        """设置当前场景。"""
        self.current_scene = scene
        logger.debug(f"Current scene set to: {scene}")

    def save_execution_state(self):
        """保存执行状态到文件。"""
        try:
            state = {
                'variables': self.variables,
                'current_scene': self.current_scene
            }
            with open(self.execution_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.info(f"Execution state saved to {self.execution_state_file}")
        except Exception as e:
            logger.error(f"Failed to save execution state: {e}")

    def load_execution_state(self):
        """从文件加载执行状态。"""
        try:
            if os.path.exists(self.execution_state_file):
                with open(self.execution_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.variables = state.get('variables', {})
                self.current_scene = state.get('current_scene')
                logger.info(f"Execution state loaded from {self.execution_state_file}")
        except Exception as e:
            logger.error(f"Failed to load execution state: {e}")
