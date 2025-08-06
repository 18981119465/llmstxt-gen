"""
配置管理API接口
"""

import os
import json
import yaml
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import logging

from .loader import ConfigLoader, ConfigManager
from .watcher import ConfigWatcher
from .notifications import ConfigNotificationService, NotificationManager
from .rollback import ConfigRollbackManager
from .validator import ConfigValidator
from .schemas import (
    AppConfig, ConfigUpdateRequest, ConfigReloadRequest, ConfigRollbackRequest,
    ConfigValidationResult, ConfigHistory, EnvironmentType
)
from .exceptions import ConfigError, ConfigNotFoundError, ConfigValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局实例
_config_manager: Optional[ConfigManager] = None
_config_watcher: Optional[ConfigWatcher] = None
_notification_service: Optional[ConfigNotificationService] = None
_rollback_manager: Optional[ConfigRollbackManager] = None


def get_config_manager():
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    return _config_manager


def get_config_watcher() -> ConfigWatcher:
    """获取配置监听器实例"""
    global _config_watcher
    if _config_watcher is None:
        raise HTTPException(status_code=500, detail="配置监听器未初始化")
    return _config_watcher


def get_notification_service() -> ConfigNotificationService:
    """获取通知服务实例"""
    global _notification_service
    if _notification_service is None:
        raise HTTPException(status_code=500, detail="通知服务未初始化")
    return _notification_service


def get_rollback_manager() -> ConfigRollbackManager:
    """获取回滚管理器实例"""
    global _rollback_manager
    if _rollback_manager is None:
        raise HTTPException(status_code=500, detail="回滚管理器未初始化")
    return _rollback_manager


def init_config_management(
    config_manager: ConfigManager,
    config_watcher: ConfigWatcher,
    notification_service: ConfigNotificationService,
    rollback_manager: ConfigRollbackManager
):
    """初始化配置管理API"""
    global _config_manager, _config_watcher, _notification_service, _rollback_manager
    _config_manager = config_manager
    _config_watcher = config_watcher
    _notification_service = notification_service
    _rollback_manager = rollback_manager


# === 基础配置查询和获取API ===

class ConfigResponse(BaseModel):
    """配置响应"""
    success: bool
    config: Dict[str, Any]
    config_info: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ServiceConfigResponse(BaseModel):
    """服务配置响应"""
    success: bool
    service_name: str
    config: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigValueResponse(BaseModel):
    """配置值响应"""
    success: bool
    key_path: str
    value: Any
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


@router.get("/", response_model=ConfigResponse)
async def get_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取完整配置"""
    try:
        config = config_manager.load_config()
        config_info = config_manager.get_config_info()
        
        return ConfigResponse(
            success=True,
            config=config,
            config_info=config_info
        )
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/service/{service_name}", response_model=ServiceConfigResponse)
async def get_service_config(
    service_name: str,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取指定服务配置"""
    try:
        config = config_manager.get_service_config(service_name)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"服务配置不存在: {service_name}")
        
        return ServiceConfigResponse(
            success=True,
            service_name=service_name,
            config=config
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务配置失败: {str(e)}")


@router.get("/value/{key_path}", response_model=ConfigValueResponse)
async def get_config_value(
    key_path: str,
    default: Optional[str] = None,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取配置值"""
    try:
        # 解析默认值
        default_value = None
        if default:
            try:
                default_value = json.loads(default)
            except json.JSONDecodeError:
                default_value = default
        
        value = config_manager.get_config_value(key_path, default_value)
        source = config_manager.get_config_source(key_path)
        
        return ConfigValueResponse(
            success=True,
            key_path=key_path,
            value=value,
            source=source
        )
    except Exception as e:
        logger.error(f"获取配置值失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置值失败: {str(e)}")


@router.get("/app", response_model=AppConfig)
async def get_app_config(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取应用配置对象"""
    try:
        return config_manager.get_app_config()
    except Exception as e:
        logger.error(f"获取应用配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取应用配置失败: {str(e)}")


@router.get("/info")
async def get_config_info(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取配置信息"""
    try:
        return config_manager.get_config_info()
    except Exception as e:
        logger.error(f"获取配置信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置信息失败: {str(e)}")


@router.get("/files")
async def list_config_files(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """列出配置文件"""
    try:
        return {"files": config_manager.list_config_files()}
    except Exception as e:
        logger.error(f"列出配置文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出配置文件失败: {str(e)}")


# === 配置更新和修改API ===

class ConfigUpdateResponse(BaseModel):
    """配置更新响应"""
    success: bool
    message: str
    updated_config: Dict[str, Any]
    changes: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigFileUpdateRequest(BaseModel):
    """配置文件更新请求"""
    file_name: str = Field(..., description="文件名")
    config: Dict[str, Any] = Field(..., description="配置内容")
    reason: str = Field(..., description="更新原因")
    create_backup: bool = Field(True, description="是否创建备份")


@router.put("/service/{service_name}", response_model=ConfigUpdateResponse)
async def update_service_config(
    service_name: str,
    request: ConfigUpdateRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    notification_service: ConfigNotificationService = Depends(get_notification_service),
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """更新服务配置"""
    try:
        # 获取当前配置
        current_config = config_manager.load_config()
        old_service_config = current_config.get(service_name, {})
        
        # 创建备份
        if request.create_backup:
            rollback_manager.create_backup(
                service_name, 
                old_service_config, 
                "system", 
                f"更新前备份: {request.reason}"
            )
        
        # 更新配置
        new_config = current_config.copy()
        new_config[service_name] = request.config_value
        
        # 保存配置到文件
        await _save_config_to_file(config_manager, new_config, request.reason)
        
        # 重载配置
        updated_config = config_manager.reload_config()
        
        # 记录变更
        changes = _detect_config_changes(old_service_config, request.config_value)
        
        # 发送通知
        background_tasks.add_task(
            notification_service.notify_config_changed,
            service_name,
            old_service_config,
            request.config_value,
            changes
        )
        
        return ConfigUpdateResponse(
            success=True,
            message=f"服务配置更新成功: {service_name}",
            updated_config=updated_config,
            changes=changes
        )
        
    except Exception as e:
        logger.error(f"更新服务配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新服务配置失败: {str(e)}")


@router.put("/file", response_model=ConfigUpdateResponse)
async def update_config_file(
    request: ConfigFileUpdateRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    notification_service: ConfigNotificationService = Depends(get_notification_service),
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """更新配置文件"""
    try:
        # 验证文件名
        if not request.file_name.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="只支持YAML格式文件")
        
        # 获取文件路径
        file_path = Path(config_manager._config_loader.config_dir) / request.file_name
        
        # 创建备份
        if request.create_backup and file_path.exists():
            backup_content = config_manager._config_loader._load_config_file(request.file_name)
            if backup_content:
                rollback_manager.create_backup(
                    request.file_name,
                    backup_content,
                    "system",
                    f"文件更新前备份: {request.reason}"
                )
        
        # 读取当前配置
        current_config = {}
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
        
        # 写入新配置
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(request.config, f, default_flow_style=False, allow_unicode=True)
        
        # 重载配置
        updated_config = config_manager.reload_config()
        
        # 记录变更
        changes = _detect_config_changes(current_config, request.config)
        
        # 发送通知
        background_tasks.add_task(
            notification_service.notify_config_file_changed,
            request.file_name,
            current_config,
            request.config,
            changes
        )
        
        return ConfigUpdateResponse(
            success=True,
            message=f"配置文件更新成功: {request.file_name}",
            updated_config=updated_config,
            changes=changes
        )
        
    except Exception as e:
        logger.error(f"更新配置文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置文件失败: {str(e)}")


# === 配置验证API ===

@router.post("/validate", response_model=ConfigValidationResult)
async def validate_config(
    config: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """验证配置"""
    try:
        validator = config_manager._config_loader.validator
        
        # 验证配置
        validation_result = validator.validate_config(config)
        
        return ConfigValidationResult(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            config=config
        )
        
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证配置失败: {str(e)}")


@router.post("/validate/file", response_model=ConfigValidationResult)
async def validate_config_file(
    file: UploadFile = File(...),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """验证配置文件"""
    try:
        # 检查文件类型
        if not file.filename.endswith(('.yaml', '.yml')):
            raise HTTPException(status_code=400, detail="只支持YAML格式文件")
        
        # 读取文件内容
        content = await file.read()
        config = yaml.safe_load(content)
        
        # 验证配置
        validator = config_manager._config_loader.validator
        validation_result = validator.validate_config(config)
        
        return ConfigValidationResult(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            config=config
        )
        
    except Exception as e:
        logger.error(f"验证配置文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证配置文件失败: {str(e)}")


@router.get("/validate/schema")
async def get_config_schema():
    """获取配置模式"""
    try:
        # 返回配置模式的JSON Schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Application Configuration",
            "description": "Application configuration schema",
            "type": "object",
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                        "debug": {"type": "boolean"},
                        "env": {"type": "string", "enum": ["development", "production", "testing"]}
                    },
                    "required": ["name", "version"]
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "minLength": 1},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "name": {"type": "string", "minLength": 1},
                        "user": {"type": "string", "minLength": 1},
                        "password": {"type": "string"}
                    },
                    "required": ["host", "name", "user"]
                }
            },
            "required": ["system", "database"]
        }
        
        return schema
        
    except Exception as e:
        logger.error(f"获取配置模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置模式失败: {str(e)}")


# === 配置导入导出API ===

class ConfigExportResponse(BaseModel):
    """配置导出响应"""
    success: bool
    export_format: str
    download_url: Optional[str] = None
    content: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


@router.get("/export", response_model=ConfigExportResponse)
async def export_config(
    format: str = "yaml",
    service_name: Optional[str] = None,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """导出配置"""
    try:
        # 获取配置
        if service_name:
            config = config_manager.get_service_config(service_name)
            if not config:
                raise HTTPException(status_code=404, detail=f"服务配置不存在: {service_name}")
        else:
            config = config_manager.load_config()
        
        # 格式化配置
        if format.lower() == "yaml":
            content = yaml.dump(config, default_flow_style=False, allow_unicode=True)
            content_type = "application/x-yaml"
            file_extension = "yaml"
        elif format.lower() == "json":
            content = json.dumps(config, indent=2, ensure_ascii=False)
            content_type = "application/json"
            file_extension = "json"
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=f'.{file_extension}', 
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(content)
        temp_file.close()
        
        return ConfigExportResponse(
            success=True,
            export_format=format,
            download_url=f"/api/v1/config/download/{temp_file.name.split('/')[-1]}"
        )
        
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")


@router.get("/download/{filename}")
async def download_config_file(filename: str):
    """下载配置文件"""
    try:
        # 安全检查
        if not filename.endswith(('.yaml', '.yml', '.json')):
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 查找临时文件
        temp_dir = tempfile.gettempdir()
        file_path = Path(temp_dir) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 确定内容类型
        if filename.endswith('.json'):
            media_type = "application/json"
        else:
            media_type = "application/x-yaml"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        logger.error(f"下载配置文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载配置文件失败: {str(e)}")


@router.post("/import", response_model=ConfigUpdateResponse)
async def import_config(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service_name: Optional[str] = None,
    create_backup: bool = True,
    config_manager: ConfigManager = Depends(get_config_manager),
    notification_service: ConfigNotificationService = Depends(get_notification_service),
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """导入配置"""
    try:
        # 检查文件类型
        if not file.filename.endswith(('.yaml', '.yml', '.json')):
            raise HTTPException(status_code=400, detail="只支持YAML和JSON格式文件")
        
        # 读取文件内容
        content = await file.read()
        
        # 解析配置
        if file.filename.endswith(('.yaml', '.yml')):
            imported_config = yaml.safe_load(content)
        else:
            imported_config = json.loads(content)
        
        # 获取当前配置
        current_config = config_manager.load_config()
        
        # 创建备份
        if create_backup:
            backup_name = service_name or "full_config"
            rollback_manager.create_backup(
                backup_name,
                current_config,
                "system",
                f"导入配置前备份: {file.filename}"
            )
        
        # 合并配置
        if service_name:
            if service_name not in imported_config:
                raise HTTPException(status_code=400, detail=f"导入的配置中不包含服务: {service_name}")
            
            old_service_config = current_config.get(service_name, {})
            new_config = current_config.copy()
            new_config[service_name] = imported_config[service_name]
            
            changes = _detect_config_changes(old_service_config, imported_config[service_name])
        else:
            new_config = imported_config
            changes = _detect_config_changes(current_config, imported_config)
        
        # 保存配置
        await _save_config_to_file(config_manager, new_config, f"导入配置: {file.filename}")
        
        # 重载配置
        updated_config = config_manager.reload_config()
        
        # 发送通知
        background_tasks.add_task(
            notification_service.notify_config_imported,
            file.filename,
            current_config,
            imported_config,
            changes
        )
        
        return ConfigUpdateResponse(
            success=True,
            message=f"配置导入成功: {file.filename}",
            updated_config=updated_config,
            changes=changes
        )
        
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")


# === 配置历史和版本API ===

class ConfigHistoryResponse(BaseModel):
    """配置历史响应"""
    success: bool
    history: List[ConfigHistory]
    total_count: int
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigVersionResponse(BaseModel):
    """配置版本响应"""
    success: bool
    config_id: str
    versions: List[Dict[str, Any]]
    total_count: int
    timestamp: datetime = Field(default_factory=datetime.now)


@router.get("/history", response_model=ConfigHistoryResponse)
async def get_config_history(
    config_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """获取配置历史"""
    try:
        # 获取备份信息
        backup_info = rollback_manager.get_backup_info()
        
        # 构建历史记录
        history = []
        for config_name, config_data in backup_info.get('configs', {}).items():
            if config_id and config_name != config_id:
                continue
            
            # 这里简化处理，实际应该从数据库或文件中获取详细历史
            history.append(ConfigHistory(
                id=f"{config_name}_latest",
                config_id=config_name,
                config_value={},  # 实际应该包含配置内容
                version=config_data.get('version_count', 0),
                changed_by="system",
                change_reason="配置更新",
                created_at=datetime.now().isoformat()
            ))
        
        return ConfigHistoryResponse(
            success=True,
            history=history[offset:offset+limit],
            total_count=len(history)
        )
        
    except Exception as e:
        logger.error(f"获取配置历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置历史失败: {str(e)}")


@router.get("/versions/{config_id}", response_model=ConfigVersionResponse)
async def get_config_versions(
    config_id: str,
    limit: int = 20,
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """获取配置版本"""
    try:
        versions = rollback_manager.get_versions(config_id)
        
        version_list = []
        for version in versions[:limit]:
            version_list.append({
                "version": version.version,
                "config": version.config,
                "changed_by": version.changed_by,
                "change_reason": version.change_reason,
                "created_at": version.created_at,
                "backup_path": str(version.backup_path) if version.backup_path else None
            })
        
        return ConfigVersionResponse(
            success=True,
            config_id=config_id,
            versions=version_list,
            total_count=len(versions)
        )
        
    except Exception as e:
        logger.error(f"获取配置版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置版本失败: {str(e)}")


@router.post("/rollback/{config_id}", response_model=ConfigUpdateResponse)
async def rollback_config(
    config_id: str,
    request: ConfigRollbackRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager),
    notification_service: ConfigNotificationService = Depends(get_notification_service)
):
    """回滚配置"""
    try:
        # 获取当前配置
        current_config = config_manager.load_config()
        
        # 执行回滚
        restored_config = rollback_manager.rollback_to_version(config_id, request.version)
        
        # 保存配置
        await _save_config_to_file(config_manager, restored_config, request.reason)
        
        # 重载配置
        updated_config = config_manager.reload_config()
        
        # 记录变更
        changes = _detect_config_changes(current_config, restored_config)
        
        # 发送通知
        background_tasks.add_task(
            notification_service.notify_config_rollback,
            config_id,
            request.version,
            request.reason
        )
        
        return ConfigUpdateResponse(
            success=True,
            message=f"配置回滚成功: {config_id} -> 版本 {request.version}",
            updated_config=updated_config,
            changes=changes
        )
        
    except Exception as e:
        logger.error(f"回滚配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"回滚配置失败: {str(e)}")


# === 辅助函数 ===

async def _save_config_to_file(config_manager: ConfigManager, config: Dict[str, Any], reason: str):
    """保存配置到文件"""
    try:
        # 这里简化处理，实际应该根据配置层次结构保存到不同文件
        config_dir = config_manager._config_loader.config_dir
        
        # 保存主配置文件
        main_config_file = config_dir / "default.yaml"
        with open(main_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"配置已保存到文件: {reason}")
        
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        raise ConfigError(f"保存配置文件失败: {str(e)}")


def _detect_config_changes(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
    """检测配置变更"""
    changes = []
    
    # 比较配置
    old_keys = set(old_config.keys())
    new_keys = set(new_config.keys())
    
    # 新增的键
    for key in new_keys - old_keys:
        changes.append(f"新增配置项: {key}")
    
    # 删除的键
    for key in old_keys - new_keys:
        changes.append(f"删除配置项: {key}")
    
    # 修改的值
    for key in old_keys & new_keys:
        if old_config[key] != new_config[key]:
            changes.append(f"修改配置项: {key}")
    
    return changes


# === 健康检查和状态API ===

@router.get("/health")
async def config_health():
    """配置服务健康检查"""
    try:
        status = {
            "status": "healthy",
            "config_manager": _config_manager is not None,
            "config_watcher": _config_watcher is not None,
            "notification_service": _notification_service is not None,
            "rollback_manager": _rollback_manager is not None,
            "watcher_running": _config_watcher.is_watching() if _config_watcher else False
        }
        
        return status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/status")
async def get_config_status(
    config_manager: ConfigManager = Depends(get_config_manager),
    config_watcher: ConfigWatcher = Depends(get_config_watcher),
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """获取配置服务状态"""
    try:
        config_info = config_manager.get_config_info()
        watcher_status = config_watcher.get_watching_status()
        backup_info = rollback_manager.get_backup_info()
        
        return {
            "config_info": config_info,
            "watcher_status": watcher_status,
            "backup_info": backup_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取配置状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")


# === 初始化函数 ===

def init_config_system(config_dir: Optional[str] = None):
    """初始化配置系统"""
    global _config_manager, _config_watcher, _notification_service, _rollback_manager
    
    try:
        # 设置配置目录
        if config_dir is None:
            # 默认配置目录为项目根目录下的config文件夹
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = str(project_root / "config")
        
        # 初始化配置管理器
        from .loader import ConfigLoader
        _config_manager = ConfigLoader(config_dir)
        logger.info(f"配置管理器初始化成功: {config_dir}")
        
        # 初始化配置监听器
        _config_watcher = ConfigWatcher(_config_manager)
        logger.info("配置监听器初始化成功")
        
        # 初始化通知服务
        from .notifications import NotificationManager
        notification_manager = NotificationManager()
        _notification_service = ConfigNotificationService(notification_manager)
        logger.info("配置通知服务初始化成功")
        
        # 初始化回滚管理器
        _rollback_manager = ConfigRollbackManager(_config_manager)
        logger.info("配置回滚管理器初始化成功")
        
        # 启动配置监听
        _config_watcher.start_watching()
        logger.info("配置监听已启动")
        
        return _config_manager
        
    except Exception as e:
        logger.error(f"配置系统初始化失败: {e}")
        raise ConfigError(f"配置系统初始化失败: {str(e)}")


def get_config_system_status() -> Dict[str, Any]:
    """获取配置系统状态"""
    return {
        "config_manager": _config_manager is not None,
        "config_watcher": _config_watcher is not None,
        "notification_service": _notification_service is not None,
        "rollback_manager": _rollback_manager is not None,
        "watcher_running": _config_watcher.is_watching() if _config_watcher else False
    }


def shutdown_config_system():
    """关闭配置系统"""
    global _config_manager, _config_watcher, _notification_service, _rollback_manager
    
    try:
        if _config_watcher:
            _config_watcher.stop_watching()
            logger.info("配置监听已停止")
        
        if _notification_service:
            _notification_service.shutdown()
            logger.info("配置通知服务已关闭")
        
        # 清理全局实例
        _config_manager = None
        _config_watcher = None
        _notification_service = None
        _rollback_manager = None
        
        logger.info("配置系统已关闭")
        
    except Exception as e:
        logger.error(f"关闭配置系统失败: {e}")
        raise ConfigError(f"关闭配置系统失败: {str(e)}")