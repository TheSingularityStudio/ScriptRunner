from typing import Dict, Any, Set
import json
import os

class StateManager:
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.flags: Set[str] = set()
        self.current_scene: str = ""
        self.save_file = "game_save.json"

    def set_variable(self, key: str, value: Any):
        """设置游戏变量。"""
        self.variables[key] = value

    def get_variable(self, key: str, default=None):
        """获取游戏变量。"""
        return self.variables.get(key, default)

    def set_flag(self, flag: str):
        """设置游戏标志。"""
        self.flags.add(flag)

    def has_flag(self, flag: str) -> bool:
        """检查标志是否已设置。"""
        return flag in self.flags

    def clear_flag(self, flag: str):
        """清除游戏标志。"""
        self.flags.discard(flag)

    def set_current_scene(self, scene_id: str):
        """设置当前场景。"""
        self.current_scene = scene_id

    def get_current_scene(self) -> str:
        """获取当前场景。"""
        return self.current_scene

    def save_game(self):
        """将游戏状态保存到文件。"""
        state = {
            'variables': self.variables,
            'flags': list(self.flags),
            'current_scene': self.current_scene
        }
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_game(self):
        """从文件加载游戏状态。"""
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.variables = state.get('variables', {})
            self.flags = set(state.get('flags', []))
            self.current_scene = state.get('current_scene', '')
            return True
        return False

    def reset(self):
        """重置游戏状态。"""
        self.variables.clear()
        self.flags.clear()
        self.current_scene = ""
