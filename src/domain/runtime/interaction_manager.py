"""
ScriptRunner 的互动管理器。
处理 DSL 互动系统的多步骤互动和物理互动。
"""

from typing import Dict, Any, List, Optional
import random
from .interfaces import IInteractionManager
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class InteractionManager(IInteractionManager):
    """管理游戏互动系统。"""

    def __init__(self, parser, state_manager, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator

        # 互动数据
        self.interaction_data: Dict[str, Any] = {}

        # 当前活跃的多步骤互动
        self.active_interactions: Dict[str, Dict[str, Any]] = {}

        logger.info("InteractionManager initialized")

    def load_interaction_data(self):
        """从解析器加载互动数据。"""
        try:
            self.interaction_data = self.parser.get_interaction_data()
            if self.interaction_data:
                logger.info(f"Loaded interaction data with {len(self.interaction_data)} sections")
        except Exception as e:
            logger.warning(f"Failed to load interaction data: {e}")
            self.interaction_data = {}

    def start_multi_step_interaction(self, interaction_name: str) -> Dict[str, Any]:
        """开始多步骤互动。"""
        if interaction_name not in self.interaction_data.get('multi_step', {}):
            return {'success': False, 'message': f"互动 '{interaction_name}' 未找到。"}

        interaction = self.interaction_data['multi_step'][interaction_name]

        # 初始化互动状态
        self.active_interactions[interaction_name] = {
            'current_step': 1,
            'data': {},
            'interaction': interaction
        }

        # 返回第一步的提示
        first_step = interaction['steps'][1]
        return {
            'success': True,
            'interaction_name': interaction_name,
            'step': 1,
            'prompt': first_step['prompt'],
            'options': first_step.get('options', [])
        }

    def process_multi_step_step(self, interaction_name: str, step: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多步骤互动的步骤。"""
        if interaction_name not in self.active_interactions:
            return {'success': False, 'message': "没有活跃的互动。"}

        active = self.active_interactions[interaction_name]
        interaction = active['interaction']

        if step not in interaction['steps']:
            return {'success': False, 'message': f"步骤 {step} 不存在。"}

        step_data = interaction['steps'][step]

        # 验证输入
        if 'validate' in step_data:
            validation = step_data['validate']
            # 简单的验证逻辑，这里可以扩展
            if not self._validate_input(validation, input_data):
                return {'success': False, 'message': "输入无效。"}

        # 存储步骤数据
        active['data'][f'step_{step}'] = input_data

        # 检查是否是最后一步
        total_steps = len(interaction['steps'])
        if step >= total_steps:
            # 完成互动
            result = self._complete_interaction(interaction_name)
            del self.active_interactions[interaction_name]
            return result

        # 移动到下一步
        next_step = step + 1
        active['current_step'] = next_step
        next_step_data = interaction['steps'][next_step]

        return {
            'success': True,
            'interaction_name': interaction_name,
            'step': next_step,
            'prompt': next_step_data['prompt'],
            'options': next_step_data.get('options', [])
        }

    def execute_physics_interaction(self, interaction_type: str, **kwargs) -> Dict[str, Any]:
        """执行物理互动。"""
        physics_data = self.interaction_data.get('physics', {})
        if interaction_type not in physics_data:
            return {'success': False, 'message': f"物理互动 '{interaction_type}' 未找到。"}

        interaction = physics_data[interaction_type]

        # 计算成功几率
        base_chance = interaction.get('base_chance', 0.5)
        modifiers = interaction.get('modifiers', {})

        # 应用修改器
        chance = base_chance
        for attr, modifier in modifiers.items():
            if '.' in modifier:
                # 复杂修改器，如 "0.1 per point above 10"
                parts = modifier.split()
                if len(parts) >= 4 and parts[1] == 'per' and parts[2] == 'point' and parts[3] == 'above':
                    threshold = int(parts[4])
                    per_point = float(parts[0])
                    attr_value = self.state.get_variable(attr, 0)
                    if attr_value > threshold:
                        bonus = (attr_value - threshold) * per_point
                        chance += bonus
            else:
                # 简单乘数
                attr_value = self.state.get_variable(attr, 0)
                chance += attr_value * float(modifier)

        # 确保几率在0-1之间
        chance = max(0, min(1, chance))

        # 掷骰
        success = random.random() < chance

        if success:
            return {'success': True, 'message': f"你成功执行了 {interaction_type}。"}
        else:
            return {'success': False, 'message': f"你未能成功执行 {interaction_type}。"}

    def _validate_input(self, validation: str, input_data: Dict[str, Any]) -> bool:
        """验证输入数据。"""
        # 这里实现简单的验证逻辑
        # 例如: "item in inventory and item.type = 'herb'"
        try:
            # 简单的解析，这里可以扩展为更复杂的条件评估
            if 'item' in input_data:
                item = input_data['item']
                inventory = self.state.get_variable('inventory', [])
                if item not in inventory:
                    return False
            return True
        except Exception:
            return False

    def _complete_interaction(self, interaction_name: str) -> Dict[str, Any]:
        """完成互动并返回结果。"""
        active = self.active_interactions[interaction_name]
        interaction = active['interaction']
        data = active['data']

        # 这里可以根据数据生成结果
        # 简单的实现
        result = interaction.get('result', {})
        success_msg = result.get('success', "互动完成！")
        failure_msg = result.get('failure', "互动失败。")

        # 假设总是成功
        return {'success': True, 'message': success_msg}