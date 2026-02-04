"""
ScriptRunner 的依赖注入容器。提供真正的依赖注入支持。
"""

from typing import Dict, Any, Callable, Type, Optional, Union
import inspect
import threading
from .logger import get_logger

logger = get_logger(__name__)


class Container:
    """依赖注入容器，支持构造函数注入。"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._types: Dict[str, Type] = {}
        self._transient_factories: Dict[str, Callable] = {}  # 新增：瞬态工厂
        self._resolving: set = set()  # 新增：用于检测循环依赖
        self._lock = threading.RLock()  # 新增：线程安全锁

    def register(self, service_name: str, service: Any):
        """注册一个单例服务实例。"""
        self._services[service_name] = service

    def register_factory(self, service_name: str, factory: Callable, transient: bool = False):
        """注册一个工厂函数用于创建服务。transient=True 表示每次都创建新实例。"""
        if transient:
            self._transient_factories[service_name] = factory
        else:
            self._factories[service_name] = factory

    def register_type(self, service_name: str, cls: Type):
        """注册一个类型，支持自动依赖解析。"""
        self._types[service_name] = cls

    def register_class(self, service_name: str, cls: Type, *args, **kwargs):
        """注册一个类以便按需实例化。"""
        def factory():
            return cls(*args, **kwargs)
        self.register_factory(service_name, factory)

    def get(self, service_name: str) -> Any:
        """获取服务实例，如果有必要则创建它。"""
        logger.debug(f"Resolving service: {service_name}")
        if service_name in self._services:
            logger.debug(f"Service {service_name} found in cache")
            return self._services[service_name]

        if service_name in self._factories:
            logger.debug(f"Creating service {service_name} from factory")
            service = self._factories[service_name]()
            # 缓存单例实例
            self._services[service_name] = service
            return service

        if service_name in self._types:
            logger.debug(f"Resolving dependencies for type {service_name}")
            service = self._resolve_dependencies(self._types[service_name])
            # 缓存单例实例
            self._services[service_name] = service
            return service

        logger.error(f"Service '{service_name}' not registered")
        raise ValueError(f"Service '{service_name}' not registered")

    def resolve(self, cls: Type) -> Any:
        """解析并创建指定类型的实例，自动注入依赖。"""
        return self._resolve_dependencies(cls)

    def _resolve_dependencies(self, cls: Type) -> Any:
        """解析类的构造函数依赖并创建实例。"""
        init_signature = inspect.signature(cls.__init__)
        parameters = init_signature.parameters

        # 跳过 'self' 参数
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue

            # 如果参数在容器中注册，则注入依赖，否则使用默认值或跳过
            if param_name in self._services or param_name in self._factories or param_name in self._types or param_name in self._transient_factories:
                kwargs[param_name] = self.get(param_name)
            elif param.default == inspect.Parameter.empty:
                # 必需参数且未注册，抛出错误
                raise ValueError(f"Cannot resolve dependency '{param_name}' for {cls.__name__}")
            # 如果有默认值且未注册，则不注入（使用默认值）

        return cls(**kwargs)

    def has(self, service_name: str) -> bool:
        """检查服务是否已注册。"""
        return (service_name in self._services or
                service_name in self._factories or
                service_name in self._types or
                service_name in self._transient_factories)

    def clear(self):
        """清除所有已注册的服务（对测试有用）。"""
        self._services.clear()
        self._factories.clear()
        self._types.clear()
        self._transient_factories.clear()
        self._resolving.clear()


# 移除全局容器实例，由调用方创建和管理
