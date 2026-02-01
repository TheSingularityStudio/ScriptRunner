"""
ScriptRunner 的元管理器。
处理 DSL 元系统的宏定义和动态脚本生成。
"""

from typing import Dict, Any, List, Optional
import re
from .interfaces import IMetaManager
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class MetaManager(IMetaManager):
    """管理游戏元系统，包括宏和动态脚本。"""

    def __init__(self, parser, state_manager, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator

        # 元数据存储
        self.macros: Dict[str, str] = {}
        self.dynamic_scripts: Dict[str, Dict[str, Any]] = {}
        self.meta_values: Dict[str, Any] = {}

        logger.info("MetaManager initialized")

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

        if script_name == 'generate_quest':
            return self._execute_generate_quest(script_config, **kwargs)
        elif script_name == 'describe_room':
            return self._execute_describe_room(script_config, **kwargs)
        else:
            logger.warning(f"Unknown dynamic script: {script_name}")
            return None

    def _execute_generate_quest(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行任务生成脚本。"""
        parameters = config.get('parameters', [])
        template = config.get('template', '')

        # 使用随机管理器生成参数
        # 这里需要访问 random_manager，但当前没有，所以使用简单随机
        import random

        replacements = {}
        for param in parameters:
            if param == 'target':
                replacements[param] = random.choice(['哥布林', '狼人', '宝藏'])
            elif param == 'reward':
                replacements[param] = random.choice(['金币', '武器', '药水'])

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
        # 简化实现
        descriptions = [
            "这是一个昏暗的房间，墙壁上布满了蜘蛛网。",
            "房间里散落着古老的书籍和破损的家具。",
            "空气中弥漫着潮湿的泥土味。",
            "远处传来滴水的声音。"
        ]
        import random
        return random.choice(descriptions)

    def get_meta_value(self, key: str) -> Any:
        """获取元数据值。"""
        return self.meta_values.get(key)

    def set_meta_value(self, key: str, value: Any) -> None:
        """设置元数据值。"""
        self.meta_values[key] = value
        logger.info(f"Set meta value '{key}' to {value}")
