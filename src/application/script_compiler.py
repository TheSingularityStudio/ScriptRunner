"""
脚本编译器
负责脚本的初始化和执行逻辑。
"""

import os
import yaml
from src.infrastructure.container import Container
from src.infrastructure.logger import get_logger
from src.utils.exceptions import GameError, ScriptError, ConfigurationError


class ScriptCompiler:
    """脚本编译器，负责脚本的初始化和执行。"""

    def __init__(self, container: Container):
        self.container = container
        self.logger = get_logger(__name__)

    def compile_script(self, script_file: str):
        """编译脚本。

        Args:
            script_file: 脚本文件路径

        Raises:
            ConfigurationError: 配置错误
            ScriptError: 脚本错误
            GameError: 脚本执行错误
        """
        # 初始化应用程序组件
        parser, state_manager, execution_engine, renderer = self._initialize_application()

        # 加载脚本
        self._load_script(parser, script_file)

        # 初始化执行上下文
        self._initialize_context(parser, state_manager)

        # 获取起始场景
        current_scene_id = parser.get_start_scene()
        self.logger.info(f"Script starting from scene: {current_scene_id}")
        print(f"脚本从场景开始: {current_scene_id}")

        # 运行执行循环
        self._run_execution_loop(execution_engine, renderer, state_manager, current_scene_id)

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

    def _load_script(self, parser, script_file: str):
        """加载脚本。"""
        self.logger.info(f"Loading script: {script_file}")
        print(f"正在加载脚本: {script_file}")
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

    def _initialize_context(self, parser, state_manager):
        """初始化执行上下文。"""
        try:
            context_data = parser.script_data.get('context', {})
            if context_data and isinstance(context_data, dict):
                # 检查是否有attributes子字典，或者直接使用context下的属性
                attributes = context_data.get('attributes', context_data)
                if isinstance(attributes, dict):
                    # 设置context为字典，包含所有属性
                    state_manager.set_variable('context', attributes)
                    self.logger.info("Context attributes initialized successfully")
                else:
                    self.logger.warning("No valid context attributes found in script data, using defaults")
                    # 设置默认上下文属性
                    state_manager.set_variable('context', {'status': 'active', 'name': 'Script'})
                    self.logger.info("Default context attributes set")
            else:
                self.logger.warning("No valid context attributes found in script data, using defaults")
                # 设置默认上下文属性
                state_manager.set_variable('context', {'status': 'active', 'name': 'Script'})
                self.logger.info("Default context attributes set")
        except KeyError as e:
            self.logger.error(f"Error initializing context attributes: {e}")
            raise ScriptError(f"上下文属性初始化失败: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during context initialization: {e}")
            raise ScriptError(f"上下文初始化意外错误: {e}")

    def _run_execution_loop(self, execution_engine, renderer, state_manager, current_scene_id: str):
        """运行主执行循环，使用脚本对象执行。"""
        invalid_choice_count = 0
        max_invalid_choices = 5  # 限制无效选择次数
        consecutive_error_count = 0
        max_consecutive_errors = 3  # 限制连续错误次数
        rerender = True

        # 获取脚本工厂
        script_factory = self.container.get('script_factory')

        while current_scene_id:
            try:
                if rerender:
                    # 执行场景
                    scene_data = execution_engine.execute_scene(current_scene_id)
                    renderer.render_scene(scene_data)

                rerender = True  # 默认重新渲染

                # 获取用户选择
                choice_index = renderer.get_player_choice()

                if choice_index == -1:
                    # 未做选择，继续当前场景，不重新渲染
                    rerender = False
                    continue

                # 处理选择
                next_scene, messages = execution_engine.process_choice(choice_index)

                # 获取广播消息
                broadcast_messages = state_manager.get_broadcast_messages()

                # 合并所有消息
                all_messages = messages + broadcast_messages

                # 显示所有消息
                if all_messages:
                    renderer.show_message('\n'.join(all_messages))

                if next_scene:
                    current_scene_id = next_scene
                    invalid_choice_count = 0  # 重置计数器
                    consecutive_error_count = 0  # 重置错误计数器
                elif not messages:
                    # 只有在没有消息（表示无效选择）时才递增计数器
                    invalid_choice_count += 1
                    if invalid_choice_count >= max_invalid_choices:
                        self.logger.warning(f"Too many invalid choices ({invalid_choice_count}), ending execution")
                        print(f"\n无效选择次数过多 ({invalid_choice_count})，执行结束。")
                        break
                    print(f"\n无效的选择，请重试。 (剩余尝试次数: {max_invalid_choices - invalid_choice_count})")
                    continue
                # 如果有消息但没有场景变化，认为是有效选择但不推进场景，不递增计数器

                consecutive_error_count = 0  # 重置错误计数器，如果没有异常

            except KeyboardInterrupt:
                self.logger.info("Execution interrupted by user during loop")
                print("\n\n执行已中断。")
                # 尝试保存执行状态
                try:
                    if self.container.has('state_manager'):
                        state_manager = self.container.get('state_manager')
                        state_manager.save_game()
                        self.logger.info("Execution state saved successfully")
                        print("执行状态已保存。")
                    else:
                        self.logger.warning("State manager not available, cannot save execution state")
                        print("状态管理器不可用，无法保存执行状态。")
                except Exception as save_error:
                    self.logger.error(f"Failed to save execution state: {save_error}")
                    print(f"保存执行状态失败: {save_error}")
                break
            except Exception as e:
                consecutive_error_count += 1
                self.logger.error(f"Unexpected error in execution loop (attempt {consecutive_error_count}/{max_consecutive_errors}): {e}")
                print(f"\n执行中发生意外错误 (第{consecutive_error_count}次): {e}")

                if consecutive_error_count >= max_consecutive_errors:
                    self.logger.error(f"Too many consecutive errors ({consecutive_error_count}), terminating program")
                    print(f"\n连续错误次数过多 ({consecutive_error_count})，程序终止。")
                    raise SystemExit(1)  # 强制退出程序
                else:
                    print("尝试继续执行...")
                    # 继续循环，但记录错误

        print("\n执行完成！")
        self.logger.info("Execution ended normally")
