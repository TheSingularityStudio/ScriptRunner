import os
from typing import Dict, Any, List
from .ui_interface import UIBackend
from ..logging.logger import get_logger

logger = get_logger(__name__)

class ConsoleRenderer(UIBackend):
    def __init__(self, execution_engine):
        self.engine = execution_engine

    def render_scene(self, scene_data: Dict[str, Any]):
        """渲染场景到控制台，支持DSL动态内容。"""
        self.clear_screen()
        print("\n" + "="*50)
        print(scene_data['text'])
        print("="*50)

        # 显示DSL对象信息
        objects = scene_data.get('objects', [])
        if objects:
            print("\n你可以看到:")
            for obj in objects:
                obj_def = self.engine.parser.get_object(obj.get('ref', ''))
                if obj_def:
                    print(f"- {obj_def.get('name', obj['ref'])}")

        choices = scene_data.get('choices', [])
        if choices:
            print("\n选择:")
            for i, choice in enumerate(choices):
                print(f"{i+1}. {choice['text']}")
        else:
            print("\n[游戏结束]")

        # 显示状态信息
        self._render_status()

    def _render_status(self):
        """渲染玩家状态。"""
        health = self.engine.state.get_variable('health', 100)
        print(f"\n状态: 生命值 {health}")

        active_effects = self.engine.state.get_active_effects()
        if active_effects:
            print("效果:", ', '.join(active_effects.keys()))

    def get_player_choice(self) -> int:
        """获取玩家的选择输入，支持自然语言。"""
        logger.debug("Waiting for player input")
        while True:
            try:
                user_input = input("\n请选择 (输入数字) 或输入命令: ").strip()
                if not user_input:
                    logger.debug("No input provided")
                    return -1  # No choice made

                # 检查是否是数字选择
                if user_input.isdigit():
                    choice = int(user_input) - 1  # Convert to 0-based index
                    logger.debug(f"Player selected choice: {choice}")
                    return choice

                # 处理自然语言输入
                result = self.engine.process_player_input(user_input)
                self.show_message(result['message'])
                logger.debug(f"Processed natural language input: {user_input}")
                return -1  # Continue current scene

            except ValueError:
                logger.warning("Invalid input format")
                print("请输入有效的数字或命令。")

    def show_message(self, message: str):
        """向玩家显示消息。"""
        print(f"\n{message}")

    def clear_screen(self):
        """清除控制台屏幕。"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def render_status(self, status_data: Dict[str, Any]):
        """渲染玩家状态信息。"""
        print("\n" + "-"*30)
        print("玩家状态:")
        for key, value in status_data.items():
            print(f"  {key}: {value}")
        print("-"*30)
