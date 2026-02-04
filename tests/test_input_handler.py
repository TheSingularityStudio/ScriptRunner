"""
Unit tests for InputHandler.
"""

import pytest
from unittest.mock import Mock, patch
from src.presentation.input.input_handler import InputHandler


class TestInputHandler:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_container = Mock()
        self.mock_config = Mock()

        # 设置config的get方法
        self.mock_config.get.side_effect = lambda key, default=None: {
            'messages.unknown_command': "未知命令。",
            'messages.execution_success': "脚本执行完成。",
            'messages.execution_error': "脚本执行出错: {error}",
            'messages.parameter_required': "参数 '{param}' 是必需的。",
            'messages.parameter_invalid': "参数 '{param}' 的值无效: {value}",
            'messages.input_prompt': "请输入 {param}: ",
        }.get(key, default)

        self.handler = InputHandler(self.mock_container, self.mock_config)

    def test_initialization(self):
        """测试 InputHandler 初始化。"""
        assert self.handler.container == self.mock_container
        assert self.handler.config == self.mock_config

    @patch('builtins.input', return_value='test_value')
    def test_get_parameter_input_string(self, mock_input):
        """测试获取字符串参数输入。"""
        result = self.handler.get_parameter_input('test_param', 'str')
        assert result == 'test_value'
        mock_input.assert_called_once_with("请输入 test_param: ")

    @patch('builtins.input', return_value='42')
    def test_get_parameter_input_int(self, mock_input):
        """测试获取整数参数输入。"""
        result = self.handler.get_parameter_input('test_param', 'int')
        assert result == 42
        mock_input.assert_called_once_with("请输入 test_param: ")

    @patch('builtins.input', return_value='3.14')
    def test_get_parameter_input_float(self, mock_input):
        """测试获取浮点数参数输入。"""
        result = self.handler.get_parameter_input('test_param', 'float')
        assert result == 3.14
        mock_input.assert_called_once_with("请输入 test_param: ")

    @patch('builtins.input', return_value='yes')
    def test_get_parameter_input_bool(self, mock_input):
        """测试获取布尔参数输入。"""
        result = self.handler.get_parameter_input('test_param', 'bool')
        assert result is True
        mock_input.assert_called_once_with("请输入 test_param: ")

    @patch('builtins.input', return_value='')
    def test_get_parameter_input_default_value(self, mock_input):
        """测试使用默认值。"""
        result = self.handler.get_parameter_input('test_param', 'str', 'default')
        assert result == 'default'
        mock_input.assert_called_once_with("请输入 test_param (默认: default): ")

    @patch('builtins.input', side_effect=['', 'valid_value'])
    def test_get_parameter_input_empty_then_valid(self, mock_input):
        """测试空输入后输入有效值。"""
        result = self.handler.get_parameter_input('test_param', 'str')
        assert result == 'valid_value'
        assert mock_input.call_count == 2

    @patch('builtins.input', return_value='invalid_int')
    def test_get_parameter_input_invalid_int(self, mock_input):
        """测试无效整数输入。"""
        with patch('builtins.print') as mock_print:
            with pytest.raises(KeyboardInterrupt):
                # 模拟用户中断，因为循环会一直等待有效输入
                mock_input.side_effect = ['invalid_int', KeyboardInterrupt]
                self.handler.get_parameter_input('test_param', 'int')

    def test_get_multiple_parameters(self):
        """测试获取多个参数。"""
        params = {
            'name': {'type': 'str', 'description': 'Enter your name'},
            'age': {'type': 'int', 'default': 25, 'description': 'Enter your age'}
        }

        with patch.object(self.handler, 'get_parameter_input') as mock_get_param:
            mock_get_param.side_effect = ['John', 30]
            result = self.handler.get_multiple_parameters(params)

            assert result == {'name': 'John', 'age': 30}
            assert mock_get_param.call_count == 2

    @patch('builtins.input', return_value='y')
    def test_confirm_action_yes(self, mock_input):
        """测试确认操作 - 是。"""
        result = self.handler.confirm_action("确认操作？")
        assert result is True
        mock_input.assert_called_once_with("确认操作？ (y/n): ")

    @patch('builtins.input', return_value='no')
    def test_confirm_action_no(self, mock_input):
        """测试确认操作 - 否。"""
        result = self.handler.confirm_action("确认操作？")
        assert result is False
        mock_input.assert_called_once_with("确认操作？ (y/n): ")

    @patch('builtins.input', side_effect=['maybe', 'n'])
    def test_confirm_action_invalid_then_no(self, mock_input):
        """测试确认操作 - 无效输入后选择否。"""
        with patch('builtins.print') as mock_print:
            result = self.handler.confirm_action("确认操作？")
            assert result is False
            assert mock_input.call_count == 2
            mock_print.assert_called_once_with("请输入 y 或 n。")
