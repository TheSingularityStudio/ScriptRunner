"""
Unit tests for StateMachineManager.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.state_machine_manager import StateMachineManager


class TestStateMachineManager:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_command_executor = Mock()
        self.mock_condition_evaluator = Mock()
        self.manager = StateMachineManager(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_command_executor,
            self.mock_condition_evaluator
        )

    def test_initialization(self):
        """测试 StateMachineManager 初始化。"""
        assert self.manager.parser == self.mock_parser
        assert self.manager.state == self.mock_state_manager
        assert self.manager.command_executor == self.mock_command_executor
        assert self.manager.condition_evaluator == self.mock_condition_evaluator
        assert self.manager.state_machines == {}

    def test_load_state_machines(self):
        """测试加载状态机。"""
        state_machines = {
            'day_night_cycle': {
                'initial_state': 'day',
                'states': {
                    'day': {'transitions': [{'condition': 'time > 7200', 'to': 'night'}]},
                    'night': {'transitions': [{'condition': 'time > 14400', 'to': 'day'}]}
                }
            }
        }
        self.mock_parser.get_state_machine_data.return_value = state_machines
        self.manager.load_state_machines()
        assert 'day_night_cycle' in self.manager.state_machines
        self.mock_state_manager.set_variable.assert_called_with('day_night_cycle_state', 'day')

    def test_update_state_machines_transition(self):
        """测试更新状态机转换。"""
        self.manager.state_machines = {
            'test_sm': {
                'states': {
                    'state1': {
                        'transitions': [{'condition': 'true_condition', 'to': 'state2', 'actions': ['set:test_var = 1']}]
                    }
                }
            }
        }
        self.mock_state_manager.get_variable.return_value = 'state1'
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        self.manager.update_state_machines()
        self.mock_state_manager.set_variable.assert_called_with('test_sm_state', 'state2')
        self.mock_command_executor.execute_command.assert_called_with({'set': 'test_var = 1'})

    def test_update_state_machines_no_transition(self):
        """测试更新状态机无转换。"""
        self.manager.state_machines = {
            'test_sm': {
                'states': {
                    'state1': {
                        'transitions': [{'condition': 'false_condition', 'to': 'state2'}]
                    }
                }
            }
        }
        self.mock_state_manager.get_variable.return_value = 'state1'
        self.mock_condition_evaluator.evaluate_condition.return_value = False
        self.manager.update_state_machines()
        self.mock_state_manager.set_variable.assert_not_called()

    def test_check_transition_condition_time(self):
        """测试检查转换条件时间。"""
        self.mock_state_manager.get_variable.return_value = 100
        transition = {'condition': 'time > 50'}
        assert self.manager._check_transition_condition(transition) is True

    def test_check_transition_condition_other(self):
        """测试检查转换条件其他。"""
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        transition = {'condition': 'has_item'}
        assert self.manager._check_transition_condition(transition) is True

    def test_execute_state_transition(self):
        """测试执行状态转换。"""
        transition = {'actions': ['set:health = 100']}
        self.manager._execute_state_transition('test_sm', 'old_state', 'new_state', transition)
        self.mock_state_manager.set_variable.assert_called_with('test_sm_state', 'new_state')
        self.mock_command_executor.execute_command.assert_called_with({'set': 'health = 100'})

    def test_execute_state_actions(self):
        """测试执行状态动作。"""
        state_def = {'actions': ['set:mana = 50']}
        self.manager._execute_state_actions('test_sm', state_def)
        self.mock_command_executor.execute_command.assert_called_with({'set': 'mana = 50'})

    def test_execute_action_set(self):
        """测试执行动作设置变量。"""
        self.manager._execute_action('set:strength = 10')
        self.mock_command_executor.execute_command.assert_called_with({'set': 'strength = 10'})

    def test_execute_action_add_flag(self):
        """测试执行动作添加标志。"""
        self.manager._execute_action('add_flag:victory')
        self.mock_state_manager.set_flag.assert_called_with('victory')

    def test_execute_action_remove_flag(self):
        """测试执行动作移除标志。"""
        self.manager._execute_action('remove_flag:defeat')
        self.mock_state_manager.clear_flag.assert_called_with('defeat')

    def test_execute_action_broadcast(self):
        """测试执行动作广播。"""
        self.manager._execute_action('broadcast:Hello world')

    def test_execute_action_log(self):
        """测试执行动作日志。"""
        self.manager._execute_action('log:State changed')

    def test_execute_action_unknown(self):
        """测试执行动作未知。"""
        self.manager._execute_action('unknown:action')

    def test_get_current_state(self):
        """测试获取当前状态。"""
        self.mock_state_manager.get_variable.return_value = 'active'
        result = self.manager.get_current_state('test_sm')
        assert result == 'active'
        self.mock_state_manager.get_variable.assert_called_with('test_sm_state')

    def test_force_state(self):
        """测试强制设置状态。"""
        self.manager.state_machines['test_sm'] = {}  # Add the state machine to the dict
        result = self.manager.force_state('test_sm', 'forced_state')
        assert result is True
        self.mock_state_manager.set_variable.assert_called_with('test_sm_state', 'forced_state')

    def test_force_state_not_exists(self):
        """测试强制设置状态不存在的状态机。"""
        result = self.manager.force_state('nonexistent', 'state')
        assert result is False

    def test_get_state_machine_info(self):
        """测试获取状态机信息。"""
        sm_info = {'states': {}}
        self.manager.state_machines['test'] = sm_info
        result = self.manager.get_state_machine_info('test')
        assert result == sm_info
