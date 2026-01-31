#!/usr/bin/env python3
"""
文字游戏脚本运行器
一个简单的基于文本的游戏引擎，用于运行YAML脚本定义的游戏，支持DSL语法。
"""

import sys
import os
from src.di.container import Container
from src.logging.logger import setup_logging, get_logger
from src.application.config import Config
from src.ui.ui_interface import UIManager
from src.plugins.plugin_manager import PluginManager
from src.utils.exceptions import GameError, ScriptError, ConfigurationError
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.ui.renderer import ConsoleRenderer
from src.application.initializer import ApplicationInitializer

# 创建 DI 容器
container = Container()

# 注册核心组件到 DI 容器
config = Config()
ui_manager = UIManager()
plugin_manager = PluginManager()
container.register('config', config)
container.register('ui_manager', ui_manager)
container.register('plugin_manager', plugin_manager)


def main():
    # 设置日志配置
    setup_logging()
    logger = get_logger('main')

    # 验证脚本文件路径
    if len(sys.argv) == 1:
        script_file = "scripts/example_game.yaml"
    elif len(sys.argv) == 2:
        script_file = sys.argv[1]
    else:
        print("用法: python main.py [脚本文件]")
        print("如果不指定脚本文件，将使用默认脚本: scripts/example_game.yaml")
        print("示例: python main.py scripts/example_game.yaml")
        sys.exit(1)

    # 检查脚本文件是否存在且可读
    if not os.path.isfile(script_file):
        logger.error(f"Script file not found: {script_file}")
        print(f"错误: 脚本文件不存在: {script_file}")
        sys.exit(1)
    if not os.access(script_file, os.R_OK):
        logger.error(f"Script file not readable: {script_file}")
        print(f"错误: 脚本文件不可读: {script_file}")
        sys.exit(1)

    try:
        # 创建并初始化应用程序
        initializer = ApplicationInitializer(container, ui_manager, plugin_manager)
        initializer.initialize()

        # 从 DI 容器获取组件
        parser = container.get('parser')
        state_manager = container.get('state_manager')
        execution_engine = container.get('execution_engine')

        # 初始化渲染器
        try:
            from src.presentation.ui.renderer import ConsoleRenderer
            renderer = ConsoleRenderer(execution_engine)
            logger.info("Renderer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize renderer: {e}")
            raise ConfigurationError(f"渲染器初始化失败: {e}")

        # 加载游戏脚本
        logger.info(f"Loading game script: {script_file}")
        print(f"正在加载游戏脚本: {script_file}")
        parser.load_script(script_file)

        # 初始化玩家属性
        try:
            player_data = parser.script_data.get('player', {})
            if 'attributes' in player_data:
                for attr, value in player_data['attributes'].items():
                    state_manager.set_variable(attr, value)
                logger.info("Player attributes initialized successfully")
            else:
                logger.warning("No player attributes found in script data")
        except KeyError as e:
            logger.error(f"Error initializing player attributes: {e}")
            raise ScriptError(f"玩家属性初始化失败: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during player initialization: {e}")
            raise ScriptError(f"玩家初始化意外错误: {e}")

        # 获取起始场景
        current_scene_id = parser.get_start_scene()
        logger.info(f"Game starting from scene: {current_scene_id}")
        print(f"游戏从场景开始: {current_scene_id}")

        # 主游戏循环
        invalid_choice_count = 0
        max_invalid_choices = 5  # 限制无效选择次数
        rerender = True
        while current_scene_id:
            # 更新效果状态
            execution_engine.effects_manager.update_effects()

            if rerender:
                # 执行当前场景
                scene_data = execution_engine.execute_scene(current_scene_id)

                # 渲染场景
                renderer.render_scene(scene_data)

            rerender = True  # 默认重新渲染

            # 获取玩家选择
            choice_index = renderer.get_player_choice()

            if choice_index == -1:
                # 未做选择，继续当前场景，不重新渲染
                rerender = False
                continue

            # 流程选择
            next_scene, messages = execution_engine.process_choice(choice_index)

            # 显示命令执行消息
            if messages:
                renderer.show_message('\n'.join(messages))

            if next_scene:
                current_scene_id = next_scene
                invalid_choice_count = 0  # 重置计数器
            else:
                invalid_choice_count += 1
                if invalid_choice_count >= max_invalid_choices:
                    logger.warning(f"Too many invalid choices ({invalid_choice_count}), ending game")
                    print(f"\n无效选择次数过多 ({invalid_choice_count})，游戏结束。")
                    break
                print(f"\n无效的选择，请重试。 (剩余尝试次数: {max_invalid_choices - invalid_choice_count})")
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
        # 尝试保存游戏状态
        try:
            if 'state_manager' in locals():
                state_manager.save_game()
                logger.info("Game state saved successfully")
                print("游戏状态已保存。")
            else:
                logger.warning("State manager not available, cannot save game")
        except Exception as save_error:
            logger.error(f"Failed to save game state: {save_error}")
            print(f"保存游戏状态失败: {save_error}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
