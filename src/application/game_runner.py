"""
游戏运行器
负责游戏的初始化和执行逻辑。
"""

import os
import yaml
from src.infrastructure.container import Container
from src.infrastructure.logger import get_logger
from src.utils.exceptions import GameError, ScriptError, ConfigurationError


class GameRunner:
    """游戏运行器，负责游戏的初始化和执行。"""

    def __init__(self, container: Container):
        self.container = container
        self.logger = get_logger(__name__)

    def run_game(self, script_file: str):
        """运行游戏。

        Args:
            script_file: 游戏脚本文件路径

        Raises:
            ConfigurationError: 配置错误
            ScriptError: 脚本错误
            GameError: 游戏运行错误
        """
        # 初始化应用程序组件
        parser, state_manager, execution_engine, renderer = self._initialize_application()

        # 加载游戏脚本
        self._load_game_script(parser, script_file)

        # 初始化玩家
        self._initialize_player(parser, state_manager)

        # 获取起始场景
        current_scene_id = parser.get_start_scene()
        self.logger.info(f"Game starting from scene: {current_scene_id}")
        print(f"游戏从场景开始: {current_scene_id}")

        # 运行游戏循环
        self._run_game_loop(execution_engine, renderer, current_scene_id)

    def _initialize_application(self):
        """初始化应用程序并返回必要的组件。"""
        # 创建并初始化应用程序
        from src.application.initializer import ApplicationInitializer
        initializer = ApplicationInitializer(self.container)
        initializer.initialize()

        # 从 DI 容器获取组件
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')
        execution_engine = self.container.get('execution_engine')

        # 初始化 state_manager 为 None，以防后续使用
        if state_manager is None:
            raise ConfigurationError("State manager could not be initialized")

        # 获取渲染器
        renderer = self.container.get('renderer')
        self.logger.info("Renderer initialized successfully")

        return parser, state_manager, execution_engine, renderer

    def _load_game_script(self, parser, script_file: str):
        """加载游戏脚本。"""
        self.logger.info(f"Loading game script: {script_file}")
        print(f"正在加载游戏脚本: {script_file}")
        try:
            parser.load_script(script_file)
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in script file: {e}")
            print(f"脚本文件 YAML 解析错误: {e}")
            raise ScriptError(f"YAML parsing error: {e}")
        except ValueError as e:
            self.logger.error(f"Script validation error: {e}")
            print(f"脚本验证错误: {e}")
            raise ScriptError(f"Script validation error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error loading script: {e}")
            print(f"加载脚本意外错误: {e}")
            raise ScriptError(f"Unexpected error loading script: {e}")

    def _initialize_player(self, parser, state_manager):
        """初始化玩家属性。"""
        try:
            player_data = parser.script_data.get('player', {})
            if player_data and isinstance(player_data, dict):
                # 检查是否有attributes子字典，或者直接使用player下的属性
                attributes = player_data.get('attributes', player_data)
                if isinstance(attributes, dict):
                    for attr, value in attributes.items():
                        state_manager.set_variable(attr, value)
                    self.logger.info("Player attributes initialized successfully")
                else:
                    self.logger.warning("No valid player attributes found in script data, using defaults")
                    # 设置默认玩家属性
                    state_manager.set_variable('health', 100)
                    state_manager.set_variable('name', 'Player')
                    self.logger.info("Default player attributes set")
            else:
                self.logger.warning("No valid player attributes found in script data, using defaults")
                # 设置默认玩家属性
                state_manager.set_variable('health', 100)
                state_manager.set_variable('name', 'Player')
                self.logger.info("Default player attributes set")
        except KeyError as e:
            self.logger.error(f"Error initializing player attributes: {e}")
            raise ScriptError(f"玩家属性初始化失败: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during player initialization: {e}")
            raise ScriptError(f"玩家初始化意外错误: {e}")

    def _run_game_loop(self, execution_engine, renderer, current_scene_id: str):
        """运行主游戏循环。"""
        invalid_choice_count = 0
        max_invalid_choices = 5  # 限制无效选择次数
        rerender = True
        while current_scene_id:
            try:
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
                elif not messages:
                    # 只有在没有消息（表示无效选择）时才递增计数器
                    invalid_choice_count += 1
                    if invalid_choice_count >= max_invalid_choices:
                        self.logger.warning(f"Too many invalid choices ({invalid_choice_count}), ending game")
                        print(f"\n无效选择次数过多 ({invalid_choice_count})，游戏结束。")
                        break
                    print(f"\n无效的选择，请重试。 (剩余尝试次数: {max_invalid_choices - invalid_choice_count})")
                    continue
                # 如果有消息但没有场景变化，认为是有效选择但不推进场景，不递增计数器

            except KeyboardInterrupt:
                self.logger.info("Game interrupted by user during loop")
                print("\n\n游戏已中断。")
                # 尝试保存游戏状态
                try:
                    if self.container.has('state_manager'):
                        state_manager = self.container.get('state_manager')
                        state_manager.save_game()
                        self.logger.info("Game state saved successfully")
                        print("游戏状态已保存。")
                    else:
                        self.logger.warning("State manager not available, cannot save game")
                        print("状态管理器不可用，无法保存游戏状态。")
                except Exception as save_error:
                    self.logger.error(f"Failed to save game state: {save_error}")
                    print(f"保存游戏状态失败: {save_error}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in game loop: {e}")
                print(f"\n游戏运行中发生意外错误: {e}")
                print("尝试继续游戏...")
                # 可以选择继续或退出，这里选择继续，但记录错误

        print("\n感谢游玩！")
        self.logger.info("Game ended normally")
