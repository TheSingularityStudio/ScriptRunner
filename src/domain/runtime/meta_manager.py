"""
ScriptRunner 的元管理器。
处理 DSL 元系统的宏定义和动态脚本生成。
"""

from typing import Dict, Any, List, Optional, Callable
import re
import yaml
from collections import defaultdict, Counter
from .interfaces import IMetaManager, IRandomManager
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class MetaManager(IMetaManager):
    """管理游戏元系统，包括宏和动态脚本。"""

    def __init__(self, parser, state_manager, condition_evaluator, random_manager: Optional[IRandomManager] = None):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator
        self.random_manager = random_manager

        # 元数据存储
        self.macros: Dict[str, str] = {}
        self.dynamic_scripts: Dict[str, Dict[str, Any]] = {}
        self.meta_values: Dict[str, Any] = {}

        # 动态脚本执行器注册
        self.script_executors: Dict[str, Callable] = {}
        self._register_default_executors()

        logger.info("MetaManager initialized")

    def _register_default_executors(self):
        """注册默认的动态脚本执行器。"""
        self.script_executors = {
            'generate_quest': self._execute_generate_quest,
            'describe_room': self._execute_describe_room,
            'generate_name': self._execute_generate_name,
            'create_item': self._execute_create_item,
        }

    def load_meta_data(self):
        """从解析器加载元数据。"""
        try:
            meta_data = self.parser.get_meta_data()
            if meta_data:
                if 'macros' in meta_data:
                    self.macros = meta_data['macros']
                    logger.info(f"Loaded {len(self.macros)} macros")

                if 'dynamic_scripts' in meta_data:
                    self.dynamic_scripts = meta_data['dynamic_scripts']
                    logger.info(f"Loaded {len(self.dynamic_scripts)} dynamic scripts")

        except (AttributeError, TypeError, KeyError) as e:
            logger.warning(f"Failed to load meta data due to data structure error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading meta data: {e}")

    def evaluate_macro(self, macro_name: str, **kwargs) -> bool:
        """评估宏条件。"""
        if macro_name not in self.macros:
            logger.warning(f"Macro '{macro_name}' not found")
            return False

        macro_expr = self.macros[macro_name]

        # 替换参数
        for key, value in kwargs.items():
            macro_expr = macro_expr.replace(f'{{{key}}}', str(value))

        # 评估条件
        try:
            return self.condition_evaluator.evaluate_condition(macro_expr)
        except Exception as e:
            logger.error(f"Error evaluating macro '{macro_name}': {e}")
            return False

    def generate_dynamic_script(self, script_name: str, **parameters) -> Optional[Dict[str, Any]]:
        """生成动态脚本。"""
        if script_name not in self.dynamic_scripts:
            logger.warning(f"Dynamic script '{script_name}' not found")
            return None

        script_def = self.dynamic_scripts[script_name]
        template = script_def.get('template', '')

        # 替换参数
        generated_script = template
        for param_name, param_value in parameters.items():
            generated_script = generated_script.replace(f'{{{param_name}}}', str(param_value))

        # 解析生成的脚本
        try:
            import yaml
            generated_data = yaml.safe_load(generated_script)
            logger.info(f"Generated dynamic script '{script_name}' with parameters: {parameters}")
            return generated_data
        except Exception as e:
            logger.error(f"Error generating dynamic script '{script_name}': {e}")
            return None

    def get_macro_names(self) -> List[str]:
        """获取所有宏名称。"""
        return list(self.macros.keys())

    def get_dynamic_script_names(self) -> List[str]:
        """获取所有动态脚本名称。"""
        return list(self.dynamic_scripts.keys())

    def has_macro(self, macro_name: str) -> bool:
        """检查宏是否存在。"""
        return macro_name in self.macros

    def has_dynamic_script(self, script_name: str) -> bool:
        """检查动态脚本是否存在。"""
        return script_name in self.dynamic_scripts

    def execute_dynamic_script(self, script_name: str, **kwargs) -> Any:
        """执行动态脚本。"""
        if script_name not in self.dynamic_scripts:
            logger.warning(f"Dynamic script '{script_name}' not found")
            return None

        script_config = self.dynamic_scripts[script_name]

        # 使用注册的执行器
        executor = self.script_executors.get(script_name)
        if executor:
            try:
                return executor(script_config, **kwargs)
            except Exception as e:
                logger.error(f"Error executing dynamic script '{script_name}': {e}")
                return None
        else:
            logger.warning(f"No executor registered for dynamic script: {script_name}")
            return None

    def _execute_generate_quest(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行任务生成脚本。"""
        parameters = config.get('parameters', [])
        template = config.get('template', '')

        replacements = {}
        for param in parameters:
            if param == 'target':
                if self.random_manager:
                    replacements[param] = self.random_manager.get_random_from_table('enemy_types') or '哥布林'
                else:
                    import random
                    replacements[param] = random.choice(['哥布林', '狼人', '宝藏'])
            elif param == 'reward':
                if self.random_manager:
                    replacements[param] = self.random_manager.get_random_from_table('rewards') or '金币'
                else:
                    import random
                    replacements[param] = random.choice(['金币', '武器', '药水'])
            elif param == 'location':
                if self.random_manager:
                    replacements[param] = self.random_manager.get_random_from_table('locations') or '森林'
                else:
                    import random
                    replacements[param] = random.choice(['森林', '山洞', '村庄'])

        # 替换模板
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))

        return {
            'type': 'generated_quest',
            'objective': result,
            'replacements': replacements
        }

    def _execute_describe_room(self, config: Dict[str, Any], **kwargs) -> str:
        """执行房间描述脚本。"""
        algorithm = config.get('algorithm', 'template')
        training_data = config.get('training_data', '')

        if algorithm == 'markov_chain':
            # 简单的马尔可夫链实现
            return self._generate_markov_description(training_data)
        else:
            return "一个普通的房间。"

    def _generate_markov_description(self, training_data: str) -> str:
        """使用马尔可夫链生成描述。"""
        if not training_data:
            # 默认描述
            descriptions = [
                "这是一个昏暗的房间，墙壁上布满了蜘蛛网。",
                "房间里散落着古老的书籍和破损的家具。",
                "空气中弥漫着潮湿的泥土味。",
                "远处传来滴水的声音。"
            ]
            import random
            return random.choice(descriptions)

        # 构建马尔可夫链
        words = training_data.split()
        if len(words) < 3:
            return training_data

        # 创建转移矩阵
        transitions = defaultdict(Counter)
        for i in range(len(words) - 1):
            transitions[words[i]][words[i + 1]] += 1

        # 生成描述
        import random
        current_word = random.choice(words)
        result = [current_word]

        for _ in range(10):  # 生成最多10个词
            if current_word not in transitions:
                break
            next_words = list(transitions[current_word].keys())
            weights = list(transitions[current_word].values())
            current_word = random.choices(next_words, weights=weights)[0]
            result.append(current_word)

        return ' '.join(result)

    def get_meta_value(self, key: str) -> Any:
        """获取元数据值。"""
        return self.meta_values.get(key)

    def set_meta_value(self, key: str, value: Any) -> None:
        """设置元数据值。"""
        self.meta_values[key] = value
        logger.info(f"Set meta value '{key}' to {value}")

    def validate_macro(self, macro_name: str) -> bool:
        """验证宏定义。"""
        if macro_name not in self.macros:
            logger.warning(f"Macro '{macro_name}' not found for validation")
            return False

        macro_expr = self.macros[macro_name]

        # 检查基本语法：括号匹配
        if not self._validate_brace_syntax(macro_expr):
            logger.error(f"Macro '{macro_name}' has invalid brace syntax")
            return False

        # 尝试评估宏（使用默认参数）
        try:
            # 替换所有参数为默认值进行测试
            test_expr = re.sub(r'\{([^}]+)\}', '1', macro_expr)
            self.condition_evaluator.evaluate_condition(test_expr)
            return True
        except Exception as e:
            logger.error(f"Macro '{macro_name}' validation failed: {e}")
            return False

    def validate_dynamic_script(self, script_name: str) -> bool:
        """验证动态脚本定义。"""
        if script_name not in self.dynamic_scripts:
            logger.warning(f"Dynamic script '{script_name}' not found for validation")
            return False

        script_def = self.dynamic_scripts[script_name]
        template = script_def.get('template', '')

        if not template:
            logger.error(f"Dynamic script '{script_name}' has empty template")
            return False

        # 检查模板语法
        if not self._validate_template_syntax(template):
            logger.error(f"Dynamic script '{script_name}' has invalid template syntax")
            return False

        # 检查是否有对应的执行器
        if script_name not in self.script_executors:
            logger.warning(f"No executor registered for dynamic script '{script_name}'")
            # 这不是错误，只是警告

        return True

    def _validate_brace_syntax(self, expr: str) -> bool:
        """验证表达式中的括号语法。"""
        stack = []
        for char in expr:
            if char == '{':
                stack.append(char)
            elif char == '}':
                if not stack:
                    return False
                stack.pop()
        return len(stack) == 0

    def _validate_template_syntax(self, template: str) -> bool:
        """验证模板语法。"""
        # 检查未闭合的括号
        return self._validate_brace_syntax(template)

    def _execute_generate_name(self, config: Dict[str, Any], **kwargs) -> str:
        """执行名称生成脚本。"""
        templates = config.get('templates', [])
        if not templates:
            return "未知名称"

        if self.random_manager:
            template = self.random_manager.get_random_from_table('name_templates') or random.choice(templates)
        else:
            import random
            template = random.choice(templates)

        # 替换参数
        result = template
        for key, value in kwargs.items():
            result = result.replace(f'{{{key}}}', str(value))

        return result

    def _execute_create_item(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行物品创建脚本。"""
        item_type = config.get('type', 'generic')
        properties = config.get('properties', {})

        # 生成物品属性
        item = {
            'type': item_type,
            'name': kwargs.get('name', f'未知{item_type}'),
            'properties': {}
        }

        for prop_name, prop_config in properties.items():
            if isinstance(prop_config, dict):
                # 从随机表获取
                table_name = prop_config.get('table')
                if table_name and self.random_manager:
                    item['properties'][prop_name] = self.random_manager.get_random_from_table(table_name)
                else:
                    item['properties'][prop_name] = prop_config.get('default', 'unknown')
            else:
                item['properties'][prop_name] = prop_config

        return item

    def register_script_executor(self, script_name: str, executor: Callable) -> None:
        """注册自定义脚本执行器。"""
        self.script_executors[script_name] = executor
        logger.info(f"Registered custom executor for script '{script_name}'")

    def unregister_script_executor(self, script_name: str) -> None:
        """注销脚本执行器。"""
        if script_name in self.script_executors:
            del self.script_executors[script_name]
            logger.info(f"Unregistered executor for script '{script_name}'")

    def get_registered_executors(self) -> List[str]:
        """获取所有注册的执行器名称。"""
        return list(self.script_executors.keys())

    def save_meta_values(self, file_path: str) -> bool:
        """保存元数据值到文件。"""
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.meta_values, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved meta values to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save meta values: {e}")
            return False

    def load_meta_values(self, file_path: str) -> bool:
        """从文件加载元数据值。"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                self.meta_values = json.load(f)
            logger.info(f"Loaded meta values from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load meta values: {e}")
            return False
