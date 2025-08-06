"""
配置管理Web界面路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import json
import yaml
from pathlib import Path

from .core import ConfigManager, ConfigValidator
from .rollback import ConfigRollbackManager
from .management import get_config_manager, get_rollback_manager
from .validator import ConfigValidator

# 创建路由器
router = APIRouter()

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 静态文件
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    router.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@router.get("/", response_class=HTMLResponse)
async def config_dashboard(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """配置管理仪表板"""
    try:
        config = config_manager.load_config()
        config_info = config_manager.get_config_info()
        
        return templates.TemplateResponse("config/dashboard.html", {
            "request": request,
            "config": config,
            "config_info": config_info
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"加载配置失败: {str(e)}"
        })


@router.get("/editor", response_class=HTMLResponse)
async def config_editor(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """配置编辑器"""
    try:
        config = config_manager.load_config()
        config_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
        
        return templates.TemplateResponse("config/editor.html", {
            "request": request,
            "config": config,
            "config_yaml": config_yaml
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"加载配置失败: {str(e)}"
        })


@router.get("/validator", response_class=HTMLResponse)
async def config_validator_page(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """配置验证页面"""
    try:
        config = config_manager.load_config()
        
        return templates.TemplateResponse("config/validator.html", {
            "request": request,
            "config": config
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"加载配置失败: {str(e)}"
        })


@router.get("/history", response_class=HTMLResponse)
async def config_history_page(
    request: Request,
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """配置历史页面"""
    try:
        history = rollback_manager.get_history()
        
        return templates.TemplateResponse("config/history.html", {
            "request": request,
            "history": history
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"加载历史记录失败: {str(e)}"
        })


@router.get("/api/config")
async def get_config_api(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """获取配置API"""
    try:
        config = config_manager.load_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/config")
async def update_config_api(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """更新配置API"""
    try:
        data = await request.json()
        config = data.get("config")
        
        if not config:
            return {
                "success": False,
                "error": "配置数据不能为空"
            }
        
        success = config_manager.save_config(config)
        
        if success:
            return {
                "success": True,
                "message": "配置更新成功"
            }
        else:
            return {
                "success": False,
                "error": "配置更新失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/config/validate")
async def validate_config_api(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager),
    validator: ConfigValidator = Depends()
):
    """验证配置API"""
    try:
        data = await request.json()
        config = data.get("config")
        
        if not config:
            return {
                "success": False,
                "error": "配置数据不能为空"
            }
        
        result = validator.validate_config(config)
        
        return {
            "success": True,
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/config/rollback")
async def rollback_config_api(
    request: Request,
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """回滚配置API"""
    try:
        data = await request.json()
        version_id = data.get("version_id")
        
        if not version_id:
            return {
                "success": False,
                "error": "版本ID不能为空"
            }
        
        success = rollback_manager.rollback(version_id)
        
        if success:
            return {
                "success": True,
                "message": "配置回滚成功"
            }
        else:
            return {
                "success": False,
                "error": "配置回滚失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/api/config/history")
async def get_config_history_api(
    rollback_manager: ConfigRollbackManager = Depends(get_rollback_manager)
):
    """获取配置历史API"""
    try:
        history = rollback_manager.get_history()
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/config/reload")
async def reload_config_api(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """重新加载配置API"""
    try:
        success = config_manager.reload_config()
        
        if success:
            return {
                "success": True,
                "message": "配置重新加载成功"
            }
        else:
            return {
                "success": False,
                "error": "配置重新加载失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }