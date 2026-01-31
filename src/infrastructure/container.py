"""
ScriptRunner 的依赖注入容器。提供真正的依赖注入支持。
"""

from typing import Dict, Any, Callable, Type, Optional, Union
import inspect
from .logger import get_logger

logger = get_logger(__name__)


class Container:
    """真正的依赖注入容器，支持构造函数注入。"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._types: Dict[str, Type] = {}

    def register(self, service_name: str, service: Any):
        """注册一个单例服务实例。"""
        self._services[service_name] = service

    def register_factory(self, service_name: str, factory: Callable):
        """注册一个工厂函数用于创建服务。"""
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

            # 检查是否有默认值
            if param.default != inspect.Parameter.empty:
                continue

            # 尝试从容器中解析依赖
            if param_name in self._services or param_name in self._factories or param_name in self._types:
                kwargs[param_name] = self.get(param_name)
            else:
                raise ValueError(f"Cannot resolve dependency '{param_name}' for {cls.__name__}")

        return cls(**kwargs)

    def has(self, service_name: str) -> bool:
        """检查服务是否已注册。"""
        return (service_name in self._services or
                service_name in self._factories or
                service_name in self._types)

    def clear(self):
        """清除所有已注册的服务（对测试有用）。"""
        self._services.clear()
        self._factories.clear()
        self._types.clear()


# 移除全局容器实例，由调用方创建和管理
