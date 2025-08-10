"""
API框架依赖注入模块
"""

from typing import Optional, Generator, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from ..schemas.response import StandardResponse

logger = logging.getLogger(__name__)

# HTTP Bearer 认证
security = HTTPBearer()


def get_db() -> Generator:
    """获取数据库会话"""
    try:
        # 这里应该从配置中获取数据库URL
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        DATABASE_URL = "postgresql://postgres:password@localhost:5432/llms_txt_gen"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="数据库服务不可用"
        )


def get_redis_client():
    """获取Redis客户端"""
    try:
        import redis
        
        REDIS_URL = "redis://localhost:6379"
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis服务不可用"
        )


def get_config_manager():
    """获取配置管理器"""
    try:
        # 简化版本，返回一个模拟的配置管理器
        class MockConfigManager:
            def get_all_configs(self):
                return {
                    "app_name": "llms.txt-gen",
                    "version": "1.0.0",
                    "debug": False,
                    "database_url": "postgresql://localhost:5432/llms_txt_gen",
                    "redis_url": "redis://localhost:6379"
                }
        
        return MockConfigManager()
    except Exception as e:
        logger.error(f"配置管理器初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="配置管理服务不可用"
        )


def get_logger() -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(__name__)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取当前用户信息"""
    try:
        # 简化版本，返回一个模拟用户
        return {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True
        }
        
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败"
        )


def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前活跃用户"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    return current_user


def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前管理员用户"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def verify_permission(required_permission: str):
    """权限验证装饰器"""
    def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        try:
            # 简化版本，检查用户角色
            user_role = current_user.get("role", "user")
            
            # 管理员拥有所有权限
            if user_role == "admin":
                return current_user
            
            # 普通用户权限检查
            if required_permission == "read":
                return current_user
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_permission} 权限"
            )
            
        except Exception as e:
            logger.error(f"权限验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限验证失败"
            )
    
    return permission_checker


def get_request_id(request) -> str:
    """获取请求ID"""
    return getattr(request.state, 'request_id', 'unknown')


def get_client_ip(request) -> str:
    """获取客户端IP地址"""
    return request.client.host if request.client else "unknown"


def get_user_agent(request) -> str:
    """获取用户代理"""
    return request.headers.get("user-agent", "unknown")


def rate_limit_dependency(request, max_requests: int = 100, time_window: int = 60):
    """限流依赖"""
    client_ip = get_client_ip(request)
    request_id = get_request_id(request)
    
    try:
        import redis
        import time
        
        redis_client = get_redis_client()
        
        # 使用Redis实现限流
        key = f"rate_limit:{client_ip}"
        current_time = time.time()
        
        # 清理过期的请求记录
        redis_client.zremrangebyscore(key, 0, current_time - time_window)
        
        # 获取当前时间窗口内的请求数
        request_count = redis_client.zcard(key)
        
        if request_count >= max_requests:
            logger.warning(
                f"请求限流: {client_ip}",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "request_count": request_count,
                    "max_requests": max_requests
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求频率过高，请稍后再试"
            )
        
        # 记录当前请求
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, time_window)
        
    except Exception as e:
        logger.error(f"限流检查失败: {e}")
        # 如果Redis不可用，跳过限流检查


def validate_pagination(
    page: int = 1,
    page_size: int = 10,
    max_page_size: int = 100
) -> tuple[int, int]:
    """验证分页参数"""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > max_page_size:
        page_size = max_page_size
    
    return page, page_size


def get_api_version() -> str:
    """获取API版本"""
    return "1.0.0"


def get_service_status() -> Dict[str, Any]:
    """获取服务状态"""
    try:
        # 检查数据库连接
        try:
            db = next(get_db())
            db.close()
            db_status = "connected"
        except:
            db_status = "disconnected"
        
        # 检查Redis连接
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            redis_status = "connected"
        except:
            redis_status = "disconnected"
        
        # 检查配置管理器
        try:
            config_manager = get_config_manager()
            config_status = "connected"
        except:
            config_status = "disconnected"
        
        return {
            "database": db_status,
            "redis": redis_status,
            "config_manager": config_status,
            "api_version": get_api_version(),
            "status": "healthy" if all([
                db_status == "connected",
                redis_status == "connected",
                config_status == "connected"
            ]) else "degraded"
        }
        
    except Exception as e:
        logger.error(f"服务状态检查失败: {e}")
        return {
            "database": "unknown",
            "redis": "unknown",
            "config_manager": "unknown",
            "api_version": get_api_version(),
            "status": "error"
        }