import yaml
import os
from typing import Dict, Any, List, Optional
import re
from .interfaces import IScriptParser

class ScriptParser(IScriptParser):
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
            # Check for start scene existence if world.start is specified and scenes/locations exist
            if 'start' in self.script_data['world']:
                start_scene = self.script_data['world']['start']
                has_scenes = 'scenes' in self.script_data or 'locations' in self.script_data
                if has_scenes:
                    scene_exists = (
                        ('scenes' in self.script_data and start_scene in self.script_data['scenes']) or
                        ('locations' in self.script_data and start_scene in self.script_data['locations'])
                    )
                    if not scene_exists:
                        raise ValueError(f"DSL脚本的起始场景'{start_scene}'在脚本中不存在")
            # Validate define_object structures
            if 'define_object' in self.script_data:
                for obj_name, obj_def in self.script_data['define_object'].items():
                    if not isinstance(obj_def, dict) or 'type' not in obj_def:
                        raise ValueError(f"DSL对象'{obj_name}'必须是字典且包含'type'字段")
        else:
            # Traditional validation - support both 'scenes' and 'locations'
            if 'scenes' not in self.script_data and 'locations' not in self.script_data:
                raise ValueError("传统脚本必须包含'scenes'或'locations'部分")
            scene_key = 'scenes' if 'scenes' in self.script_data else 'locations'
            for scene_id, scene in self.script_data[scene_key].items():
                if 'text' not in scene and 'description' not in scene:
                    raise ValueError(f"场景'{scene_id}'必须有'text'或'description'字段")

    def _parse_dsl_structures(self):
        """解析DSL结构。"""
        try:
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
        except Exception as e:
            raise ValueError(f"DSL结构解析失败: {str(e)}")

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

    def get_random_table_data(self) -> Dict[str, Any]:
        """获取所有随机表数据。"""
        return self.script_data.get('random_system', {})

    def get_state_machine(self, sm_name: str) -> Dict[str, Any]:
        """获取状态机。"""
        return self.state_machines.get(sm_name, {})

    def get_state_machine_data(self) -> Dict[str, Any]:
        """获取所有状态机数据。"""
        return self.state_machines

    def get_meta_data(self) -> Dict[str, Any]:
        """获取元数据。"""
        return self.script_data.get('meta', {})

    def get_effect(self, effect_name: str) -> Dict[str, Any]:
        """获取效果定义。"""
        return self.effects.get(effect_name, {})

    def parse_player_command(self, input_text: str) -> Dict[str, Any]:
        """解析玩家输入命令，返回动作字典。"""
        if not self.command_parser_config:
            # 回退到简单解析
            return {'action': 'unknown', 'target': input_text}

        verbs = self.command_parser_config.get('verbs', {})
        nouns = self.command_parser_config.get('nouns', {})

        # 简单分词
        tokens = input_text.lower().split()

        # 寻找动词
        action = None
        for verb, config in verbs.items():
            patterns = config.get('patterns', [])
            aliases = config.get('aliases', [])
            all_patterns = patterns + aliases
            for pattern in all_patterns:
                if pattern in input_text:
                    action = verb
                    break
            if action:
                break

        if not action:
            return {'action': 'unknown', 'input': input_text}

        # 提取目标（改进实现）
        target = None

        # 检查代词
        pronouns = nouns.get('pronouns', {})
        for token in tokens:
            if token in pronouns:
                target = pronouns[token]
                break

        # 如果没有代词，尝试提取名词
        if not target:
            # 改进目标提取：移除动词后，提取剩余的连续文本作为目标
            remaining_text = input_text.lower()
            for verb_config in verbs.values():
                for pattern in verb_config.get('patterns', []):
                    remaining_text = re.sub(r'\b' + re.escape(pattern) + r'\b', '', remaining_text).strip()
                for alias in verb_config.get('aliases', []):
                    remaining_text = re.sub(r'\b' + re.escape(alias) + r'\b', '', remaining_text).strip()

            # 移除多余空格
            remaining_text = re.sub(r'\s+', ' ', remaining_text).strip()

            if remaining_text and remaining_text != input_text.lower():
                target = remaining_text
            else:
                # 如果没有剩余文本，尝试从原始输入中提取可能的名称
                # 例如，从 "attack the goblin" 提取 "the goblin"
                words = input_text.lower().split()
                if len(words) > 1:
                    # 假设动词后是目标
                    target_start = -1
                    for i, word in enumerate(words):
                        for verb_config in verbs.values():
                            if word in verb_config.get('patterns', []) or word in verb_config.get('aliases', []):
                                target_start = i + 1
                                break
                        if target_start != -1:
                            break
                    if target_start != -1 and target_start < len(words):
                        target = ' '.join(words[target_start:])

        # 解析目标别名
        if target:
            target = self._resolve_target_alias(target)

        return {
            'action': action,
            'target': target,
            'original_input': input_text
        }

    def _resolve_target_alias(self, target_text: str) -> str:
        """解析目标的别名，返回标准名称。"""
        # 检查对象别名
        for obj_name, obj_def in self.objects.items():
            aliases = obj_def.get('aliases', [])
            if target_text in aliases or target_text == obj_def.get('name', ''):
                return obj_name

        return target_text

    def get_effect(self, effect_name: str) -> Optional[Dict[str, Any]]:
        """获取效果定义。"""
        effects = self.script_data.get('effects', {})
        return effects.get(effect_name)
