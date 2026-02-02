"""
ScriptRunner 的效果管理器。
处理 DSL 效果系统的应用、持续时间和更新。
"""

from typing import Dict, Any, List, Optional
import time
from .interfaces import IEffectsManager
from ...infrastructure.logger import get_logger
from .action_executor import ActionExecutor

logger = get_logger(__name__)


class EffectsManager(IEffectsManager):
    """管理游戏效果系统。"""

    def __init__(self, parser, state_manager, command_executor):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor

        # 统一的动作执行器
        self.action_executor = ActionExecutor(state_manager, command_executor)

        # 活跃效果存储
        self.active_effects: Dict[str, Dict[str, Any]] = {}

        logger.info("EffectsManager initialized")

    def apply_effect(self, effect_name: str, target: Optional[str] = None) -> bool:
        """应用效果到目标（默认为玩家）。"""
        effect_data = self.parser.get_effect(effect_name)
        if not effect_data:
            logger.warning(f"Effect '{effect_name}' not found")
            return False

        # 如果效果已存在，刷新持续时间
        if effect_name in self.active_effects:
            self.active_effects[effect_name]['duration'] = effect_data.get('duration', 0)
            logger.info(f"Refreshed effect: {effect_name}")
        else:
            # 创建新效果实例
            effect_instance = effect_data.copy()

            # 解析持续时间字符串
            duration = effect_instance.get('duration', 0)
            if isinstance(duration, str):
                # 解析字符串持续时间，如 "5 turns"
                duration_parts = duration.split()
                if duration_parts:
                    try:
                        effect_instance['duration'] = int(duration_parts[0])
                    except ValueError:
                        effect_instance['duration'] = 0
                else:
                    effect_instance['duration'] = 0
            elif not isinstance(duration, int):
                effect_instance['duration'] = 0

            effect_instance['start_time'] = time.time()
            effect_instance['target'] = target or 'player'
            self.active_effects[effect_name] = effect_instance

            # 执行效果的初始动作
            self._execute_effect_actions(effect_instance, 'apply')

            logger.info(f"Applied effect: {effect_name} to {target or 'player'}")

        return True

    def remove_effect(self, effect_name: str) -> bool:
        """移除效果。"""
        if effect_name in self.active_effects:
            effect_data = self.active_effects[effect_name]

            # 执行移除时的动作
            self._execute_effect_actions(effect_data, 'remove')

            del self.active_effects[effect_name]
            logger.info(f"Removed effect: {effect_name}")
            return True

        return False

    def update_effects(self) -> None:
        """更新所有活跃效果，处理持续时间和tick动作。"""
        current_time = time.time()
        expired_effects = []

        for effect_name, effect_data in self.active_effects.items():
            # 检查持续时间
            duration = effect_data.get('duration', 0)
            if duration > 0:
                # 减少持续时间
                effect_data['duration'] -= 1

                # 检查是否到期
                if effect_data['duration'] <= 0:
                    expired_effects.append(effect_name)
                    continue

            # 执行tick动作（如果有）
            tick_action = effect_data.get('tick')
            if tick_action:
                tick_rate = effect_data.get('tick_rate', 1)  # 每回合执行一次

                # 计算自开始以来经过的tick数
                elapsed_ticks = int((current_time - effect_data['start_time']) / tick_rate)
                last_tick = effect_data.get('last_tick', 0)

                if elapsed_ticks > last_tick:
                    self._execute_tick_action(tick_action, effect_data)
                    effect_data['last_tick'] = elapsed_ticks

        # 移除过期效果
        for effect_name in expired_effects:
            self.remove_effect(effect_name)

    def get_active_effects(self, target: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取活跃效果，可按目标过滤。"""
        if target is None:
            return self.active_effects.copy()

        return {name: data for name, data in self.active_effects.items()
                if data.get('target') == target}

    def has_effect(self, effect_name: str, target: Optional[str] = None) -> bool:
        """检查目标是否拥有指定效果。"""
        effects = self.get_active_effects(target)
        return effect_name in effects

    def get_effect_modifier(self, stat_name: str, target: Optional[str] = None) -> float:
        """
        计算特定属性从所有有效效果中获得的总修改值。

        此方法汇总作用于目标（默认：player）的所有效果的修改值。
        修改值可以是加法（5，-2）、乘法（*1.1）或直接数值。
        应用顺序对于乘法修改值非常重要。

        Args:
            stat_name: 要获取修正值的属性名称 (例如, 'strength', 'health')
            target: 目标实体名称，如果为 None，则默认为 'player'

        Returns:
            应用于属性的总修改器数值。对于乘法修改器，这会返回合并后的乘数（例如，10% 增加对应 1.1）

        Note:
            - 加成修正（ /-）直接相加
            - 乘法修正（*）相乘
            - 直接数值视为加成
            - 复杂的属性计算应由调用方处理
        """
        total_modifier = 0.0
        effects = self.get_active_effects(target)

        for effect_data in effects.values():
            modifiers = effect_data.get('modifiers', {})
            if stat_name in modifiers:
                modifier_value = modifiers[stat_name]

                # 根据字符串前缀或直接值处理不同类型的修饰符
                if isinstance(modifier_value, str):
                    if modifier_value.startswith('*'):
                        # 乘法修饰符，例如，"*1.1"表示增加10%
                        multiplier = float(modifier_value[1:])
                        # 乘以现有的修饰符（乘法初始值为 1.0）
                        if total_modifier == 0.0:
                            total_modifier = multiplier
                        else:
                            total_modifier *= multiplier
                    elif modifier_value.startswith('+'):
                        # 加法修饰符，例如，“2”表示加2
                        total_modifier += float(modifier_value[1:])
                    elif modifier_value.startswith('-'):
                        # 减法修饰符，例如：“-1”表示减去1
                        total_modifier -= float(modifier_value[1:])
                elif isinstance(modifier_value, (int, float)):
                    # 直接数值修饰符，视为加法
                    total_modifier += modifier_value

        return total_modifier

    def _execute_effect_actions(self, effect_data: Dict[str, Any], action_type: str) -> None:
        """执行效果的特定类型动作。"""
        actions = effect_data.get(action_type, [])
        if isinstance(actions, list):
            for action in actions:
                self._execute_single_action(action, effect_data)
        elif isinstance(actions, str):
            self._execute_single_action(actions, effect_data)

    def _execute_tick_action(self, tick_action: str, effect_data: Dict[str, Any]) -> None:
        """执行tick动作。"""
        self._execute_single_action(tick_action, effect_data)

    def _execute_single_action(self, action: str, effect_data: Dict[str, Any]) -> None:
        """执行单个效果动作。"""
        try:
            if action.startswith('player.health'):
                # 生命值修改，如 "player.health -= 5" 或 "player.health += 10"
                if '-=' in action:
                    parts = action.split('-=', 1)
                    damage_str = parts[1].strip()
                    # 支持表达式，如 "5" 或 "strength * 2"
                    damage = self._parse_damage_expression(damage_str, effect_data)
                    player = self.state.get_variable('player', {'health': 100})
                    current_health = player.get('health', 100)
                    new_health = max(0, current_health - damage)
                    player['health'] = new_health
                    self.state.set_variable('player', player)
                    logger.debug(f"Effect damage: {damage}, health now {new_health}")
                elif '+=' in action:
                    parts = action.split('+=', 1)
                    heal_str = parts[1].strip()
                    heal = self._parse_damage_expression(heal_str, effect_data)
                    player = self.state.get_variable('player', {'health': 100})
                    current_health = player.get('health', 100)
                    new_health = current_health + heal
                    player['health'] = new_health
                    self.state.set_variable('player', player)
                    logger.debug(f"Effect heal: {heal}, health now {new_health}")
            else:
                # 使用统一的动作执行器处理其他动作
                self.action_executor.execute_action(action, effect_data)

        except Exception as e:
            logger.error(f"Error executing effect action '{action}': {e}")

    def _parse_damage_expression(self, damage_str: str, effect_data: Dict[str, Any]) -> int:
        """解析伤害表达式，支持数字和简单表达式。"""
        try:
            # 尝试直接转换为整数
            return int(damage_str)
        except ValueError:
            # 如果是表达式，暂时返回默认值（可以扩展为支持更复杂的表达式）
            logger.warning(f"Complex damage expression '{damage_str}' not supported, using default 5")
            return 5

    def get_status_message(self) -> str:
        """获取效果状态消息。"""
        if not self.active_effects:
            return ""

        effect_names = list(self.active_effects.keys())
        return f"效果: {', '.join(effect_names)}"
