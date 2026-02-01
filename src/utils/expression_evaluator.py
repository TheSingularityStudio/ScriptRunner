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
        Safely evaluate a mathematical or logical expression with limited context.

        Args:
            expression: The expression string to evaluate
            context: Dictionary containing variables available in the expression

        Returns:
            The result of the expression evaluation, or 0 if evaluation fails
        """
        # Create a safe context that allows dictionary access via dot notation
        class DotDict(dict):
            """Dictionary subclass that allows attribute-style access for dot notation."""
            def __getattr__(self, key):
                return self[key]

        def is_safe_value(v):
            """Check if a value is safe to include in the evaluation context."""
            if isinstance(v, (int, float, bool)):
                return True
            elif isinstance(v, dict):
                # Ensure all nested values are also safe
                return all(isinstance(sub_v, (int, float, bool)) for sub_v in v.values())
            return False

        safe_context = {}
        for k, v in context.items():
            if isinstance(v, dict):
                # Wrap dictionaries to support dot notation (e.g., player.health)
                safe_context[k] = DotDict(v)
            elif is_safe_value(v):
                safe_context[k] = v

        # Add random function for dice rolls and similar mechanics
        import random
        safe_context['random'] = random.randint

        # Evaluate the expression in the restricted environment
        try:
            return eval(expression, {"__builtins__": {}}, safe_context)
        except (NameError, TypeError, SyntaxError, ZeroDivisionError) as e:
            # Log expected evaluation errors (invalid syntax, undefined variables, etc.)
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return 0
        except Exception as e:
            # Catch any unexpected errors during evaluation
            logger.error(f"Unexpected error evaluating expression '{expression}': {e}")
            return 0