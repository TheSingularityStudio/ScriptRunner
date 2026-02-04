"""
Unit tests for ExecutionEngine.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.domain.runtime.execution_engine import ExecutionEngine
from src.domain.runtime.script_object import ScriptObject


class TestExecutionEngine:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_scene_executor = Mock()
        self.mock_command_executor = Mock()
        self.mock_condition_evaluator = Mock()
        self.mock_choice_processor = Mock()
        self.mock_input_handler = Mock()
        self.mock_script_factory = Mock()

    def test_initialization_without_script_factory(self):
        """测试 ExecutionEngine 初始化（无脚本工厂）。"""
        engine = ExecutionEngine(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_scene_executor,
            self.mock_command_executor,
            self.mock_condition_evaluator,
            self.mock_choice_processor,
            self.mock_input_handler
        )

        assert engine.parser == self.mock_parser
        assert engine.state == self.mock_state_manager
        assert engine.scene_executor == self.mock_scene_executor
        assert engine.script_object_executor == self.mock_command_executor
        assert engine.condition_evaluator == self.mock_condition_evaluator
        assert engine.choice_processor == self.mock_choice_processor



    def test_execute_scene(self):
        """测试场景执行。"""
        engine = ExecutionEngine(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_scene_executor,
            self.mock_command_executor,
            self.mock_condition_evaluator,
            self.mock_choice_processor,
            self.mock_input_handler
        )

        expected_result = {'text': 'Scene content', 'choices': []}
        self.mock_scene_executor.execute_scene.return_value = expected_result

        result = engine.execute_scene('test_scene')

        self.mock_scene_executor.execute_scene.assert_called_once_with('test_scene')
        assert result == expected_result

    def test_process_choice(self):
        """测试选择处理。"""
        engine = ExecutionEngine(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_scene_executor,
            self.mock_command_executor,
            self.mock_condition_evaluator,
            self.mock_choice_processor,
            self.mock_input_handler
        )

        expected_next_scene = 'next_scene'
        self.mock_choice_processor.process_choice.return_value = expected_next_scene

        result = engine.process_choice(1)

        self.mock_choice_processor.process_choice.assert_called_once_with(1)
        assert result == expected_next_scene

    def test_process_choice_no_next_scene(self):
        """测试选择处理无下一个场景。"""
        engine = ExecutionEngine(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_scene_executor,
            self.mock_command_executor,
            self.mock_condition_evaluator,
            self.mock_choice_processor,
            self.mock_input_handler
        )

        self.mock_choice_processor.process_choice.return_value = None

        result = engine.process_choice(0)

        self.mock_choice_processor.process_choice.assert_called_once_with(0)
        assert result is None

    def test_process_player_input(self):
        """测试玩家输入处理。"""
        engine = ExecutionEngine(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_scene_executor,
            self.mock_command_executor,
            self.mock_condition_evaluator,
            self.mock_choice_processor,
            self.mock_input_handler
        )

        expected_result = {'action': 'move', 'target': 'north'}
        self.mock_input_handler.process_player_input.return_value = expected_result

        result = engine.process_player_input('go north')

        self.mock_input_handler.process_player_input.assert_called_once_with('go north')
        assert result == expected_result
