"""
ScriptRunner 的事件管理器。
处理 DSL 事件系统的调度和触发。
"""

from typing import Dict, Any, List, Optional, Callable
import random
import time
from collections import deque
from .interfaces import IEventManager
from ...infrastructure.logger import get_logger
from .action_executor import ActionExecutor

logger = get_logger(__name__)


class EventManager(IEventManager):
    """管理游戏事件系统。"""

    # 优先级常量
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

        # 统一的动作执行器
        self.action_executor = ActionExecutor(state_manager, command_executor)

        # 事件数据 - 现在支持优先级和启用状态
        self.scheduled_events = []  # List of dicts with 'id', 'enabled', 'priority', etc.
        self.reactive_events = []   # List of dicts with 'id', 'enabled', 'priority', etc.
        self.last_check_time = time.time()

        # 动作处理器注册表
        self.action_handlers = {}

        # 事件历史记录
        self.event_history = deque(maxlen=1000)

        # 加载事件数据
        self._load_events()

        # 注册默认动作处理器
        self._register_default_handlers()

    def _load_events(self):
        """从解析器加载事件数据。"""
        try:
            events = self.parser.get_events()
            if events:
                # 处理定时事件
                raw_scheduled = events.get('scheduled_events', [])
                self.scheduled_events = []
                for event in raw_scheduled:
                    processed_event = self._process_event_data(event, 'scheduled')
                    if processed_event:
                        self.scheduled_events.append(processed_event)

                # 处理反应事件
                raw_reactive = events.get('reactive_events', [])
                self.reactive_events = []
                for event in raw_reactive:
                    processed_event = self._process_event_data(event, 'reactive')
                    if processed_event:
                        self.reactive_events.append(processed_event)

                # 按优先级排序事件
                self._sort_events_by_priority()

                scheduled_count = len(self.scheduled_events)
                reactive_count = len(self.reactive_events)
                logger.info(f"Loaded {scheduled_count} scheduled events and {reactive_count} reactive events")

                # 验证事件配置
                validation_errors = self.validate_events()
                if validation_errors:
                    logger.warning(f"Event validation errors: {validation_errors}")
        except Exception as e:
            logger.error(f"Failed to load events: {e}")
            self.scheduled_events = []
            self.reactive_events = []

    def _process_event_data(self, event: Dict[str, Any], event_type: str) -> Optional[Dict[str, Any]]:
        """处理单个事件数据，确保格式正确。"""
        try:
            processed = dict(event)  # 复制原事件数据

            # 确保有ID
            if 'id' not in processed:
                processed['id'] = f"{event_type}_{hash(str(event))}"

            # 确保有启用状态
            processed.setdefault('enabled', True)

            # 确保有优先级
            processed.setdefault('priority', self.PRIORITY_MEDIUM)

            # 验证优先级值
            if processed['priority'] not in [self.PRIORITY_HIGH, self.PRIORITY_MEDIUM, self.PRIORITY_LOW]:
                logger.warning(f"Invalid priority '{processed['priority']}' for event {processed['id']}, defaulting to medium")
                processed['priority'] = self.PRIORITY_MEDIUM

            return processed
        except Exception as e:
            logger.error(f"Failed to process event data: {e}")
            return None

    def _sort_events_by_priority(self):
        """按优先级排序事件，高优先级在前。"""
        priority_order = {self.PRIORITY_HIGH: 0, self.PRIORITY_MEDIUM: 1, self.PRIORITY_LOW: 2}

        self.scheduled_events.sort(key=lambda e: priority_order.get(e.get('priority', self.PRIORITY_MEDIUM), 1))
        self.reactive_events.sort(key=lambda e: priority_order.get(e.get('priority', self.PRIORITY_MEDIUM), 1))

    def _register_default_handlers(self):
        """注册默认的动作处理器。"""
        self.action_handlers = {
            'spawn_werewolf': self._handle_spawn_werewolf,
            'spawn_object': self._handle_spawn_object,
            'transform': self._handle_transform,
            'broadcast': self._handle_broadcast,
            'log': self._handle_log,
        }

    def check_scheduled_events(self) -> None:
        """检查定时事件是否应该触发。"""
        current_time = time.time()
        game_time = self.state.get_variable('game_time', 0)  # 假设有游戏时间变量

        for event in self.scheduled_events:
            # 检查事件是否启用
            if not event.get('enabled', True):
                continue

            trigger = event.get('trigger', '')
            chance = event.get('chance', 1.0)
            action = event.get('action', '')

            # 检查时间触发条件
            if self._check_time_trigger(trigger, game_time):
                # 检查随机几率
                if random.random() <= chance:
                    self._execute_event_action(action, event)
                    self._record_event_history('event_triggered', 'scheduled', {'event_id': event.get('id'), 'action': action})
                    logger.info(f"Scheduled event triggered: {action}")

    def check_reactive_events(self, trigger_type: str, **kwargs) -> None:
        """检查反应事件是否应该触发。"""
        for event in self.reactive_events:
            # 检查事件是否启用
            if not event.get('enabled', True):
                continue

            event_trigger = event.get('trigger', '')

            # 检查触发类型匹配
            if self._matches_trigger(event_trigger, trigger_type, kwargs):
                # 检查条件
                conditions = event.get('conditions', [])
                if self._check_conditions(conditions):
                    actions = event.get('actions', [])
                    self._execute_actions(actions)
                    self._record_event_history('event_triggered', 'reactive', {'event_id': event.get('id'), 'trigger': event_trigger, 'actions': actions})
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
        elif event_trigger.startswith('scene.change'):
            # 场景变更触发器
            return trigger_type == 'scene_change'
        elif event_trigger.startswith('variable.'):
            # 变量变更触发器
            var_trigger = event_trigger[9:]
            if '=' in var_trigger:
                var_name, expected_value = var_trigger.split('=', 1)
                var_name = var_name.strip()
                expected_value = expected_value.strip().strip('"\'' )
                return trigger_type == 'variable_change' and kwargs.get('variable') == var_name and str(kwargs.get('new_value')) == expected_value
        elif event_trigger.startswith('custom.'):
            # 自定义触发器
            custom_type = event_trigger[7:]
            return trigger_type == 'custom' and kwargs.get('custom_type') == custom_type
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
            # 添加到游戏消息队列以供界面显示
            self.state.add_broadcast_message(message)
            logger.info(f"Broadcast message: {message}")
        elif action == 'log:':
            message = event.get('message', 'Event logged')
            logger.info(f"Event log: {message}")

    def _execute_actions(self, actions: List[str]) -> None:
        """执行多个动作。"""
        for action in actions:
            try:
                self._execute_single_action(action)
            except Exception as e:
                logger.error(f"Failed to execute action '{action}': {e}")

    def _execute_single_action(self, action: str) -> None:
        """执行单个动作，使用处理器注册表。"""
        # 解析动作类型和参数
        if ':' in action:
            action_type, params = action.split(':', 1)
            action_type = action_type.strip()
            params = params.strip()
        else:
            action_type = action.strip()
            params = ''

        # 查找处理器
        handler = self.action_handlers.get(action_type)
        if handler:
            handler(params)
        else:
            # 回退到通用动作执行器
            self.action_executor.execute_action(action)

    # 默认动作处理器
    def _handle_spawn_werewolf(self, params: str) -> None:
        """处理生成狼人动作。"""
        self.state.set_variable('werewolf_spawned', True)
        self._record_event_history('action', 'spawn_werewolf', {'params': params})
        logger.info("Werewolf spawned due to event")

    def _handle_spawn_object(self, params: str) -> None:
        """处理生成对象动作。"""
        obj_name = params.strip('"\'' )
        current_scene = self.state.get_current_scene()
        if current_scene:
            # 这里需要扩展状态管理器来支持场景对象
            logger.info(f"Object {obj_name} spawned in scene {current_scene}")
        self._record_event_history('action', 'spawn_object', {'object': obj_name, 'scene': current_scene})

    def _handle_transform(self, params: str) -> None:
        """处理对象变换动作。"""
        transform_spec = params
        logger.info(f"Transformation triggered: {transform_spec}")
        self._record_event_history('action', 'transform', {'spec': transform_spec})

    def _handle_broadcast(self, params: str) -> None:
        """处理广播消息动作。"""
        message = params.strip('"\'' )
        self.state.add_broadcast_message(message)
        self._record_event_history('action', 'broadcast', {'message': message})
        logger.info(f"Broadcast message: {message}")

    def _handle_log(self, params: str) -> None:
        """处理日志动作。"""
        message = params.strip('"\'' ) if params else 'Event logged'
        self._record_event_history('action', 'log', {'message': message})
        logger.info(f"Event log: {message}")

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

    def enable_event(self, event_id: str) -> bool:
        """启用指定事件。"""
        return self._set_event_enabled(event_id, True)

    def disable_event(self, event_id: str) -> bool:
        """禁用指定事件。"""
        return self._set_event_enabled(event_id, False)

    def remove_event(self, event_id: str) -> bool:
        """移除指定事件。"""
        try:
            # 从定时事件中移除
            self.scheduled_events = [e for e in self.scheduled_events if e.get('id') != event_id]
            # 从反应事件中移除
            self.reactive_events = [e for e in self.reactive_events if e.get('id') != event_id]

            self._record_event_history('event_removed', 'management', {'event_id': event_id})
            logger.info(f"Event {event_id} removed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to remove event {event_id}: {e}")
            return False

    def _set_event_enabled(self, event_id: str, enabled: bool) -> bool:
        """设置事件的启用状态。"""
        try:
            # 检查定时事件
            for event in self.scheduled_events:
                if event.get('id') == event_id:
                    event['enabled'] = enabled
                    self._record_event_history('event_enabled' if enabled else 'event_disabled', 'management', {'event_id': event_id})
                    logger.info(f"Event {event_id} {'enabled' if enabled else 'disabled'}")
                    return True

            # 检查反应事件
            for event in self.reactive_events:
                if event.get('id') == event_id:
                    event['enabled'] = enabled
                    self._record_event_history('event_enabled' if enabled else 'event_disabled', 'management', {'event_id': event_id})
                    logger.info(f"Event {event_id} {'enabled' if enabled else 'disabled'}")
                    return True

            logger.warning(f"Event {event_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to {'enable' if enabled else 'disable'} event {event_id}: {e}")
            return False

    def trigger_scene_change(self, old_scene: str, new_scene: str) -> None:
        """触发场景变更事件。"""
        self.check_reactive_events('scene_change', old_scene=old_scene, new_scene=new_scene)
        self._record_event_history('scene_change', 'trigger', {'old_scene': old_scene, 'new_scene': new_scene})

    def trigger_variable_change(self, variable_name: str, old_value: Any, new_value: Any) -> None:
        """触发变量变更事件。"""
        self.check_reactive_events('variable_change', variable=variable_name, old_value=old_value, new_value=new_value)
        self._record_event_history('variable_change', 'trigger', {'variable': variable_name, 'old_value': old_value, 'new_value': new_value})

    def register_action_handler(self, action_type: str, handler: Callable[[str], None]) -> None:
        """注册动作处理器。"""
        try:
            self.action_handlers[action_type] = handler
            self._record_event_history('handler_registered', 'management', {'action_type': action_type})
            logger.info(f"Action handler registered for type: {action_type}")
        except Exception as e:
            logger.error(f"Failed to register action handler for {action_type}: {e}")

    def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取事件历史记录。"""
        return list(self.event_history)[-limit:]

    def validate_events(self) -> List[str]:
        """验证所有事件配置。"""
        errors = []

        all_events = self.scheduled_events + self.reactive_events

        for event in all_events:
            event_id = event.get('id', 'unknown')

            # 检查必需字段
            if not event.get('trigger'):
                errors.append(f"Event {event_id}: missing 'trigger' field")

            # 检查优先级
            priority = event.get('priority', self.PRIORITY_MEDIUM)
            if priority not in [self.PRIORITY_HIGH, self.PRIORITY_MEDIUM, self.PRIORITY_LOW]:
                errors.append(f"Event {event_id}: invalid priority '{priority}'")

            # 检查定时事件的动作
            if event in self.scheduled_events and not event.get('action'):
                errors.append(f"Scheduled event {event_id}: missing 'action' field")

            # 检查反应事件的动作
            if event in self.reactive_events and not event.get('actions'):
                errors.append(f"Reactive event {event_id}: missing 'actions' field")

        return errors

    def _record_event_history(self, event_type: str, category: str, data: Dict[str, Any]) -> None:
        """记录事件历史。"""
        try:
            history_entry = {
                'timestamp': time.time(),
                'type': event_type,
                'category': category,
                'data': data
            }
            self.event_history.append(history_entry)
        except Exception as e:
            logger.error(f"Failed to record event history: {e}")
