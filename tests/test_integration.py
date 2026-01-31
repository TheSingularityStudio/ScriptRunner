"""
Integration tests for ScriptRunner.
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch
from src.infrastructure.container import Container
from src.domain.parser.parser import ScriptParser
from src.infrastructure.state_manager import StateManager
from src.domain.runtime.execution_engine import ExecutionEngine
from src.domain.runtime.scene_executor import SceneExecutor
from src.domain.runtime.script_command_executor import ScriptCommandExecutor
from src.domain.runtime.condition_evaluator import ConditionEvaluator
from src.domain.runtime.choice_processor import ChoiceProcessor
from src.domain.runtime.input_handler import InputHandler


class TestIntegration:
    def setup_method(self):
        """设置集成测试方法。"""
        self.container = Container()

        # 创建测试脚本内容
        self.test_script = {
            'scenes': {
                'start': {
                    'text': 'Welcome to the test game!',
                    'commands': [
                        {'set_variable': {'name': 'health', 'value': 100}}
                    ],
                    'choices': [
                        {'text': 'Go to room', 'next': 'room1'},
                        {'text': 'Quit', 'next': None, 'condition': 'has_flag(quit)'}
                    ]
                },
                'room1': {
                    'text': 'You are in room 1. Health: {health}',
                    'choices': [
                        {'text': 'Go back', 'next': 'start'}
                    ]
                }
            },
            'start_scene': 'start',
            'commands': {
                'set_variable': {
                    'actions': ['set_variable']
                }
            }
        }

    def test_full_game_flow(self):
        """测试完整的游戏流程。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_script, f)
            script_file = f.name

        try:
            # 初始化组件
            parser = ScriptParser()
            state_manager = StateManager()
            condition_evaluator = ConditionEvaluator(state_manager)
            mock_plugin_manager = Mock()
            mock_plugin_manager.get_plugins_by_type.return_value = []
            command_executor = ScriptCommandExecutor(parser, state_manager, condition_evaluator, mock_plugin_manager)
            scene_executor = SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

            # Mock choice processor and input handler
            choice_processor = Mock()
            input_handler = Mock()

            # Initialize managers
            from src.domain.runtime.effects_manager import EffectsManager
            from src.domain.runtime.event_manager import EventManager
            from src.domain.runtime.random_manager import RandomManager
            from src.domain.runtime.state_machine_manager import StateMachineManager
            from src.domain.runtime.meta_manager import MetaManager

            effects_manager = EffectsManager(parser, state_manager, command_executor)
            event_manager = EventManager(parser, state_manager, command_executor, condition_evaluator)
            random_manager = RandomManager(parser, state_manager)
            state_machine_manager = StateMachineManager(parser, state_manager, command_executor, condition_evaluator)
            meta_manager = MetaManager(parser, state_manager, condition_evaluator)

            execution_engine = ExecutionEngine(
                parser, state_manager, scene_executor, command_executor,
                condition_evaluator, choice_processor, input_handler,
                event_manager, effects_manager, state_machine_manager,
                meta_manager, random_manager
            )

            # 加载脚本
            parser.load_script(script_file)

            # 设置标志以使第二个选择可见
            state_manager.set_flag('quit')

            # 执行起始场景
            scene_data = execution_engine.execute_scene('start')

            # 验证场景执行结果
            assert 'text' in scene_data
            assert scene_data['text'] == 'Welcome to the test game!'
            assert len(scene_data['choices']) == 2
            assert state_manager.get_variable('health') == 100

            # 模拟选择处理
            choice_processor.process_choice.return_value = 'room1'
            next_scene = execution_engine.process_choice(0)
            assert next_scene == 'room1'

            # 执行下一个场景
            scene_data = execution_engine.execute_scene('room1')
            assert 'text' in scene_data
            assert 'Health: 100' in scene_data['text']

        finally:
            os.unlink(script_file)

    def test_di_container_integration(self):
        """测试DI容器集成。"""
        # 注册组件到容器
        self.container.register('parser', ScriptParser())
        self.container.register('state_manager', StateManager())

        # 获取组件实例
        parser = self.container.get('parser')
        state_manager = self.container.get('state_manager')

        assert isinstance(parser, ScriptParser)
        assert isinstance(state_manager, StateManager)

        # 测试组件间交互
        state_manager.set_variable('test', 'value')
        assert state_manager.get_variable('test') == 'value'

    def test_script_parsing_and_execution_integration(self):
        """测试脚本解析和执行的集成。"""
        dsl_script = {
            'game': {'title': 'Integration Test Game'},
            'world': {'start': 'start'},
            'define_object': {
                'sword': {'damage': 15, 'type': 'weapon'}
            },
            'locations': {
                'start': {
                    'description': 'Starting location',
                    'choices': [
                        {'text': 'Pick up sword', 'next': 'start', 'condition': 'true'}
                    ]
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(dsl_script, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)

            # 验证DSL解析
            assert parser.get_start_scene() == 'start'
            assert parser.get_object('sword') == {'damage': 15, 'type': 'weapon'}

            # 验证场景获取
            start_scene = parser.get_scene('start')
            assert 'description' in start_scene
            assert start_scene['description'] == 'Starting location'

        finally:
            os.unlink(script_file)

    @patch('builtins.input', side_effect=['1'])
    @patch('builtins.print')
    def test_main_game_loop_simulation(self, mock_print, mock_input):
        """测试主游戏循环模拟。"""
        # 创建简单的测试脚本
        simple_script = {
            'scenes': {
                'start': {
                    'text': 'Test scene',
                    'choices': [
                        {'text': 'End game', 'next': None}
                    ]
                }
            },
            'start_scene': 'start'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(simple_script, f)
            script_file = f.name

        try:
            # 这里可以模拟主循环的部分逻辑
            parser = ScriptParser()
            state_manager = StateManager()

            parser.load_script(script_file)
            start_scene = parser.get_start_scene()

            assert start_scene == 'start'

            # 验证场景数据
            scene = parser.get_scene(start_scene)
            assert scene['text'] == 'Test scene'
            assert len(scene['choices']) == 1

        finally:
            os.unlink(script_file)

    def test_state_persistence_integration(self):
        """测试状态持久化集成。"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            save_file = f.name

        try:
            # 创建状态管理器
            state_manager = StateManager(save_file)

            # 设置状态
            state_manager.set_variable('score', 150)
            state_manager.set_flag('completed_tutorial')
            state_manager.set_current_scene('level2')
            state_manager.apply_effect('buff', {'duration': 3, 'type': 'temporary'})

            # 保存状态
            state_manager.save_game()  # Should not raise exception

            # 创建新实例并加载
            new_state_manager = StateManager(save_file)
            assert new_state_manager.load_game() is True

            # 验证状态恢复
            assert new_state_manager.get_variable('score') == 150
            assert new_state_manager.has_flag('completed_tutorial') is True
            assert new_state_manager.get_current_scene() == 'level2'
            assert 'buff' in new_state_manager.get_active_effects()

        finally:
            if os.path.exists(save_file):
                os.unlink(save_file)

    def test_condition_evaluation_integration(self):
        """测试条件评估集成。"""
        state_manager = StateManager()
        condition_evaluator = ConditionEvaluator(state_manager)

        # 设置测试状态
        state_manager.set_variable('health', 80)
        state_manager.set_flag('has_key')

        # 测试各种条件
        assert condition_evaluator.evaluate_condition('health > 50') is True
        assert condition_evaluator.evaluate_condition('health < 50') is False
        assert condition_evaluator.evaluate_condition('has_flag(has_key)') is True
        assert condition_evaluator.evaluate_condition('has_flag(no_key)') is False
        assert condition_evaluator.evaluate_condition('exists:health') is True
        assert condition_evaluator.evaluate_condition('exists:mana') is False
        assert condition_evaluator.evaluate_condition(None) is True  # 无条件
