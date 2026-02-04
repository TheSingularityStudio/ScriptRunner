"""
Unit tests for ScriptObjectExecutor.
"""

import pytest
from unittest.mock import Mock
from src.domain.runtime.script_object_executor import ScriptObjectExecutor
from src.domain.runtime.script_object import ScriptObject


class TestScriptObjectExecutor:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.mock_script_factory = Mock()
        self.mock_core_command_executor = Mock()
        self.executor = ScriptObjectExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_script_factory,
            self.mock_core_command_executor
        )

    def test_initialization(self):
        """测试 ScriptObjectExecutor 初始化。"""
        assert self.executor.parser == self.mock_parser
        assert self.executor.state == self.mock_state_manager
        assert self.executor.condition_evaluator == self.mock_condition_evaluator
        assert self.executor.current_script_object is None

    def test_set_current_script_object(self):
        """测试设置当前脚本对象。"""
        mock_script = ScriptObject()
        self.executor.set_current_script_object(mock_script)
        assert self.executor.current_script_object == mock_script

    def test_execute_commands_empty_list(self):
        """测试执行空命令列表。"""
        messages = self.executor.execute_commands([])
        assert messages == []

    def test_execute_commands_multiple(self):
        """测试执行多个命令。"""
        commands = [
            {'set': 'health = 100'},
            {'set': 'strength = 50'}
        ]
        messages = self.executor.execute_commands(commands)
        assert messages == []
        self.mock_core_command_executor.execute_command.assert_any_call({'set': 'health = 100'})
        self.mock_core_command_executor.execute_command.assert_any_call({'set': 'strength = 50'})

    def test_execute_command_set(self):
        """测试 set 命令。"""
        command = {'set': 'health = 100'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_core_command_executor.execute_command.assert_called_with({'set': 'health = 100'})

    def test_execute_command_set_with_addition(self):
        """测试 set 命令带加法。"""
        command = {'set': 'health += 25'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_core_command_executor.execute_command.assert_called_with({'set': 'health += 25'})

    def test_execute_command_action_without_script_object(self):
        """测试 action 命令无脚本对象。"""
        command = {'action': {'action': 'attack', 'value': '10'}}
        messages = self.executor.execute_command(command)
        assert messages == []

    def test_execute_command_action_with_script_object(self):
        """测试 action 命令有脚本对象。"""
        mock_script = Mock()
        mock_script.execute_action.return_value = [{'set': 'damage=10'}]
        self.executor.set_current_script_object(mock_script)

        command = {'action': {'action': 'attack', 'value': '10'}}
        messages = self.executor.execute_command(command)
        assert messages == []
        mock_script.execute_action.assert_called_with('attack', value='10')
        self.mock_core_command_executor.execute_command.assert_called_with({'set': 'damage=10'})

    def test_execute_command_event_without_script_object(self):
        """测试 event 命令无脚本对象。"""
        command = {'event': 'on_enter'}
        messages = self.executor.execute_command(command)
        assert messages == []

    def test_execute_command_event_with_script_object(self):
        """测试 event 命令有脚本对象。"""
        mock_script = Mock()
        mock_script.trigger_event.return_value = [{'set': 'entered=true'}]
        self.executor.set_current_script_object(mock_script)

        command = {'event': 'on_enter'}
        messages = self.executor.execute_command(command)
        assert messages == []
        mock_script.trigger_event.assert_called_with('on_enter')
        self.mock_core_command_executor.execute_command.assert_called_with({'set': 'entered=true'})

    def test_execute_command_unknown(self):
        """测试未知命令。"""
        command = {'unknown': 'value'}
        messages = self.executor.execute_command(command)
        assert messages == []

    def test_execute_command_empty(self):
        """测试空命令。"""
        command = {}
        messages = self.executor.execute_command(command)
        assert messages == []

    def test_substitute_variables(self):
        """测试变量替换。"""
        self.mock_state_manager.get_variable.return_value = 'world'
        result = self.executor._substitute_variables('Hello {greeting}', None)
        assert result == 'Hello world'

    def test_substitute_variables_with_value(self):
        """测试变量替换带value。"""
        result = self.executor._substitute_variables('Damage {value}', '10')
        assert result == 'Damage 10'

    def test_get_nested_variable(self):
        """测试获取嵌套变量。"""
        self.mock_state_manager.get_variable.return_value = {'health': 100}
        result = self.executor._get_nested_variable('player.health')
        assert result == 100
        self.mock_state_manager.get_variable.assert_called_with('player', {})

    def test_substitute_command(self):
        """测试命令替换。"""
        self.mock_state_manager.get_variable.return_value = 'sword'
        command = {'message': 'You attack with {weapon}'}
        substituted = self.executor._substitute_command(command, None)
        assert substituted == {'message': 'You attack with sword'}
