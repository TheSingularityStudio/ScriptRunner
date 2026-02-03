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


class IInteractionManager(ABC):
    """互动管理器接口。"""

    @abstractmethod
    def start_multi_step_interaction(self, interaction_name: str) -> Dict[str, Any]:
        """开始多步骤互动。"""
        pass

    @abstractmethod
    def process_multi_step_step(self, interaction_name: str, step: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多步骤互动的步骤。"""
        pass

    @abstractmethod
    def execute_physics_interaction(self, interaction_type: str, **kwargs) -> Dict[str, Any]:
        """执行物理互动。"""
        pass


class IScriptObject(ABC):
    """脚本对象接口，用于面向对象的脚本执行。"""

    @abstractmethod
    def get_variable(self, name: str) -> Any:
        """获取脚本变量。"""
        pass

    @abstractmethod
    def set_variable(self, name: str, value: Any) -> None:
        """设置脚本变量。"""
        pass

    @abstractmethod
    def execute_action(self, action_name: str, **kwargs) -> Any:
        """执行脚本动作。"""
        pass

    @abstractmethod
    def trigger_event(self, event_name: str, **kwargs) -> Any:
        """触发脚本事件。"""
        pass
