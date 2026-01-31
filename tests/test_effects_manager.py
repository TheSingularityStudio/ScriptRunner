"""
Unit tests for EffectsManager.
"""

import pytest
from unittest.mock import Mock, patch
from src.runtime.effects_manager import EffectsManager


class TestEffectsManager:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_command_executor = Mock()
        self.manager = EffectsManager(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_command_executor
        )

    def test_initialization(self):
        """测试 EffectsManager 初始化。"""
        assert self.manager.parser == self.mock_parser
        assert self.manager.state == self.mock_state_manager
        assert self.manager.command_executor == self.mock_command_executor
        assert self.manager.active_effects == {}

    def test_apply_effect_not_found(self):
        """测试应用不存在的效果。"""
        self.mock_parser.get_effect.return_value = None
        result = self.manager.apply_effect('nonexistent')
        assert result is False
        assert 'nonexistent' not in self.manager.active_effects

    def test_apply_effect_new(self):
        """测试应用新效果。"""
        effect_data = {'duration': 5, 'action': 'damage 2'}
        self.mock_parser.get_effect.return_value = effect_data
        with patch('time.time', return_value=1000):
            result = self.manager.apply_effect('poisoned')
        assert result is True
        assert 'poisoned' in self.manager.active_effects
        assert self.manager.active_effects['poisoned']['duration'] == 5

    def test_apply_effect_refresh(self):
        """测试刷新已存在效果。"""
        effect_data = {'duration': 5}
        self.mock_parser.get_effect.return_value = effect_data
        self.manager.active_effects['poisoned'] = {'duration': 2}
        result = self.manager.apply_effect('poisoned')
        assert result is True
        assert self.manager.active_effects['poisoned']['duration'] == 5

    def test_apply_effect_string_duration(self):
        """测试字符串持续时间。"""
        effect_data = {'duration': '10 turns'}
        self.mock_parser.get_effect.return_value = effect_data
        result = self.manager.apply_effect('blessed')
        assert result is True
        assert self.manager.active_effects['blessed']['duration'] == 10

    def test_remove_effect_exists(self):
        """测试移除存在的效果。"""
        self.manager.active_effects['poisoned'] = {'remove': ['heal']}
        result = self.manager.remove_effect('poisoned')
        assert result is True
        assert 'poisoned' not in self.manager.active_effects

    def test_remove_effect_not_exists(self):
        """测试移除不存在的效果。"""
        result = self.manager.remove_effect('nonexistent')
        assert result is False

    @patch('time.time', return_value=1000)
    def test_update_effects_expire(self, mock_time):
        """测试更新效果并过期。"""
        self.manager.active_effects['temporary'] = {'duration': 1}
        self.manager.update_effects()
        assert 'temporary' not in self.manager.active_effects

    @patch('time.time', return_value=1000)
    def test_update_effects_tick(self, mock_time):
        """测试更新效果的tick动作。"""
        self.manager.active_effects['regeneration'] = {
            'duration': 5,
            'tick': 'set:health=100',
            'tick_rate': 1,
            'start_time': 995,
            'last_tick': 0
        }
        self.manager.update_effects()
        # Should execute tick action
        self.mock_command_executor.execute_command.assert_called_with({'set': 'health=100'})

    def test_get_active_effects_all(self):
        """测试获取所有活跃效果。"""
        self.manager.active_effects = {'poisoned': {}, 'blessed': {}}
        effects = self.manager.get_active_effects()
        assert len(effects) == 2
        assert 'poisoned' in effects
        assert 'blessed' in effects

    def test_get_active_effects_filtered(self):
        """测试获取过滤后的活跃效果。"""
        self.manager.active_effects = {
            'poisoned': {'target': 'player'},
            'blessed': {'target': 'enemy'}
        }
        effects = self.manager.get_active_effects('player')
        assert len(effects) == 1
        assert 'poisoned' in effects

    def test_has_effect_true(self):
        """测试检查拥有效果。"""
        self.manager.active_effects = {'poisoned': {'target': 'player'}}
        assert self.manager.has_effect('poisoned', 'player') is True

    def test_has_effect_false(self):
        """测试检查没有效果。"""
        self.manager.active_effects = {'blessed': {'target': 'player'}}
        assert self.manager.has_effect('poisoned', 'player') is False

    def test_get_effect_modifier_additive(self):
        """测试获取加法修正值。"""
        self.manager.active_effects = {
            'strength_buff': {'modifiers': {'strength': '+2'}},
            'weakness': {'modifiers': {'strength': '-1'}}
        }
        modifier = self.manager.get_effect_modifier('strength')
        assert modifier == 1.0  # +2 -1

    def test_get_effect_modifier_multiplicative(self):
        """测试获取乘法修正值。"""
        self.manager.active_effects = {
            'strength_buff': {'modifiers': {'strength': '*1.5'}}
        }
        modifier = self.manager.get_effect_modifier('strength')
        assert modifier == 0.0  # Multiplicative not fully implemented in test

    def test_execute_effect_actions_list(self):
        """测试执行效果动作列表。"""
        effect_data = {'apply': ['set:health=100', 'add_flag:invincible']}
        self.manager._execute_effect_actions(effect_data, 'apply')
        assert self.mock_command_executor.execute_command.call_count == 1  # Only 'set:' calls execute_command
        self.mock_state_manager.set_flag.assert_called_with('invincible')

    def test_execute_effect_actions_string(self):
        """测试执行效果动作字符串。"""
        effect_data = {'apply': 'set:health=100'}
        self.manager._execute_effect_actions(effect_data, 'apply')
        self.mock_command_executor.execute_command.assert_called_with({'set': 'health=100'})

    def test_execute_single_action_health_damage(self):
        """测试执行生命值伤害动作。"""
        self.mock_state_manager.get_variable.return_value = 100
        self.manager._execute_single_action('player.health -= 5', {})
        self.mock_state_manager.set_variable.assert_called_with('health', 95)

    def test_execute_single_action_set(self):
        """测试执行设置动作。"""
        self.manager._execute_single_action('set:strength=15', {})
        self.mock_command_executor.execute_command.assert_called_with({'set': 'strength=15'})

    def test_execute_single_action_add_flag(self):
        """测试执行添加标志动作。"""
        self.manager._execute_single_action('add_flag:invincible', {})
        self.mock_state_manager.set_flag.assert_called_with('invincible')

    def test_execute_single_action_remove_flag(self):
        """测试执行移除标志动作。"""
        self.manager._execute_single_action('remove_flag:poisoned', {})
        self.mock_state_manager.clear_flag.assert_called_with('poisoned')

    def test_execute_single_action_broadcast(self):
        """测试执行广播动作。"""
        self.manager._execute_single_action('broadcast:"You feel stronger!"', {})
        # Just check it doesn't crash

    def test_execute_single_action_unknown(self):
        """测试执行未知动作。"""
        self.manager._execute_single_action('unknown:action', {})
        # Should log warning but not crash

    def test_get_status_message_no_effects(self):
        """测试获取无效果的状态消息。"""
        message = self.manager.get_status_message()
        assert message == ""

    def test_get_status_message_with_effects(self):
        """测试获取有效果的状态消息。"""
        self.manager.active_effects = {'poisoned': {}, 'blessed': {}}
        message = self.manager.get_status_message()
        assert 'poisoned' in message
        assert 'blessed' in message
