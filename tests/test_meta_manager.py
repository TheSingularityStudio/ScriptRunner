"""
Unit tests for MetaManager.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.runtime.meta_manager import MetaManager


class TestMetaManager:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.mock_condition_evaluator = Mock()
        self.manager = MetaManager(
            self.mock_parser,
            self.mock_state_manager,
            self.mock_condition_evaluator
        )

    def test_initialization(self):
        """测试 MetaManager 初始化。"""
        assert self.manager.parser == self.mock_parser
        assert self.manager.state == self.mock_state_manager
        assert self.manager.condition_evaluator == self.mock_condition_evaluator
        assert self.manager.macros == {}
        assert self.manager.dynamic_scripts == {}

    def test_load_meta_data(self):
        """测试加载元数据。"""
        meta_data = {
            'macros': {'health_check': 'health > 0'},
            'dynamic_scripts': {'combat_scene': {'template': 'You fight a {enemy}'}}
        }
        self.mock_parser.get_meta_data.return_value = meta_data
        self.manager.load_meta_data()
        assert 'health_check' in self.manager.macros
        assert 'combat_scene' in self.manager.dynamic_scripts

    def test_evaluate_macro_exists(self):
        """测试评估存在的宏。"""
        self.manager.macros['test_macro'] = 'strength > 10'
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        result = self.manager.evaluate_macro('test_macro')
        assert result is True
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('strength > 10')

    def test_evaluate_macro_with_parameters(self):
        """测试评估带参数的宏。"""
        self.manager.macros['level_check'] = 'player_level >= {min_level}'
        self.mock_condition_evaluator.evaluate_condition.return_value = True
        result = self.manager.evaluate_macro('level_check', min_level='5')
        assert result is True
        self.mock_condition_evaluator.evaluate_condition.assert_called_with('player_level >= 5')

    def test_evaluate_macro_not_exists(self):
        """测试评估不存在的宏。"""
        result = self.manager.evaluate_macro('nonexistent')
        assert result is False

    def test_evaluate_macro_error(self):
        """测试评估宏时发生错误。"""
        self.manager.macros['bad_macro'] = 'invalid condition'
        self.mock_condition_evaluator.evaluate_condition.side_effect = Exception('Parse error')
        result = self.manager.evaluate_macro('bad_macro')
        assert result is False

    def test_generate_dynamic_script_exists(self):
        """测试生成存在的动态脚本。"""
        self.manager.dynamic_scripts['test_script'] = {
            'template': 'Hello {name}, welcome to {place}!'
        }
        with patch('yaml.safe_load', return_value={'message': 'Hello John, welcome to town!'}):
            result = self.manager.generate_dynamic_script('test_script', name='John', place='town')
        assert result is not None

    def test_generate_dynamic_script_with_parameters(self):
        """测试生成带参数的动态脚本。"""
        self.manager.dynamic_scripts['quest'] = {
            'template': 'Find the {item} in the {location}.'
        }
        with patch('yaml.safe_load', return_value={'quest': 'Find the sword in the forest.'}):
            result = self.manager.generate_dynamic_script('quest', item='sword', location='forest')
        assert result is not None

    def test_generate_dynamic_script_not_exists(self):
        """测试生成不存在的动态脚本。"""
        result = self.manager.generate_dynamic_script('nonexistent')
        assert result is None

    def test_generate_dynamic_script_error(self):
        """测试生成动态脚本时发生错误。"""
        self.manager.dynamic_scripts['bad_script'] = {
            'template': 'Invalid yaml: {unclosed'
        }
        with patch('yaml.safe_load', side_effect=Exception('YAML error')):
            result = self.manager.generate_dynamic_script('bad_script')
        assert result is None

    def test_get_macro_names(self):
        """测试获取宏名称列表。"""
        self.manager.macros = {'macro1': 'cond1', 'macro2': 'cond2'}
        result = self.manager.get_macro_names()
        assert set(result) == {'macro1', 'macro2'}

    def test_get_dynamic_script_names(self):
        """测试获取动态脚本名称列表。"""
        self.manager.dynamic_scripts = {'script1': {}, 'script2': {}}
        result = self.manager.get_dynamic_script_names()
        assert set(result) == {'script1', 'script2'}

    def test_has_macro_true(self):
        """测试检查宏存在。"""
        self.manager.macros['existing'] = 'condition'
        assert self.manager.has_macro('existing') is True

    def test_has_macro_false(self):
        """测试检查宏不存在。"""
        assert self.manager.has_macro('nonexistent') is False

    def test_has_dynamic_script_true(self):
        """测试检查动态脚本存在。"""
        self.manager.dynamic_scripts['existing'] = {}
        assert self.manager.has_dynamic_script('existing') is True

    def test_has_dynamic_script_false(self):
        """测试检查动态脚本不存在。"""
        assert self.manager.has_dynamic_script('nonexistent') is False
