"""
ScriptRunner 的配置管理。
从 YAML 文件加载和管理应用程序设置。
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """ScriptRunner 的配置管理器。"""

    def __init__(self, config_file: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_file = config_file or self._get_default_config_file()
        self.load()

    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径。"""
        return os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')

    def load(self):
        """从文件加载配置。"""
        config_path = Path(self._config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # 加载默认配置
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置值。"""
        return {
            'logging': {
                'level': 'INFO',
                'file': 'scriptrunner.log'
            },
            'game': {
                'save_file': 'game_save.json',
                'auto_save': True
            },
            'ui': {
                'type': 'console',
                'clear_screen': True
            },
            'plugins': {
                'enabled': [],
                'directory': 'plugins'
            }
        }

    def get(self, key: str, default=None):
        """通过键获取配置值（支持点号表示法）。"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """通过键设置配置值（支持点号表示法）。"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """将当前配置保存到文件。"""
        config_path = Path(self._config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

    def reload(self):
        """从文件重新加载配置。"""
        self.load()

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置值。"""
        return self._config.copy()


# 移除全局配置实例，由调用方创建和管理
