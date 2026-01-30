from typing import Dict, Any, List, Optional
import re

class ExecutionEngine:
    def __init__(self, parser, state_manager):
        self.parser = parser
        self.state = state_manager

    def execute_scene(self, scene_id: str) -> Dict[str, Any]:
        """执行场景并返回结果。"""
        scene = self.parser.get_scene(scene_id)
        if not scene:
            raise ValueError(f"场景'{scene_id}'未找到")

        self.state.set_current_scene(scene_id)

        # 执行场景中的任何命令
        self._execute_commands(scene.get('commands', []))

        # 处理条件选择
        processed_scene = self._process_scene(scene)

        return processed_scene

    def _execute_commands(self, commands: List[Dict[str, Any]]):
        """执行场景命令。"""
        for command in commands:
            self._execute_command(command)

    def _execute_command(self, command: Dict[str, Any]):
        """执行单个命令。"""
        if 'set' in command:
            self._execute_set_command(command['set'])
        elif 'add_flag' in command:
            self.state.set_flag(command['add_flag'])
        elif 'remove_flag' in command:
            self.state.clear_flag(command['remove_flag'])
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

    def _process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """处理场景的条件内容。"""
        processed = scene.copy()

        # 处理条件选择
        choices = scene.get('choices', [])
        processed_choices = []

        for choice in choices:
            if self._evaluate_condition(choice.get('condition')):
                processed_choices.append(choice)

        processed['choices'] = processed_choices
        return processed

    def _evaluate_condition(self, condition: Optional[str]) -> bool:
        """评估简单条件。"""
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
            next_scene = choice.get('next')
            if next_scene:
                return next_scene

        return None
