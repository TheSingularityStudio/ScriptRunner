"""
ScriptRunner 的基础动作插件。
提供常见的游戏动作，如攻击和搜索。
"""

from typing import Dict, Any, List, Callable
from src.infrastructure.plugin_interface import ActionPlugin
from src.infrastructure.logger import get_logger
from src.utils.expression_evaluator import ExpressionEvaluator

logger = get_logger(__name__)


class BasicActionsPlugin(ActionPlugin):
    """提供攻击和搜索功能的基础动作插件。"""

    @property
    def name(self) -> str:
        return "BasicActions"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件。"""
        logger.info("BasicActions plugin initialized")
        return True

    def shutdown(self) -> None:
        """关闭插件。"""
        logger.info("BasicActions plugin shutdown")

    def get_actions(self) -> Dict[str, Callable[[str, Dict[str, Any]], Dict[str, Any]]]:
        """返回此插件提供的动作。"""
        return {
            'attack': self._execute_attack,
            'search': self._execute_search,
            'roll_table': self._execute_roll_table,
        }

    def _execute_attack(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行攻击命令并返回结果。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        messages = []
        actions = []
        # 获取目标对象
        target_obj = parser.get_object(target)
        if not target_obj:
            logger.warning(f"Attack target not found: {target}")
            return {'success': False, 'message': f"无法找到攻击目标 {target}", 'actions': []}

        target_attrs = target_obj.get('attributes', {})
        behaviors = target_obj.get('behaviors', {})
        attack_behavior = behaviors.get('attack', {})

        # 从配置中获取战斗属性
        combat_attributes = attack_behavior.get('combat_attributes', ['strength', 'agility', 'defense', 'health'])
        player_attrs = {}
        for attr in combat_attributes:
            player_attrs[attr] = state.get_variable(attr, 0)

        # 计算命中几率
        hit_chance_expr = attack_behavior.get('hit_chance', '0.5')
        context = {**player_attrs, **target_attrs}
        # 添加 player. 前缀变量
        context.update({f'player.{k}': v for k, v in player_attrs.items()})
        # 添加 player 和 target 字典以支持点号访问
        context['player'] = player_attrs
        context['target'] = target_attrs
        hit_chance = ExpressionEvaluator.evaluate_expression(hit_chance_expr, context)

        import random
        if random.random() < hit_chance:
            # 命中
            damage_expr = attack_behavior.get('damage', '10')
            damage = ExpressionEvaluator.evaluate_expression(damage_expr, context)

            # 对目标造成伤害
            health_attr = attack_behavior.get('health_attribute', 'health')
            states = target_obj.get('states', [])
            for state in states:
                state_name = state.get('name', 'health')  # 默认使用health
                if state_name == health_attr:
                    old_value = state['value']
                    state['value'] = max(0, state['value'] - damage)
                    # 添加设置变量的动作
                    actions.append(f"parse_and_set:{target}_{health_attr}={state['value']}")
                    break

            # 成功消息
            success_msg = attack_behavior.get('success', '你击中了{target}，造成{damage}点伤害！')
            success_msg = success_msg.replace('{target}', target).replace('{damage}', str(damage))
            messages.append(success_msg)
            logger.debug(success_msg)
        else:
            # 未命中
            failure_msg = attack_behavior.get('failure', '你没能打中{target}')
            failure_msg = failure_msg.replace('{target}', target)
            messages.append(failure_msg)
            logger.debug(failure_msg)

        # 反击
        counter_msg = attack_behavior.get('counter', '')
        if counter_msg:
            messages.append(counter_msg)
            logger.debug(counter_msg)
            # 从配置中获取反击伤害，默认 5
            counter_damage = attack_behavior.get('counter_damage', 5)
            player_health_attr = attack_behavior.get('player_health_attribute', 'health')
            player_health = state.get_variable(player_health_attr, 100)
            state.set_variable(player_health_attr, max(0, player_health - counter_damage))
            counter_damage_msg = attack_behavior.get('counter_damage_msg', '你受到了{counter_damage}点反击伤害！')
            counter_damage_msg = counter_damage_msg.replace('{counter_damage}', str(counter_damage))
            messages.append(counter_damage_msg)
            logger.debug(f"Player took {counter_damage} counter damage")
        
        return {'success': True, 'message': '\n'.join(messages), 'actions': actions}

    def _execute_search(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索命令并返回结果。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        messages = []
        logger.info(f"Searching {target}...")

        # 动态构建搜索表名称，例如 {location}_search
        table_name = f"{target}_search"
        table = parser.get_random_table(table_name)
        if table:
            result = self._execute_roll_table(table_name, context)
            return result
        else:
            msg = f"你搜索了{target}，但没有发现什么特别的东西。"
            return {'success': True, 'message': msg, 'actions': []}

    def _execute_roll_table(self, table_param: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行随机表掷骰并返回结果。"""
        parser = context['parser']
        state = context['state']
        condition_evaluator = context.get('condition_evaluator')
        
        # 处理参数：可以是字符串或字典
        if isinstance(table_param, dict):
            table_name = table_param.get('table')
            result_var = table_param.get('result_var')
        elif isinstance(table_param, str):
            table_name = table_param
            result_var = None
        else:
            return {'success': False, 'message': "无效的roll_table参数", 'actions': []}
        
        messages = []
        table = parser.get_random_table(table_name)
        if not table:
            logger.warning(f"Random table not found: {table_name}")
            return {'success': False, 'message': f"找不到随机表 {table_name}", 'actions': []}

        # 处理表格式：可以是dict或list
        if isinstance(table, dict):
            entries = table.get('entries', [])
        elif isinstance(table, list):
            entries = table
        else:
            return {'success': False, 'message': f"随机表 {table_name} 格式错误", 'actions': []}

        import random
        # 随机选择条目
        result = random.choice(entries)
        logger.debug(f"Rolled table {table_name}: {result}")

        # 如果结果有消息，添加消息
        message = ""
        if isinstance(result, dict) and 'message' in result:
            message = result['message']

        # 如果结果有命令，执行它们
        actions = []
        if isinstance(result, dict) and 'commands' in result:
            # 将命令转换为DSL动作
            for cmd in result['commands']:
                if 'set_flag' in cmd:
                    actions.append(f"add_flag:{cmd['set_flag']}")
                elif 'set' in cmd:
                    actions.append(f"parse_and_set:{cmd['set']}")
                # 其他命令可以扩展
            logger.debug(f"Would execute commands: {result['commands']}")
        
        # 如果指定了result_var，设置变量
        if result_var and isinstance(result, str):
            actions.append(f"parse_and_set:{result_var}={result}")
        elif result_var and isinstance(result, dict) and 'item' in result:
            actions.append(f"parse_and_set:{result_var}={result['item']}")
        elif result_var and isinstance(result, dict) and 'value' in result:
            actions.append(f"parse_and_set:{result_var}={result['value']}")
        
        return {'success': True, 'message': message, 'actions': actions}
