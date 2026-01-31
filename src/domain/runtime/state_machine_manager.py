"""
ScriptRunner 的状态机管理器。
处理 DSL 状态机系统的状态转换和自动更新。
"""

from typing import Dict, Any, List, Optional
import time
from ..logging.logger import get_logger

logger = get_logger(__name__)


class StateMachineManager:
    """管理游戏状态机系统。"""

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

        # 状态机存储
        self.state_machines: Dict[str, Dict[str, Any]] = {}
        self.last_update_time = time.time()

        logger.info("StateMachineManager initialized")

    def load_state_machines(self):
        """从解析器加载状态机数据。"""
        try:
            state_machines = self.parser.get_state_machine_data()
            if state_machines:
                self.state_machines = state_machines
                logger.info(f"Loaded {len(self.state_machines)} state machines")

                # 初始化所有状态机的当前状态
                for sm_name, sm_data in self.state_machines.items():
                    initial_state = sm_data.get('initial_state')
                    if initial_state:
                        self.state.set_variable(f"{sm_name}_state", initial_state)
                        logger.debug(f"Initialized state machine '{sm_name}' to state '{initial_state}'")

        except Exception as e:
            logger.warning(f"Failed to load state machines: {e}")

    def update_state_machines(self) -> None:
        """更新所有状态机，检查转换条件。"""
        current_time = time.time()

        for sm_name, sm_data in self.state_machines.items():
            try:
                self._update_state_machine(sm_name, sm_data, current_time)
            except Exception as e:
                logger.error(f"Error updating state machine '{sm_name}': {e}")

        self.last_update_time = current_time

    def _update_state_machine(self, sm_name: str, sm_data: Dict[str, Any], current_time: float) -> None:
        """更新单个状态机。"""
        current_state = self.state.get_variable(f"{sm_name}_state")
        if not current_state:
            return

        # 获取当前状态的定义
        states = sm_data.get('states', {})
        state_def = states.get(current_state, {})

        # 检查转换条件
        transitions = state_def.get('transitions', [])
        for transition in transitions:
            if self._check_transition_condition(transition):
                new_state = transition.get('to')
                if new_state and new_state != current_state:
                    self._execute_state_transition(sm_name, current_state, new_state, transition)
                    break

        # 执行当前状态的持续动作
        self._execute_state_actions(sm_name, state_def)

    def _check_transition_condition(self, transition: Dict[str, Any]) -> bool:
        """检查状态转换条件。"""
        condition = transition.get('condition')

        if not condition:
            return False

        # 处理时间条件
        if condition.startswith('time > ') or condition.startswith('time >= ') or \
           condition.startswith('time < ') or condition.startswith('time <= '):
            try:
                # 解析时间条件，如 "time > 360 && time < 420"
                time_conditions = condition.split('&&')
                game_time = self.state.get_variable('game_time', 0)

                for time_cond in time_conditions:
                    time_cond = time_cond.strip()
                    if time_cond.startswith('time > '):
                        threshold = float(time_cond[7:])
                        if not (game_time > threshold):
                            return False
                    elif time_cond.startswith('time >= '):
                        threshold = float(time_cond[8:])
                        if not (game_time >= threshold):
                            return False
                    elif time_cond.startswith('time < '):
                        threshold = float(time_cond[7:])
                        if not (game_time < threshold):
                            return False
                    elif time_cond.startswith('time <= '):
                        threshold = float(time_cond[8:])
                        if not (game_time <= threshold):
                            return False

                return True

            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid time condition '{condition}': {e}")
                return False

        # 处理其他条件
        return self.condition_evaluator.evaluate_condition(condition)

    def _execute_state_transition(self, sm_name: str, from_state: str, to_state: str, transition: Dict[str, Any]) -> None:
        """执行状态转换。"""
        logger.info(f"State machine '{sm_name}' transitioning from '{from_state}' to '{to_state}'")

        # 更新状态
        self.state.set_variable(f"{sm_name}_state", to_state)

        # 执行转换动作
        actions = transition.get('actions', [])
        for action in actions:
            self._execute_action(action)

        # 触发转换事件
        self._trigger_transition_event(sm_name, from_state, to_state)

    def _execute_state_actions(self, sm_name: str, state_def: Dict[str, Any]) -> None:
        """执行状态的持续动作。"""
        actions = state_def.get('actions', [])
        for action in actions:
            self._execute_action(action)

    def _execute_action(self, action: str) -> None:
        """执行单个动作。"""
        try:
            if action.startswith('set:'):
                # 设置变量
                var_expr = action[4:].strip()
                self.command_executor.execute_command({'set': var_expr})

            elif action.startswith('add_flag:'):
                # 添加标志
                flag = action[9:].strip()
                self.state.set_flag(flag)

            elif action.startswith('remove_flag:'):
                # 移除标志
                flag = action[12:].strip()
                self.state.clear_flag(flag)

            elif action.startswith('broadcast:'):
                # 广播消息
                message = action[10:].strip('"\'' )
                logger.info(f"State machine broadcast: {message}")

            elif action.startswith('log:'):
                # 日志记录
                message = action[4:].strip('"\'' )
                logger.info(f"State machine log: {message}")

            else:
                logger.warning(f"Unknown state machine action: {action}")

        except Exception as e:
            logger.error(f"Error executing state machine action '{action}': {e}")

    def _trigger_transition_event(self, sm_name: str, from_state: str, to_state: str) -> None:
        """触发状态转换事件。"""
        # 这里可以集成到事件管理器中
        logger.debug(f"State transition event: {sm_name} {from_state} -> {to_state}")

    def get_current_state(self, sm_name: str) -> Optional[str]:
        """获取状态机的当前状态。"""
        return self.state.get_variable(f"{sm_name}_state")

    def force_state(self, sm_name: str, state: str) -> bool:
        """强制设置状态机的状态。"""
        if sm_name in self.state_machines:
            self.state.set_variable(f"{sm_name}_state", state)
            logger.info(f"Forced state machine '{sm_name}' to state '{state}'")
            return True
        return False

    def get_state_machine_info(self, sm_name: str) -> Optional[Dict[str, Any]]:
        """获取状态机信息。"""
        return self.state_machines.get(sm_name)
