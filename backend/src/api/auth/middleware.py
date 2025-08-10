"""
认证中间件
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Callable
import logging
from ..auth.jwt import verify_access_token, verify_refresh_token, invalidate_token
from ..auth.rbac import rbac_manager, UserRole, Resource, Permission
from ..core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self):
        self.public_paths = [
            "/",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/system/status",
            "/api/v1/system/health",
            "/api/v1/system/config",
            "/api/v1/system/metrics",
            "/api/v1/system/logs",
            "/api/v1/system/version",
            "/api/v1/info",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    def is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    async def __call__(self, request: Request, call_next: Callable):
        """中间件调用"""
        path = request.url.path
        
        # 跳过公开路径
        if self.is_public_path(path):
            return await call_next(request)
        
        # 获取认证头
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("缺少认证令牌")
        
        token = auth_header.split(" ")[1]
        
        try:
            # 验证令牌
            payload = verify_access_token(token)
            
            # 将用户信息添加到请求状态
            request.state.user = payload
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role", UserRole.GUEST)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"认证失败: {e}")
            raise AuthenticationError("认证失败")
        
        return await call_next(request)


def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前用户"""
    if not hasattr(request.state, 'user'):
        raise AuthenticationError("用户未认证")
    
    return request.state.user


def get_current_user_id(request: Request) -> str:
    """获取当前用户ID"""
    if not hasattr(request.state, 'user_id'):
        raise AuthenticationError("用户未认证")
    
    return request.state.user_id


def get_current_user_role(request: Request) -> UserRole:
    """获取当前用户角色"""
    if not hasattr(request.state, 'user_role'):
        raise AuthenticationError("用户未认证")
    
    return request.state.user_role


def require_permission(resource: Resource, permission: Permission):
    """权限验证装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取请求对象"
                )
            
            # 获取用户角色
            user_role = get_current_user_role(request)
            user_id = get_current_user_id(request)
            
            # 检查资源所有者
            resource_owner_id = kwargs.get('resource_owner_id')
            
            # 验证权限
            if not rbac_manager.has_permission(
                user_role, resource, permission, resource_owner_id, user_id
            ):
                raise AuthorizationError(f"需要 {permission.value} 权限")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(required_role: UserRole):
    """角色验证装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取请求对象"
                )
            
            # 获取用户角色
            user_role = get_current_user_role(request)
            
            # 验证角色
            if user_role != required_role:
                raise AuthorizationError(f"需要 {required_role.value} 角色")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(roles: list[UserRole]):
    """任意角色验证装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取请求对象"
                )
            
            # 获取用户角色
            user_role = get_current_user_role(request)
            
            # 验证角色
            if user_role not in roles:
                raise AuthorizationError(f"需要以下角色之一: {[role.value for role in roles]}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin():
    """管理员权限装饰器"""
    return require_role(UserRole.ADMIN)


def require_user():
    """用户权限装饰器"""
    return require_any_role([UserRole.USER, UserRole.ADMIN])


async def get_token_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """从令牌获取用户信息"""
    try:
        payload = verify_access_token(credentials.credentials)
        return payload
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"令牌验证失败: {e}")
        raise AuthenticationError("令牌验证失败")


async def get_refresh_token_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """从刷新令牌获取用户信息"""
    try:
        payload = verify_refresh_token(credentials.credentials)
        return payload
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"刷新令牌验证失败: {e}")
        raise AuthenticationError("刷新令牌验证失败")


class TokenValidator:
    """令牌验证器"""
    
    def __init__(self):
        self.blacklisted_tokens = set()
    
    def is_token_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        return token in self.blacklisted_tokens
    
    def blacklist_token(self, token: str):
        """将令牌加入黑名单"""
        self.blacklisted_tokens.add(token)
        invalidate_token(token)
        logger.info(f"令牌已加入黑名单: {token[:20]}...")
    
    def remove_from_blacklist(self, token: str):
        """从黑名单中移除令牌"""
        if token in self.blacklisted_tokens:
            self.blacklisted_tokens.remove(token)
            logger.info(f"令牌已从黑名单中移除: {token[:20]}...")


# 全局实例
auth_middleware = AuthMiddleware()
token_validator = TokenValidator()


# 常用的依赖注入函数
async def get_current_active_user(
    user: Dict[str, Any] = Depends(get_token_user)
) -> Dict[str, Any]:
    """获取当前活跃用户"""
    if not user.get("is_active", True):
        raise AuthenticationError("用户已被禁用")
    
    return user


async def get_current_admin_user(
    user: Dict[str, Any] = Depends(get_token_user)
) -> Dict[str, Any]:
    """获取当前管理员用户"""
    user_role = user.get("role", UserRole.GUEST)
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("需要管理员权限")
    
    return user


async def verify_user_permission(
    user: Dict[str, Any] = Depends(get_token_user),
    resource: Resource = None,
    permission: Permission = None,
    resource_owner_id: str = None
) -> bool:
    """验证用户权限"""
    user_role = user.get("role", UserRole.GUEST)
    user_id = user.get("sub")
    
    return rbac_manager.has_permission(
        user_role, resource, permission, resource_owner_id, user_id
    )