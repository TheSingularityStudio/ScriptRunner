#!/usr/bin/env python3
"""
文字游戏脚本运行器
一个简单的基于文本的游戏引擎，用于运行YAML脚本定义的游戏。
"""

import sys
import os
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.ui.renderer import Renderer

def main():
    if len(sys.argv) != 2:
        print("用法: python main.py <脚本文件>")
        print("示例: python main.py example_game.yaml")
        sys.exit(1)

    script_file = sys.argv[1]

    try:
        # 初始化组件
        parser = ScriptParser()
        state_manager = StateManager()
        execution_engine = ExecutionEngine(parser, state_manager)
        renderer = Renderer(execution_engine)

        # 加载游戏脚本
        print(f"正在加载游戏脚本: {script_file}")
        parser.load_script(script_file)

        # 获取起始场景
        current_scene_id = parser.get_start_scene()
        print(f"游戏从场景开始: {current_scene_id}")

        # 主游戏循环
        while current_scene_id:
            # 执行当前场景
            scene_data = execution_engine.execute_scene(current_scene_id)

            # 渲染场景
            renderer.render_scene(scene_data)

            # 获取玩家选择
            choice_index = renderer.get_player_choice()

            if choice_index == -1:
                # 没有做出选择，继续当前场景
                continue

            # 处理选择
            next_scene = execution_engine.process_choice(choice_index)

            if next_scene:
                current_scene_id = next_scene
            else:
                print("\n无效的选择，请重试。")
                continue

        print("\n感谢游玩！")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"脚本错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n游戏已中断。")
        # 可选：在此保存游戏状态
        sys.exit(0)
    except Exception as e:
        print(f"意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
