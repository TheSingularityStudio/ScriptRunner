"""
ScriptRunner 的输入处理器。
处理脚本参数输入。
"""

from typing import Dict, Any, Optional
from ...domain.runtime.interfaces import IInputHandler
from ...infrastructure.logger import get_logger
from ...infrastructure.config import Config
from ...infrastructure.container import Container
from ...utils.exceptions import ExecutionError

logger = get_logger(__name__)


class InputHandler(IInputHandler):
    """处理脚本参数输入。"""

    def __init__(self, container: Container, config: Config):
        self.container = container
        self.config = config

    def get_parameter_input(self, param_name: str, param_type: str = 'str', default_value: Any = None) -> Any:
        """
        获取参数输入。

        Args:
            param_name: 参数名称
            param_type: 参数类型 ('str', 'int', 'float', 'bool')
            default_value: 默认值

        Returns:
            参数值

        Raises:
            ExecutionError: 当输入无效时抛出
        """
        logger.debug(f"Getting parameter input: {param_name} ({param_type})")

        while True:
            try:
                prompt = f"请输入 {param_name}"
                if default_value is not None:
                    prompt += f" (默认: {default_value})"
                prompt += ": "

                user_input = input(prompt).strip()

                # 如果输入为空且有默认值，使用默认值
                if not user_input and default_value is not None:
                    logger.debug(f"Using default value for {param_name}: {default_value}")
                    return default_value

                # 如果输入为空且无默认值，继续循环
                if not user_input:
                    continue

                # 根据类型转换输入
                if param_type == 'int':
                    return int(user_input)
                elif param_type == 'float':
                    return float(user_input)
                elif param_type == 'bool':
                    return user_input.lower() in ('true', '1', 'yes', 'y')
                else:
                    return user_input

            except ValueError:
                logger.warning(f"Invalid input type for {param_name}, expected {param_type}")
                print(f"请输入有效的 {param_type} 类型值。")
            except KeyboardInterrupt:
                logger.info("Input interrupted by user")
                raise ExecutionError("用户中断输入")
            except Exception as e:
                logger.error(f"Unexpected error during parameter input: {e}")
                print(f"输入时发生意外错误: {e}")
                print("请重试。")

    def get_multiple_parameters(self, params: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取多个参数输入。

        Args:
            params: 参数配置字典，格式为 {param_name: {'type': str, 'default': value, 'description': str}}

        Returns:
            参数值字典
        """
        logger.debug(f"Getting multiple parameters: {list(params.keys())}")
        result = {}

        for param_name, config in params.items():
            param_type = config.get('type', 'str')
            default_value = config.get('default')
            description = config.get('description', '')

            if description:
                print(f"\n{description}")

            value = self.get_parameter_input(param_name, param_type, default_value)
            result[param_name] = value

        return result

    def confirm_action(self, message: str) -> bool:
        """
        确认操作。

        Args:
            message: 确认消息

        Returns:
            是否确认
        """
        logger.debug(f"Confirming action: {message}")

        while True:
            try:
                user_input = input(f"{message} (y/n): ").strip().lower()
                if user_input in ('y', 'yes', 'true', '1'):
                    return True
                elif user_input in ('n', 'no', 'false', '0'):
                    return False
                else:
                    print("请输入 y 或 n。")
            except KeyboardInterrupt:
                logger.info("Confirmation interrupted by user")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during confirmation: {e}")
                print(f"确认时发生意外错误: {e}")
                print("请重试。")

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """
        处理输入（为了兼容接口，实际不处理自然语言输入）。

        Args:
            input_text: 输入文本

        Returns:
            处理结果字典
        """
        logger.warning("process_player_input called on generic InputHandler - this should be handled by game plugin")
        return {
            'success': False,
            'message': '此输入处理器不支持自然语言输入，请使用参数输入方法。',
            'action': 'unsupported'
        }
