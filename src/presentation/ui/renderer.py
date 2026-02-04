import os
from typing import Dict, Any
from .ui_interface import UIBackend
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)

class ConsoleRenderer(UIBackend):
    def __init__(self, execution_engine):
        self.engine = execution_engine

    def render_output(self, output_data: Dict[str, Any]):
        """渲染通用脚本输出到控制台。"""
        self.clear_screen()
        print("\n" + "="*50)
        text = output_data.get('text', '')
        print(text)
        print("="*50)

        # 显示附加信息
        additional_info = output_data.get('additional_info', {})
        if additional_info:
            print("\n附加信息:")
            for key, value in additional_info.items():
                print(f"- {key}: {value}")

    def get_parameter_input(self, param_name: str, param_type: str = 'str') -> Any:
        """获取参数输入。"""
        logger.debug(f"Waiting for parameter input: {param_name}")
        while True:
            try:
                user_input = input(f"\n请输入 {param_name}: ").strip()
                if not user_input:
                    logger.debug("No input provided")
                    return None

                # 根据类型转换输入
                if param_type == 'int':
                    return int(user_input)
                elif param_type == 'float':
                    return float(user_input)
                else:
                    return user_input

            except ValueError:
                logger.warning(f"Invalid input type for {param_name}, expected {param_type}")
                print(f"请输入有效的 {param_type} 类型值。")
            except KeyboardInterrupt:
                logger.info("Input interrupted by user")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during input: {e}")
                print(f"输入时发生意外错误: {e}")
                print("请重试。")

    def show_message(self, message: str):
        """显示消息。"""
        print(f"\n{message}")
        input("按回车键继续...")

    def clear_screen(self):
        """清除控制台屏幕。"""
        os.system('cls' if os.name == 'nt' else 'clear')
