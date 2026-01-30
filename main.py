#!/usr/bin/env python3
"""
文字游戏脚本运行器
一个简单的基于文本的游戏引擎，用于运行YAML脚本定义的游戏，支持DSL语法。
"""

import sys
import os
from src.di.container import container
from src.logging.logger import setup_logging, get_logger
from src.config.config import config
from src.ui.ui_interface import ui_manager
from src.plugins.plugin_manager import plugin_manager
from src.utils.exceptions import GameError, ScriptError, ConfigurationError
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.ui.renderer import ConsoleRenderer

logger = get_logger(__name__)


def setup_application():
    """Setup the application with DI container."""
    # Setup logging
    setup_logging()

    # Register services in DI container
    container.register('parser', ScriptParser())
    container.register('state_manager', StateManager())
    container.register('execution_engine', ExecutionEngine(
        container.get('parser'),
        container.get('state_manager')
    ))

    # Register UI backend
    ui_manager.register_backend('console', ConsoleRenderer)
    ui_manager.set_backend('console')

    # Load plugins
    plugin_manager.load_plugins()

    logger.info("Application setup completed")


def main():
    if len(sys.argv) != 2:
        print("用法: python main.py <脚本文件>")
        print("示例: python main.py example_game.yaml")
        sys.exit(1)

    script_file = sys.argv[1]

    try:
        # Setup application
        setup_application()

        # Get components from DI container
        parser = container.get('parser')
        state_manager = container.get('state_manager')
        execution_engine = container.get('execution_engine')
        renderer = ui_manager.get_current_backend()(execution_engine)

        # Load game script
        logger.info(f"Loading game script: {script_file}")
        print(f"正在加载游戏脚本: {script_file}")
        parser.load_script(script_file)

        # Initialize player attributes
        player_data = parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            state_manager.set_variable(attr, value)

        # Get starting scene
        current_scene_id = parser.get_start_scene()
        logger.info(f"Game starting from scene: {current_scene_id}")
        print(f"游戏从场景开始: {current_scene_id}")

        # Main game loop
        while current_scene_id:
            # Execute current scene
            scene_data = execution_engine.execute_scene(current_scene_id)

            # Render scene
            renderer.render_scene(scene_data)

            # Get player choice
            choice_index = renderer.get_player_choice()

            if choice_index == -1:
                # No choice made, continue current scene
                continue

            # Process choice
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
        # Optional: save game state here
        state_manager.save_game()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
