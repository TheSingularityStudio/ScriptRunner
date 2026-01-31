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
        Evaluate a condition string against the current game state.

        This method supports various condition types including equality checks,
        flag checks, numeric comparisons, variable existence, and object state checks.
        Conditions use a simple DSL syntax for game logic evaluation.

        Args:
            condition: The condition string to evaluate. If None or empty, returns True.

        Returns:
            True if the condition is met, False otherwise. Unsupported conditions
            log a warning and return True as fallback.

        Supported condition formats:
            - Equality: "variable == value" or "variable == "string""
            - Flag checks: "has_flag(flag_name)" or "has_flag("flag_name")"
            - Numeric comparisons: "variable > 5", "variable < 10", "variable >= 0", "variable <= 100"
            - Negation: "!flag_name" (checks if flag is NOT set)
            - Variable existence: "exists:variable_name"
            - Object state: "object_name.state_name" (e.g., "door.open")

        Note:
            - String values should be enclosed in double quotes
            - Variable values are retrieved from game state
            - Object state checks require a parser and current scene context
            - Unsupported conditions are logged but return True to avoid blocking gameplay
        """
        if not condition:
            # Empty conditions are considered always true (no restriction)
            return True

        logger.debug(f"Evaluating condition: {condition}")

        # Equality comparison: variable == value
        if '==' in condition:
            left, right = condition.split('==', 1)
            left = left.strip()
            right = right.strip()

            # Remove quotes from string literals
            if right.startswith('"') and right.endswith('"'):
                right = right[1:-1]

            left_value = self._get_value(left)
            return str(left_value) == right

        # Flag existence check: has_flag(flag_name)
        elif 'has_flag' in condition:
            # Extract flag name from function call syntax
            flag = condition.split('(', 1)[1].rstrip(')')
            return self.state.has_flag(flag.strip('"\'')) 

        # Numeric comparison operators
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

        # Negation operator: !flag_name
        elif condition.startswith('!'):
            flag = condition[1:].strip()
            return not self.state.has_flag(flag)

        # Variable existence check: exists:variable_name
        elif condition.startswith('exists:'):
            var_name = condition[7:].strip()
            return var_name in self.state.variables

        # Object state check using dot notation: object.state
        elif '.' in condition:
            parts = condition.split('.', 1)
            if len(parts) == 2:
                obj_name, state_name = parts
                return self._check_object_state(obj_name.strip(), state_name.strip())

        # Fallback for unsupported complex conditions
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
