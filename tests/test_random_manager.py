"""
Unit tests for RandomManager.
"""

import pytest
from unittest.mock import Mock, patch
from src.runtime.random_manager import RandomManager


class TestRandomManager:
    def setup_method(self):
        """设置测试方法。"""
        self.mock_parser = Mock()
        self.mock_state_manager = Mock()
        self.manager = RandomManager(
            self.mock_parser,
            self.mock_state_manager
        )

    def test_initialization(self):
        """测试 RandomManager 初始化。"""
        assert self.manager.parser == self.mock_parser
        assert self.manager.state == self.mock_state_manager
        assert self.manager.random_tables == {}

    def test_load_random_tables(self):
        """测试加载随机表。"""
        random_data = {'tables': {'treasure': {'entries': [{'item': 'gold', 'weight': 5}]}}}
        self.mock_parser.get_random_table_data.return_value = random_data
        self.manager.load_random_tables()
        assert 'treasure' in self.manager.random_tables

    def test_roll_random_range_single_value(self):
        """测试范围随机单个值。"""
        result = self.manager.roll_random_range('42')
        assert result == 42

    def test_roll_random_range_int_range(self):
        """测试整数范围随机。"""
        with patch('random.uniform', return_value=25.7):
            result = self.manager.roll_random_range('20-30')
        assert result == 25

    def test_roll_random_range_float_range(self):
        """测试浮点范围随机。"""
        with patch('random.uniform', return_value=2.5):
            result = self.manager.roll_random_range('1.0-4.0')
        assert result == 2.5

    def test_roll_random_range_invalid(self):
        """测试无效范围。"""
        result = self.manager.roll_random_range('invalid')
        assert result == 0

    def test_roll_weighted_table_not_found(self):
        """测试加权表不存在。"""
        result = self.manager.roll_weighted_table('nonexistent')
        assert result is None

    def test_roll_weighted_table_empty(self):
        """测试空加权表。"""
        self.manager.random_tables['empty'] = {'entries': []}
        result = self.manager.roll_weighted_table('empty')
        assert result is None

    @patch('random.uniform')
    def test_roll_weighted_table_success(self, mock_uniform):
        """测试加权表成功滚动。"""
        mock_uniform.return_value = 3
        self.manager.random_tables['treasure'] = {
            'entries': [
                {'item': 'gold', 'weight': 5},
                {'item': 'silver', 'weight': 3}
            ]
        }
        result = self.manager.roll_weighted_table('treasure')
        assert result in ['gold', 'silver']

    def test_generate_random_list_json(self):
        """测试JSON风格列表生成。"""
        with patch('random.sample', return_value=['apple', 'cherry']):
            result = self.manager.generate_random_list('["apple", "banana", "cherry"]', 2)
        assert result == ['apple', 'cherry']

    def test_generate_random_list_comma_separated(self):
        """测试逗号分隔列表生成。"""
        with patch('random.sample', return_value=['sword', 'shield']):
            result = self.manager.generate_random_list('sword, shield, potion', 2)
        assert result == ['sword', 'shield']

    def test_generate_random_list_all(self):
        """测试选择所有项目。"""
        result = self.manager.generate_random_list('["a", "b"]', 3)
        assert result == ['a', 'b']

    def test_generate_random_list_invalid(self):
        """测试无效列表（被视为单个项目）。"""
        result = self.manager.generate_random_list('invalid', 1)
        assert result == ['invalid']

    def test_generate_procedural_name_simple(self):
        """测试简单程序化名称生成。"""
        result = self.manager.generate_procedural_name('Dragon {name}', name='Firebreath')
        assert result == 'Dragon Firebreath'

    def test_generate_procedural_name_with_options(self):
        """测试带选项的程序化名称生成。"""
        with patch('random.choice', return_value='Red'):
            result = self.manager.generate_procedural_name('{Red|Blue|Green} Dragon')
        assert result == 'Red Dragon'

    def test_generate_procedural_name_invalid(self):
        """测试无效程序化名称。"""
        result = self.manager.generate_procedural_name('{invalid')
        assert result == '{invalid'

    def test_generate_random_event_combat(self):
        """测试生成战斗随机事件。"""
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = {'type': 'enemy_encounter', 'description': 'Enemies!'}
            result = self.manager.generate_random_event('combat')
        assert result['type'] == 'enemy_encounter'

    def test_generate_random_event_generic(self):
        """测试生成通用随机事件。"""
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = {'type': 'random_event', 'description': 'Something happened!'}
            result = self.manager.generate_random_event('generic')
        assert result['type'] == 'random_event'

    def test_generate_random_event_unknown_type(self):
        """测试未知类型随机事件。"""
        result = self.manager.generate_random_event('unknown')
        assert result is None

    def test_calculate_random_modifier(self):
        """测试计算随机修正值。"""
        with patch('random.random', return_value=0.5):
            result = self.manager.calculate_random_modifier(100, 0.1)
        assert isinstance(result, (int, float))

    def test_calculate_random_modifier_negative_base(self):
        """测试负数基础值的随机修正。"""
        with patch('random.random', return_value=0.0):
            result = self.manager.calculate_random_modifier(-10, 0.2)
        assert result < 0

    def test_shuffle_list(self):
        """测试列表随机打乱。"""
        original = [1, 2, 3, 4, 5]
        with patch('random.shuffle') as mock_shuffle:
            mock_shuffle.side_effect = lambda x: x.reverse()
            result = self.manager.shuffle_list(original)
        assert result == [5, 4, 3, 2, 1]
        assert original == [1, 2, 3, 4, 5]  # Original unchanged

    @patch('random.uniform')
    def test_pick_unique_items(self, mock_uniform):
        """测试选择不重复项目。"""
        mock_uniform.return_value = 2
        self.manager.random_tables['items'] = {
            'entries': [
                {'item': 'sword', 'weight': 5},
                {'item': 'shield', 'weight': 3},
                {'item': 'potion', 'weight': 2}
            ]
        }
        result = self.manager.pick_unique_items('items', 2)
        assert len(result) == 2
        assert all(item in ['sword', 'shield', 'potion'] for item in result)

    def test_pick_unique_items_exclude(self):
        """测试选择不重复项目并排除。"""
        self.manager.random_tables['items'] = {
            'entries': [
                {'item': 'sword', 'weight': 1},
                {'item': 'shield', 'weight': 1}
            ]
        }
        result = self.manager.pick_unique_items('items', 1, ['sword'])
        assert result == ['shield']

    def test_get_table_info_exists(self):
        """测试获取存在的表信息。"""
        table_info = {'entries': []}
        self.manager.random_tables['test'] = table_info
        result = self.manager.get_table_info('test')
        assert result == table_info

    def test_get_table_info_not_exists(self):
        """测试获取不存在的表信息。"""
        result = self.manager.get_table_info('nonexistent')
        assert result is None

    def test_list_tables(self):
        """测试列出表名称。"""
        self.manager.random_tables = {'table1': {}, 'table2': {}}
        result = self.manager.list_tables()
        assert set(result) == {'table1', 'table2'}
