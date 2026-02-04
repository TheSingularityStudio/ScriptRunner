"""
脚本编译器
负责脚本的初始化和执行逻辑。
"""

import os
import yaml
from src.infrastructure.container import Container
from src.infrastructure.logger import get_logger
from src.utils.exceptions import ScriptExecutionError, ScriptError, ConfigurationError


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

        # 获取起始动作
        start_action = parser.script_data.get('start_action', 'main')
        self.logger.info(f"Script starting from action: {start_action}")
        print(f"脚本从动作开始: {start_action}")

        # 运行执行循环
        self._run_execution_loop(execution_engine, renderer, state_manager, start_action)

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
            # Initialize variables from script
            variables = parser.script_data.get('variables', {})
            if isinstance(variables, dict):
                for var_name, var_value in variables.items():
                    state_manager.set_variable(var_name, var_value)
                self.logger.info(f"Initialized {len(variables)} variables from script")

            # Set context with script metadata
            context = {
                'name': parser.script_data.get('name', 'Unnamed Script'),
                'description': parser.script_data.get('description', ''),
                'version': parser.script_data.get('version', '1.0.0'),
                'status': 'active'
            }
            state_manager.set_variable('context', context)
            self.logger.info("Context initialized successfully")
        except Exception as e:
            self.logger.error(f"Unexpected error during context initialization: {e}")
            raise ScriptError(f"上下文初始化意外错误: {e}")

    def _run_execution_loop(self, execution_engine, renderer, state_manager, start_action: str):
        """运行主执行循环，执行脚本动作。"""
        consecutive_error_count = 0
        max_consecutive_errors = 3  # 限制连续错误次数

        try:
            # 检查是否需要使用游戏插件进行交互式执行
            plugin_manager = self.container.get('plugin_manager')
            game_plugin = plugin_manager.get_plugin('game_runner') if plugin_manager else None

            if game_plugin and self._should_use_game_plugin():
                # 使用游戏插件进行交互式执行
                self._run_game_execution_loop(execution_engine, renderer, state_manager, start_action, game_plugin)
            else:
                # 使用标准动作执行
                self._execute_action(start_action, execution_engine, renderer, state_manager)
                self.logger.info(f"Executed action: {start_action}")

        except KeyboardInterrupt:
            self.logger.info("Execution interrupted by user")
            print("\n\n执行已中断。")
            # 尝试保存执行状态
            try:
                if self.container.has('state_manager'):
                    state_manager = self.container.get('state_manager')
                    state_manager.save_execution_state()
                    self.logger.info("Execution state saved successfully")
                    print("执行状态已保存。")
                else:
                    self.logger.warning("State manager not available, cannot save execution state")
                    print("状态管理器不可用，无法保存执行状态。")
            except Exception as save_error:
                self.logger.error(f"Failed to save execution state: {save_error}")
                print(f"保存执行状态失败: {save_error}")
        except Exception as e:
            consecutive_error_count += 1
            self.logger.error(f"Unexpected error in execution (attempt {consecutive_error_count}/{max_consecutive_errors}): {e}")
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

    def _execute_action(self, action_name: str, execution_engine, renderer, state_manager):
        """执行一个脚本动作。"""
        script_data = self.container.get('parser').script_data
        actions = script_data.get('actions', {})

        if action_name not in actions:
            raise ScriptError(f"Action '{action_name}' not found in script")

        action = actions[action_name]
        commands = action.get('commands', [])

        for command in commands:
            self._execute_command(command, renderer, state_manager)

    def _execute_command(self, command: dict, renderer, state_manager):
        """执行单个命令。"""
        command_type = command.get('type')
        if command_type == 'print':
            message = command.get('message', '')
            # 替换变量
            message = self._replace_variables(message, state_manager)
            renderer.show_message(message)
        elif command_type == 'set_variable':
            name = command.get('name')
            value = command.get('value')
            # 替换变量值中的变量
            value = self._replace_variables(str(value), state_manager)
            state_manager.set_variable(name, value)
        elif command_type == 'input':
            name = command.get('name')
            message = command.get('message', f'请输入 {name}')
            # 替换消息中的变量
            message = self._replace_variables(message, state_manager)
            # Get input handler from container
            input_handler = self.container.get('input_handler')
            if input_handler:
                user_input = input_handler.get_parameter_input(name, 'str')
                state_manager.set_variable(name, user_input)
            else:
                self.logger.error("Input handler not available")
        elif command_type == 'if':
            condition = command.get('condition', '')
            then_commands = command.get('then', [])
            else_commands = command.get('else', [])

            # Evaluate condition
            from src.utils.expression_evaluator import ExpressionEvaluator
            variables = {}
            # Get all current variables for condition evaluation
            for var_name in state_manager.get_all_variables().keys():
                variables[var_name] = state_manager.get_variable(var_name)

            condition_result = ExpressionEvaluator.evaluate_expression(condition, variables)
            if condition_result:
                for cmd in then_commands:
                    self._execute_command(cmd, renderer, state_manager)
            else:
                for cmd in else_commands:
                    self._execute_command(cmd, renderer, state_manager)
        else:
            self.logger.warning(f"Unknown command type: {command_type}")

    def _replace_variables(self, text: str, state_manager) -> str:
        """替换文本中的变量占位符。"""
        import re
        def replace_match(match):
            var_name = match.group(1)
            return str(state_manager.get_variable(var_name, ''))
        return re.sub(r'\{(\w+)\}', replace_match, text)
