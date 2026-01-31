import sys
import os
from typing import Tuple
from ..parser.parser import ScriptParser

def check_syntax(file_path: str) -> Tuple[bool, str]:
    """
    检查指定脚本文件的语法是否合格。

    Args:
        file_path (str): 脚本文件路径

    Returns:
        Tuple[bool, str]: (是否合格, 错误信息或成功消息)
    """
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"

    try:
        parser = ScriptParser()
        parser.load_script(file_path)
        return True, "语法检查通过"
    except Exception as e:
        return False, f"语法错误: {str(e)}"

def main():
    """命令行入口点"""
    if len(sys.argv) != 2:
        print("用法: python -m src.utils.syntax_checker <脚本文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    is_valid, message = check_syntax(file_path)

    if is_valid:
        print(f"✓ {message}")
        sys.exit(0)
    else:
        print(f"✗ {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
