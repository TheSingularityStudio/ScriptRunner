"""
ScriptRunner 的日志系统。提供集中式日志配置和实用工具.
"""

import logging
import logging.config
import os
import threading
from datetime import datetime
from typing import Optional, Dict, Any


class Logger:
    """集中式日志配置和工具。"""

    _configured = False
    _lock = threading.RLock()

    @classmethod
    def setup(cls, config: Optional[Dict[str, Any]] = None, log_file: Optional[str] = None, propagate: Optional[bool] = None):
        """设置日志配置。"""
        with cls._lock:
            if cls._configured:
                return

            if config is None:
                # 使用默认配置，但允许覆盖参数
                if log_file is None:
                    # 使用时间命名的日志文件
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    default_log_file = f'logs/{current_date}.log'
                else:
                    default_log_file = log_file
                # 确保日志目录存在
                os.makedirs(os.path.dirname(default_log_file), exist_ok=True)
                default_propagate = propagate if propagate is not None else True
                config = cls._get_default_config(default_log_file, default_propagate)

            # 验证配置
            if not cls._validate_config(config):
                raise ValueError("无效的日志配置")

            logging.config.dictConfig(config)
            cls._configured = True

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> bool:
        """验证日志配置。"""
        if not isinstance(config, dict):
            return False
        if 'version' not in config:
            return False
        if 'handlers' in config and not isinstance(config['handlers'], dict):
            return False
        if 'loggers' in config and not isinstance(config['loggers'], dict):
            return False
        return True

    @classmethod
    def _get_default_config(cls, log_file: str = 'scriptrunner.log', propagate: bool = True) -> Dict[str, Any]:
        """获取默认日志配置。"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'filename': log_file,
                    'when': 'midnight',
                    'interval': 1,
                    'backupCount': 30,
                    'encoding': 'utf-8'
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console', 'file']
            },
            'loggers': {
                'scriptrunner': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': propagate
                }
            }
        }

    @classmethod
    def get_logger(cls, name: str = 'scriptrunner') -> logging.Logger:
        """获取一个日志记录器实例。"""
        if not cls._configured:
            cls.setup()
        return logging.getLogger(name)


# 便捷函数
def get_logger(name: str = 'scriptrunner') -> logging.Logger:
    """获取一个日志记录器实例。"""
    return Logger.get_logger(name)


def setup_logging(config: Optional[Dict[str, Any]] = None, log_file: Optional[str] = None, propagate: Optional[bool] = None):
    """设置日志配置。"""
    Logger.setup(config, log_file, propagate)


# 移除全局logger实例，由调用方创建和管理
