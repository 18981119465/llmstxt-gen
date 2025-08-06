"""
配置管理SDK
提供简单的Python接口来管理配置
"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import aiohttp
import async_timeout

from .core import ConfigManager
from .validator import ConfigValidator
from .rollback import ConfigRollbackManager
from .exceptions import ConfigError


@dataclass
class ConfigClientOptions:
    """配置客户端选项"""
    api_base_url: str = "http://localhost:8000/api/v1/config"
    web_base_url: str = "http://localhost:8000/config"
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0


class ConfigClient:
    """配置管理客户端"""
    
    def __init__(self, options: Optional[ConfigClientOptions] = None):
        self.options = options or ConfigClientOptions()
        self.session = None
        self._config_manager = None
        self._validator = None
        self._rollback_manager = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.options.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.options.api_base_url}{endpoint}"
        
        for attempt in range(self.options.retry_count):
            try:
                async with async_timeout.timeout(self.options.timeout):
                    async with self.session.request(method, url, **kwargs) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_data = await response.json()
                            raise ConfigError(f"API请求失败: {error_data.get('error', '未知错误')}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.options.retry_count - 1:
                    raise ConfigError(f"请求失败: {str(e)}")
                await asyncio.sleep(self.options.retry_delay * (2 ** attempt))
    
    async def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        result = await self._request("GET", "/")
        if result.get("success"):
            return result.get("config", {})
        else:
            raise ConfigError(result.get("error", "获取配置失败"))
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """更新配置"""
        result = await self._request("POST", "/", json={"config": config})
        return result.get("success", False)
    
    async def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置部分"""
        result = await self._request("GET", f"/sections/{section}")
        if result.get("success"):
            return result.get("section", {})
        else:
            raise ConfigError(result.get("error", "获取配置部分失败"))
    
    async def update_section(self, section: str, data: Dict[str, Any]) -> bool:
        """更新配置部分"""
        result = await self._request("PUT", f"/sections/{section}", json={"section": data})
        return result.get("success", False)
    
    async def get_value(self, key: str) -> Any:
        """获取配置值"""
        result = await self._request("GET", f"/values/{key}")
        if result.get("success"):
            return result.get("value")
        else:
            raise ConfigError(result.get("error", "获取配置值失败"))
    
    async def set_value(self, key: str, value: Any) -> bool:
        """设置配置值"""
        result = await self._request("POST", f"/values/{key}", json={"value": value})
        return result.get("success", False)
    
    async def validate_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证配置"""
        if config is None:
            config = await self.get_config()
        
        result = await self._request("POST", "/validate", json={"config": config})
        if result.get("success"):
            return {
                "valid": result.get("valid", False),
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", []),
                "suggestions": result.get("suggestions", [])
            }
        else:
            raise ConfigError(result.get("error", "验证配置失败"))
    
    async def reload_config(self) -> bool:
        """重新加载配置"""
        result = await self._request("POST", "/reload")
        return result.get("success", False)
    
    async def export_config(self, format: str = "yaml") -> str:
        """导出配置"""
        result = await self._request("GET", f"/export?format={format}")
        if result.get("success"):
            return result.get("content", "")
        else:
            raise ConfigError(result.get("error", "导出配置失败"))
    
    async def import_config(self, config_data: str, format: str = "yaml") -> bool:
        """导入配置"""
        if format == "yaml":
            try:
                config_dict = yaml.safe_load(config_data)
            except yaml.YAMLError as e:
                raise ConfigError(f"YAML解析失败: {str(e)}")
        elif format == "json":
            try:
                config_dict = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise ConfigError(f"JSON解析失败: {str(e)}")
        else:
            raise ConfigError(f"不支持的格式: {format}")
        
        result = await self._request("POST", "/import", json={"config": config_dict})
        return result.get("success", False)
    
    async def get_history(self) -> List[Dict[str, Any]]:
        """获取配置历史"""
        result = await self._request("GET", "/history")
        if result.get("success"):
            return result.get("history", [])
        else:
            raise ConfigError(result.get("error", "获取历史记录失败"))
    
    async def rollback(self, version_id: str) -> bool:
        """回滚配置"""
        result = await self._request("POST", "/rollback", json={"version_id": version_id})
        return result.get("success", False)
    
    async def watch_config(self, callback):
        """监视配置变化（模拟）"""
        # 这是一个简化的实现，实际应该使用WebSocket或轮询
        last_config = await self.get_config()
        
        while True:
            try:
                await asyncio.sleep(5)  # 每5秒检查一次
                current_config = await self.get_config()
                
                if current_config != last_config:
                    last_config = current_config
                    await callback(current_config)
            except Exception as e:
                print(f"监视配置时出错: {e}")
                await asyncio.sleep(10)  # 出错后等待更长时间


class LocalConfigManager:
    """本地配置管理器（不依赖API）"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config_manager = ConfigManager(str(self.config_path))
        self.validator = ConfigValidator()
        self.rollback_manager = ConfigRollbackManager(str(self.config_path))
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        return self.config_manager.load_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        return self.config_manager.save_config(config)
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return self.config_manager.get_config_info()
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证配置"""
        if config is None:
            config = self.load_config()
        
        result = self.validator.validate_config(config)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions
        }
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置部分"""
        config = self.load_config()
        return config.get(section, {})
    
    def update_section(self, section: str, data: Dict[str, Any]) -> bool:
        """更新配置部分"""
        config = self.load_config()
        config[section] = data
        return self.save_config(config)
    
    def get_value(self, key: str) -> Any:
        """获取配置值"""
        return self.config_manager.get_config_value(key)
    
    def set_value(self, key: str, value: Any) -> bool:
        """设置配置值"""
        return self.config_manager.update_config_value(key, value)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取配置历史"""
        return self.rollback_manager.get_history()
    
    def rollback(self, version_id: str) -> bool:
        """回滚配置"""
        return self.rollback_manager.rollback(version_id)
    
    def export_config(self, format: str = "yaml") -> str:
        """导出配置"""
        config = self.load_config()
        
        if format == "yaml":
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        elif format == "json":
            return json.dumps(config, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def import_config(self, config_data: str, format: str = "yaml") -> bool:
        """导入配置"""
        if format == "yaml":
            try:
                config_dict = yaml.safe_load(config_data)
            except yaml.YAMLError as e:
                raise ConfigError(f"YAML解析失败: {str(e)}")
        elif format == "json":
            try:
                config_dict = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise ConfigError(f"JSON解析失败: {str(e)}")
        else:
            raise ConfigError(f"不支持的格式: {format}")
        
        return self.save_config(config_dict)


# 便捷函数
async def create_config_client(options: Optional[ConfigClientOptions] = None) -> ConfigClient:
    """创建配置客户端"""
    client = ConfigClient(options)
    await client.__aenter__()
    return client


def create_local_config_manager(config_path: str) -> LocalConfigManager:
    """创建本地配置管理器"""
    return LocalConfigManager(config_path)


# 使用示例
async def example_usage():
    """使用示例"""
    # 使用远程API客户端
    async with ConfigClient() as client:
        # 获取配置
        config = await client.get_config()
        print("当前配置:", config)
        
        # 更新配置
        config["app"]["debug"] = True
        await client.update_config(config)
        
        # 验证配置
        validation_result = await client.validate_config()
        print("验证结果:", validation_result)
        
        # 获取历史
        history = await client.get_history()
        print("配置历史:", history)
    
    # 使用本地配置管理器
    local_manager = create_local_config_manager("config/config.yaml")
    
    # 加载配置
    config = local_manager.load_config()
    print("本地配置:", config)
    
    # 验证配置
    validation_result = local_manager.validate_config()
    print("本地验证结果:", validation_result)


if __name__ == "__main__":
    asyncio.run(example_usage())