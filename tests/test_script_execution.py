"""
Integration tests for script execution, specifically testing if scripts/example_game.yaml can run normally.
"""

import pytest
import os
from unittest.mock import Mock
from src.parser.parser import ScriptParser
from src.state.state_manager import StateManager
from src.runtime.execution_engine import ExecutionEngine
from src.runtime.scene_executor import SceneExecutor
from src.runtime.command_executor import CommandExecutor
from src.runtime.condition_evaluator import ConditionEvaluator
from src.runtime.choice_processor import ChoiceProcessor
from src.runtime.input_handler import InputHandler


class TestScriptExecution:
    def setup_method(self):
        """设置测试方法。"""
        self.script_file = "scripts/example_game.yaml"

    def test_example_game_script_loads_and_parses(self):
        """测试 example_game.yaml 脚本能否正常加载和解析。"""
        assert os.path.exists(self.script_file), f"脚本文件不存在: {self.script_file}"

        parser = ScriptParser()

        # 加载脚本不应抛出异常
        script_data = parser.load_script(self.script_file)

        # 验证基本结构
        assert 'game' in script_data
        assert script_data['game'] == "Elderwood Chronicles"
        assert 'world' in script_data
        assert 'start' in script_data['world']

        # 验证起始场景
        start_scene = parser.get_start_scene()
        assert start_scene == "village_square"

        # 验证对象定义
        goblin = parser.get_object('goblin')
        assert goblin['type'] == 'creature'
        state_names = [state['name'] for state in goblin['states']]
        assert 'health' in state_names

        # 验证位置定义
        village_square = parser.get_scene('village_square')
        assert 'description' in village_square
        assert 'choices' in village_square

    def test_example_game_script_execution(self):
        """测试 example_game.yaml 脚本的执行流程。"""
        parser = ScriptParser()
        state_manager = StateManager()
        condition_evaluator = ConditionEvaluator(state_manager)
        command_executor = CommandExecutor(parser, state_manager, condition_evaluator)
        scene_executor = SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

        # Mock choice processor and input handler for execution
        choice_processor = Mock()
        input_handler = Mock()

        execution_engine = ExecutionEngine(
            parser, state_manager, scene_executor, command_executor,
            condition_evaluator, choice_processor, input_handler
        )

        # 加载脚本
        parser.load_script(self.script_file)

        # 初始化玩家属性
        player_data = parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            state_manager.set_variable(attr, value)

        # 获取起始场景
        start_scene_id = parser.get_start_scene()
        assert start_scene_id == "village_square"

        # 执行起始场景
        scene_data = execution_engine.execute_scene(start_scene_id)

        # 验证场景执行结果
        assert 'text' in scene_data
        assert 'choices' in scene_data
        assert len(scene_data['choices']) > 0

        # 验证场景文本包含预期内容
        assert '村庄广场' in scene_data['text'] or 'village square' in scene_data['text'].lower()

        # 验证玩家属性已设置
        assert state_manager.get_variable('strength') == 10
        assert state_manager.get_variable('intelligence') == 8
        assert state_manager.get_variable('agility') == 12

    def test_example_game_scene_transitions(self):
        """测试 example_game.yaml 脚本的场景转换。"""
        parser = ScriptParser()
        state_manager = StateManager()
        condition_evaluator = ConditionEvaluator(state_manager, parser)
        command_executor = CommandExecutor(parser, state_manager, condition_evaluator)
        scene_executor = SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

        choice_processor = ChoiceProcessor(parser, state_manager, command_executor)
        input_handler = Mock()

        execution_engine = ExecutionEngine(
            parser, state_manager, scene_executor, command_executor,
            condition_evaluator, choice_processor, input_handler
        )

        # 加载脚本
        parser.load_script(self.script_file)

        # 初始化玩家属性
        player_data = parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            state_manager.set_variable(attr, value)

        # 执行起始场景
        current_scene_id = parser.get_start_scene()
        scene_data = execution_engine.execute_scene(current_scene_id)

        # 模拟选择第一个选项（进入森林）
        choice_index = 0
        next_scene = execution_engine.process_choice(choice_index)

        # 验证场景转换
        assert next_scene is not None
        assert next_scene == "forest_path"

        # 执行下一个场景
        scene_data = execution_engine.execute_scene(next_scene)
        assert 'text' in scene_data
        assert '森林' in scene_data['text'] or 'forest' in scene_data['text'].lower()

    def test_example_game_object_interactions(self):
        """测试 example_game.yaml 脚本的对象交互。"""
        parser = ScriptParser()
        state_manager = StateManager()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证对象获取
        goblin = parser.get_object('goblin')
        assert goblin is not None
        assert goblin['name'] == '哥布林'

        ancient_chest = parser.get_object('ancient_chest')
        assert ancient_chest is not None
        assert '古老的箱子' in ancient_chest['name']

        werewolf = parser.get_object('werewolf')
        assert werewolf is not None
        assert werewolf['name'] == '狼人'

    def test_example_game_event_system(self):
        """测试 example_game.yaml 脚本的事件系统。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证事件系统
        events = parser.get_events()
        assert 'scheduled_events' in events
        assert 'reactive_events' in events

        # 验证预定事件
        scheduled_events = events['scheduled_events']
        assert len(scheduled_events) > 0
        assert 'trigger' in scheduled_events[0]
        assert 'action' in scheduled_events[0]

        # 验证反应事件
        reactive_events = events['reactive_events']
        assert len(reactive_events) > 0
        assert 'trigger' in reactive_events[0]
        assert 'conditions' in reactive_events[0]

    def test_example_game_random_system(self):
        """测试 example_game.yaml 脚本的随机系统。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证随机表
        forest_encounters = parser.get_random_table('forest_encounters')
        assert forest_encounters is not None
        assert forest_encounters['type'] == 'weighted'
        assert 'entries' in forest_encounters

        # 验证动态对话
        dynamic_dialog = parser.get_random_table('dynamic_dialog')
        assert dynamic_dialog is not None
        assert dynamic_dialog['type'] == 'template'
        assert 'template' in dynamic_dialog

    def test_example_game_state_machines(self):
        """测试 example_game.yaml 脚本的状态机。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证状态机
        day_night_cycle = parser.get_state_machine('day_night_cycle')
        assert day_night_cycle is not None
        assert 'states' in day_night_cycle
        assert 'transitions' in day_night_cycle
        assert 'effects' in day_night_cycle

    def test_example_game_effects(self):
        """测试 example_game.yaml 脚本的效果系统。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证效果
        poisoned = parser.get_effect('poisoned')
        assert poisoned is not None
        assert 'duration' in poisoned
        assert 'action' in poisoned

        blessed = parser.get_effect('blessed')
        assert blessed is not None
        assert 'modifiers' in blessed
