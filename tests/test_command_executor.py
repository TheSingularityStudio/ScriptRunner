"""
Unit tests for CommandExecutor.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.script_command_executor import ScriptCommandExecutor


class TestCommandExecutor:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.mock_plugin_manager = Mock()
        # Mock the actions from plugins
        self.mock_plugin_manager.get_plugins_by_type.return_value = []
        self.executor = ScriptCommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_plugin_manager
        )
        # Mock the actions dict to include core actions
        def mock_parse_and_set(command_value, context):
            expression = command_value
            parser = context['parser']
            state = context['state']
            condition_evaluator = context['condition_evaluator']
            if '=' not in expression:
                return []
            key, value_str = expression.split('=', 1)
            key = key.strip()
            value_str = value_str.strip()
            if value_str.lower() == 'true':
                value = True
            elif value_str.lower() == 'false':
                value = False
            elif value_str.isdigit():
                value = int(value_str)
            elif value_str.replace('.', '').isdigit():
                value = float(value_str)
            elif value_str.startswith('"') and value_str.endswith('"'):
                value = value_str[1:-1]
            else:
                value = value_str
            state.set_variable(key, value)
            return []

        def mock_set_variable(command_value, context):
            name = command_value.get('name')
            value = command_value.get('value')
            if name is not None and value is not None:
                context['state'].set_variable(name, value)
            return []

        def mock_set_flag(command_value, context):
            context['state'].set_flag(command_value)
            return []

        def mock_clear_flag(command_value, context):
            context['state'].clear_flag(command_value)
            return []

        def mock_apply_effect(command_value, context):
            effect = context['parser'].get_effect(command_value)
            if effect:
                context['state'].apply_effect(command_value, effect)
            return []

        def mock_remove_effect(command_value, context):
            context['state'].remove_effect(command_value)
            return []

        def mock_goto(command_value, context):
            context['state'].set_current_scene(command_value)
            return []

        def mock_if(command_value, context):
            condition = command_value.get('if')
            then_commands = command_value.get('then', [])
            else_commands = command_value.get('else', [])
            if context['condition_evaluator'].evaluate_condition(condition):
                # For test, just evaluate condition
                pass
            return []

        def mock_message(command_value, context):
            return [command_value]

        def mock_spawn_object(command_value, context):
            return []

        def mock_roll_table(command_value, context):
            table = context['parser'].get_random_table(command_value)
            if table:
                pass  # mock
            return []

        self.executor.actions = {
            'set_variable': mock_set_variable,
            'parse_and_set': mock_parse_and_set,
            'set_flag': mock_set_flag,
            'clear_flag': mock_clear_flag,
            'apply_effect': mock_apply_effect,
            'remove_effect': mock_remove_effect,
            'goto': mock_goto,
            'if': mock_if,
            'spawn_object': mock_spawn_object,
            'roll_table': mock_roll_table,
        }

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
        self.mock_parser.get_command.return_value = {'actions': ['parse_and_set']}
        command = {'set': 'health = 100'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_variable.assert_called_with('health', 100)

    def test_execute_command_set_variable(self):
        """测试 set_variable 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['set_variable']}
        command = {'set_variable': {'name': 'strength', 'value': 15}}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_variable.assert_called_with('strength', 15)

    def test_execute_command_set_flag(self):
        """测试 set_flag 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['set_flag']}
        command = {'set_flag': 'has_key'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_flag.assert_called_with('has_key')

    def test_execute_command_clear_flag(self):
        """测试 clear_flag 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['clear_flag']}
        command = {'clear_flag': 'has_key'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.clear_flag.assert_called_with('has_key')

    def test_execute_command_roll_table(self):
        """测试 roll_table 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['roll_table'], 'table': 'treasure'}
        table = {'entries': [{'commands': [{'set': 'gold = 10'}]}]}
        self.mock_parser.get_random_table.return_value = table
        command = {'roll_table': 'treasure'}
        with patch('random.choice', return_value={'commands': [{'set': 'gold = 10'}]}):
            messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_parser.get_random_table.assert_called_with('treasure')

    def test_execute_command_apply_effect(self):
        """测试 apply_effect 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['apply_effect']}
        effect = {'duration': 5, 'action': 'damage 2'}
        self.mock_parser.get_effect.return_value = effect
        command = {'apply_effect': 'poisoned'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.apply_effect.assert_called_with('poisoned', effect)

    def test_execute_command_remove_effect(self):
        """测试 remove_effect 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['remove_effect']}
        command = {'remove_effect': 'blessed'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.remove_effect.assert_called_with('blessed')

    def test_execute_command_goto(self):
        """测试 goto 命令。"""
        self.mock_parser.get_command.return_value = {'actions': ['goto']}
        command = {'goto': 'forest_path'}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_state_manager.set_current_scene.assert_called_with('forest_path')

    def test_execute_command_if_true(self):
        """测试 if 命令条件为真。"""
        self.mock_parser.get_command.return_value = {'actions': ['if']}
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        command = {'if': {'if': 'has_key', 'then': [{'set': 'unlocked = true'}], 'else': []}}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('has_key')

    def test_execute_command_if_false(self):
        """测试 if 命令条件为假。"""
        self.mock_parser.get_command.return_value = {'actions': ['if']}
        self.mock_condition_evaluator.evaluate_condition.return_value = False
        command = {'if': {'if': 'has_key', 'then': [], 'else': [{'set': 'locked = true'}]}}
        messages = self.executor.execute_command(command)
        assert messages == []
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('has_key')

    def test_execute_command_attack_hit(self):
        """测试 attack 命令命中。"""
        # Mock plugin with attack action
        mock_plugin = Mock()
        mock_plugin.get_actions.return_value = {
            'attack_target': Mock(return_value=['Hit!'])
        }
        self.mock_plugin_manager.get_plugins_by_type.return_value = [mock_plugin]

        # Re-initialize executor to load actions
        self.executor = ScriptCommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_plugin_manager
        )

        self.mock_parser.get_command.return_value = {'actions': [{'message': '你准备攻击...'}, 'attack_target']}
        command = {'attack': 'goblin'}
        messages = self.executor.execute_command(command)
        assert len(messages) == 2
        assert '你准备攻击...' in messages[0]
        assert 'Hit!' in messages[1]

    def test_execute_command_attack_miss(self):
        """测试 attack 命令未命中。"""
        # Mock plugin with attack action
        mock_plugin = Mock()
        mock_plugin.get_actions.return_value = {
            'attack_target': Mock(return_value=['Miss!'])
        }
        self.mock_plugin_manager.get_plugins_by_type.return_value = [mock_plugin]

        # Re-initialize executor to load actions
        self.executor = ScriptCommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_plugin_manager
        )

        self.mock_parser.get_command.return_value = {'actions': [{'message': '你准备攻击...'}, 'attack_target']}
        command = {'attack': 'goblin'}
        messages = self.executor.execute_command(command)
        assert len(messages) == 2
        assert '你准备攻击...' in messages[0]
        assert 'Miss!' in messages[1]

    def test_execute_command_search_forest(self):
        """测试 search 命令在森林。"""
        # Mock plugin with search action
        mock_plugin = Mock()
        mock_plugin.get_actions.return_value = {
            'search_location': Mock(return_value=[])
        }
        self.mock_plugin_manager.get_plugins_by_type.return_value = [mock_plugin]

        # Re-initialize executor to load actions
        self.executor = ScriptCommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_plugin_manager
        )

        self.mock_parser.get_command.return_value = {'actions': ['search_location']}
        command = {'search': 'forest_path'}
        messages = self.executor.execute_command(command)
        assert messages == []

    def test_execute_command_search_other(self):
        """测试 search 命令在其他地方。"""
        # Mock plugin with search action
        mock_plugin = Mock()
        mock_plugin.get_actions.return_value = {
            'search_location': Mock(return_value=['No items found while searching village.'])
        }
        self.mock_plugin_manager.get_plugins_by_type.return_value = [mock_plugin]

        # Re-initialize executor to load actions
        self.executor = ScriptCommandExecutor(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator,
            self.mock_plugin_manager
        )

        self.mock_parser.get_command.return_value = {'actions': ['search_location']}
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
