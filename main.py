#!/usr/bin/env python3
"""
文字游戏脚本运行器
一个简单的基于文本的游戏引擎，用于运行YAML脚本定义的游戏，支持DSL语法。
"""

import sys
import os
from src.di.container import Container
from src.logging.logger import setup_logging, get_logger
from src.config.config import Config
from src.ui.ui_interface import UIManager
from src.plugins.plugin_manager import PluginManager
from src.utils.exceptions import GameError, ScriptError, ConfigurationError
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.ui.renderer import ConsoleRenderer
from src.app.initializer import ApplicationInitializer

# 创建所有依赖实例
container = Container()
config = Config()
ui_manager = UIManager()
plugin_manager = PluginManager()
logger = get_logger(__name__)


def main():
    if len(sys.argv) == 1:
        script_file = "scripts/example_game.yaml"
    elif len(sys.argv) == 2:
        script_file = sys.argv[1]
    else:
        print("用法: python main.py [脚本文件]")
        print("如果不指定脚本文件，将使用默认脚本: scripts/example_game.yaml")
        print("示例: python main.py scripts/example_game.yaml")
        sys.exit(1)

    try:
        # 创建并初始化应用程序
        initializer = ApplicationInitializer(container, ui_manager, plugin_manager)
        initializer.initialize()

        # 从 DI 容器获取组件
        parser = container.get('parser')
        state_manager = container.get('state_manager')
        execution_engine = container.get('execution_engine')
        renderer = ui_manager.get_current_backend()(execution_engine)

        # 加载游戏脚本
        logger.info(f"Loading game script: {script_file}")
        print(f"正在加载游戏脚本: {script_file}")
        parser.load_script(script_file)

        # 初始化玩家属性
        player_data = parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            state_manager.set_variable(attr, value)

        # 获取起始场景
        current_scene_id = parser.get_start_scene()
        logger.info(f"Game starting from scene: {current_scene_id}")
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
                # 未做选择，继续当前场景
                continue

            # 流程选择
            next_scene = execution_engine.process_choice(choice_index)

            if next_scene:
                current_scene_id = next_scene
            else:
                print("\n无效的选择，请重试。")
                continue

        print("\n感谢游玩！")
        logger.info("Game ended normally")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"错误: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Script error: {e}")
        print(f"脚本错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
        print("\n\n游戏已中断。")
        # 可选：在此保存游戏状态
        state_manager.save_game()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
