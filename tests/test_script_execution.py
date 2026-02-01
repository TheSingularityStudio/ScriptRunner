"""
Integration tests for script execution, specifically testing if scripts/example_game.yaml can run normally.
"""

import pytest
import os
from unittest.mock import Mock
from src.domain.parser.parser import ScriptParser
from src.infrastructure.state_manager import StateManager
from src.domain.runtime.execution_engine import ExecutionEngine
from src.domain.runtime.scene_executor import SceneExecutor
from src.domain.runtime.script_command_executor import ScriptCommandExecutor
from src.domain.runtime.condition_evaluator import ConditionEvaluator
from src.domain.runtime.choice_processor import ChoiceProcessor
from src.domain.runtime.input_handler import InputHandler


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
        assert script_data['game']['title'] == "洞穴冒险"
        assert 'world' in script_data
        assert 'start' in script_data['world']

        # 验证起始场景
        start_scene = parser.get_start_scene()
        assert start_scene == "cave_entrance"

        # 验证对象定义
        rusty_sword = parser.get_object('rusty_sword')
        assert rusty_sword['type'] == 'weapon'
        assert rusty_sword['name'] == '生锈的剑'

        goblin = parser.get_object('goblin')
        assert goblin['type'] == 'enemy'
        assert goblin['name'] == '哥布林'
        assert 'health' in goblin
        assert 'damage' in goblin

        # 验证位置定义
        cave_entrance = parser.get_scene('cave_entrance')
        assert 'description' in cave_entrance
        assert 'choices' in cave_entrance

    def test_example_game_script_execution(self):
        """测试 example_game.yaml 脚本的执行流程。"""
        parser = ScriptParser()
        state_manager = StateManager()
        condition_evaluator = ConditionEvaluator(state_manager)
        mock_plugin_manager = Mock()
        mock_plugin_manager.get_plugins_by_type.return_value = []
        command_executor = ScriptCommandExecutor(parser, state_manager, condition_evaluator, mock_plugin_manager)
        scene_executor = SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

        # Mock choice processor and input handler for execution
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
        parser.load_script(self.script_file)

        # 初始化玩家属性
        player_data = parser.script_data.get('player', {})
        state_manager.set_variable('health', player_data.get('health', 0))
        state_manager.set_variable('max_health', player_data.get('max_health', 0))
        state_manager.set_variable('score', player_data.get('variables', {}).get('score', 0))

        # 获取起始场景
        start_scene_id = parser.get_start_scene()
        assert start_scene_id == "cave_entrance"

        # 执行起始场景
        scene_data = execution_engine.execute_scene(start_scene_id)

        # 验证场景执行结果
        assert 'text' in scene_data
        assert 'choices' in scene_data
        assert len(scene_data['choices']) > 0

        # 验证场景文本包含预期内容
        assert '洞穴入口' in scene_data['text'] or 'cave entrance' in scene_data['text'].lower()

        # 验证玩家属性已设置
        assert state_manager.get_variable('health') == 100
        assert state_manager.get_variable('max_health') == 100
        assert state_manager.get_variable('score') == 0

    def test_example_game_scene_transitions(self):
        """测试 example_game.yaml 脚本的场景转换。"""
        parser = ScriptParser()
        state_manager = StateManager()
        condition_evaluator = ConditionEvaluator(state_manager, parser)
        mock_plugin_manager = Mock()
        mock_plugin_manager.get_plugins_by_type.return_value = []
        command_executor = ScriptCommandExecutor(parser, state_manager, condition_evaluator, mock_plugin_manager)
        scene_executor = SceneExecutor(parser, state_manager, command_executor, condition_evaluator)

        choice_processor = ChoiceProcessor(parser, state_manager, command_executor, condition_evaluator)
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
        parser.load_script(self.script_file)

        # 初始化玩家属性
        player_data = parser.script_data.get('player', {})
        for attr, value in player_data.get('attributes', {}).items():
            state_manager.set_variable(attr, value)

        # 执行起始场景
        current_scene_id = parser.get_start_scene()
        scene_data = execution_engine.execute_scene(current_scene_id)

        # 模拟选择第一个选项（进入洞穴）
        choice_index = 0
        next_scene, messages = execution_engine.process_choice(choice_index)

        # 验证场景转换
        assert next_scene is not None
        assert next_scene == "main_chamber"

        # 执行下一个场景
        scene_data = execution_engine.execute_scene(next_scene)
        assert 'text' in scene_data
        assert '洞穴主室' in scene_data['text'] or 'main chamber' in scene_data['text'].lower()

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

        treasure_chest = parser.get_object('treasure_chest')
        assert treasure_chest is not None
        assert treasure_chest['name'] == '宝箱'

        gold = parser.get_object('gold')
        assert gold is not None
        assert gold['name'] == '金币'

        health_potion = parser.get_object('health_potion')
        assert health_potion is not None
        assert health_potion['name'] == '治疗药水'

    def test_example_game_random_system(self):
        """测试 example_game.yaml 脚本的随机系统。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证随机表
        goblin_loot = parser.get_random_table('goblin_loot')
        assert goblin_loot is not None
        assert isinstance(goblin_loot, list)
        assert len(goblin_loot) > 0
        assert 'item' in goblin_loot[0]
        assert 'weight' in goblin_loot[0]



    def test_example_game_effects(self):
        """测试 example_game.yaml 脚本的效果系统。"""
        parser = ScriptParser()

        # 加载脚本
        parser.load_script(self.script_file)

        # 验证效果
        strength_buff = parser.get_effect('strength_buff')
        assert strength_buff is not None
        assert 'duration' in strength_buff
        assert 'modifiers' in strength_buff

        poison = parser.get_effect('poison')
        assert poison is not None
        assert 'duration' in poison
        assert 'damage_per_turn' in poison

        healing = parser.get_effect('healing')
        assert healing is not None
        assert 'healing' in healing
