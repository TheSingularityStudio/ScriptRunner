"""
ScriptRunner 的依赖注入容器。提供一种简易的服务定位模式，用于管理组件依赖。
"""

from typing import Dict, Any, Callable, Type, Optional
import inspect


class Container:
    """使用服务定位器模式的简单依赖注入容器。"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

    def register(self, service_name: str, service: Any):
        """注册一个单例服务实例。"""
        self._services[service_name] = service

    def register_factory(self, service_name: str, factory: Callable):
        """注册一个工厂函数用于创建服务。"""
        self._factories[service_name] = factory

    def register_class(self, service_name: str, cls: Type, *args, **kwargs):
        """注册一个类以便按需实例化。"""
        def factory():
            return cls(*args, **kwargs)
        self.register_factory(service_name, factory)

    def get(self, service_name: str) -> Any:
        """获取服务实例，如果有必要则创建它。"""
        if service_name in self._services:
            return self._services[service_name]

        if service_name in self._factories:
            service = self._factories[service_name]()
            # 缓存单例实例
            self._services[service_name] = service
            return service

        raise ValueError(f"Service '{service_name}' not registered")

    def has(self, service_name: str) -> bool:
        """检查服务是否已注册。"""
        return service_name in self._services or service_name in self._factories

    def clear(self):
        """清除所有已注册的服务（对测试有用）。"""
        self._services.clear()
        self._factories.clear()


# 全局容器实例
container = Container()
