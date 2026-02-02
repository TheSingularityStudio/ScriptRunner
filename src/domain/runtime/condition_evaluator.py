"""
ScriptRunner 的条件评估器。
处理选择和其他条件逻辑的条件评估。
"""

from typing import Optional
import re
from .interfaces import IConditionEvaluator
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class ConditionEvaluator(IConditionEvaluator):
    """评估选择和其他条件逻辑的条件。"""

    def __init__(self, state_manager, parser=None):
        self.state = state_manager
        self.parser = parser

    def evaluate_condition(self, condition: Optional[str]) -> bool:
        """
        根据当前游戏状态评估条件字符串。

        此方法支持各种条件类型，包括相等检查，
        标志检查、数字比较、变量存在性、对象状态检查，以及逻辑运算符（and、or）。
        条件使用一种简单的 DSL 语法来进行游戏逻辑评估。

        Args:
            condition: 要评估的条件字符串。如果为 None 或为空，则返回 True。

        Returns:
            如果条件满足则为 True，否则为 False。不支持的条件会记录警告，并返回 True 作为后备。

        Supported condition formats:
            - 相等："variable == value" 或 "variable == "string""
            - 标志检查："has_flag(flag_name)" 或 "has_flag("flag_name")"
            - 数值比较："variable > 5"，"variable < 10"，"variable >= 0"，"variable <= 100"
            - 否定："!flag_name"（检查标志是否未设置）
            - 变量存在性："exists:variable_name"
            - 对象状态："object_name.state_name"（例如，"door.open"）
            - 逻辑运算符："condition1 and condition2"，"condition1 or condition2"

        Note:
            - 字符串值应使用双引号括起来
            - 变量值从游戏状态中获取
            - 对象状态检查需要解析器和当前场景上下文
            - 逻辑运算符的优先级低于比较运算符
            - 不支持的条件会记录日志，但返回 True 以避免阻碍游戏进行。
        """
        if not condition:
            # 空条件被视为始终为 True（无限制）
            return True

        logger.debug(f"Evaluating condition: {condition}")

        # 先处理逻辑运算符（优先级较低）
        if ' and ' in condition:
            parts = condition.split(' and ', 1)
            return self.evaluate_condition(parts[0].strip()) and self.evaluate_condition(parts[1].strip())
        elif ' or ' in condition:
            parts = condition.split(' or ', 1)
            return self.evaluate_condition(parts[0].strip()) or self.evaluate_condition(parts[1].strip())

        # 相等比较: variable == value
        if '==' in condition:
            left, right = condition.split('==', 1)
            left = left.strip()
            right = right.strip()

            # 从字符串字面量中移除引号
            if right.startswith('"') and right.endswith('"'):
                right = right[1:-1]

            left_value = self._get_value(left)
            return str(left_value) == right

        # 标志存在检查: has_flag(flag_name)
        elif 'has_flag' in condition:
            # Extract flag name from function call syntax
            flag = condition.split('(', 1)[1].rstrip(')')
            return self.state.has_flag(flag.strip('"\'')) 

        # 物品存在性检查: has_item(item_name)
        elif 'has_item' in condition:
            # 从函数调用语法中提取物品名称
            item = condition.split('(', 1)[1].rstrip(')')
            inventory = self.state.get_variable('inventory', [])
            return item.strip('"\'' ) in inventory

        # 数值比较运算符（按长度顺序检查以避免冲突）
        elif '>=' in condition:
            left, right = condition.split('>=', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            right_value = self._get_value(right)
            return float(left_value) >= float(right_value)

        elif '<=' in condition:
            left, right = condition.split('<=', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            right_value = self._get_value(right)
            return float(left_value) <= float(right_value)

        elif '>' in condition:
            left, right = condition.split('>', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            right_value = self._get_value(right)
            return float(left_value) > float(right_value)

        elif '<' in condition:
            left, right = condition.split('<', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            right_value = self._get_value(right)
            return float(left_value) < float(right_value)

        # 否定运算符: !flag_name
        elif condition.startswith('!'):
            flag = condition[1:].strip()
            return not self.state.has_flag(flag)

        # 变量存在性检查: exists:variable_name
        elif condition.startswith('exists:'):
            var_name = condition[7:].strip()
            return var_name in self.state.variables

        # 使用点表示法进行对象状态检查: object.state
        elif '.' in condition:
            parts = condition.split('.', 1)
            if len(parts) == 2:
                obj_name, state_name = parts
                return self._check_object_state(obj_name.strip(), state_name.strip())

        # 不支持的复杂条件的备用方案
        logger.warning(f"Complex condition not fully supported: {condition}")
        return True

    def _get_value(self, expression: str):
        """从表达式中获取值（变量或字面量）。"""
        expression = expression.strip()
        if expression in self.state.variables:
            return self.state.variables[expression]
        return expression

    def _check_object_state(self, obj_name: str, state_name: str) -> bool:
        """检查对象是否具有指定的状态。"""
        if not self.parser:
            logger.warning(f"Parser not available for object state check: {obj_name}.{state_name}")
            return False

        # 获取当前场景
        current_scene_id = self.state.get_current_scene()
        if not current_scene_id:
            return False

        scene_data = self.parser.get_scene(current_scene_id)
        if not scene_data:
            return False

        # 检查场景中的对象
        objects = scene_data.get('objects', [])
        for obj in objects:
            if isinstance(obj, dict) and obj.get('ref') == obj_name:
                # 检查生成条件
                spawn_condition = obj.get('spawn_condition')
                if spawn_condition and not self.evaluate_condition(spawn_condition):
                    continue  # 对象未生成

                # 如果状态是'present'，表示对象存在
                if state_name == 'present':
                    return True

                # 检查对象的状态
                obj_def = self.parser.get_object(obj_name)
                if obj_def:
                    states = obj_def.get('states', [])
                    for state in states:
                        if state.get('name') == state_name:
                            value = state.get('value', False)
                            return bool(value)

        return False
