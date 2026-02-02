"""
ScriptRunner 的输入处理器。
处理玩家的自然语言输入。
"""

from typing import Dict, Any, Optional, Callable
from .interfaces import IInputHandler
from ...infrastructure.logger import get_logger
from ...infrastructure.config import Config
from ...infrastructure.container import Container
from ...infrastructure.plugin_manager import PluginManager
from ...infrastructure.plugin_interface import ActionPlugin
from ...utils.exceptions import ExecutionError, GameError

logger = get_logger(__name__)


class InputHandler(IInputHandler):
    """处理玩家的自然语言输入。"""

    def __init__(self, container: Container, config: Config):
        self.container = container
        self.config = config

        # 懒加载依赖
        self._parser = None
        self._state_manager = None
        self._command_executor = None
        self._event_manager = None
        self._condition_evaluator = None
        self._interaction_manager = None
        self._action_executor = None

        # 获取插件管理器（已由ApplicationInitializer加载）
        self.plugin_manager = self.container.get('plugin_manager')

        # 从插件加载动作处理器
        self.action_handlers: Dict[str, Callable[[str], Dict[str, Any]]] = {}
        self._load_actions_from_plugins()

        # 从脚本加载组合配方（将在第一次访问parser时设置）
        self._combine_recipes = None

        # 缓存常用数据
        self._scene_cache: Dict[str, Any] = {}
        self._object_cache: Dict[str, Any] = {}

    def _load_actions_from_plugins(self):
        """从插件加载动作处理器。"""
        action_plugins = self.plugin_manager.get_plugins_by_type(ActionPlugin)
        for plugin in action_plugins:
            actions = plugin.get_actions()
            for action_name, action_func in actions.items():
                # 创建包装函数，为动作函数提供上下文
                def create_wrapped_handler(action_func, action_name):
                    def wrapped_handler(target: str) -> Dict[str, Any]:
                        context = self._get_action_context()
                        return action_func(target, context)
                    return wrapped_handler
                
                self.action_handlers[action_name] = create_wrapped_handler(action_func, action_name)
                logger.info(f"Loaded action '{action_name}' from plugin '{plugin.name}'")

    def _get_action_context(self) -> Dict[str, Any]:
        """获取动作执行上下文。"""
        state = self.state
        if not hasattr(state, 'get_variable'):
            logger.error(f"State manager is not properly initialized: {type(state)}")
            raise ExecutionError("State manager is not properly initialized")
        return {
            'parser': self.parser,
            'state': state,
            'config': self.config,
            'condition_evaluator': self.condition_evaluator,
            'interaction_manager': self.interaction_manager,
            'action_executor': self.action_executor,
            'input_handler': self,
            'is_object_accessible': self._is_object_accessible,
        }

    @property
    def parser(self):
        if self._parser is None:
            self._parser = self.container.get('parser')
        return self._parser

    @property
    def state(self):
        if self._state_manager is None:
            self._state_manager = self.container.get('state_manager')
        return self._state_manager

    @property
    def command_executor(self):
        if self._command_executor is None:
            self._command_executor = self.container.get('command_executor')
        return self._command_executor

    @property
    def event_manager(self):
        if self._event_manager is None and self.container.has('event_manager'):
            self._event_manager = self.container.get('event_manager')
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value):
        self._event_manager = value

    @property
    def condition_evaluator(self):
        if self._condition_evaluator is None and self.container.has('condition_evaluator'):
            self._condition_evaluator = self.container.get('condition_evaluator')
        return self._condition_evaluator

    @condition_evaluator.setter
    def condition_evaluator(self, value):
        self._condition_evaluator = value

    @property
    def interaction_manager(self):
        if self._interaction_manager is None and self.container.has('interaction_manager'):
            self._interaction_manager = self.container.get('interaction_manager')
        return self._interaction_manager

    @interaction_manager.setter
    def interaction_manager(self, value):
        self._interaction_manager = value

    @property
    def action_executor(self):
        if self._action_executor is None and self.container.has('action_executor'):
            self._action_executor = self.container.get('action_executor')
        return self._action_executor

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """
        处理玩家的自然语言输入并返回结果。

        Args:
            input_text: 玩家的输入文本

        Returns:
            包含处理结果的字典，包含success, message, action等键

        Raises:
            GameError: 当输入处理失败时抛出
        """
        logger.debug(f"Processing player input: {input_text}")
        start_time = logger.isEnabledFor(10)  # DEBUG level

        try:
            # 解析输入
            parsed_command = self.parser.parse_player_command(input_text)
            action = parsed_command.get('action', 'unknown')
            target = parsed_command.get('target')

            logger.debug(f"Parsed action: {action}, target: {target}")

            # 验证动作
            if action == 'unknown':
                message = self.config.get('messages.unknown_action', f"我不理解 '{input_text}'。")
                return {
                    'success': False,
                    'message': message,
                    'action': action
                }

            # 执行动作
            result = self._execute_action(action, target)

            # 如果动作执行成功，触发事件
            if result['success'] and self.event_manager:
                try:
                    self.event_manager.trigger_player_action(action, target=target)
                    logger.debug(f"Triggered event for action: {action}")
                except Exception as e:
                    logger.warning(f"Failed to trigger event for action {action}: {e}")

            if start_time:
                logger.debug(f"Input processing completed in {logger.isEnabledFor(10)}ms")

            return {
                'success': result['success'],
                'action': action,
                'target': target,
                'message': result['message'],
                'original_input': input_text
            }

        except ExecutionError as e:
            logger.error(f"Execution error for input '{input_text}': {e}")
            return {
                'success': False,
                'action': action if 'action' in locals() else 'unknown',
                'target': target if 'target' in locals() else None,
                'message': str(e),
                'original_input': input_text
            }
        except Exception as e:
            logger.error(f"Unexpected error processing input '{input_text}': {e}")
            return {
                'success': False,
                'action': action if 'action' in locals() else 'unknown',
                'target': target if 'target' in locals() else None,
                'message': f"处理输入时发生意外错误: {e}",
                'original_input': input_text
            }

    def _execute_action(self, action: str, target: str) -> Dict[str, Any]:
        """
        执行特定动作。

        Args:
            action: 动作名称
            target: 目标对象

        Returns:
            执行结果字典

        Raises:
            ExecutionError: 当动作执行失败时抛出
        """
        logger.debug(f"Executing action: {action} with target: {target}")

        # 使用可扩展的动作处理器
        handler = self.action_handlers.get(action)
        if not handler:
            raise ExecutionError(f"未知动作: {action}")

        try:
            result = handler(target)
            logger.debug(f"Action {action} executed with result: success={result['success']}")

            # 如果有action_executor且有actions，执行它们
            if self.action_executor and result.get('actions'):
                try:
                    self.action_executor.execute_actions(result['actions'])
                    logger.debug(f"Executed {len(result['actions'])} additional actions for {action}")
                except Exception as e:
                    logger.error(f"Error executing additional actions for {action}: {e}")
                    raise ExecutionError(f"执行动作 '{action}' 的附加操作时出错") from e

            return result

        except ExecutionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in action {action}: {e}")
            raise ExecutionError(f"执行动作 '{action}' 时发生意外错误") from e

    def register_action(self, action_name: str, handler: Callable[[str], Dict[str, Any]]):
        """
        注册新的动作处理器。

        Args:
            action_name: 动作名称
            handler: 动作处理函数
        """
        self.action_handlers[action_name] = handler
        logger.info(f"Registered new action handler: {action_name}")

    def validate_target(self, target: str, require_accessible: bool = True) -> Optional[Dict[str, Any]]:
        """
        验证目标对象是否存在且可访问。

        Args:
            target: 目标对象ID
            require_accessible: 是否要求对象可访问

        Returns:
            对象数据字典，如果无效则返回None

        Raises:
            ExecutionError: 当目标无效时抛出
        """
        if not target:
            raise ExecutionError("需要指定目标对象")

        obj = self._get_cached_object(target)
        if not obj:
            raise ExecutionError(f"这里没有 {target}")

        if require_accessible and not self._is_object_accessible(target):
            raise ExecutionError(f"无法访问 {target}")

        return obj








    def _get_cached_object(self, obj_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的对象数据。"""
        if obj_id not in self._object_cache:
            self._object_cache[obj_id] = self.parser.get_object(obj_id)
        return self._object_cache[obj_id]

    def _get_cached_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的场景数据。"""
        if scene_id not in self._scene_cache:
            self._scene_cache[scene_id] = self.parser.get_scene(scene_id)
        return self._scene_cache[scene_id]

    def _is_object_accessible(self, obj_id: str) -> bool:
        """
        检查对象是否在当前场景中可访问。

        Args:
            obj_id: 对象ID

        Returns:
            是否可访问
        """
        current_scene_id = self.state.get_current_scene()
        if not current_scene_id:
            return False

        scene = self._get_cached_scene(current_scene_id)
        if not scene:
            return False

        # 检查场景中的对象列表
        objects_in_scene = scene.get('objects', [])
        for obj_ref in objects_in_scene:
            if isinstance(obj_ref, dict) and obj_ref.get('ref') == obj_id:
                return True
            elif isinstance(obj_ref, str) and obj_ref == obj_id:
                return True

        return False

    def _remove_object_from_scene(self, obj_id: str):
        """从当前场景中移除对象。"""
        current_scene_id = self.state.get_current_scene()
        if not current_scene_id:
            return

        # 注意：这里我们不能直接修改parser的数据，因为它是不可变的
        # 相反，我们应该在状态管理器中记录移除的对象
        removed_objects = self.state.get_variable('removed_objects', [])
        if obj_id not in removed_objects:
            removed_objects.append(obj_id)
            self.state.set_variable('removed_objects', removed_objects)
