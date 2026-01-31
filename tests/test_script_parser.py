"""
Unit tests for ScriptParser.
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch
from src.parser.parser import ScriptParser


class TestScriptParser:
    def test_initialization(self):
        """测试 ScriptParser 初始化。"""
        parser = ScriptParser()
        assert parser.script_data == {}
        assert parser.objects == {}
        assert parser.events == {}
        assert parser.command_parser_config == {}
        assert parser.random_tables == {}
        assert parser.state_machines == {}
        assert parser.effects == {}

    def test_load_script_file_not_found(self):
        """测试加载不存在的脚本文件。"""
        parser = ScriptParser()
        with pytest.raises(FileNotFoundError):
            parser.load_script("nonexistent.yaml")

    def test_load_traditional_script(self):
        """测试加载传统格式脚本。"""
        script_content = {
            'scenes': {
                'start': {
                    'text': 'Welcome to the game!',
                    'choices': [
                        {'text': 'Start game', 'next': 'room1'}
                    ]
                }
            },
            'start_scene': 'start'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            result = parser.load_script(script_file)
            assert result == script_content
            assert parser.script_data == script_content
        finally:
            os.unlink(script_file)

    def test_load_dsl_script(self):
        """测试加载DSL格式脚本。"""
        script_content = {
            'game': {'title': 'Test Game'},
            'world': {'start': 'start_scene'},
            'define_object': {
                'sword': {'type': 'weapon', 'damage': 10}
            },
            'effects': {
                'buff': {'type': 'temporary', 'duration': 5}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            result = parser.load_script(script_file)
            assert result == script_content
            assert 'sword' in parser.objects
            assert 'buff' in parser.effects
        finally:
            os.unlink(script_file)

    def test_validate_traditional_script_missing_scenes(self):
        """测试传统脚本缺少scenes字段。"""
        script_content = {'start_scene': 'start'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            with pytest.raises(ValueError, match="传统脚本必须包含'scenes'或'locations'部分"):
                parser.load_script(script_file)
        finally:
            os.unlink(script_file)

    def test_validate_dsl_script_missing_game(self):
        """测试DSL脚本缺少game字段。"""
        script_content = {
            'world': {'start': 'start'},
            'define_object': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            with pytest.raises(ValueError, match="DSL脚本必须包含'game'部分"):
                parser.load_script(script_file)
        finally:
            os.unlink(script_file)

    def test_get_scene_traditional(self):
        """测试获取传统格式场景。"""
        script_content = {
            'scenes': {
                'start': {'text': 'Hello'},
                'room1': {'text': 'Room'}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)
            assert parser.get_scene('start') == {'text': 'Hello'}
            assert parser.get_scene('nonexistent') == {}
        finally:
            os.unlink(script_file)

    def test_get_scene_dsl(self):
        """测试获取DSL格式场景。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'start'},
            'define_object': {},  # Add DSL key to trigger DSL mode
            'locations': {
                'start': {'description': 'Start location'}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)
            assert parser.get_scene('start') == {'description': 'Start location'}
        finally:
            os.unlink(script_file)

    def test_get_start_scene_dsl(self):
        """测试获取DSL起始场景。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'custom_start'},
            'define_object': {}  # Add DSL key to trigger DSL mode
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)
            assert parser.get_start_scene() == 'custom_start'
        finally:
            os.unlink(script_file)

    def test_get_start_scene_traditional(self):
        """测试获取传统起始场景。"""
        script_content = {
            'scenes': {'start': {'text': 'Start scene'}},
            'start_scene': 'custom_start'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)
            assert parser.get_start_scene() == 'custom_start'
        finally:
            os.unlink(script_file)

    def test_get_object(self):
        """测试获取DSL对象。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'start'},
            'define_object': {
                'sword': {'type': 'weapon', 'damage': 10},
                'shield': {'type': 'armor', 'defense': 5}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)
            assert parser.get_object('sword') == {'type': 'weapon', 'damage': 10}
            assert parser.get_object('nonexistent') == {}
        finally:
            os.unlink(script_file)

    def test_parse_player_command_with_config(self):
        """测试带配置的玩家命令解析。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'start'},
            'command_parser': {
                'verbs': {
                    'take': {'patterns': ['take', 'get', 'pick up']},
                    'use': {'patterns': ['use', 'utilize']}
                },
                'nouns': {
                    'dynamic_match': {'sword': 'weapon', 'key': 'item'}
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)

            result = parser.parse_player_command('take sword')
            assert result['action'] == 'take'
            assert result['target'] == 'sword'

            result = parser.parse_player_command('use key')
            assert result['action'] == 'use'
            assert result['target'] == 'key'

            result = parser.parse_player_command('unknown command')
            assert result['action'] == 'unknown'
        finally:
            os.unlink(script_file)

    def test_parse_player_command_without_config(self):
        """测试无配置的玩家命令解析。"""
        parser = ScriptParser()
        result = parser.parse_player_command('some input')
        assert result == {'action': 'unknown', 'target': 'some input'}

    def test_validate_dsl_start_scene_exists(self):
        """测试DSL起始场景存在性验证。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'nonexistent_scene'},
            'define_object': {},
            'locations': {'existing_scene': {'description': 'Test'}}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            with pytest.raises(ValueError, match="DSL脚本的起始场景'nonexistent_scene'在脚本中不存在"):
                parser.load_script(script_file)
        finally:
            os.unlink(script_file)

    def test_validate_object_structure(self):
        """测试DSL对象结构验证。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'start'},
            'define_object': {
                'invalid_obj': 'not_a_dict'  # Invalid: not a dict
            },
            'locations': {'start': {'description': 'Start'}}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            with pytest.raises(ValueError, match="DSL对象'invalid_obj'必须是字典且包含'type'字段"):
                parser.load_script(script_file)
        finally:
            os.unlink(script_file)

    def test_traditional_script_with_locations(self):
        """测试传统脚本使用locations字段。"""
        script_content = {
            'locations': {
                'start': {'description': 'Start location'},
                'room1': {'text': 'Room 1'}
            },
            'start_scene': 'start'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            result = parser.load_script(script_file)
            assert result == script_content
            assert parser.get_scene('start') == {'description': 'Start location'}
        finally:
            os.unlink(script_file)

    def test_parse_player_command_multi_word_target(self):
        """测试多词目标的命令解析。"""
        script_content = {
            'game': {'title': 'Test'},
            'world': {'start': 'start'},
            'command_parser': {
                'verbs': {
                    'attack': {'patterns': ['attack', 'fight']},
                },
                'nouns': {}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            parser.load_script(script_file)

            result = parser.parse_player_command('attack the goblin')
            assert result['action'] == 'attack'
            assert result['target'] == 'the goblin'
        finally:
            os.unlink(script_file)
