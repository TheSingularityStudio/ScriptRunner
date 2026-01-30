"""
ScriptRunner 的日志系统。提供集中式日志配置和实用工具.
"""

import logging
import logging.config
import os
from typing import Optional, Dict, Any


class Logger:
    """集中式日志配置和工具。"""

    _configured = False

    @classmethod
    def setup(cls, config: Optional[Dict[str, Any]] = None):
        """设置日志配置。"""
        if cls._configured:
            return

        if config is None:
            config = cls._get_default_config()

        logging.config.dictConfig(config)
        cls._configured = True

    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
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
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': 'scriptrunner.log',
                    'mode': 'a'
                }
            },
            'loggers': {
                'scriptrunner': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file'],
                    'propagate': False
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


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """设置日志配置。"""
    Logger.setup(config)
