"""
Service factory for creating configured services.
Provides a centralized way to create services with proper configuration management.
"""

import logging
from typing import Type, TypeVar, Dict, Any, Optional, Union
from functools import lru_cache

from src.config.core import ConfigManager
from src.config.management import get_config_manager
from src.config.rollback import ConfigRollbackManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceFactory:
    """
    Factory class for creating services with proper configuration management.
    Provides dependency injection and configuration setup.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager
        self.rollback_manager = ConfigRollbackManager() if config_manager else None
        self._service_registry = {}
    
    def register_service(self, service_name: str, service_class: Type[T]) -> None:
        """Register a service class with the factory"""
        self._service_registry[service_name] = service_class
        logger.info(f"Registered service: {service_name}")
    
    def create_service(self, service_name: str, **kwargs) -> T:
        """Create a service instance with proper configuration"""
        if service_name not in self._service_registry:
            raise ValueError(f"Service '{service_name}' not registered")
        
        service_class = self._service_registry[service_name]
        
        # Inject configuration manager
        if 'config_manager' not in kwargs:
            kwargs['config_manager'] = self.config_manager
        
        # Create service instance
        try:
            service = service_class(**kwargs)
            logger.info(f"Created service instance: {service_name}")
            return service
        except Exception as e:
            logger.error(f"Failed to create service '{service_name}': {e}")
            raise
    
    async def initialize_service(self, service_name: str, **kwargs) -> T:
        """Create and initialize a service"""
        service = self.create_service(service_name, **kwargs)
        
        if hasattr(service, 'initialize'):
            await service.initialize()
        
        return service
    
    def get_registered_services(self) -> Dict[str, Type]:
        """Get all registered services"""
        return self._service_registry.copy()
    
    def is_service_registered(self, service_name: str) -> bool:
        """Check if a service is registered"""
        return service_name in self._service_registry


# Global service factory instance (延迟初始化)
_service_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """Get the global service factory instance"""
    global _service_factory
    if _service_factory is None:
        try:
            config_manager = get_config_manager()
            _service_factory = ServiceFactory(config_manager)
        except:
            # 如果配置系统未初始化，创建不带配置管理器的工厂
            _service_factory = ServiceFactory()
    return _service_factory


def register_service(service_name: str):
    """Decorator to register a service class"""
    def decorator(service_class: Type[T]) -> Type[T]:
        _service_factory.register_service(service_name, service_class)
        return service_class
    return decorator


def create_service(service_name: str, **kwargs) -> T:
    """Create a service using the global factory"""
    return _service_factory.create_service(service_name, **kwargs)


async def initialize_service(service_name: str, **kwargs) -> T:
    """Initialize a service using the global factory"""
    return await _service_factory.initialize_service(service_name, **kwargs)


# Configuration service registry
class ServiceRegistry:
    """Registry for managing service configurations"""
    
    def __init__(self):
        self._service_configs = {}
        self._service_instances = {}
    
    def register_service_config(self, service_name: str, config_path: str) -> None:
        """Register a service configuration"""
        self._service_configs[service_name] = config_path
        logger.info(f"Registered service config: {service_name} -> {config_path}")
    
    def get_service_config_path(self, service_name: str) -> Optional[str]:
        """Get configuration path for a service"""
        return self._service_configs.get(service_name)
    
    def register_service_instance(self, service_name: str, instance: Any) -> None:
        """Register a service instance"""
        self._service_instances[service_name] = instance
        logger.info(f"Registered service instance: {service_name}")
    
    def get_service_instance(self, service_name: str) -> Optional[Any]:
        """Get a registered service instance"""
        return self._service_instances.get(service_name)
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services"""
        result = {}
        for service_name in self._service_configs:
            result[service_name] = {
                'config_path': self._service_configs[service_name],
                'instance_registered': service_name in self._service_instances
            }
        return result


# Global service registry
_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry"""
    return _service_registry


# Example base service class
class ConfiguredService:
    """Base class for services that use configuration management"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.rollback_manager = ConfigRollbackManager()
        self._config_cache = {}
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service with configuration"""
        try:
            await self._load_config()
            await self._setup_service()
            self._is_initialized = True
            logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
    
    async def _load_config(self) -> None:
        """Load configuration - to be overridden by subclasses"""
        config = self.config_manager.load_config()
        self._config_cache = config
    
    async def _setup_service(self) -> None:
        """Setup service-specific configuration - to be overridden by subclasses"""
        pass
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        if key is None:
            return self._config_cache
        return self._config_cache.get(key, default)
    
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._is_initialized


# Service configuration utilities
class ServiceConfigUtils:
    """Utilities for service configuration management"""
    
    @staticmethod
    def validate_service_config(config: Dict[str, Any], required_keys: list) -> bool:
        """Validate service configuration"""
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required configuration key: {key}")
                return False
        return True
    
    @staticmethod
    def merge_service_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge service configurations"""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ServiceConfigUtils.merge_service_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def get_service_section(config: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Get service-specific configuration section"""
        return config.get(service_name, {})


# Example usage and registration
if __name__ == "__main__":
    # This would be used in a real application
    
    # Register services
    from .document_service import DocumentProcessingService
    
    service_factory = get_service_factory()
    service_factory.register_service('document_processor', DocumentProcessingService)
    
    # Create a service
    document_service = service_factory.create_service('document_processor')
    
    # Or use the global functions
    # document_service = create_service('document_processor')