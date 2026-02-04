#!/usr/bin/env python3
"""
脚本编译器
一个简单的基于文本的脚本执行引擎，用于编译和运行YAML脚本定义的脚本，支持DSL语法。
"""

import sys
import os
from src.infrastructure.container import Container
from src.infrastructure.logger import get_logger
from src.utils.exceptions import ScriptError
from src.application.script_compiler import ScriptCompiler

# 创建 DI 容器
container = Container()


def parse_arguments():
    """Parse command line arguments and return the script file path."""
    logger = get_logger('main')
    if len(sys.argv) == 1:
        script_file = "scripts/main.yaml"
    elif len(sys.argv) == 2:
        script_file = sys.argv[1]
    else:
        logger.error("用法: python main.py [脚本文件]")
        logger.error("如果不指定脚本文件，将使用默认脚本: scripts/main.yaml")
        logger.error("示例: python main.py scripts/main.yaml")
        sys.exit(1)

    # 规范化文件路径
    script_file = os.path.normpath(os.path.abspath(script_file))
    return script_file


def validate_script_file(script_file):
    """Validate that the script file exists and is readable."""
    logger = get_logger('main')
    if not os.path.isfile(script_file):
        logger.error(f"Script file not found: {script_file}")
        logger.error(f"错误: 脚本文件不存在: {script_file}")
        sys.exit(1)
    if not os.access(script_file, os.R_OK):
        logger.error(f"Script file not readable: {script_file}")
        logger.error(f"错误: 脚本文件不可读: {script_file}")
        sys.exit(1)


def main():
    logger = get_logger('main')

    script_file = parse_arguments()
    validate_script_file(script_file)

    try:
        script_compiler = ScriptCompiler(container)
        script_compiler.compile_script(script_file)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error(f"错误: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Script error: {e}")
        logger.error(f"脚本错误: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"意外错误: {e}")
        sys.exit(1)
    finally:
        # 清理资源
        logger.info("Cleaning up resources")
        # 这里可以添加更多的清理逻辑，比如关闭文件句柄、重置状态等
        # 目前容器和组件是全局的，不需要显式清理

if __name__ == "__main__":
    main()
