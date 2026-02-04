"""
ScriptRunner 脚本执行器的自定义异常。
"""


class ScriptExecutionError(Exception):
    """脚本执行相关错误的基础异常。"""
    pass


class ScriptError(Exception):
    """因脚本解析和验证错误而引发异常。"""
    pass


class ConfigurationError(Exception):
    """因配置相关错误而引发的异常。"""
    pass


class PluginError(Exception):
    """因插件加载和执行错误而引发的异常。"""
    pass


class ExecutionError(Exception):
    """因运行时执行错误而引发的异常。"""
    pass
