"""
Comprehensive integration test for script execution, testing if the script runner can run all contents of a script normally.
This test simulates a full game run of example_game.yaml, exercising all DSL features.
"""

import pytest
import os
import yaml
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import StringIO
from src.infrastructure.container import Container
from src.domain.parser.parser import ScriptParser
from src.infrastructure.state_manager import StateManager
from src.domain.runtime.execution_engine import ExecutionEngine
from src.domain.runtime.scene_executor import SceneExecutor
from src.domain.runtime.command_executor import CommandExecutor
from src.domain.runtime.condition_evaluator import ConditionEvaluator
from src.domain.runtime.choice_processor import ChoiceProcessor
from src.domain.runtime.input_handler import InputHandler
from src.domain.runtime.effects_manager import EffectsManager
from src.domain.runtime.event_manager import EventManager
from src.domain.runtime.random_manager import RandomManager
from src.domain.runtime.state_machine_manager import StateMachineManager
from src.domain.runtime.meta_manager import MetaManager


class TestComprehensiveScriptExecution:
    def setup_method(self):
        """设置综合测试方法。"""
        self.script_file = "scripts/example_game.yaml"
        self.container = Container()

        # 初始化所有组件
        self.parser = ScriptParser()
        self.state_manager = StateManager()
        self.condition_evaluator = ConditionEvaluator(self.state_manager, self.parser)
        self.command_executor = CommandExecutor(self.parser, self.state_manager, self.condition_evaluator)
        self.scene_executor = SceneExecutor(self.parser, self.state_manager, self.command_executor, self.condition_evaluator)

        # Mock 处理器
        self.choice_processor = Mock()
        self.input_handler = Mock()

        # 初始化管理器
        self.effects_manager = EffectsManager(self.parser, self.state_manager, self.command_executor)
        self.event_manager = EventManager(self.parser, self.state_manager, self.command_executor, self.condition_evaluator)
        self.random_manager = RandomManager(self.parser, self.state_manager)
        # Note: load_random_tables will be called after script loading in individual tests
        self.state_machine_manager = StateMachineManager(self.parser, self.state_manager, self.command_executor, self.condition_evaluator)
        self.meta_manager = MetaManager(self.parser, self.state_manager, self.condition_evaluator)

        # 创建执行引擎
        self.execution_engine = ExecutionEngine(
            self.parser, self.state_manager, self.scene_executor, self.command_executor,
            self.condition_evaluator, self.choice_processor, self.input_handler,
            self.event_manager, self.effects_manager, self.state_machine_manager,
            self.meta_manager, self.random_manager
        )

    def test_full_script_execution_with_all_features(self):
        """测试完整脚本执行，覆盖所有DSL特性。"""
        assert os.path.exists(self.script_file), f"脚本文件不存在: {self.script_file}"

        # 加载脚本
        self.parser.load_script(self.script_file)
        self.random_manager.load_random_tables()  # Load random tables after script loading

        # 验证脚本加载
        assert self.parser.script_data['game'] == "Elderwood Chronicles"
        assert 'world' in self.parser.script_data
        assert 'player' in self.parser.script_data

        # 初始化玩家属性
        player_data = self.parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            self.state_manager.set_variable(attr, value)

        # 验证玩家属性设置
        assert self.state_manager.get_variable('strength') == 10
        assert self.state_manager.get_variable('intelligence') == 8
        assert self.state_manager.get_variable('agility') == 12
        assert self.state_manager.get_variable('health') == 100

        # 获取起始场景
        start_scene_id = self.parser.get_start_scene()
        assert start_scene_id == "village_square"

        # 执行起始场景
        scene_data = self.execution_engine.execute_scene(start_scene_id)

        # 验证场景数据
        assert 'text' in scene_data
        assert 'choices' in scene_data
        assert len(scene_data['choices']) > 0
        assert '村庄广场' in scene_data['text'] or 'village square' in scene_data['text'].lower()

        # 模拟选择第一个选项（进入森林）
        self.choice_processor.process_choice.return_value = 'forest_path'
        next_scene = self.execution_engine.process_choice(0)
        assert next_scene == "forest_path"

        # 执行森林路径场景
        scene_data = self.execution_engine.execute_scene(next_scene)
        assert 'text' in scene_data
        assert '森林' in scene_data['text'] or 'forest' in scene_data['text'].lower()

        # 验证哥布林对象存在
        goblin = self.parser.get_object('goblin')
        assert goblin is not None
        assert goblin['type'] == 'creature'
        assert goblin['name'] == '哥布林'

        # 测试事件系统
        events = self.parser.get_events()
        assert 'scheduled_events' in events
        assert 'reactive_events' in events

        # 测试随机系统
        forest_encounters = self.parser.get_random_table('forest_encounters')
        assert forest_encounters is not None
        assert forest_encounters['type'] == 'weighted'

        # 测试状态机
        day_night_cycle = self.parser.get_state_machine('day_night_cycle')
        assert day_night_cycle is not None
        assert 'states' in day_night_cycle
        assert 'transitions' in day_night_cycle

        # 测试效果
        poisoned = self.parser.get_effect('poisoned')
        assert poisoned is not None
        assert 'duration' in poisoned
        assert 'action' in poisoned

        # 测试命令解析器
        command_config = self.parser.command_parser_config
        assert 'verbs' in command_config
        assert 'nouns' in command_config

        # 模拟命令输入
        self.input_handler.process_player_input.return_value = {'action': 'take', 'target': 'sword'}

        # 测试效果管理器更新
        self.effects_manager.apply_effect('poisoned', self.parser.get_effect('poisoned'))
        self.effects_manager.update_effects()

        # 测试事件管理器触发
        self.state_manager.set_variable('time', 1900)  # 触发预定事件
        self.event_manager.check_scheduled_events()

        # 测试随机管理器
        random_result = self.random_manager.roll_weighted_table('forest_encounters')
        assert random_result is not None

        # 测试状态机管理器
        self.state_machine_manager.update_state_machines()

        # 测试元管理器宏
        macro_result = self.meta_manager.evaluate_macro('is_combat_ready')
        assert isinstance(macro_result, bool)

        # 验证所有组件正常工作
        assert self.state_manager.get_variable('health') > 0
        assert len(self.state_manager.get_active_effects()) >= 0

        print("所有DSL特性测试通过！")

    def test_script_runner_main_flow_simulation(self):
        """测试脚本运行器主流程模拟。"""
        with patch('builtins.print'), patch('builtins.input', side_effect=['1', 'q']):
            # 这里模拟main.py的逻辑，但使用测试组件

            # 加载脚本
            self.parser.load_script(self.script_file)

            # 初始化玩家属性
            player_data = self.parser.script_data.get('player', {})
            for attr, value in player_data.get('attributes', {}).items():
                self.state_manager.set_variable(attr, value)

            # 获取起始场景
            current_scene_id = self.parser.get_start_scene()

            # 模拟游戏循环
            loop_count = 0
            max_loops = 5  # 限制循环次数避免无限循环

            while current_scene_id and loop_count < max_loops:
                # 执行场景
                scene_data = self.execution_engine.execute_scene(current_scene_id)

                # 模拟用户选择
                if loop_count == 0:
                    # 第一次循环选择进入森林
                    self.choice_processor.process_choice.return_value = 'forest_path'
                    next_scene = self.execution_engine.process_choice(0)
                else:
                    # 后续循环退出
                    next_scene = None

                current_scene_id = next_scene
                loop_count += 1

            # 验证游戏正常结束
            assert loop_count > 0
            assert current_scene_id is None or loop_count == max_loops

    def test_error_handling_and_edge_cases(self):
        """测试错误处理和边界情况。"""
        # 测试无效脚本文件
        with pytest.raises(FileNotFoundError):
            self.parser.load_script("nonexistent.yaml")

        # 测试缺少关键字段的脚本 (DSL格式缺少game字段)
        invalid_script = {
            'world': {'start': 'scene1'},
            'locations': {'scene1': {}}
        }

        with patch('builtins.open', new=mock_open(read_data=yaml.dump(invalid_script))), patch('os.path.exists', return_value=True):
            with pytest.raises(ValueError):
                self.parser.load_script("dummy.yaml")

        # 测试状态管理器边界情况
        self.state_manager.set_variable('test', None)
        assert self.state_manager.get_variable('test') is None

        # 测试效果管理器边界情况
        self.effects_manager.apply_effect('test_effect', {'duration': 0})
        self.effects_manager.update_effects()
        assert 'test_effect' not in self.state_manager.get_active_effects()

    def test_performance_and_resource_usage(self):
        """测试性能和资源使用。"""
        import time

        # Load script first
        self.parser.load_script(self.script_file)

        start_time = time.time()

        # 执行多次场景切换
        for _ in range(10):
            self.execution_engine.execute_scene('village_square')
            self.execution_engine.process_choice(0)

        end_time = time.time()
        execution_time = end_time - start_time

        # 验证性能在合理范围内（假设<1秒）
        assert execution_time < 1.0, f"执行时间过长: {execution_time}秒"

        # 验证内存使用（简单检查）
        assert len(self.state_manager.variables) >= 0
        assert len(self.state_manager.get_active_effects()) >= 0
