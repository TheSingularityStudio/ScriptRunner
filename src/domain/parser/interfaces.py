"""
ScriptRunner 解析器抽象接口。
定义解析器组件的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IScriptParser(ABC):
    """脚本解析器接口。"""

    @abstractmethod
    def load_script(self, file_path: str) -> Dict[str, Any]:
        """加载并解析脚本文件。"""
        pass

    @abstractmethod
    def get_scene(self, scene_id: str) -> Dict[str, Any]:
        """获取场景。"""
        pass

    @abstractmethod
    def get_start_scene(self) -> str:
        """获取起始场景。"""
        pass

    @abstractmethod
    def parse_player_command(self, input_text: str) -> Dict[str, Any]:
        """解析玩家命令。"""
        pass
