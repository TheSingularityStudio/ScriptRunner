"""
ScriptRunner 的条件评估器。
处理选择和其他条件逻辑的条件评估。
"""

from typing import Optional
import re
from ..logging.logger import get_logger

logger = get_logger(__name__)


class ConditionEvaluator:
    """评估选择和其他条件逻辑的条件。"""

    def __init__(self, state_manager):
        self.state = state_manager

    def evaluate_condition(self, condition: Optional[str]) -> bool:
        """评估条件字符串。"""
        if not condition:
            return True

        logger.debug(f"Evaluating condition: {condition}")

        # 简单平等
        if '==' in condition:
            left, right = condition.split('==', 1)
            left = left.strip()
            right = right.strip()

            if right.startswith('"') and right.endswith('"'):
                right = right[1:-1]

            left_value = self._get_value(left)
            return str(left_value) == right

        # 旗标检查
        elif 'has_flag' in condition:
            flag = condition.split('(', 1)[1].rstrip(')')
            return self.state.has_flag(flag.strip('"\'')) 

        # 数字比较
        elif '>' in condition:
            left, right = condition.split('>', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            return float(left_value) > float(right)

        elif '<' in condition:
            left, right = condition.split('<', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            return float(left_value) < float(right)

        elif '>=' in condition:
            left, right = condition.split('>=', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            return float(left_value) >= float(right)

        elif '<=' in condition:
            left, right = condition.split('<=', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            return float(left_value) <= float(right)

        # 否定
        elif condition.startswith('!'):
            flag = condition[1:].strip()
            return not self.state.has_flag(flag)

        # 变量存在
        elif condition.startswith('exists:'):
            var_name = condition[7:].strip()
            return var_name in self.state.variables

        # 对于复杂条件默认设置为真
        logger.warning(f"Complex condition not fully supported: {condition}")
        return True

    def _get_value(self, expression: str):
        """从表达式中获取值（变量或字面量）。"""
        expression = expression.strip()
        if expression in self.state.variables:
            return self.state.variables[expression]
        return expression
