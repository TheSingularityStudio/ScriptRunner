"""
ScriptRunner 的玩家动作插件。
提供玩家输入相关的动作，如拿起、使用、检查等。
"""

from typing import Dict, Any, List, Callable
from src.infrastructure.plugin_interface import ActionPlugin
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)


class PlayerActionsPlugin(ActionPlugin):
    """提供玩家动作的基础插件。"""

    @property
    def name(self) -> str:
        return "PlayerActions"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件。"""
        logger.info("PlayerActions plugin initialized")
        return True

    def shutdown(self) -> None:
        """关闭插件。"""
        logger.info("PlayerActions plugin shutdown")

    def get_actions(self) -> Dict[str, Callable[[str, Dict[str, Any]], Dict[str, Any]]]:
        """返回此插件提供的动作。"""
        return {
            'take': self._execute_take,
            'use': self._execute_use,
            'examine': self._execute_examine,
            'combine': self._execute_combine,
            'inventory': self._execute_inventory,
            'add_item': self._execute_add_item,
        }

    def _execute_take(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行拿起物品动作。"""
        parser = context['parser']
        state = context['state']
        config = context['config']
        
        try:
            obj = self._validate_target(target, context, require_accessible=True)
            if not obj:
                return {'success': False, 'message': f"无法找到 {target}", 'actions': []}

            # 检查是否为可拿取物品
            if obj.get('type') not in ['item', 'loot']:
                return {'success': False, 'message': f"无法拿起 {target}", 'actions': []}

            # 检查是否已经在库存中
            inventory = state.get_variable('inventory', [])
            if target in inventory:
                return {'success': False, 'message': f"已经拿起了 {target}", 'actions': []}

            # 构建DSL动作
            actions = [
                f"set:inventory={inventory + [target]}",  # 添加到库存
                f"add_flag:removed_{target}"  # 标记为已移除
            ]

            message = config.get('messages.take_success', f"你拿起了 {target}。")
            message = message.replace('{target}', target)
            return {'success': True, 'message': message, 'actions': actions}

        except Exception as e:
            return {'success': False, 'message': str(e), 'actions': []}

    def _execute_use(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行使用物品动作。"""
        parser = context['parser']
        state = context['state']

        if not target:
            return {'success': False, 'message': "需要指定要使用的物品。", 'actions': []}

        inventory = state.get_variable('inventory', [])
        if target not in inventory:
            return {'success': False, 'message': f"你没有 {target}。", 'actions': []}

        # 获取物品对象
        obj = parser.get_object(target)
        if not obj:
            return {'success': False, 'message': f"无法找到物品 {target}。", 'actions': []}

        actions = []
        message = ""

        # 根据物品类型处理使用逻辑
        item_type = obj.get('type', 'item')
        if item_type == 'item':
            # 检查是否有治疗属性
            if 'healing' in obj:
                healing_amount = obj['healing']
                current_health = state.get_variable('health', 100)
                max_health = state.get_variable('max_health', 100)
                new_health = min(max_health, current_health + healing_amount)
                actions.append(f"set:health={new_health}")
                message = f"你使用了 {target}，恢复了 {healing_amount} 点生命值。"
                # 移除物品
                new_inventory = [item for item in inventory if item != target]
                actions.append(f"set:inventory={new_inventory}")

            # 检查是否有魔法恢复属性
            elif 'mana_restore' in obj:
                mana_restore = obj['mana_restore']
                current_mana = state.get_variable('mana', 0)
                max_mana = state.get_variable('max_mana', 100)
                new_mana = min(max_mana, current_mana + mana_restore)
                actions.append(f"set:mana={new_mana}")
                message = f"你使用了 {target}，恢复了 {mana_restore} 点魔法值。"
                # 移除物品
                new_inventory = [item for item in inventory if item != target]
                actions.append(f"set:inventory={new_inventory}")

            else:
                message = f"你使用了 {target}，但没有任何效果。"

        else:
            message = f"{target} 不是可使用的物品。"

        return {'success': True, 'message': message, 'actions': actions}

    def _execute_examine(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行检查物品动作。"""
        parser = context['parser']
        state = context['state']
        
        try:
            obj = self._validate_target(target, context, require_accessible=False)
            if not obj:
                return {'success': False, 'message': f"无法找到 {target}", 'actions': []}

            # 检查是否在场景中或在库存中
            inventory = state.get_variable('inventory', [])
            if not (context['is_object_accessible'](target) or target in inventory):
                return {'success': False, 'message': f"无法检查 {target}", 'actions': []}

            description = obj.get('description', f"这是一个 {target}。")
            return {'success': True, 'message': description, 'actions': []}

        except Exception as e:
            return {'success': False, 'message': str(e), 'actions': []}

    def _execute_combine(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行组合物品动作。"""
        state = context['state']
        config = context['config']
        interaction_manager = context.get('interaction_manager')
        
        try:
            if not target:
                return {'success': False, 'message': "需要指定要组合的物品", 'actions': []}

            # 检查是否有对应的多步骤互动
            if interaction_manager:
                multi_step = interaction_manager.interaction_data.get('multi_step', {})
                if target in multi_step:
                    return interaction_manager.start_multi_step_interaction(target)

            inventory = state.get_variable('inventory', [])

            # 从输入处理器获取组合配方
            combine_recipes = context['input_handler'].combine_recipes

            # 检查配方
            for result, ingredients in combine_recipes.items():
                if all(item in inventory for item in ingredients):
                    # 构建动作：移除原料，添加结果
                    new_inventory = [item for item in inventory if item not in ingredients] + [result]
                    actions = [f"set:inventory={new_inventory}"]
                    message = config.get('messages.combine_success', f"你成功组合出了 {result}！")
                    return {'success': True, 'message': message, 'actions': actions}

            # 如果没有匹配的配方
            return {'success': False, 'message': f"无法组合 {target}", 'actions': []}

        except Exception as e:
            return {'success': False, 'message': str(e), 'actions': []}

    def _execute_inventory(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行查看背包动作。"""
        state = context['state']
        config = context['config']
        
        inventory = state.get_variable('inventory', [])
        if not inventory:
            message = config.get('messages.inventory_empty', "你的背包是空的。")
        else:
            items_str = ', '.join(inventory)
            message = config.get('messages.inventory_show', f"你的背包里有: {items_str}")
        
        return {'success': True, 'message': message, 'actions': []}

    def _validate_target(self, target: str, context: Dict[str, Any], require_accessible: bool = True) -> Dict[str, Any]:
        """验证目标对象。"""
        parser = context['parser']
        
        if not target:
            raise ValueError("需要指定目标对象")

        obj = parser.get_object(target)
        if not obj:
            raise ValueError(f"这里没有 {target}")

        if require_accessible and not context['is_object_accessible'](target):
            raise ValueError(f"无法访问 {target}")

        return obj

    def _is_object_accessible(self, target: str, context: Dict[str, Any]) -> bool:
        """检查对象是否可访问。"""
        parser = context['parser']
        state = context['state']
        
        current_scene_id = state.get_current_scene()
        if not current_scene_id:
            return False

        scene = parser.get_scene(current_scene_id)
        if not scene:
            return False

        # 检查对象是否在当前场景中
        return target in scene.get('objects', [])

    def _execute_add_item(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行添加物品到背包动作。"""
        state = context['state']
        config = context['config']
        
        if not target:
            return {'success': False, 'message': "需要指定要添加的物品。", 'actions': []}

        try:
            # 获取当前背包
            inventory = state.get_variable('inventory', [])
            
            # 检查物品是否已经在背包中
            if target in inventory:
                return {'success': False, 'message': f"你已经拥有 {target}。", 'actions': []}

            # 添加物品到背包
            new_inventory = inventory + [target]
            actions = [f"set:inventory={new_inventory}"]
            
            message = config.get('messages.add_item_success', f"获得了 {target}。")
            message = message.replace('{item}', target)
            return {'success': True, 'message': message, 'actions': actions}

        except Exception as e:
            return {'success': False, 'message': str(e), 'actions': []}