"""
Unit tests for InputHandler.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.input_handler import InputHandler


class TestInputHandler:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_command_executor = Mock()
        self.mock_event_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.mock_action_executor = Mock()
        self.handler = InputHandler(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_command_executor,
            self.mock_event_manager,
            self.mock_condition_evaluator,
            action_executor=self.mock_action_executor
        )

    def test_initialization(self):
        """测试 InputHandler 初始化。"""
        assert self.handler.parser == self.mock_parser
        assert self.handler.state == self.mock_state_manager
        assert self.handler.command_executor == self.mock_command_executor
        assert self.handler.event_manager == self.mock_event_manager
        assert self.handler.condition_evaluator == self.mock_condition_evaluator
        assert 'take' in self.handler.action_handlers
        assert 'use' in self.handler.action_handlers

    def test_process_player_input_unknown_action(self):
        """测试处理未知动作的输入。"""
        self.mock_parser.parse_player_command.return_value = {'action': 'unknown'}
        result = self.handler.process_player_input('invalid command')
        assert result['success'] is False
        assert '我不理解' in result['message']
        assert result['action'] == 'unknown'

    def test_process_player_input_known_action(self):
        """测试处理已知动作的输入。"""
        self.mock_parser.parse_player_command.return_value = {'action': 'take', 'target': 'sword'}
        # Mock the action handler to avoid calling the real method
        mock_execute = Mock(return_value={'success': True, 'message': 'Taken'})
        self.handler.action_handlers['take'] = mock_execute
        result = self.handler.process_player_input('take sword')
        assert result['success'] is True
        assert result['action'] == 'take'
        assert result['target'] == 'sword'
        self.mock_event_manager.trigger_player_action.assert_called_with('take', target='sword')
        mock_execute.assert_called_once()

    def test_process_player_input_exception(self):
        """测试处理输入时发生异常。"""
        self.mock_parser.parse_player_command.return_value = {'action': 'take', 'target': 'sword'}
        with patch.object(self.handler, '_execute_take', side_effect=Exception('Test error')):
            result = self.handler.process_player_input('take sword')
        assert result['success'] is False
        assert '出错' in result['message']

    def test_register_action(self):
        """测试注册新动作。"""
        def custom_handler(target):
            return {'success': True, 'message': 'Custom action'}
        self.handler.register_action('custom', custom_handler)
        assert 'custom' in self.handler.action_handlers

    def test_execute_take_no_target(self):
        """测试拿起物品无目标。"""
        result = self.handler._execute_take('')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_take_object_not_found(self):
        """测试拿起不存在的物品。"""
        self.mock_parser.get_object.return_value = None
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_take('nonexistent')
        assert result['success'] is False
        assert '这里没有' in result['message']

    def test_execute_take_not_item(self):
        """测试拿起非物品对象。"""
        obj = {'type': 'creature'}
        self.mock_parser.get_object.return_value = obj
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_take('goblin')
        assert result['success'] is False
        assert '无法拿起' in result['message']

    def test_execute_take_success(self):
        """测试成功拿起物品。"""
        obj = {'type': 'item'}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.return_value = []
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            with patch.object(self.handler, '_remove_object_from_scene'):
                result = self.handler._execute_take('sword')
        assert result['success'] is True
        assert '拿起了' in result['message']
        assert len(result['actions']) == 2
        assert 'set:inventory=' in result['actions'][0]
        assert 'add_flag:removed_sword' in result['actions'][1]

    def test_execute_use_no_target(self):
        """测试使用物品无目标。"""
        result = self.handler._execute_use('')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_use_not_in_inventory(self):
        """测试使用不在库存中的物品。"""
        self.mock_state_manager.get_variable.return_value = ['sword']
        result = self.handler._execute_use('potion')
        assert result['success'] is False
        assert '你没有' in result['message']

    def test_execute_use_success(self):
        """测试成功使用物品。"""
        self.mock_state_manager.get_variable.return_value = ['potion']
        result = self.handler._execute_use('potion')
        assert result['success'] is True
        assert '使用了' in result['message']

    def test_execute_examine_no_target(self):
        """测试检查物品无目标。"""
        result = self.handler._execute_examine('')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_examine_object_not_found(self):
        """测试检查不存在的物品。"""
        self.mock_parser.get_object.return_value = None
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_examine('chest')
        assert result['success'] is False
        assert '这里没有' in result['message']

    def test_execute_examine_success(self):
        """测试成功检查物品。"""
        obj = {'description': 'A shiny sword'}
        self.mock_parser.get_object.return_value = obj
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_examine('sword')
        assert result['success'] is True
        assert result['message'] == 'A shiny sword'

    def test_execute_attack_no_target(self):
        """测试攻击无目标。"""
        result = self.handler._execute_attack('')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_attack_not_accessible(self):
        """测试攻击不可访问的目标。"""
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_attack('goblin')
        assert result['success'] is False
        assert '这里没有' in result['message']

    def test_execute_attack_success(self):
        """测试成功攻击。"""
        obj = {'type': 'creature', 'states': [{'value': 30}]}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=0: 10 if key == 'player_strength' else 30
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_attack('goblin')
        assert result['success'] is True
        assert '攻击了' in result['message']
        assert len(result['actions']) == 1
        assert 'set:goblin_health=' in result['actions'][0]

    def test_execute_search_no_scene(self):
        """测试搜索无场景。"""
        self.mock_state_manager.get_current_scene.return_value = None
        result = self.handler._execute_search('area')
        assert result['success'] is False
        assert '无法确定' in result['message']

    def test_execute_search_with_table(self):
        """测试搜索有随机表。"""
        scene = {'objects': []}
        self.mock_parser.get_scene.return_value = scene
        table = {'entries': [{'message': 'Found gold!'}]}
        self.mock_parser.get_random_table.return_value = table
        self.mock_state_manager.get_current_scene.return_value = 'forest'
        with patch('random.choice', return_value={'message': 'Found gold!'}):
            result = self.handler._execute_search('forest')
        assert result['success'] is True
        assert 'Found gold!' in result['message']

    def test_execute_combine_no_target(self):
        """测试组合无目标。"""
        result = self.handler._execute_combine('')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_combine_success(self):
        """测试成功组合。"""
        self.mock_state_manager.get_variable.return_value = ['herb', 'bottle']
        result = self.handler._execute_combine('herb_potion')
        assert result['success'] is True
        assert '成功组合' in result['message']
        assert len(result['actions']) == 1
        assert 'set:inventory=' in result['actions'][0]

    def test_is_object_accessible_no_scene(self):
        """测试对象可访问性无场景。"""
        self.mock_state_manager.get_current_scene.return_value = None
        assert not self.handler._is_object_accessible('sword')

    def test_is_object_accessible_in_scene(self):
        """测试对象在场景中可访问。"""
        scene = {'objects': [{'ref': 'sword'}]}
        self.mock_parser.get_scene.return_value = scene
        self.mock_state_manager.get_current_scene.return_value = 'village'
        assert self.handler._is_object_accessible('sword')

    def test_remove_object_from_scene(self):
        """测试从场景中移除对象。"""
        self.mock_state_manager.get_current_scene.return_value = 'village'
        self.mock_state_manager.get_variable.return_value = []
        self.handler._remove_object_from_scene('sword')
        self.mock_state_manager.set_variable.assert_called_with('removed_objects', ['sword'])
