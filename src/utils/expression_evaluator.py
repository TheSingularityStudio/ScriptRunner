"""
ScriptRunner 表达式评估器工具模块。
提供安全的数学和逻辑表达式评估功能。
"""

from typing import Any, Dict
from ..infrastructure.logger import get_logger

logger = get_logger(__name__)


class ExpressionEvaluator:
    """表达式评估器，提供安全的表达式评估。"""

    @staticmethod
    def evaluate_expression(expression: str, context: Dict[str, Any]) -> Any:
        """
        在有限的上下文中安全地评估数学或逻辑表达式。

        Args:
            expression: 要计算的表达式字符串
            context: 包含表达式中可用变量的字典

        Returns:
            表达式计算的结果，如果计算失败则为 0
        """
        # 如果存在，去掉大括号（用于表示变量替换）
        expression = expression.strip('{}')

        # 创建一个允许通过点符号访问字典的安全环境
        class DotDict(dict):
            """字典子类，允许使用点符号进行属性式访问。"""
            def __getattr__(self, key):
                return self[key]

        def is_safe_value(v):
            """检查一个值是否可以安全地包含在评估上下文中。"""
            if isinstance(v, (int, float, bool)):
                return True
            elif isinstance(v, dict):
                # 确保所有嵌套的值也安全
                return all(isinstance(sub_v, (int, float, bool)) for sub_v in v.values())
            return False

        safe_context = {}
        for k, v in context.items():
            if isinstance(v, dict):
                # 封装字典以支持点符号访问（例如，player.health）
                safe_context[k] = DotDict(v)
            elif is_safe_value(v):
                safe_context[k] = v

        # 为掷骰子和类似机制添加随机功能
        import random
        safe_context['random'] = random.randint

        # 定义安全的内置函数
        safe_builtins = {
            'max': max,
            'min': min,
            'abs': abs,
            'round': round,
            'int': int,
            'float': float,
            'bool': bool,
            'str': str,
        }

        # 在受限环境中求值该表达式
        try:
            return eval(expression, {"__builtins__": safe_builtins}, safe_context)
        except (NameError, TypeError, SyntaxError, ZeroDivisionError) as e:
            # 记录预期的评估错误（无效语法、未定义变量等）
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return 0
        except Exception as e:
            # 在评估过程中捕获任何意外错误
            logger.error(f"Unexpected error evaluating expression '{expression}': {e}")
            return 0
