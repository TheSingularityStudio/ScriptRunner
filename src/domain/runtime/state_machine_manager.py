"""
ScriptRunner 的状态机管理器。
处理 DSL 状态机系统的状态转换和自动更新。
"""

from typing import Dict, Any, List, Optional
import time
from .interfaces import IStateMachineManager
from ...infrastructure.logger import get_logger
from .action_executor import ActionExecutor

logger = get_logger(__name__)


class StateMachineManager(IStateMachineManager):
    """管理游戏状态机系统。"""

    def __init__(self, parser, state_manager, command_executor, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.condition_evaluator = condition_evaluator

        # 统一的动作执行器
        self.action_executor = ActionExecutor(state_manager, command_executor)

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

        except (AttributeError, TypeError, KeyError) as e:
            logger.warning(f"Failed to load state machines due to data structure error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading state machines: {e}")

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
        """
        Evaluate the condition for a state machine transition.

        This method handles various types of transition conditions, including time-based
        conditions and general game state conditions. Time conditions support ranges
        using logical AND (&&) operator.

        Args:
            transition: Dictionary containing transition data, must include 'condition' key

        Returns:
            True if the condition is met and transition should occur, False otherwise

        Supported condition formats:
            - Time conditions: "time > 360", "time >= 100 && time < 200"
            - General conditions: Any condition supported by ConditionEvaluator
            - Empty/None conditions: Always return False (no automatic transition)

        Note:
            - Time conditions compare against the 'game_time' state variable
            - Complex time ranges are supported via && conjunction
            - Invalid time conditions are logged and return False
            - Non-time conditions are delegated to the condition evaluator
        """
        condition = transition.get('condition')

        if not condition:
            # No condition means transition doesn't happen automatically
            return False

        # Handle time-based conditions with support for ranges
        if condition.startswith('time > ') or condition.startswith('time >= ') or \
           condition.startswith('time < ') or condition.startswith('time <= '):
            try:
                # Parse compound time conditions like "time > 360 && time < 420"
                time_conditions = condition.split('&&')
                game_time = self.state.get_variable('game_time', 0)

                # Check each time condition in the compound statement
                for time_cond in time_conditions:
                    time_cond = time_cond.strip()
                    if time_cond.startswith('time > '):
                        # Greater than condition: time > threshold
                        threshold = float(time_cond[7:])
                        if not (game_time > threshold):
                            return False
                    elif time_cond.startswith('time >= '):
                        # Greater than or equal: time >= threshold
                        threshold = float(time_cond[8:])
                        if not (game_time >= threshold):
                            return False
                    elif time_cond.startswith('time < '):
                        # Less than condition: time < threshold
                        threshold = float(time_cond[7:])
                        if not (game_time < threshold):
                            return False
                    elif time_cond.startswith('time <= '):
                        # Less than or equal: time <= threshold
                        threshold = float(time_cond[8:])
                        if not (game_time <= threshold):
                            return False

                # All time conditions in the compound statement are satisfied
                return True

            except (ValueError, IndexError) as e:
                # Log parsing errors for time conditions
                logger.warning(f"Invalid time condition '{condition}': {e}")
                return False

        # Delegate non-time conditions to the general condition evaluator
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
        self.action_executor.execute_action(action)

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

    def transition_state(self, machine_name: str, event: str) -> bool:
        """状态转换。"""
        if machine_name not in self.state_machines:
            return False

        current_state = self.get_current_state(machine_name)
        if not current_state:
            return False

        sm_data = self.state_machines[machine_name]
        states = sm_data.get('states', {})
        state_def = states.get(current_state, {})

        transitions = state_def.get('transitions', [])
        for transition in transitions:
            if transition.get('event') == event and self._check_transition_condition(transition):
                new_state = transition.get('to')
                if new_state and new_state != current_state:
                    self._execute_state_transition(machine_name, current_state, new_state, transition)
                    return True

        return False
