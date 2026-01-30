import yaml
import os
from typing import Dict, Any

class ScriptParser:
    def __init__(self):
        self.script_data = {}

    def load_script(self, file_path: str) -> Dict[str, Any]:
        """加载并解析YAML脚本文件。"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"脚本文件未找到: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            self.script_data = yaml.safe_load(file)

        self._validate_script()
        return self.script_data

    def _validate_script(self):
        """脚本结构的初步验证。"""
        if 'scenes' not in self.script_data:
            raise ValueError("脚本必须包含'scenes'部分")

        for scene_id, scene in self.script_data['scenes'].items():
            if 'text' not in scene:
                raise ValueError(f"场景'{scene_id}'必须有'text'字段")

    def get_scene(self, scene_id: str) -> Dict[str, Any]:
        """通过ID获取特定场景。"""
        return self.script_data['scenes'].get(scene_id, {})

    def get_start_scene(self) -> str:
        """获取起始场景ID。"""
        return self.script_data.get('start_scene', 'start')
