from typing import Dict, Any, List

class Renderer:
    def __init__(self, execution_engine):
        self.engine = execution_engine

    def render_scene(self, scene_data: Dict[str, Any]):
        """渲染场景到控制台，支持DSL动态内容。"""
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

        active_effects = getattr(self.engine, 'active_effects', {})
        if active_effects:
            print("效果:", ', '.join(active_effects.keys()))

    def get_player_choice(self) -> int:
        """获取玩家的选择输入，支持自然语言。"""
        while True:
            try:
                user_input = input("\n请选择 (输入数字) 或输入命令: ").strip()
                if not user_input:
                    return -1  # No choice made

                # 检查是否是数字选择
                if user_input.isdigit():
                    return int(user_input) - 1  # Convert to 0-based index

                # 处理自然语言输入
                result = self.engine.process_player_input(user_input)
                self.show_message(result['message'])
                return -1  # Continue current scene

            except ValueError:
                print("请输入有效的数字或命令。")

    def show_message(self, message: str):
        """向玩家显示消息。"""
        print(f"\n{message}")

    def clear_screen(self):
        """清除控制台屏幕。"""
        print("\n" * 50)  # Simple screen clear
