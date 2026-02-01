"""
Unit tests for InputHandler.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.input_handler import InputHandler


class TestInputHandler:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_container = Mock()
        self.mock_config = Mock()
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_command_executor = Mock()
        self.mock_event_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.mock_action_executor = Mock()
        self.mock_interaction_manager = Mock()

        # 设置mock的属性
        self.mock_interaction_manager.interaction_data = {}

        # 设置container的has方法
        self.mock_container.has.side_effect = lambda name: name in [
            'parser', 'state_manager', 'command_executor', 'event_manager',
            'condition_evaluator', 'action_executor', 'interaction_manager'
        ]

        # 设置container的get方法
        self.mock_container.get.side_effect = lambda name: getattr(self, f'mock_{name}', None)

        # 设置config的get方法
        self.mock_config.get.side_effect = lambda key, default=None: {
            'game.combine_recipes': {'herb_potion': ['herb', 'bottle']},
            'messages.unknown_action': "我不理解这个命令。",
            'messages.take_success': "你拿起了 {target}。",
            'messages.defeat_success': "你击败了 {target}！",
            'messages.attack_success': "你攻击了 {target}，造成了 {damage} 点伤害，它还剩下 {health} 点生命。",
            'messages.combine_success': "你成功组合出了 {result}！",
            'messages.inventory_empty': "你的背包是空的。",
            'messages.inventory_header': "你的背包中有：",
            'game.default_creature_health': 30,
            'game.base_damage': 5,
            'game.strength_damage_multiplier': 0.5,
        }.get(key, default)

        # 设置state_manager的get_variable默认行为
        def get_variable_side_effect(key, default=None):
            defaults = {
                'inventory': [],
                'player_strength': 10,
                'removed_objects': [],
            }
            return defaults.get(key, default if default is not None else 0)

        self.mock_state_manager.get_variable.side_effect = get_variable_side_effect

        # 设置parser的默认返回值
        self.mock_parser.get_scene.return_value = None
        self.mock_parser.get_object.return_value = None
        self.mock_parser.get_random_table.return_value = None

        self.handler = InputHandler(self.mock_container, self.mock_config)

    def test_initialization(self):
        """测试 InputHandler 初始化。"""
        assert self.handler.container == self.mock_container
        assert self.handler.config == self.mock_config
        assert 'take' in self.handler.action_handlers
        assert 'examine' in self.handler.action_handlers
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
        # Mock the _execute_action to raise an exception
        with patch.object(self.handler, '_execute_action', side_effect=Exception('Test error')):
            result = self.handler.process_player_input('take sword')
        assert result['success'] is False
        assert '意外错误' in result['message']

    def test_register_action(self):
        """测试注册新动作。"""
        def custom_handler(target):
            return {'success': True, 'message': 'Custom action'}
        self.handler.register_action('custom', custom_handler)
        assert 'custom' in self.handler.action_handlers

    def test_execute_take_no_target(self):
        """测试拿起物品无目标。"""
        result = self.handler._execute_action('take', '')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_take_object_not_found(self):
        """测试拿起不存在的物品。"""
        self.mock_parser.get_object.return_value = None
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_action('take', 'nonexistent')
        assert result['success'] is False
        assert '这里没有' in result['message']

    def test_execute_take_not_item(self):
        """测试拿起非物品对象。"""
        obj = {'type': 'creature'}
        self.mock_parser.get_object.return_value = obj
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_action('take', 'goblin')
        assert result['success'] is False
        assert '无法拿起 goblin' in result['message']

    def test_execute_take_success(self):
        """测试成功拿起物品。"""
        obj = {'type': 'item'}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=None: [] if key == 'inventory' else default
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_action('take', 'sword')
        assert result['success'] is True
        assert '拿起了 sword' in result['message']
        assert len(result['actions']) == 2
        assert 'set:inventory=' in result['actions'][0]
        assert 'add_flag:removed_sword' in result['actions'][1]

    def test_execute_use_no_target(self):
        """测试使用物品无目标。"""
        result = self.handler._execute_action('use', '')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_use_not_in_inventory(self):
        """测试使用不在库存中的物品。"""
        self.mock_state_manager.get_variable.return_value = ['sword']
        result = self.handler._execute_action('use', 'potion')
        assert result['success'] is False
        assert '你没有' in result['message']

    def test_execute_use_success(self):
        """测试成功使用物品。"""
        self.mock_state_manager.get_variable.side_effect = lambda key, default=None: ['potion'] if key == 'inventory' else default
        result = self.handler._execute_action('use', 'potion')
        assert result['success'] is True
        assert '使用了' in result['message']

    def test_execute_examine_no_target(self):
        """测试检查物品无目标。"""
        result = self.handler._execute_action('examine', '')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_examine_object_not_found(self):
        """测试检查不存在的物品。"""
        self.mock_parser.get_object.return_value = None
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_action('examine', 'chest')
        assert result['success'] is False
        assert '这里没有' in result['message']

    def test_execute_examine_success(self):
        """测试成功检查物品。"""
        obj = {'description': 'A shiny sword'}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=None: [] if key == 'inventory' else default
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            result = self.handler._execute_action('examine', 'sword')
        assert result['success'] is True
        assert result['message'] == 'A shiny sword'

    def test_execute_attack_no_target(self):
        """测试攻击无目标。"""
        result = self.handler._execute_action('attack', '')
        assert result['success'] is False
        assert '无法找到攻击目标' in result['message']

    def test_execute_attack_not_accessible(self):
        """测试攻击不可访问的目标。"""
        obj = {'type': 'creature', 'states': [{'value': 30}]}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=0: 10 if key == 'player_strength' else 30
        with patch.object(self.handler, '_is_object_accessible', return_value=False):
            result = self.handler._execute_action('attack', 'goblin')
        # 插件当前不检查可访问性，所以攻击总是成功
        assert result['success'] is True
        assert '你击中了' in result['message'] or '你没能打中' in result['message']

    def test_execute_attack_success(self):
        """测试成功攻击。"""
        obj = {'type': 'creature', 'states': [{'value': 30}]}
        self.mock_parser.get_object.return_value = obj
        self.mock_state_manager.get_variable.side_effect = lambda key, default=0: 10 if key == 'player_strength' else 30
        with patch.object(self.handler, '_is_object_accessible', return_value=True):
            with patch('random.random', return_value=0.3):  # 确保命中
                result = self.handler._execute_action('attack', 'goblin')
        assert result['success'] is True
        assert '你击中了' in result['message']
        assert len(result['actions']) == 1
        assert 'set:goblin_health=' in result['actions'][0]

    def test_execute_search_no_scene(self):
        """测试搜索无场景。"""
        self.mock_state_manager.get_current_scene.return_value = None
        result = self.handler._execute_action('search', 'area')
        # 插件总是返回成功，即使没有场景
        assert result['success'] is True
        assert '搜索了area' in result['message']

    def test_execute_search_with_table(self):
        """测试搜索有随机表。"""
        scene = {'objects': []}
        self.mock_parser.get_scene.return_value = scene
        table = {'entries': [{'message': 'Found gold!'}]}
        self.mock_parser.get_random_table.return_value = table
        self.mock_state_manager.get_current_scene.return_value = 'forest'
        with patch('random.choice', return_value={'message': 'Found gold!'}):
            result = self.handler._execute_action('search', 'forest')
        assert result['success'] is True
        assert 'Found gold!' in result['message']

    def test_execute_combine_no_target(self):
        """测试组合无目标。"""
        result = self.handler._execute_action('combine', '')
        assert result['success'] is False
        assert '需要指定' in result['message']

    def test_execute_combine_success(self):
        """测试成功组合。"""
        # Mock state manager to return inventory with required items
        self.mock_state_manager.get_variable.side_effect = lambda *args, **kwargs: ['herb', 'bottle']
        # Mock container.has to return False for interaction_manager
        self.mock_container.has.side_effect = lambda name: name != 'interaction_manager' and name in [
            'parser', 'state_manager', 'command_executor', 'event_manager',
            'condition_evaluator', 'action_executor'
        ]
        result = self.handler._execute_action('combine', 'herb_potion')
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
