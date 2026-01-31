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

        # 对象状态检查 (dot notation)
        elif '.' in condition:
            parts = condition.split('.', 1)
            if len(parts) == 2:
                obj_name, state_name = parts
                return self._check_object_state(obj_name.strip(), state_name.strip())

        # 对于复杂条件默认设置为真
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
