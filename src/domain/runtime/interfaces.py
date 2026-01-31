"""
ScriptRunner 运行时组件抽象接口。
定义核心组件的接口以提高抽象层质量。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISceneExecutor(ABC):
    """场景执行器接口。"""

    @abstractmethod
    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        pass


class ICommandExecutor(ABC):
    """命令执行器接口。"""

    @abstractmethod
    def execute_commands(self, commands: List[Dict[str, Any]]) -> None:
        """执行命令列表。"""
        pass

    @abstractmethod
    def execute_command(self, command: Dict[str, Any]) -> None:
        """执行单个命令。"""
        pass


class IConditionEvaluator(ABC):
    """条件评估器接口。"""

    @abstractmethod
    def evaluate_condition(self, condition: Optional[str]) -> bool:
        """评估条件字符串。"""
        pass


class IChoiceProcessor(ABC):
    """选择处理器接口。"""

    @abstractmethod
    def process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理玩家选择并返回下一个场景和消息列表。"""
        pass

    @abstractmethod
    def get_available_choices(self) -> List[Dict[str, Any]]:
        """获取当前可用选择列表。"""
        pass


class IInputHandler(ABC):
    """输入处理器接口。"""

    @abstractmethod
    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入。"""
        pass


class IEventManager(ABC):
    """事件管理器接口。"""

    @abstractmethod
    def check_scheduled_events(self) -> None:
        """检查定时事件。"""
        pass

    @abstractmethod
    def check_reactive_events(self, trigger_type: str, **kwargs) -> None:
        """检查反应事件。"""
        pass

    @abstractmethod
    def update_game_time(self, delta_time: float) -> None:
        """更新游戏时间。"""
        pass

    @abstractmethod
    def trigger_player_action(self, action: str, **kwargs) -> None:
        """触发玩家动作事件。"""
        pass


class IEffectsManager(ABC):
    """效果管理器接口。"""

    @abstractmethod
    def apply_effect(self, effect_name: str, target: Optional[str] = None) -> bool:
        """应用效果。"""
        pass

    @abstractmethod
    def remove_effect(self, effect_name: str) -> bool:
        """移除效果。"""
        pass

    @abstractmethod
    def update_effects(self) -> None:
        """更新效果。"""
        pass

    @abstractmethod
    def get_active_effects(self, target: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """获取活跃效果。"""
        pass

    @abstractmethod
    def has_effect(self, effect_name: str, target: Optional[str] = None) -> bool:
        """检查是否有指定效果。"""
        pass

    @abstractmethod
    def get_effect_modifier(self, stat_name: str, target: Optional[str] = None) -> float:
        """获取效果修正值。"""
        pass


class IStateMachineManager(ABC):
    """状态机管理器接口。"""

    @abstractmethod
    def load_state_machines(self) -> None:
        """加载状态机。"""
        pass

    @abstractmethod
    def get_current_state(self, machine_name: str) -> Optional[str]:
        """获取当前状态。"""
        pass

    @abstractmethod
    def transition_state(self, machine_name: str, event: str) -> bool:
        """状态转换。"""
        pass


class IMetaManager(ABC):
    """元数据管理器接口。"""

    @abstractmethod
    def load_meta_data(self) -> None:
        """加载元数据。"""
        pass

    @abstractmethod
    def get_meta_value(self, key: str) -> Any:
        """获取元数据值。"""
        pass

    @abstractmethod
    def set_meta_value(self, key: str, value: Any) -> None:
        """设置元数据值。"""
        pass


class IRandomManager(ABC):
    """随机管理器接口。"""

    @abstractmethod
    def load_random_tables(self) -> None:
        """加载随机表。"""
        pass

    @abstractmethod
    def roll_dice(self, sides: int) -> int:
        """掷骰子。"""
        pass

    @abstractmethod
    def get_random_from_table(self, table_name: str) -> Any:
        """从随机表获取随机值。"""
        pass


class IExecutionEngine(ABC):
    """执行引擎接口。"""

    @abstractmethod
    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景。"""
        pass

    @abstractmethod
    def process_choice(self, choice_index: int) -> tuple[Optional[str], List[str]]:
        """处理选择。"""
        pass

    @abstractmethod
    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家输入。"""
        pass
