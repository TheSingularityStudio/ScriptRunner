"""
ScriptRunner 的元管理器。
处理 DSL 元系统的宏定义和动态脚本生成。
"""

from typing import Dict, Any, List, Optional
import re
from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


class MetaManager:
    """管理游戏元系统，包括宏和动态脚本。"""

    def __init__(self, parser, state_manager, condition_evaluator):
        self.parser = parser
        self.state = state_manager
        self.condition_evaluator = condition_evaluator

        # 元数据存储
        self.macros: Dict[str, str] = {}
        self.dynamic_scripts: Dict[str, Dict[str, Any]] = {}

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

        except Exception as e:
            logger.warning(f"Failed to load meta data: {e}")

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
