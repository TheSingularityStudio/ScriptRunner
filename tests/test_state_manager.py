"""
Unit tests for StateManager.
"""

import pytest
import tempfile
import os
from src.state.state_manager import StateManager


class TestStateManager:
    def test_initialization(self):
        """测试 StateManager 初始化。"""
        manager = StateManager()
        assert manager.variables == {}
        assert manager.flags == set()
        assert manager.current_scene == ""
        assert manager.active_effects == {}

    def test_variable_operations(self):
        """测试变量获取/设置操作。"""
        manager = StateManager()

        # Test setting and getting variables
        manager.set_variable('health', 100)
        assert manager.get_variable('health') == 100
        assert manager.get_variable('nonexistent', 'default') == 'default'

        # Test different data types
        manager.set_variable('name', 'player')
        manager.set_variable('is_alive', True)
        manager.set_variable('score', 42.5)

        assert manager.get_variable('name') == 'player'
        assert manager.get_variable('is_alive') is True
        assert manager.get_variable('score') == 42.5

    def test_flag_operations(self):
        """测试标志操作。"""
        manager = StateManager()

        # Test setting and checking flags
        manager.set_flag('has_key')
        assert manager.has_flag('has_key') is True
        assert manager.has_flag('no_flag') is False

        # Test clearing flags
        manager.clear_flag('has_key')
        assert manager.has_flag('has_key') is False

        # Test clearing non-existent flag (should not raise error)
        manager.clear_flag('nonexistent')

    def test_scene_operations(self):
        """测试场景操作。"""
        manager = StateManager()

        manager.set_current_scene('start')
        assert manager.get_current_scene() == 'start'

        manager.set_current_scene('room1')
        assert manager.get_current_scene() == 'room1'

    def test_effect_operations(self):
        """测试效果操作。"""
        manager = StateManager()

        effect_data = {'duration': 5, 'type': 'buff'}
        manager.apply_effect('strength', effect_data)

        effects = manager.get_active_effects()
        assert 'strength' in effects
        assert effects['strength'] == effect_data

        # Test removing effects
        manager.remove_effect('strength')
        assert 'strength' not in manager.get_active_effects()

        # Test removing non-existent effect
        manager.remove_effect('nonexistent')

    def test_effect_updates(self):
        """测试效果持续时间更新。"""
        manager = StateManager()

        # Add effect with duration
        manager.apply_effect('temp_buff', {'duration': 2, 'type': 'buff'})
        manager.apply_effect('perm_buff', {'duration': 0, 'type': 'permanent'})

        # Update effects
        manager.update_effects()
        effects = manager.get_active_effects()
        assert effects['temp_buff']['duration'] == 1
        assert effects['perm_buff']['duration'] == 0

        # Update again - temp_buff should expire
        manager.update_effects()
        effects = manager.get_active_effects()
        assert 'temp_buff' not in effects
        assert 'perm_buff' in effects

    def test_save_load_game(self):
        """测试游戏保存和加载功能。"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            save_file = f.name

        try:
            manager = StateManager(save_file)

            # Set up some state
            manager.set_variable('health', 80)
            manager.set_variable('name', 'test_player')
            manager.set_flag('has_sword')
            manager.set_current_scene('battle')
            manager.apply_effect('poison', {'duration': 3})

            # Save game
            manager.save_game()

            # Create new manager and load
            new_manager = StateManager(save_file)
            assert new_manager.load_game() is True

            # Verify loaded state
            assert new_manager.get_variable('health') == 80
            assert new_manager.get_variable('name') == 'test_player'
            assert new_manager.has_flag('has_sword') is True
            assert new_manager.get_current_scene() == 'battle'
            assert 'poison' in new_manager.get_active_effects()

        finally:
            if os.path.exists(save_file):
                os.unlink(save_file)

    def test_load_nonexistent_file(self):
        """测试从不存在的文件加载。"""
        manager = StateManager('nonexistent.json')
        assert manager.load_game() is False

    def test_reset(self):
        """测试状态重置。"""
        manager = StateManager()

        # Set up state
        manager.set_variable('health', 50)
        manager.set_flag('has_item')
        manager.set_current_scene('test_scene')
        manager.apply_effect('test_effect', {'duration': 1})

        # Reset
        manager.reset()

        # Verify reset
        assert manager.variables == {}
        assert manager.flags == set()
        assert manager.current_scene == ""
        assert manager.active_effects == {}
