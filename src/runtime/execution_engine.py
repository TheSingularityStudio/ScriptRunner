from typing import Dict, Any, List, Optional
import re
import random

class ExecutionEngine:
    def __init__(self, parser, state_manager):
        self.parser = parser
        self.state = state_manager
        self.active_effects = {}  # DSL effects

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果，支持DSL语法。"""
        scene = self.parser.get_scene(scene_id)
        if not scene:
            raise ValueError(f"场景'{scene_id}'未找到")

        self.state.set_current_scene(scene_id)

        # 执行场景中的任何命令
        self._execute_commands(scene.get('commands', []))

        # 处理DSL变量替换
        processed_scene = self._process_scene(scene)

        # 确保有'text'字段（兼容传统格式）
        if 'description' in processed_scene and 'text' not in processed_scene:
            processed_scene['text'] = self._replace_variables(processed_scene['description'])

        return processed_scene

    def _execute_commands(self, commands: List[Dict[str, Any]]):
        """执行场景命令，支持DSL命令。"""
        for command in commands:
            self._execute_command(command)

    def _execute_command(self, command: Dict[str, Any]):
        """执行单个命令，支持DSL扩展。"""
        if 'set' in command:
            self._execute_set_command(command['set'])
        elif 'add_flag' in command:
            self.state.set_flag(command['add_flag'])
        elif 'remove_flag' in command:
            self.state.clear_flag(command['remove_flag'])
        elif 'spawn_object' in command:
            self._execute_spawn_command(command['spawn_object'])
        elif 'apply_effect' in command:
            self._execute_apply_effect_command(command['apply_effect'])
        elif 'remove_effect' in command:
            self._execute_remove_effect_command(command['remove_effect'])
        elif 'roll_table' in command:
            self._execute_roll_table_command(command['roll_table'])
        # 根据需要添加更多命令类型

    def _execute_set_command(self, expression: str):
        """执行设置命令（例如，'variable = value'）。"""
        match = re.match(r'(\w+)\s*=\s*(.+)', expression)
        if match:
            var_name, value = match.groups()
            # 简单评估 - 在实际实现中，您需要一个适当的表达式评估器
            if value.isdigit():
                self.state.set_variable(var_name, int(value))
            elif value.lower() in ('true', 'false'):
                self.state.set_variable(var_name, value.lower() == 'true')
            else:
                self.state.set_variable(var_name, value.strip('"\'')) 

    def _execute_spawn_command(self, obj_ref: str):
        """执行生成对象命令。"""
        self.state.set_variable(f"spawned_{obj_ref}", True)

    def _execute_apply_effect_command(self, effect_name: str):
        """执行应用效果命令。"""
        effect_data = self.parser.get_effect(effect_name)
        if effect_data:
            self.state.apply_effect(effect_name, effect_data)

    def _execute_remove_effect_command(self, effect_name: str):
        """执行移除效果命令。"""
        self.state.remove_effect(effect_name)

    def _execute_roll_table_command(self, table_name: str):
        """执行掷骰表命令。"""
        table = self.parser.get_random_table(table_name)
        if table:
            result = self._roll_table(table)
            self.state.set_variable(f"roll_result_{table_name}", result)

    def _roll_table(self, table: Dict[str, Any]) -> str:
        """掷骰表。"""
        if table.get('type') == 'weighted':
            entries = table.get('entries', [])
            total_weight = sum(entry.get('weight', 1) for entry in entries)
            roll = random.randint(1, total_weight)
            current_weight = 0
            for entry in entries:
                current_weight += entry.get('weight', 1)
                if roll <= current_weight:
                    return entry.get('value', '')
        return ''

    def _process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """处理场景的条件内容，支持DSL。"""
        processed = scene.copy()

        # 处理条件选择
        choices = scene.get('choices', [])
        processed_choices = []

        for choice in choices:
            if self._evaluate_condition(choice.get('condition')):
                processed_choices.append(choice)

        processed['choices'] = processed_choices
        return processed

    def _replace_variables(self, text: str) -> str:
        """替换DSL变量。"""
        variables = self.parser.get_scene(self.state.get_current_scene()).get('variables', {})

        for var_name, var_value in variables.items():
            if isinstance(var_value, list):
                # 随机选择
                replacement = random.choice(var_value)
            elif isinstance(var_value, str) and '-' in var_value:
                # 范围随机
                try:
                    min_val, max_val = map(int, var_value.split('-'))
                    replacement = str(random.randint(min_val, max_val))
                except ValueError:
                    replacement = var_value
            else:
                replacement = str(var_value)

            text = text.replace(f"{{{var_name}}}", replacement)

        return text

    def _evaluate_condition(self, condition: Optional[str]) -> bool:
        """评估简单条件，支持DSL扩展。"""
        if not condition:
            return True

        # 非常基本的条件评估 - 根据需要扩展
        if '==' in condition:
            left, right = condition.split('==', 1)
            left = left.strip()
            right = right.strip()

            if right.startswith('"') and right.endswith('"'):
                right = right[1:-1]

            left_value = self._get_value(left)
            return str(left_value) == right
        elif 'has_flag' in condition:
            flag = condition.split('(', 1)[1].rstrip(')')
            return self.state.has_flag(flag.strip('"\'')) 
        elif '>' in condition:
            left, right = condition.split('>', 1)
            left = left.strip()
            right = right.strip()
            left_value = self._get_value(left)
            return float(left_value) > float(right)
        elif '!' in condition and condition.startswith('!'):
            flag = condition[1:].strip()
            return not self.state.has_flag(flag)

        return True  # 如果条件复杂，默认返回真

    def _get_value(self, expression: str):
        """从表达式获取值（变量或字面量）。"""
        expression = expression.strip()
        if expression in self.state.variables:
            return self.state.variables[expression]
        return expression

    def process_choice(self, choice_index: int) -> Optional[str]:
        """处理玩家选择并返回下一个场景。"""
        current_scene = self.parser.get_scene(self.state.get_current_scene())
        choices = current_scene.get('choices', [])

        if 0 <= choice_index < len(choices):
            choice = choices[choice_index]
            # 执行选择中的命令
            self._execute_commands(choice.get('commands', []))
            next_scene = choice.get('next')
            if next_scene:
                return next_scene

        return None

    def process_player_input(self, input_text: str) -> Dict[str, Any]:
        """处理玩家自然语言输入。"""
        parsed = self.parser.parse_player_command(input_text)
        action = parsed.get('action', 'unknown')

        if action == 'attack':
            target = parsed.get('target')
            if target:
                # 简化处理：应用伤害
                self.state.set_variable('health', self.state.get_variable('health', 100) - 10)
                return {'message': f"你攻击了{target}！"}
        elif action == 'examine':
            target = parsed.get('target')
            if target:
                obj_def = self.parser.get_object(target)
                if obj_def:
                    return {'message': obj_def.get('description', f"你仔细检查了{target}。")}
        elif action == 'use':
            item = parsed.get('target')
            if item == 'key' and self.state.has_flag('has_key'):
                return {'message': "你使用了钥匙。也许可以打开什么门。"}

        return {'message': f"我不明白'{input_text}'的意思。"}
