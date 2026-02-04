"""
Unit tests for ScriptParser.
"""

import pytest
import tempfile
import os
import yaml
from src.domain.parser.parser import ScriptParser


class TestScriptParser:
    def test_initialization(self):
        """测试 ScriptParser 初始化。"""
        parser = ScriptParser()
        assert parser.script_data == {}

    def test_load_script_file_not_found(self):
        """测试加载不存在的脚本文件。"""
        parser = ScriptParser()
        with pytest.raises(FileNotFoundError):
            parser.load_script("nonexistent.yaml")

    def test_load_script_with_variables_actions_events(self):
        """测试加载包含variables、actions、events的脚本。"""
        script_content = {
            'name': 'Test Script with Variables and Events',
            'variables': {'health': 100, 'score': 0},
            'actions': {
                'greet': {
                    'commands': [{'type': 'print', 'message': 'Hello!'}]
                }
            },
            'events': {
                'on_start': [{'type': 'call_action', 'action': 'greet'}]
            }
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

    def test_load_script_without_expected_keys(self):
        """测试加载不包含预期键的脚本（应发出警告但不失败）。"""
        script_content = {
            'name': 'Minimal Script',
            'actions': {
                'do_nothing': {
                    'commands': [{'type': 'print', 'message': 'Nothing'}]
                }
            },
            'events': {
                'on_start': [{'type': 'call_action', 'action': 'do_nothing'}]
            }
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

    def test_validate_script_invalid_format(self):
        """测试脚本格式验证 - 无效格式。"""
        script_content = "not a dict"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(script_content, f)
            script_file = f.name

        try:
            parser = ScriptParser()
            with pytest.raises(ValueError, match="Script must be a dictionary"):
                parser.load_script(script_file)
        finally:
            os.unlink(script_file)

    def test_create_script_object(self):
        """测试创建脚本对象。"""
        script_data = {
            'name': 'Test Object Creation',
            'variables': {'counter': 0},
            'actions': {
                'increment': {
                    'commands': [{'type': 'set_variable', 'name': 'counter', 'value': 1}]
                }
            },
            'events': {}
        }

        parser = ScriptParser()
        script_object = parser.create_script_object(script_data)

        # Verify the script object was created
        assert script_object is not None
        assert script_object.get_variable('counter') == 0
