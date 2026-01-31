"""
ScriptRunner 的随机管理器。
处理 DSL 随机系统的加权随机选择、范围随机和程序化生成。
"""

from typing import Dict, Any, List, Optional, Union
import random
import re
from ..logging.logger import get_logger

logger = get_logger(__name__)


class RandomManager:
    """管理游戏随机系统，包括加权随机和程序化生成。"""

    def __init__(self, parser, state_manager):
        self.parser = parser
        self.state = state_manager

        # 随机表存储
        self.random_tables: Dict[str, Dict[str, Any]] = {}

        logger.info("RandomManager initialized")

    def load_random_tables(self):
        """从解析器加载随机表数据。"""
        try:
            random_data = self.parser.get_random_table_data()
            if random_data:
                self.random_tables = random_data.get('tables', {})
                logger.info(f"Loaded {len(self.random_tables)} random tables")

        except Exception as e:
            logger.warning(f"Failed to load random tables: {e}")

    def roll_random_range(self, range_str: str) -> Union[int, float]:
        """从范围字符串中生成随机数，如 '20-40' 或 '1.5-3.0'。"""
        try:
            if '-' not in range_str:
                # 单个值
                return float(range_str) if '.' in range_str else int(range_str)

            parts = range_str.split('-')
            if len(parts) != 2:
                raise ValueError(f"Invalid range format: {range_str}")

            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())

            if min_val > max_val:
                min_val, max_val = max_val, min_val

            # 生成随机数
            result = random.uniform(min_val, max_val)

            # 如果都是整数，返回整数
            if '.' not in range_str:
                result = int(result)

            return result

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing random range '{range_str}': {e}")
            return 0

    def roll_weighted_table(self, table_name: str) -> Optional[str]:
        """从加权随机表中选择一个条目。"""
        if table_name not in self.random_tables:
            logger.warning(f"Random table '{table_name}' not found")
            return None

        table = self.random_tables[table_name]
        entries = table.get('entries', [])

        if not entries:
            logger.warning(f"Random table '{table_name}' has no entries")
            return None

        # 计算总权重
        total_weight = 0
        for entry in entries:
            weight = entry.get('weight', 1)
            total_weight += weight

        if total_weight <= 0:
            logger.warning(f"Random table '{table_name}' has invalid weights")
            return None

        # 加权随机选择
        roll = random.uniform(0, total_weight)
        current_weight = 0

        for entry in entries:
            current_weight += entry.get('weight', 1)
            if roll <= current_weight:
                return entry.get('item', '')

        # 备用选择（不应该到达这里）
        return entries[0].get('item', '')

    def generate_random_list(self, list_expr: str, count: int = 1) -> List[str]:
        """从列表表达式生成随机选择，如 '["apple", "banana", "cherry"]'。"""
        try:
            # 解析列表表达式
            if list_expr.startswith('[') and list_expr.endswith(']'):
                # JSON风格列表
                import json
                items = json.loads(list_expr)
            else:
                # 逗号分隔的字符串
                items = [item.strip() for item in list_expr.split(',')]

            if not items:
                return []

            # 随机选择指定数量的项目
            if count >= len(items):
                return items
            else:
                return random.sample(items, count)

        except Exception as e:
            logger.error(f"Error parsing random list '{list_expr}': {e}")
            return []

    def generate_procedural_name(self, template: str, **replacements) -> str:
        """根据模板生成程序化名称。"""
        try:
            result = template

            # 替换变量
            for key, value in replacements.items():
                result = result.replace(f'{{{key}}}', str(value))

            # 处理随机选择
            while '{' in result and '}' in result:
                start = result.find('{')
                end = result.find('}', start)
                if end == -1:
                    break

                option_str = result[start+1:end]
                if '|' in option_str:
                    # 随机选择选项
                    options = [opt.strip() for opt in option_str.split('|')]
                    choice = random.choice(options)
                    result = result[:start] + choice + result[end+1:]
                else:
                    # 可能是未替换的变量，跳过
                    break

            return result

        except Exception as e:
            logger.error(f"Error generating procedural name from template '{template}': {e}")
            return template

    def generate_random_event(self, event_type: str = 'generic') -> Optional[Dict[str, Any]]:
        """生成随机事件。"""
        # 这里可以扩展为基于事件类型的随机事件生成
        # 例如，根据当前游戏状态生成相关事件

        event_templates = {
            'combat': [
                {'type': 'enemy_encounter', 'description': '你遇到了一群野兽！'},
                {'type': 'ambush', 'description': '突然从暗处跳出敌人！'},
                {'type': 'trap', 'description': '你触发了一个陷阱！'}
            ],
            'exploration': [
                {'type': 'treasure', 'description': '你发现了一个隐藏的宝藏！'},
                {'type': 'clue', 'description': '你找到了一条重要线索。'},
                {'type': 'shortcut', 'description': '你发现了一条捷径。'}
            ],
            'social': [
                {'type': 'merchant', 'description': '一个商人向你走来。'},
                {'type': 'beggar', 'description': '一个乞丐向你求助。'},
                {'type': 'rumor', 'description': '你听到了一些传闻。'}
            ]
        }

        templates = event_templates.get(event_type, event_templates['generic'])
        if templates:
            return random.choice(templates)

        return None

    def calculate_random_modifier(self, base_value: Union[int, float], variance: float = 0.1) -> Union[int, float]:
        """计算带随机变异的数值。"""
        try:
            variation = base_value * variance * (random.random() * 2 - 1)  # -variance 到 +variance
            result = base_value + variation

            # 确保不为负数（除非原始值就是负数）
            if base_value > 0 and result < 0:
                result = 0

            return result

        except Exception as e:
            logger.error(f"Error calculating random modifier for {base_value}: {e}")
            return base_value

    def shuffle_list(self, items: List[Any]) -> List[Any]:
        """随机打乱列表顺序。"""
        result = items.copy()
        random.shuffle(result)
        return result

    def pick_unique_items(self, table_name: str, count: int, exclude: List[str] = None) -> List[str]:
        """从随机表中选择多个不重复的条目。"""
        if table_name not in self.random_tables:
            return []

        table = self.random_tables[table_name]
        entries = table.get('entries', [])

        if not entries:
            return []

        # 过滤排除的项目
        available_entries = [e for e in entries if e.get('item', '') not in (exclude or [])]

        if len(available_entries) <= count:
            return [e.get('item', '') for e in available_entries]

        # 加权随机选择多个不重复条目
        selected = []
        remaining_entries = available_entries.copy()

        for _ in range(min(count, len(remaining_entries))):
            if not remaining_entries:
                break

            # 计算剩余条目的总权重
            total_weight = sum(e.get('weight', 1) for e in remaining_entries)

            if total_weight <= 0:
                # 如果权重无效，使用均匀随机
                choice = random.choice(remaining_entries)
            else:
                # 加权随机选择
                roll = random.uniform(0, total_weight)
                current_weight = 0

                for entry in remaining_entries:
                    current_weight += entry.get('weight', 1)
                    if roll <= current_weight:
                        choice = entry
                        break
                else:
                    choice = remaining_entries[0]

            selected.append(choice.get('item', ''))
            remaining_entries.remove(choice)

        return selected

    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取随机表信息。"""
        return self.random_tables.get(table_name)

    def list_tables(self) -> List[str]:
        """列出所有随机表名称。"""
        return list(self.random_tables.keys())
