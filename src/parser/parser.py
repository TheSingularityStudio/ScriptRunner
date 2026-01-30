import yaml
import os
from typing import Dict, Any, List, Optional
import re

class ScriptParser:
    def __init__(self):
        self.script_data = {}
        self.objects = {}  # DSL objects
        self.events = {}   # DSL events
        self.command_parser_config = {}  # DSL command parser
        self.random_tables = {}  # DSL random systems
        self.state_machines = {}  # DSL state machines
        self.effects = {}  # DSL effects

    def load_script(self, file_path: str) -> Dict[str, Any]:
        """加载并解析YAML脚本文件，支持DSL语法。"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"脚本文件未找到: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            self.script_data = yaml.safe_load(file)

        self._validate_script()
        self._parse_dsl_structures()
        return self.script_data

    def _validate_script(self):
        """脚本结构的初步验证，支持DSL和传统格式。"""
        # Check for DSL structures
        has_dsl = any(key in self.script_data for key in ['define_object', 'scene', 'event_system', 'command_parser', 'random_system', 'state_machines', 'effects'])

        if has_dsl:
            # DSL validation
            if 'game' not in self.script_data:
                raise ValueError("DSL脚本必须包含'game'部分")
            if 'world' not in self.script_data:
                raise ValueError("DSL脚本必须包含'world'部分")
        else:
            # Traditional validation
            if 'scenes' not in self.script_data:
                raise ValueError("传统脚本必须包含'scenes'部分")
            for scene_id, scene in self.script_data['scenes'].items():
                if 'text' not in scene:
                    raise ValueError(f"场景'{scene_id}'必须有'text'字段")

    def _parse_dsl_structures(self):
        """解析DSL结构。"""
        if 'define_object' in self.script_data:
            self._parse_objects()
        if 'event_system' in self.script_data:
            self._parse_events()
        if 'command_parser' in self.script_data:
            self._parse_command_parser()
        if 'random_system' in self.script_data:
            self._parse_random_system()
        if 'state_machines' in self.script_data:
            self._parse_state_machines()
        if 'effects' in self.script_data:
            self._parse_effects()

    def _parse_objects(self):
        """解析对象定义。"""
        for obj_name, obj_def in self.script_data['define_object'].items():
            self.objects[obj_name] = obj_def

    def _parse_events(self):
        """解析事件系统。"""
        self.events = self.script_data['event_system']

    def _parse_command_parser(self):
        """解析命令解析器配置。"""
        self.command_parser_config = self.script_data['command_parser']

    def _parse_random_system(self):
        """解析随机系统。"""
        self.random_tables = self.script_data['random_system'].get('tables', {})

    def _parse_state_machines(self):
        """解析状态机。"""
        self.state_machines = self.script_data['state_machines']

    def _parse_effects(self):
        """解析效果系统。"""
        self.effects = self.script_data['effects']

    def get_scene(self, scene_id: str) -> Dict[str, Any]:
        """通过ID获取特定场景，支持DSL和传统格式。"""
        if 'scenes' in self.script_data:
            return self.script_data['scenes'].get(scene_id, {})
        elif 'locations' in self.script_data:
            return self.script_data['locations'].get(scene_id, {})
        return {}

    def get_start_scene(self) -> str:
        """获取起始场景ID。"""
        if 'world' in self.script_data and 'start' in self.script_data['world']:
            return self.script_data['world']['start']
        return self.script_data.get('start_scene', 'start')

    def get_object(self, obj_id: str) -> Dict[str, Any]:
        """获取DSL对象定义。"""
        return self.objects.get(obj_id, {})

    def get_events(self) -> Dict[str, Any]:
        """获取事件系统。"""
        return self.events

    def get_command_parser_config(self) -> Dict[str, Any]:
        """获取命令解析器配置。"""
        return self.command_parser_config

    def get_random_table(self, table_name: str) -> Dict[str, Any]:
        """获取随机表。"""
        return self.random_tables.get(table_name, {})

    def get_state_machine(self, sm_name: str) -> Dict[str, Any]:
        """获取状态机。"""
        return self.state_machines.get(sm_name, {})

    def get_effect(self, effect_name: str) -> Dict[str, Any]:
        """获取效果定义。"""
        return self.effects.get(effect_name, {})

    def parse_player_command(self, input_text: str) -> Dict[str, Any]:
        """解析玩家输入命令，返回动作字典。"""
        if not self.command_parser_config:
            # Fallback to simple parsing
            return {'action': 'unknown', 'target': input_text}

        verbs = self.command_parser_config.get('verbs', {})
        nouns = self.command_parser_config.get('nouns', {})

        # Simple tokenization
        tokens = input_text.lower().split()

        # Find verb
        action = None
        for verb, config in verbs.items():
            patterns = config.get('patterns', [])
            for pattern in patterns:
                if pattern in input_text:
                    action = verb
                    break
            if action:
                break

        if not action:
            return {'action': 'unknown', 'input': input_text}

        # Extract target (simple implementation)
        target = None
        for token in tokens:
            if token in nouns.get('dynamic_match', {}):
                target = token
                break

        return {
            'action': action,
            'target': target,
            'original_input': input_text
        }
