from typing import Dict, Any, List

class Renderer:
    def __init__(self, execution_engine):
        self.engine = execution_engine

    def render_scene(self, scene_data: Dict[str, Any]):
        """渲染场景到控制台。"""
        print("\n" + "="*50)
        print(scene_data['text'])
        print("="*50)

        choices = scene_data.get('choices', [])
        if choices:
            print("\n选择:")
            for i, choice in enumerate(choices):
                print(f"{i+1}. {choice['text']}")
        else:
            print("\n[游戏结束]")

    def get_player_choice(self) -> int:
        """获取玩家的选择输入。"""
        while True:
            try:
                choice = input("\n请选择 (输入数字): ").strip()
                if not choice:
                    return -1  # No choice made
                return int(choice) - 1  # Convert to 0-based index
            except ValueError:
                print("请输入有效的数字。")

    def show_message(self, message: str):
        """向玩家显示消息。"""
        print(f"\n{message}")

    def clear_screen(self):
        """清除控制台屏幕。"""
        print("\n" * 50)  # Simple screen clear
