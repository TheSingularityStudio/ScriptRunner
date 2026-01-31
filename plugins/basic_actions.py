"""
Basic Actions Plugin for ScriptRunner.
Provides common game actions like attack and search.
"""

from typing import Dict, Any, List, Callable
from ..src.infrastructure.plugin_interface import ActionPlugin
from ..src.infrastructure.logger import get_logger

logger = get_logger(__name__)


class BasicActionsPlugin(ActionPlugin):
    """Basic actions plugin providing attack and search functionality."""

    @property
    def name(self) -> str:
        return "BasicActions"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        logger.info("BasicActions plugin initialized")
        return True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        logger.info("BasicActions plugin shutdown")

    def get_actions(self) -> Dict[str, Callable]:
        """Return the actions provided by this plugin."""
        return {
            'attack_target': self._execute_attack,
            'search_location': self._execute_search,
        }

    def _execute_attack(self, parser, state, condition_evaluator, target: str) -> List[str]:
        """Execute attack command and return messages."""
        messages = []
        # Get target object
        target_obj = parser.get_object(target)
        if not target_obj:
            logger.warning(f"Attack target not found: {target}")
            return messages

        target_attrs = target_obj.get('attributes', {})
        behaviors = target_obj.get('behaviors', {})
        attack_behavior = behaviors.get('attack', {})

        # Get combat attributes from config
        combat_attributes = attack_behavior.get('combat_attributes', ['strength', 'agility', 'defense', 'health'])
        player_attrs = {}
        for attr in combat_attributes:
            player_attrs[attr] = state.get_variable(attr, 0)

        # Calculate hit chance
        hit_chance_expr = attack_behavior.get('hit_chance', '0.5')
        context = {**player_attrs, **target_attrs}
        # Add player. prefixed variables
        context.update({f'player.{k}': v for k, v in player_attrs.items()})
        # Add player and target dicts for dot notation access
        context['player'] = player_attrs
        context['target'] = target_attrs
        hit_chance = self._evaluate_expression(hit_chance_expr, context)

        import random
        if random.random() < hit_chance:
            # Hit
            damage_expr = attack_behavior.get('damage', '10')
            damage = self._evaluate_expression(damage_expr, context)

            # Apply damage to target
            health_attr = attack_behavior.get('health_attribute', 'health')
            states = target_obj.get('states', [])
            for state in states:
                if state['name'] == health_attr:
                    state['value'] = max(0, state['value'] - damage)
                    break

            # Success message
            success_msg = attack_behavior.get('success', '你击中了{target}，造成{damage}点伤害！')
            success_msg = success_msg.replace('{target}', target).replace('{damage}', str(damage))
            messages.append(success_msg)
            logger.debug(success_msg)
        else:
            # Miss
            failure_msg = attack_behavior.get('failure', '你没能打中{target}')
            failure_msg = failure_msg.replace('{target}', target)
            messages.append(failure_msg)
            logger.debug(failure_msg)

        # Counter attack
        counter_msg = attack_behavior.get('counter', '')
        if counter_msg:
            messages.append(counter_msg)
            logger.debug(counter_msg)
            # Counter damage from config, default 5
            counter_damage = attack_behavior.get('counter_damage', 5)
            player_health_attr = attack_behavior.get('player_health_attribute', 'health')
            player_health = state.get_variable(player_health_attr, 100)
            state.set_variable(player_health_attr, max(0, player_health - counter_damage))
            counter_damage_msg = attack_behavior.get('counter_damage_msg', '你受到了{counter_damage}点反击伤害！')
            counter_damage_msg = counter_damage_msg.replace('{counter_damage}', str(counter_damage))
            messages.append(counter_damage_msg)
            logger.debug(f"Player took {counter_damage} counter damage")
        return messages

    def _execute_search(self, parser, state, condition_evaluator, location: str) -> List[str]:
        """Execute search command and return messages."""
        messages = []
        logger.info(f"Searching {location}...")

        # Dynamically build search table name, e.g. {location}_search
        table_name = f"{location}_search"
        table = parser.get_random_table(table_name)
        if table:
            messages.extend(self._execute_roll_table(parser, table_name))
        else:
            msg = f"No items found while searching {location}."
            messages.append(msg)
            logger.info(msg)
        return messages

    def _execute_roll_table(self, parser, table_name: str) -> List[str]:
        """Execute random table roll and return messages."""
        messages = []
        table = parser.get_random_table(table_name)
        if not table:
            logger.warning(f"Random table not found: {table_name}")
            return messages

        entries = table.get('entries', [])
        if not entries:
            logger.warning(f"Random table {table_name} has no entries")
            return messages

        import random
        # Randomly select entry
        result = random.choice(entries)
        logger.debug(f"Rolled table {table_name}: {result}")

        # If result has message, add message
        if isinstance(result, dict) and 'message' in result:
            messages.append(result['message'])

        # If result has commands, execute them
        if isinstance(result, dict) and 'commands' in result:
            # Note: This would need access to the executor to execute commands
            # For now, just log that commands would be executed
            logger.debug(f"Would execute commands: {result['commands']}")
        return messages

    def _evaluate_expression(self, expression: str, context: dict) -> Any:
        """
        Safely evaluate a mathematical or logical expression with limited context.
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
