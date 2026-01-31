"""
ScriptRunner 的配置管理。
从 YAML 文件加载和管理应用程序设置。
"""

import yaml
import os
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)


class Config:
    """ScriptRunner 的配置管理器。"""

    def __init__(self, config_file: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_file = config_file or self._get_default_config_file()
        self._lock = threading.RLock()  # 使用可重入锁
        self.load()

    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径。"""
        # 首先检查环境变量
        env_config = os.environ.get('SCRIPTRUNNER_CONFIG')
        if env_config:
            return env_config

        # 检查多个可能的路径
        possible_paths = [
            # 当前工作目录
            'config.yaml',
            # 用户配置目录
            os.path.join(os.path.expanduser('~'), '.scriptrunner', 'config.yaml'),
            # 项目根目录
            os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 返回默认路径（项目根目录）
        return os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')

    def load(self):
        """从文件加载配置。"""
        config_path = Path(self._config_file)
        logger.info(f"Loading configuration from: {config_path}")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            logger.debug(f"Configuration loaded with {len(self._config)} top-level keys")
        else:
            logger.warning(f"Configuration file not found, using defaults: {config_path}")
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
        with self._lock:
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
        with self._lock:
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
