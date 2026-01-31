"""
Unit tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.command_executor import CommandExecutor


class TestCommandExecutor:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.executor = CommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator
        )

    def test_initialization(self):
        """测试 CommandExecutor 初始化。"""
        assert self.executor.parser == self.mock_parser
        assert self.executor.state == self.mock_state_manager
        assert self.executor.condition_evaluator == self.mock_condition_evaluator

    def test_execute_commands_empty_list(self):
        """测试执行空命令列表。"""
        messages = self.executor.execute_commands([])
        assert messages == []

    def test_execute_commands_multiple(self):
        """测试执行多个命令。"""
        commands = [
            {'set': 'health = 100'},
            {'set_flag': 'visited_forest'}
        ]
        messages = self.executor.execute_commands(commands)
        assert messages == []

    def test_execute_command_set(self):
        """测试 set 命令。"""
        command = {'set': 'health = 100'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_variable.assert_called_with('health', 100)

    def test_execute_command_set_variable(self):
        """测试 set_variable 命令。"""
        command = {'set_variable': {'name': 'strength', 'value': 15}}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_variable.assert_called_with('strength', 15)

    def test_execute_command_set_flag(self):
        """测试 set_flag 命令。"""
        command = {'set_flag': 'has_key'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_flag.assert_called_with('has_key')

    def test_execute_command_clear_flag(self):
        """测试 clear_flag 命令。"""
        command = {'clear_flag': 'has_key'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.clear_flag.assert_called_with('has_key')

    def test_execute_command_roll_table(self):
        """测试 roll_table 命令。"""
        table = {'entries': [{'commands': [{'set': 'gold = 10'}]}]}
        self.mock_parser.get_random_table.return_value = table
        command = {'roll_table': 'treasure'}
        with patch('random.choice', return_value={'commands': [{'set': 'gold = 10'}]}):
            messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_parser.get_random_table.assert_called_with('treasure')

    def test_execute_command_apply_effect(self):
        """测试 apply_effect 命令。"""
        effect = {'duration': 5, 'action': 'damage 2'}
        self.mock_parser.get_effect.return_value = effect
        command = {'apply_effect': 'poisoned'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.apply_effect.assert_called_with('poisoned', effect)

    def test_execute_command_remove_effect(self):
        """测试 remove_effect 命令。"""
        command = {'remove_effect': 'blessed'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.remove_effect.assert_called_with('blessed')

    def test_execute_command_goto(self):
        """测试 goto 命令。"""
        command = {'goto': 'forest_path'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_current_scene.assert_called_with('forest_path')

    def test_execute_command_if_true(self):
        """测试 if 命令条件为真。"""
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        command = {'if': 'has_key', 'then': [{'set': 'unlocked = true'}], 'else': []}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('has_key')

    def test_execute_command_if_false(self):
        """测试 if 命令条件为假。"""
        self.mock_condition_evaluator.evaluate_condition.return_value = False
        command = {'if': 'has_key', 'then': [], 'else': [{'set': 'locked = true'}]}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('has_key')

    @patch('random.random', return_value=0.3)
    def test_execute_command_attack_hit(self, mock_random):
        """测试 attack 命令命中。"""
        target_obj = {
            'attributes': {'defense': 5},
            'behaviors': {'attack': {'hit_chance': '0.5', 'damage': '10', 'success': 'Hit!'}},
            'states': [{'name': 'health', 'value': 50}]
        }
        self.mock_parser.get_object.return_value = target_obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=0: {'strength': 10, 'agility': 12}.get(key, default)
        command = {'attack': 'goblin'}
        messages = self.executor.execute_command(command)
        assert len(messages) > 0
        assert 'Hit!' in messages[0]

    @patch('random.random', return_value=0.7)
    def test_execute_command_attack_miss(self, mock_random):
        """测试 attack 命令未命中。"""
        target_obj = {
            'attributes': {'defense': 5},
            'behaviors': {'attack': {'hit_chance': '0.5', 'failure': 'Miss!'}},
            'states': [{'name': 'health', 'value': 50}]
        }
        self.mock_parser.get_object.return_value = target_obj
        command = {'attack': 'goblin'}
        messages = self.executor.execute_command(command)
        assert len(messages) > 0
        assert 'Miss!' in messages[0]

    def test_execute_command_search_forest(self):
        """测试 search 命令在森林。"""
        table = {'entries': [{'commands': [{'set': 'gold = 5'}]}]}
        self.mock_parser.get_random_table.return_value = table
        command = {'search': 'forest_path'}
        with patch('random.choice', return_value={'commands': [{'set': 'gold = 5'}]}):
            messages = self.executor.execute_command(command)
        assert messages == []

    def test_execute_command_search_other(self):
        """测试 search 命令在其他地方。"""
        command = {'search': 'village'}
        messages = self.executor.execute_command(command)
        assert len(messages) == 1
        assert 'No items found' in messages[0]

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
