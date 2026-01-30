from typing import Dict, Any, Set, Optional
import json
import os
import time
from pathlib import Path
from ..logging.logger import get_logger

logger = get_logger(__name__)


class StateManager:
    def __init__(self, save_file: Optional[str] = None):
        self.variables: Dict[str, Any] = {}
        self.flags: Set[str] = set()
        self.current_scene: str = ""
        self.save_file = save_file or "game_save.json"
        self.active_effects: Dict[str, Dict[str, Any]] = {}  # DSL 效果

        # 缓存与优化
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._auto_save_enabled = True
        self._last_save_time = 0
        self._save_interval = 300  # 5 分钟

        # 性能追踪
        self._operation_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

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
