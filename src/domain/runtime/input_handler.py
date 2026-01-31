"""
ScriptRunner 的输入处理器。
处理玩家的自然语言输入。
"""

from typing import Dict, Any
from .interfaces import IInputHandler
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class InputHandler(IInputHandler):
    """处理玩家的自然语言输入。"""

    def __init__(self, parser, state_manager, command_executor, event_manager=None, condition_evaluator=None):
        self.parser = parser
        self.state = state_manager
        self.command_executor = command_executor
        self.event_manager = event_manager
        self.condition_evaluator = condition_evaluator

        # 可扩展的动作注册表
        self.action_handlers = {
            'take': self._execute_take,
            'use': self._execute_use,
            'examine': self._execute_examine,
            'attack': self._execute_attack,
            'search': self._execute_search,
            'combine': self._execute_combine,
            'inventory': self._execute_inventory,
        }

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家的自然语言输入并返回结果。"""
        logger.debug(f"Processing player input: {input_text}")

        # 解析输入
        parsed_command = self.parser.parse_player_command(input_text)

        action = parsed_command.get('action', 'unknown')
        target = parsed_command.get('target')

        logger.info(f"Parsed action: {action}, target: {target}")

        # 根据动作执行相应逻辑
        if action == 'unknown':
            return {
                'success': False,
                'message': f"我不理解 '{input_text}'。",
                'action': action
            }

        # 执行动作
        try:
            result = self._execute_action(action, target)

            # 如果动作执行成功，触发事件
            if result['success'] and self.event_manager:
                self.event_manager.trigger_player_action(action, target=target)

            return {
                'success': result['success'],
                'action': action,
                'target': target,
                'message': result['message'],
                'original_input': input_text
            }
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {
                'success': False,
                'action': action,
                'target': target,
                'message': f"执行动作 '{action}' 时出错。",
                'original_input': input_text
            }

    def _execute_action(self, action: str, target: str) -> Dict[str, Any]:
        """执行特定动作。"""
        # 使用可扩展的动作处理器
        handler = self.action_handlers.get(action)
        if handler:
            return handler(target)
        else:
            return {
                'success': False,
                'message': f"未知动作: {action}"
            }

    def register_action(self, action_name: str, handler):
        """注册新的动作处理器。"""
        self.action_handlers[action_name] = handler
        logger.info(f"Registered new action handler: {action_name}")

    def _execute_take(self, target: str) -> Dict[str, Any]:
        """执行拿起物品动作。"""
        if not target:
            return {'success': False, 'message': "需要指定要拿起的物品。"}

        # 检查物品是否存在且可访问
        obj = self.parser.get_object(target)
        if not obj:
            return {'success': False, 'message': f"这里没有 {target}。"}

        if not self._is_object_accessible(target):
            return {'success': False, 'message': f"这里没有 {target}。"}

        # 检查是否为可拿取物品
        if obj.get('type') not in ['item', 'loot']:
            return {'success': False, 'message': f"你无法拿起 {target}。"}

        # 添加到玩家库存
        inventory = self.state.get_variable('inventory', [])
        if target not in inventory:
            inventory.append(target)
            self.state.set_variable('inventory', inventory)
            # 从场景中移除物品
            self._remove_object_from_scene(target)
            return {'success': True, 'message': f"你拿起了 {target}。"}

        return {'success': False, 'message': f"你已经拿起了 {target}。"}

    def _execute_use(self, target: str) -> Dict[str, Any]:
        """执行使用物品动作。"""
        if not target:
            return {'success': False, 'message': "需要指定要使用的物品。"}

        inventory = self.state.get_variable('inventory', [])
        if target not in inventory:
            return {'success': False, 'message': f"你没有 {target}。"}

        # 简单的使用逻辑（可以扩展）
        return {'success': True, 'message': f"你使用了 {target}。"}

    def _execute_examine(self, target: str) -> Dict[str, Any]:
        """执行检查物品动作。"""
        if not target:
            return {'success': False, 'message': "需要指定要检查的物品。"}

        obj = self.parser.get_object(target)
        if not obj:
            return {'success': False, 'message': f"这里没有 {target}。"}

        # 检查是否在场景中或在库存中
        if not (self._is_object_accessible(target) or target in self.state.get_variable('inventory', [])):
            return {'success': False, 'message': f"这里没有 {target}。"}

        description = obj.get('description', f"这是一个 {target}。")
        return {'success': True, 'message': description}

    def _execute_attack(self, target: str) -> Dict[str, Any]:
        """执行攻击动作。"""
        if not target:
            return {'success': False, 'message': "需要指定攻击目标。"}

        # 检查目标是否在当前场景中
        if not self._is_object_accessible(target):
            return {'success': False, 'message': f"这里没有 {target}。"}

        obj = self.parser.get_object(target)
        if obj and obj.get('type') == 'creature':
            # 使用状态管理器存储可变状态
            health_var = f"{target}_health"
            default_health = obj.get('states', [{}])[0].get('value', 30)  # 从配置获取，默认30
            health = self.state.get_variable(health_var, default_health)

            if health > 0:
                # 计算伤害基于玩家属性
                player_strength = self.state.get_variable('player_strength', 10)
                base_damage = 5
                damage = base_damage + (player_strength // 2)  # 力量每2点加1点伤害

                health -= damage
                self.state.set_variable(health_var, health)

                if health <= 0:
                    # 执行击败逻辑，可能触发事件或命令
                    self.command_executor.execute_commands([{'set_flag': f"defeated_{target}"}])
                    return {'success': True, 'message': f"你击败了 {target}！"}
                else:
                    return {'success': True, 'message': f"你攻击了 {target}，造成了 {damage} 点伤害，它还剩下 {health} 点生命。"}

        return {'success': False, 'message': f"无法攻击 {target}。"}

    def _execute_search(self, target: str) -> Dict[str, Any]:
        """执行搜索动作。"""
        current_scene_id = self.state.get_current_scene()
        if not current_scene_id:
            return {'success': False, 'message': "无法确定当前位置。"}

        # 获取当前场景
        scene = self.parser.get_scene(current_scene_id)
        if not scene:
            return {'success': False, 'message': "场景信息不可用。"}

        # 检查是否有随机表用于搜索
        random_table_name = f"{current_scene_id}_search"
        table = self.parser.get_random_table(random_table_name)
        if table:
            # 使用随机表
            import random
            entries = table.get('entries', [])
            if entries:
                result = random.choice(entries)
                messages = []
                if isinstance(result, dict) and 'commands' in result:
                    # 执行命令并收集消息
                    command_messages = self.command_executor.execute_commands(result['commands'])
                    messages.extend(command_messages)
                base_message = f"你仔细搜索了{target or '周围'}，{result.get('message', '发现了什么东西！')}"
                messages.insert(0, base_message)
                return {'success': True, 'message': '\n'.join(messages)}

        # 检查事件系统是否有搜索相关事件
        # 这里可以扩展为触发事件系统中的搜索事件

        # 默认搜索逻辑
        return {'success': True, 'message': f"你搜索了{target or '周围'}，但没有发现什么特别的东西。"}

    def _execute_combine(self, target: str) -> Dict[str, Any]:
        """执行组合物品动作。"""
        if not target:
            return {'success': False, 'message': "需要指定要组合的物品。"}

        inventory = self.state.get_variable('inventory', [])

        # 检查是否有交互定义用于组合
        # 这里可以扩展为使用DSL中的interaction.multi_step定义
        # 例如，检查是否有craft_potion这样的交互

        # 简单的组合逻辑：检查常见组合
        combine_recipes = {
            'herb_potion': ['herb', 'bottle'],
            'sword_dagger': ['sword', 'dagger'],  # 示例
        }

        for result, ingredients in combine_recipes.items():
            if all(item in inventory for item in ingredients):
                # 移除原料
                for item in ingredients:
                    inventory.remove(item)
                self.state.set_variable('inventory', inventory)

                # 添加结果
                inventory.append(result)
                self.state.set_variable('inventory', inventory)

                return {'success': True, 'message': f"你成功组合出了 {result}！"}

        # 如果没有匹配的配方
        return {'success': False, 'message': f"你尝试组合 {target}，但没有成功。"}

    def _execute_inventory(self, target: str) -> Dict[str, Any]:
        """执行查看背包动作。"""
        inventory = self.state.get_variable('inventory', [])
        if not inventory:
            return {'success': True, 'message': "你的背包是空的。"}

        # 获取物品描述
        item_descriptions = []
        for item_id in inventory:
            obj = self.parser.get_object(item_id)
            if obj:
                name = obj.get('name', item_id)
                item_descriptions.append(f"- {name}")
            else:
                item_descriptions.append(f"- {item_id}")

        message = "你的背包中有：\n" + "\n".join(item_descriptions)
        return {'success': True, 'message': message}

    def _is_object_accessible(self, obj_id: str) -> bool:
        """检查对象是否在当前场景中可访问。"""
        current_scene_id = self.state.get_current_scene()
        if not current_scene_id:
            return False

        scene = self.parser.get_scene(current_scene_id)
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
