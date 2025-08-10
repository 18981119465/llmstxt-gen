"""
RBAC授权模块
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 系统管理员
    USER = "user"            # 普通用户
    API_CLIENT = "api"       # API客户端
    GUEST = "guest"          # 访客


class Permission(str, Enum):
    """权限类型枚举"""
    READ = "read"            # 读取权限
    WRITE = "write"          # 写入权限
    DELETE = "delete"        # 删除权限
    ADMIN = "admin"          # 管理权限
    MANAGE_USERS = "manage_users"    # 用户管理
    MANAGE_CONFIG = "manage_config"    # 配置管理
    MANAGE_SYSTEM = "manage_system"    # 系统管理


class Resource(str, Enum):
    """资源类型枚举"""
    DOCUMENTS = "documents"  # 文档
    PROJECTS = "projects"    # 项目
    USERS = "users"          # 用户
    CONFIG = "config"        # 配置
    SYSTEM = "system"        # 系统
    LOGS = "logs"            # 日志
    API = "api"              # API


class RolePermission:
    """角色权限映射"""
    
    # 角色权限映射
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            Resource.DOCUMENTS: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
            Resource.PROJECTS: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
            Resource.USERS: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.MANAGE_USERS],
            Resource.CONFIG: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.MANAGE_CONFIG],
            Resource.SYSTEM: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.MANAGE_SYSTEM],
            Resource.LOGS: [Permission.READ, Permission.WRITE, Permission.DELETE],
            Resource.API: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
        },
        UserRole.USER: {
            Resource.DOCUMENTS: [Permission.READ, Permission.WRITE],
            Resource.PROJECTS: [Permission.READ, Permission.WRITE],
            Resource.USERS: [Permission.READ],
            Resource.CONFIG: [Permission.READ],
            Resource.SYSTEM: [Permission.READ],
            Resource.LOGS: [Permission.READ],
            Resource.API: [Permission.READ, Permission.WRITE],
        },
        UserRole.API_CLIENT: {
            Resource.DOCUMENTS: [Permission.READ, Permission.WRITE],
            Resource.PROJECTS: [Permission.READ, Permission.WRITE],
            Resource.USERS: [Permission.READ],
            Resource.CONFIG: [Permission.READ],
            Resource.SYSTEM: [Permission.READ],
            Resource.LOGS: [Permission.READ],
            Resource.API: [Permission.READ, Permission.WRITE],
        },
        UserRole.GUEST: {
            Resource.DOCUMENTS: [Permission.READ],
            Resource.PROJECTS: [Permission.READ],
            Resource.USERS: [],
            Resource.CONFIG: [],
            Resource.SYSTEM: [Permission.READ],
            Resource.LOGS: [Permission.READ],
            Resource.API: [Permission.READ],
        }
    }
    
    # 权限继承关系
    PERMISSION_HIERARCHY = {
        Permission.READ: set(),
        Permission.WRITE: {Permission.READ},
        Permission.DELETE: {Permission.READ, Permission.WRITE},
        Permission.ADMIN: {Permission.READ, Permission.WRITE, Permission.DELETE},
        Permission.MANAGE_USERS: {Permission.READ, Permission.WRITE, Permission.DELETE},
        Permission.MANAGE_CONFIG: {Permission.READ, Permission.WRITE},
        Permission.MANAGE_SYSTEM: {Permission.READ, Permission.WRITE, Permission.DELETE},
    }


class RBACManager:
    """RBAC管理器"""
    
    def __init__(self):
        self.role_permissions = RolePermission.ROLE_PERMISSIONS
        self.permission_hierarchy = RolePermission.PERMISSION_HIERARCHY
    
    def has_permission(self, 
                      user_role: UserRole, 
                      resource: Resource, 
                      permission: Permission,
                      resource_owner_id: Optional[str] = None,
                      user_id: Optional[str] = None) -> bool:
        """检查用户是否有指定权限"""
        try:
            # 获取角色的权限列表
            role_permissions = self.role_permissions.get(user_role, {})
            resource_permissions = role_permissions.get(resource, [])
            
            # 检查是否有直接权限
            if permission in resource_permissions:
                return True
            
            # 检查权限继承
            for perm in resource_permissions:
                if permission in self.permission_hierarchy.get(perm, set()):
                    return True
            
            # 资源所有者权限检查
            if resource_owner_id and user_id and resource_owner_id == user_id:
                # 资源所有者通常有更多权限
                owner_permissions = [Permission.READ, Permission.WRITE, Permission.DELETE]
                if permission in owner_permissions:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    def get_user_permissions(self, user_role: UserRole) -> Dict[Resource, List[Permission]]:
        """获取用户的所有权限"""
        return self.role_permissions.get(user_role, {})
    
    def check_multiple_permissions(self, 
                                 user_role: UserRole,
                                 permissions: List[tuple[Resource, Permission]],
                                 resource_owner_id: Optional[str] = None,
                                 user_id: Optional[str] = None) -> Dict[str, bool]:
        """检查多个权限"""
        results = {}
        
        for resource, permission in permissions:
            key = f"{resource.value}:{permission.value}"
            results[key] = self.has_permission(
                user_role, resource, permission, resource_owner_id, user_id
            )
        
        return results
    
    def get_accessible_resources(self, user_role: UserRole) -> List[Resource]:
        """获取用户可访问的资源"""
        accessible_resources = []
        
        for resource, permissions in self.role_permissions.get(user_role, {}).items():
            if permissions:  # 如果有权限，则可以访问
                accessible_resources.append(resource)
        
        return accessible_resources
    
    def get_resource_permissions(self, user_role: UserRole, resource: Resource) -> List[Permission]:
        """获取用户对指定资源的权限"""
        return self.role_permissions.get(user_role, {}).get(resource, [])
    
    def add_permission_to_role(self, user_role: UserRole, resource: Resource, permission: Permission):
        """为角色添加权限"""
        if user_role not in self.role_permissions:
            self.role_permissions[user_role] = {}
        
        if resource not in self.role_permissions[user_role]:
            self.role_permissions[user_role][resource] = []
        
        if permission not in self.role_permissions[user_role][resource]:
            self.role_permissions[user_role][resource].append(permission)
            logger.info(f"为角色 {user_role} 添加了 {resource}:{permission} 权限")
    
    def remove_permission_from_role(self, user_role: UserRole, resource: Resource, permission: Permission):
        """从角色移除权限"""
        if user_role in self.role_permissions:
            if resource in self.role_permissions[user_role]:
                if permission in self.role_permissions[user_role][resource]:
                    self.role_permissions[user_role][resource].remove(permission)
                    logger.info(f"从角色 {user_role} 移除了 {resource}:{permission} 权限")
    
    def create_custom_role(self, role_name: str, permissions: Dict[Resource, List[Permission]]):
        """创建自定义角色"""
        if role_name not in self.role_permissions:
            self.role_permissions[role_name] = permissions
            logger.info(f"创建了自定义角色 {role_name}")
        else:
            logger.warning(f"角色 {role_name} 已存在")


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, rbac_manager: RBACManager):
        self.rbac_manager = rbac_manager
    
    def require_permission(self, resource: Resource, permission: Permission):
        """权限检查装饰器工厂"""
        def permission_decorator(func):
            def wrapper(*args, **kwargs):
                # 从kwargs中获取用户信息
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户未认证"
                    )
                
                user_role = current_user.get('role', UserRole.GUEST)
                user_id = current_user.get('id')
                
                # 检查资源所有者
                resource_owner_id = kwargs.get('resource_owner_id')
                
                if not self.rbac_manager.has_permission(
                    user_role, resource, permission, resource_owner_id, user_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要 {permission.value} 权限"
                    )
                
                return func(*args, **kwargs)
            return wrapper
        return permission_decorator
    
    def require_role(self, required_role: UserRole):
        """角色检查装饰器工厂"""
        def role_decorator(func):
            def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户未认证"
                    )
                
                user_role = current_user.get('role', UserRole.GUEST)
                
                if user_role != required_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要 {required_role.value} 角色"
                    )
                
                return func(*args, **kwargs)
            return wrapper
        return role_decorator
    
    def require_any_role(self, roles: List[UserRole]):
        """任意角色检查装饰器工厂"""
        def role_decorator(func):
            def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户未认证"
                    )
                
                user_role = current_user.get('role', UserRole.GUEST)
                
                if user_role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要以下角色之一: {[role.value for role in roles]}"
                    )
                
                return func(*args, **kwargs)
            return wrapper
        return role_decorator


# 全局实例
rbac_manager = RBACManager()
permission_checker = PermissionChecker(rbac_manager)


def check_user_permission(user: Dict[str, Any], required_permission: str) -> bool:
    """检查用户权限（简化版本）"""
    user_role = user.get('role', UserRole.GUEST)
    
    # 管理员拥有所有权限
    if user_role == UserRole.ADMIN:
        return True
    
    # 普通用户权限
    if user_role == UserRole.USER:
        return required_permission in ['read', 'write']
    
    # API客户端权限
    if user_role == UserRole.API_CLIENT:
        return required_permission in ['read', 'write']
    
    # 访客权限
    if user_role == UserRole.GUEST:
        return required_permission == 'read'
    
    return False


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """根据用户ID获取用户信息（简化版本）"""
    # 这里应该从数据库获取用户信息
    # 返回模拟数据
    return {
        "id": user_id,
        "username": "testuser",
        "email": "test@example.com",
        "role": UserRole.USER,
        "is_active": True
    }


def get_user_permissions(user: Dict[str, Any]) -> Dict[str, List[str]]:
    """获取用户权限（简化版本）"""
    user_role = user.get('role', UserRole.GUEST)
    
    permissions = {
        UserRole.ADMIN: ['read', 'write', 'delete', 'admin'],
        UserRole.USER: ['read', 'write'],
        UserRole.API_CLIENT: ['read', 'write'],
        UserRole.GUEST: ['read']
    }
    
    return {
        "role": user_role.value,
        "permissions": permissions.get(user_role, [])
    }