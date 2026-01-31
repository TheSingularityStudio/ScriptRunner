"""
ScriptRunner 的事件管理器。
处理 DSL 事件系统的调度和触发。
"""

from typing import Dict, Any, List, Optional
import random
import time
from ..logging.logger import get_logger

logger = get_logger(__name__)


class EventManager:
    """管理游戏事件系统。"""

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

        # 事件数据
        self.scheduled_events = []
        self.reactive_events = []
        self.last_check_time = time.time()

        # 加载事件数据
        self._load_events()

    def _load_events(self):
        """从解析器加载事件数据。"""
        try:
            events = self.parser.get_events()
            if events:
                self.scheduled_events = events.get('scheduled_events', [])
                self.reactive_events = events.get('reactive_events', [])
                # 安全地获取长度，避免在mock对象上调用len()
                scheduled_count = len(self.scheduled_events) if hasattr(self.scheduled_events, '__len__') else 0
                reactive_count = len(self.reactive_events) if hasattr(self.reactive_events, '__len__') else 0
                logger.info(f"Loaded {scheduled_count} scheduled events and {reactive_count} reactive events")
        except Exception as e:
            logger.warning(f"Failed to load events: {e}")
            self.scheduled_events = []
            self.reactive_events = []

    def check_scheduled_events(self) -> None:
        """检查定时事件是否应该触发。"""
        current_time = time.time()
        game_time = self.state.get_variable('game_time', 0)  # 假设有游戏时间变量

        for event in self.scheduled_events:
            trigger = event.get('trigger', '')
            chance = event.get('chance', 1.0)
            action = event.get('action', '')

            # 检查时间触发条件
            if self._check_time_trigger(trigger, game_time):
                # 检查随机几率
                if random.random() <= chance:
                    self._execute_event_action(action, event)
                    logger.info(f"Scheduled event triggered: {action}")

    def check_reactive_events(self, trigger_type: str, **kwargs) -> None:
        """检查反应事件是否应该触发。"""
        for event in self.reactive_events:
            event_trigger = event.get('trigger', '')

            # 检查触发类型匹配
            if self._matches_trigger(event_trigger, trigger_type, kwargs):
                # 检查条件
                conditions = event.get('conditions', [])
                if self._check_conditions(conditions):
                    actions = event.get('actions', [])
                    self._execute_actions(actions)
                    logger.info(f"Reactive event triggered: {event_trigger}")

    def _check_time_trigger(self, trigger: str, game_time: float) -> bool:
        """检查时间触发条件。"""
        if trigger.startswith('time > '):
            threshold = float(trigger[7:])
            return game_time > threshold
        elif trigger.startswith('time >= '):
            threshold = float(trigger[8:])
            return game_time >= threshold
        elif trigger.startswith('time < '):
            threshold = float(trigger[7:])
            return game_time < threshold
        elif trigger.startswith('time <= '):
            threshold = float(trigger[8:])
            return game_time <= threshold
        return False

    def _matches_trigger(self, event_trigger: str, trigger_type: str, kwargs: Dict[str, Any]) -> bool:
        """检查事件触发器是否匹配。"""
        if event_trigger.startswith('player.action = '):
            action = event_trigger[16:].strip('"\'' )
            return trigger_type == 'player_action' and kwargs.get('action') == action
        elif event_trigger.startswith('world.'):
            world_prop = event_trigger[6:]
            if '=' in world_prop:
                key, value = world_prop.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'' )
                return self.state.get_variable(f'world_{key}') == value
        return False

    def _check_conditions(self, conditions: List[str]) -> bool:
        """检查事件条件。"""
        for condition in conditions:
            if not self.condition_evaluator.evaluate_condition(condition):
                return False
        return True

    def _execute_event_action(self, action: str, event: Dict[str, Any]) -> None:
        """执行事件动作。"""
        if action == 'spawn_werewolf':
            # 示例：生成狼人
            self.state.set_variable('werewolf_spawned', True)
            logger.info("Werewolf spawned due to event")
        elif action.startswith('spawn_object:'):
            obj_name = action[13:].strip()
            # 在当前场景添加对象
            current_scene = self.state.get_current_scene()
            if current_scene:
                # 这里需要扩展状态管理器来支持场景对象
                logger.info(f"Object {obj_name} spawned in scene {current_scene}")
        elif action.startswith('transform:'):
            # 对象变换
            transform_spec = action[10:]
            logger.info(f"Transformation triggered: {transform_spec}")
        elif action.startswith('broadcast:'):
            message = action[10:].strip('"\'' )
            # 这里可以添加到消息队列
            logger.info(f"Broadcast message: {message}")
        elif action == 'log:':
            message = event.get('message', 'Event logged')
            logger.info(f"Event log: {message}")

    def _execute_actions(self, actions: List[str]) -> None:
        """执行多个动作。"""
        for action in actions:
            if action.startswith('spawn_object:'):
                obj_name = action[13:].strip('"\'' )
                logger.info(f"Spawning object: {obj_name}")
            elif action.startswith('log:'):
                message = action[4:].strip('"\'' )
                logger.info(f"Event log: {message}")
            elif action.startswith('set:'):
                # 转换为命令格式
                self.command_executor.execute_command({'set': action[4:].strip()})
            elif action.startswith('add_flag:'):
                flag = action[9:].strip()
                self.state.set_flag(flag)

    def update_game_time(self, delta_time: float) -> None:
        """更新游戏时间并检查定时事件。"""
        current_game_time = self.state.get_variable('game_time', 0)
        new_game_time = current_game_time + delta_time
        self.state.set_variable('game_time', new_game_time)

        # 检查定时事件
        self.check_scheduled_events()

    def trigger_player_action(self, action: str, **kwargs) -> None:
        """触发玩家动作事件。"""
        self.check_reactive_events('player_action', action=action, **kwargs)
