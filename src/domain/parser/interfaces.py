"""
ScriptRunner 解析器抽象接口。
定义解析器组件的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IScriptParser(ABC):
    """脚本解析器接口。"""

    @abstractmethod
    def load_script(self, file_path: str) -> Dict[str, Any]:
        """加载并解析脚本文件。"""
        pass

    @abstractmethod
    def create_script_object(self, script_data: Dict[str, Any]):
        """从脚本数据创建脚本对象实例。"""
        pass
