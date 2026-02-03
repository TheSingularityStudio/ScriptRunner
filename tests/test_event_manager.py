"""
Unit tests for EventManager.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.event_manager import EventManager


class TestEventManager:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_command_executor = Mock()
        self.mock_condition_evaluator = Mock()
        self.manager = EventManager(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_command_executor,
            self.mock_condition_evaluator
        )

    def test_initialization(self):
        """测试 EventManager 初始化。"""
        self.mock_parser.get_events.return_value = None  # Mock to return None for events
        manager = EventManager(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_command_executor,
            self.mock_condition_evaluator
        )
        assert manager.parser == self.mock_parser
        assert manager.state == self.mock_state_manager
        assert manager.command_executor == self.mock_command_executor
        assert manager.condition_evaluator == self.mock_condition_evaluator
        assert manager.scheduled_events == []
        assert manager.reactive_events == []

    def test_load_events(self):
        """测试加载事件。"""
        events = {
            'scheduled_events': [{'trigger': 'time > 100', 'action': 'spawn_werewolf'}],
            'reactive_events': [{'trigger': 'player.action = take', 'conditions': ['has_sword']}]
        }
        self.mock_parser.get_events.return_value = events
        self.manager._load_events()
        assert len(self.manager.scheduled_events) == 1
        assert len(self.manager.reactive_events) == 1

    def test_check_scheduled_events_time_trigger(self):
        """测试检查定时事件时间触发。"""
        self.manager.scheduled_events = [{'trigger': 'time > 100', 'action': 'spawn_werewolf', 'chance': 1.0}]
        self.mock_state_manager.get_variable.return_value = 150
        with patch('random.random', return_value=0.5):
            self.manager.check_scheduled_events()
        self.mock_state_manager.set_variable.assert_called_with('werewolf_spawned', True)

    def test_check_scheduled_events_no_trigger(self):
        """测试检查定时事件无触发。"""
        self.manager.scheduled_events = [{'trigger': 'time > 200', 'action': 'spawn_werewolf'}]
        self.mock_state_manager.get_variable.return_value = 150
        self.manager.check_scheduled_events()
        self.mock_state_manager.set_variable.assert_not_called()

    def test_check_reactive_events_player_action(self):
        """测试检查反应事件玩家动作。"""
        self.manager.reactive_events = [{
            'trigger': 'player.action = take',
            'conditions': ['has_sword'],
            'actions': ['log:Item taken']
        }]
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        self.manager.check_reactive_events('player_action', action='take')
        # Should have logged the action

    def test_check_reactive_events_no_match(self):
        """测试检查反应事件无匹配。"""
        self.manager.reactive_events = [{
            'trigger': 'player.action = drop',
            'conditions': ['has_sword'],
            'actions': ['log:Item dropped']
        }]
        self.manager.check_reactive_events('player_action', action='take')
        # No actions should be executed

    def test_check_time_trigger_greater(self):
        """测试时间触发大于条件。"""
        assert self.manager._check_time_trigger('time > 100', 150) is True
        assert self.manager._check_time_trigger('time > 100', 50) is False

    def test_check_time_trigger_greater_equal(self):
        """测试时间触发大于等于条件。"""
        assert self.manager._check_time_trigger('time >= 100', 100) is True
        assert self.manager._check_time_trigger('time >= 100', 50) is False

    def test_check_time_trigger_less(self):
        """测试时间触发小于条件。"""
        assert self.manager._check_time_trigger('time < 100', 50) is True
        assert self.manager._check_time_trigger('time < 100', 150) is False

    def test_check_time_trigger_less_equal(self):
        """测试时间触发小于等于条件。"""
        assert self.manager._check_time_trigger('time <= 100', 100) is True
        assert self.manager._check_time_trigger('time <= 100', 150) is False

    def test_matches_trigger_player_action(self):
        """测试匹配触发器玩家动作。"""
        assert self.manager._matches_trigger('player.action = take', 'player_action', {'action': 'take'}) is True
        assert self.manager._matches_trigger('player.action = drop', 'player_action', {'action': 'take'}) is False

    def test_matches_trigger_world_property(self):
        """测试匹配触发器世界属性。"""
        self.mock_state_manager.get_variable.return_value = 'night'
        assert self.manager._matches_trigger('world.time = night', 'world_change', {}) is True

    def test_check_conditions_all_true(self):
        """测试检查条件全部为真。"""
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        assert self.manager._check_conditions(['cond1', 'cond2']) is True

    def test_check_conditions_some_false(self):
        """测试检查条件部分为假。"""
        self.mock_condition_evaluator.evaluate_condition.side_effect = [True, False]
        assert self.manager._check_conditions(['cond1', 'cond2']) is False

    def test_execute_event_action_spawn_werewolf(self):
        """测试执行事件动作生成狼人。"""
        self.manager._execute_event_action('spawn_werewolf', {})
        self.mock_state_manager.set_variable.assert_called_with('werewolf_spawned', True)

    def test_execute_event_action_spawn_object(self):
        """测试执行事件动作生成对象。"""
        self.mock_state_manager.get_current_scene.return_value = 'forest'
        self.manager._execute_event_action('spawn_object:goblin', {})

    def test_execute_event_action_broadcast(self):
        """测试执行事件动作广播。"""
        self.manager._execute_event_action('broadcast:Hello world', {})

    def test_execute_actions_set(self):
        """测试执行动作设置变量。"""
        self.manager._execute_actions(['set:health = 100'])
        self.mock_command_executor.execute_command.assert_called_with({'set': 'health = 100'})

    def test_execute_actions_add_flag(self):
        """测试执行动作添加标志。"""
        self.manager._execute_actions(['add_flag:victory'])
        self.mock_state_manager.set_flag.assert_called_with('victory')

    def test_update_game_time(self):
        """测试更新游戏时间。"""
        self.manager.scheduled_events = []  # Ensure it's a list, not a Mock
        self.mock_state_manager.get_variable.return_value = 100
        self.manager.update_game_time(10)
        self.mock_state_manager.set_variable.assert_called_with('game_time', 110)

    def test_trigger_player_action(self):
        """测试触发玩家动作。"""
        with patch.object(self.manager, 'check_reactive_events') as mock_check:
            self.manager.trigger_player_action('take', target='sword')
            mock_check.assert_called_with('player_action', action='take', target='sword')

    def test_enable_event(self):
        """测试启用事件。"""
        self.manager.scheduled_events = [{'id': 'test_event', 'enabled': False, 'trigger': 'time > 100', 'action': 'spawn_werewolf'}]
        result = self.manager.enable_event('test_event')
        assert result is True
        assert self.manager.scheduled_events[0]['enabled'] is True

    def test_disable_event(self):
        """测试禁用事件。"""
        self.manager.scheduled_events = [{'id': 'test_event', 'enabled': True, 'trigger': 'time > 100', 'action': 'spawn_werewolf'}]
        result = self.manager.disable_event('test_event')
        assert result is True
        assert self.manager.scheduled_events[0]['enabled'] is False

    def test_remove_event(self):
        """测试移除事件。"""
        self.manager.scheduled_events = [{'id': 'test_event', 'enabled': True, 'trigger': 'time > 100', 'action': 'spawn_werewolf'}]
        result = self.manager.remove_event('test_event')
        assert result is True
        assert len(self.manager.scheduled_events) == 0

    def test_trigger_scene_change(self):
        """测试触发场景变更。"""
        with patch.object(self.manager, 'check_reactive_events') as mock_check:
            self.manager.trigger_scene_change('forest', 'castle')
            mock_check.assert_called_with('scene_change', old_scene='forest', new_scene='castle')

    def test_trigger_variable_change(self):
        """测试触发变量变更。"""
        with patch.object(self.manager, 'check_reactive_events') as mock_check:
            self.manager.trigger_variable_change('health', 100, 80)
            mock_check.assert_called_with('variable_change', variable='health', old_value=100, new_value=80)

    def test_register_action_handler(self):
        """测试注册动作处理器。"""
        def custom_handler(params):
            pass

        self.manager.register_action_handler('custom_action', custom_handler)
        assert 'custom_action' in self.manager.action_handlers
        assert self.manager.action_handlers['custom_action'] == custom_handler

    def test_get_event_history(self):
        """测试获取事件历史。"""
        # 记录一些历史
        self.manager._record_event_history('test', 'category', {'key': 'value'})
        history = self.manager.get_event_history()
        assert len(history) == 1
        assert history[0]['type'] == 'test'
        assert history[0]['category'] == 'category'

    def test_validate_events(self):
        """测试事件验证。"""
        self.manager.scheduled_events = [
            {'id': 'valid_event', 'trigger': 'time > 100', 'action': 'spawn_werewolf', 'priority': 'high'},
            {'id': 'invalid_event', 'trigger': '', 'action': 'spawn_werewolf'},  # 缺少trigger
            {'id': 'invalid_priority', 'trigger': 'time > 100', 'action': 'spawn_werewolf', 'priority': 'invalid'}
        ]
        errors = self.manager.validate_events()
        assert len(errors) >= 2  # 应该至少有两个错误

    def test_event_prioritization(self):
        """测试事件优先级排序。"""
        self.manager.scheduled_events = [
            {'id': 'low', 'priority': 'low', 'trigger': 'time > 100', 'action': 'log'},
            {'id': 'high', 'priority': 'high', 'trigger': 'time > 100', 'action': 'log'},
            {'id': 'medium', 'priority': 'medium', 'trigger': 'time > 100', 'action': 'log'}
        ]
        self.manager._sort_events_by_priority()
        assert self.manager.scheduled_events[0]['priority'] == 'high'
        assert self.manager.scheduled_events[1]['priority'] == 'medium'
        assert self.manager.scheduled_events[2]['priority'] == 'low'

    def test_extended_triggers(self):
        """测试扩展触发器。"""
        # 测试场景变更触发器
        assert self.manager._matches_trigger('scene.change', 'scene_change', {}) is True

        # 测试变量变更触发器
        assert self.manager._matches_trigger('variable.health = 50', 'variable_change', {'variable': 'health', 'new_value': 50}) is True

        # 测试自定义触发器
        assert self.manager._matches_trigger('custom.battle_start', 'custom', {'custom_type': 'battle_start'}) is True

    def test_action_handler_execution(self):
        """测试动作处理器执行。"""
        # 测试已注册的处理器
        self.manager._execute_single_action('spawn_werewolf:test')
        self.mock_state_manager.set_variable.assert_called_with('werewolf_spawned', True)

        # 测试未注册的处理器（应该回退到通用执行器）
        self.manager._execute_single_action('unknown_action:test')
        self.mock_command_executor.execute_command.assert_called_with({'unknown_action': 'test'})
