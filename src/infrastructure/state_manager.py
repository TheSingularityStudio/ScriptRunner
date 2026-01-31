from typing import Dict, Any, Set, Optional
import json
import os
from .logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """游戏状态管理器，专注于状态存储和管理。"""

    def __init__(self, save_file: Optional[str] = None):
        self.variables: Dict[str, Any] = {}
        self.flags: Set[str] = set()
        self.current_scene: str = ""
        self.save_file = save_file or "game_save.json"
        self.active_effects: Dict[str, Dict[str, Any]] = {}  # DSL 效果

    def set_variable(self, key: str, value: Any):
        """设置游戏变量。"""
        self.variables[key] = value

    def get_variable(self, key: str, default=None):
        """获取游戏变量。"""
        return self.variables.get(key, default)

    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量。"""
        return self.variables.copy()

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

    def apply_effect(self, effect_name: str, effect_data: Dict[str, Any]):
        """应用DSL效果。"""
        self.active_effects[effect_name] = effect_data

    def remove_effect(self, effect_name: str):
        """移除DSL效果。"""
        self.active_effects.pop(effect_name, None)

    def get_active_effects(self) -> Dict[str, Dict[str, Any]]:
        """获取活跃效果。"""
        return self.active_effects

    def update_effects(self):
        """更新效果状态（例如，持续时间）。"""
        expired = []
        for effect_name, effect in self.active_effects.items():
            duration = effect.get('duration', 0)
            if duration > 0:
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    expired.append(effect_name)

        for effect_name in expired:
            self.remove_effect(effect_name)

    def save_game(self):
        """将游戏状态保存到文件，包括DSL效果。"""
        state = {
            'variables': self.variables,
            'flags': list(self.flags),
            'current_scene': self.current_scene,
            'active_effects': self.active_effects
        }
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_game(self):
        """从文件加载游戏状态，包括DSL效果。"""
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.variables = state.get('variables', {})
            self.flags = set(state.get('flags', []))
            self.current_scene = state.get('current_scene', '')
            self.active_effects = state.get('active_effects', {})
            return True
        return False

    def reset(self):
        """重置游戏状态，包括DSL效果。"""
        self.variables.clear()
        self.flags.clear()
        self.current_scene = ""
        self.active_effects.clear()
