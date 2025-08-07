"""
健康检查API端点

提供HTTP接口用于健康检查和状态监控。
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..config import get_config_system
from .health import get_health_checker, HealthStatus, HealthCheckResult
from .logger import get_logger

router = APIRouter(tags=["Health Monitoring"])
logger = get_logger("health.api")


@router.get("/", response_model=Dict[str, Any])
async def get_health_overview():
    """获取整体健康状态概览"""
    try:
        checker = get_health_checker()
        summary = checker.get_health_summary()
        
        logger.info("健康状态概览请求", 
                   overall_status=summary['overall_status'],
                   total_checks=summary['total_checks'])
        
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("获取健康状态概览失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def get_health_status():
    """获取健康状态"""
    try:
        checker = get_health_checker()
        overall_status = checker.get_overall_health()
        
        status_info = {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "description": _get_status_description(overall_status)
        }
        
        logger.info("健康状态请求", status=overall_status.value)
        
        return {
            "success": True,
            "data": status_info
        }
        
    except Exception as e:
        logger.error("获取健康状态失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checks", response_model=Dict[str, Any])
async def get_health_checks(
    service_name: Optional[str] = Query(None, description="服务名称过滤"),
    check_type: Optional[str] = Query(None, description="检查类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤")
):
    """获取所有健康检查结果"""
    try:
        checker = get_health_checker()
        results = checker.results.copy()
        
        # 过滤结果
        filtered_results = {}
        for name, result in results.items():
            if service_name and service_name not in name:
                continue
            if check_type and result.check_type.value != check_type:
                continue
            if status and result.status.value != status:
                continue
            
            filtered_results[name] = {
                "name": result.name,
                "type": result.check_type.value,
                "status": result.status.value,
                "response_time": result.response_time,
                "message": result.message,
                "critical": result.critical,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details
            }
        
        logger.info("健康检查结果请求", 
                   total_results=len(filtered_results),
                   filters=f"service={service_name}, type={check_type}, status={status}")
        
        return {
            "success": True,
            "data": {
                "checks": filtered_results,
                "total": len(filtered_results)
            }
        }
        
    except Exception as e:
        logger.error("获取健康检查结果失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checks/{service_name}", response_model=Dict[str, Any])
async def get_service_health(service_name: str):
    """获取特定服务的健康状态"""
    try:
        checker = get_health_checker()
        
        if service_name not in checker.results:
            raise HTTPException(status_code=404, detail=f"服务 {service_name} 不存在")
        
        result = checker.results[service_name]
        
        service_health = {
            "name": result.name,
            "type": result.check_type.value,
            "status": result.status.value,
            "response_time": result.response_time,
            "message": result.message,
            "critical": result.critical,
            "timestamp": result.timestamp.isoformat(),
            "details": result.details
        }
        
        logger.info("服务健康状态请求", 
                   service_name=service_name,
                   status=result.status.value)
        
        return {
            "success": True,
            "data": service_health
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取服务健康状态失败", error=str(e), service_name=service_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=Dict[str, Any])
async def trigger_health_check():
    """触发健康检查"""
    try:
        checker = get_health_checker()
        
        # 执行健康检查
        import asyncio
        results = await checker.check_all_health()
        
        # 转换结果格式
        check_results = {}
        for name, result in results.items():
            check_results[name] = {
                "name": result.name,
                "type": result.check_type.value,
                "status": result.status.value,
                "response_time": result.response_time,
                "message": result.message,
                "critical": result.critical,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details
            }
        
        overall_status = checker.get_overall_health()
        
        logger.info("触发健康检查", 
                   overall_status=overall_status.value,
                   total_checks=len(check_results))
        
        return {
            "success": True,
            "data": {
                "overall_status": overall_status.value,
                "timestamp": datetime.now().isoformat(),
                "checks": check_results
            }
        }
        
    except Exception as e:
        logger.error("触发健康检查失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_health_metrics():
    """获取健康检查指标"""
    try:
        checker = get_health_checker()
        results = checker.results
        
        metrics = {
            "total_checks": len(results),
            "healthy_checks": sum(1 for r in results.values() 
                               if r.status == HealthStatus.HEALTHY),
            "degraded_checks": sum(1 for r in results.values() 
                                 if r.status == HealthStatus.DEGRADED),
            "unhealthy_checks": sum(1 for r in results.values() 
                                  if r.status == HealthStatus.UNHEALTHY),
            "critical_checks": sum(1 for r in results.values() 
                                 if r.critical and r.status != HealthStatus.HEALTHY),
            "average_response_time": sum(r.response_time for r in results.values()) / len(results) if results else 0,
            "slowest_check": max(results.items(), key=lambda x: x[1].response_time, default=(None, 0))[0],
            "fastest_check": min(results.items(), key=lambda x: x[1].response_time, default=(None, float('inf')))[0]
        }
        
        logger.info("健康检查指标请求", **metrics)
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        logger.error("获取健康检查指标失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def get_health_history(
    limit: int = Query(100, ge=1, le=1000, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取健康检查历史记录"""
    try:
        # 这里应该从数据库或缓存中获取历史记录
        # 暂时返回空数组，实际实现需要连接数据存储
        
        logger.info("健康检查历史请求", limit=limit, offset=offset)
        
        return {
            "success": True,
            "data": {
                "history": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error("获取健康检查历史失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=Dict[str, Any])
async def get_health_config():
    """获取健康检查配置"""
    try:
        config_manager = get_config_manager()
        monitoring_config = config_manager.get_config()
        
        health_config = {
            "endpoint": monitoring_config.health.endpoint,
            "check_interval": monitoring_config.health.check_interval,
            "timeout": monitoring_config.health.timeout,
            "checks": monitoring_config.health.checks
        }
        
        logger.info("健康检查配置请求")
        
        return {
            "success": True,
            "data": health_config
        }
        
    except Exception as e:
        logger.error("获取健康检查配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=Dict[str, Any])
async def update_health_config(config_data: Dict[str, Any]):
    """更新健康检查配置"""
    try:
        config_manager = get_config_manager()
        monitoring_config = config_manager.get_config()
        
        # 更新配置
        if "endpoint" in config_data:
            monitoring_config.health.endpoint = config_data["endpoint"]
        if "check_interval" in config_data:
            monitoring_config.health.check_interval = config_data["check_interval"]
        if "timeout" in config_data:
            monitoring_config.health.timeout = config_data["timeout"]
        if "checks" in config_data:
            monitoring_config.health.checks = config_data["checks"]
        
        # 保存配置
        success = config_manager.save_config(monitoring_config)
        
        if not success:
            raise HTTPException(status_code=500, detail="配置保存失败")
        
        logger.info("健康检查配置更新", **config_data)
        
        return {
            "success": True,
            "message": "配置更新成功",
            "data": config_data
        }
        
    except Exception as e:
        logger.error("更新健康检查配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=Dict[str, Any])
async def reload_health_config():
    """重新加载健康检查配置"""
    try:
        checker = get_health_checker()
        
        # 停止监控
        checker.stop_monitoring()
        
        # 重新加载配置
        config_manager = get_config_manager()
        config_manager.reload_config()
        
        # 重新初始化检查器
        checker.config = config_manager.get_config()
        checker._init_checks()
        
        # 重新启动监控
        checker.start_monitoring()
        
        logger.info("健康检查配置重新加载")
        
        return {
            "success": True,
            "message": "配置重新加载成功"
        }
        
    except Exception as e:
        logger.error("重新加载健康检查配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live", response_model=Dict[str, Any])
async def liveness_probe():
    """存活探针"""
    try:
        # 简单的存活检查
        return {
            "success": True,
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("存活探针失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_probe():
    """就绪探针"""
    try:
        checker = get_health_checker()
        overall_status = checker.get_overall_health()
        
        # 检查是否就绪
        is_ready = overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        
        status_code = 200 if is_ready else 503
        
        return {
            "success": True,
            "status": "ready" if is_ready else "not_ready",
            "overall_health": overall_status.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("就绪探针失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _get_status_description(status: HealthStatus) -> str:
    """获取状态描述"""
    descriptions = {
        HealthStatus.HEALTHY: "系统运行正常，所有检查都通过",
        HealthStatus.DEGRADED: "系统运行但某些检查失败，性能可能受影响",
        HealthStatus.UNHEALTHY: "系统存在严重问题，需要立即处理",
        HealthStatus.UNKNOWN: "系统状态未知，无法确定健康状态"
    }
    return descriptions.get(status, "未知状态")