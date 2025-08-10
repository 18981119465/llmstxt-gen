"""
认证路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone

from ..auth.jwt import (
    jwt_handler, 
    password_handler, 
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
    invalidate_token
)
from ..auth.rbac import UserRole, Resource, Permission, rbac_manager
from ..auth.middleware import (
    get_token_user,
    get_refresh_token_user,
    get_current_active_user,
    get_current_admin_user,
    require_permission,
    require_role
)
from ..schemas.response import (
    StandardResponse,
    ErrorResponse,
    create_success_response,
    create_error_response
)
from ..utils.security import SecurityHelper

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# 请求模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not SecurityHelper.validate_username(v):
            raise ValueError("用户名格式不正确")
        return v


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="确认密码")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not SecurityHelper.validate_username(v):
            raise ValueError("用户名格式不正确")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        result = password_handler.validate_password_strength(v)
        if not result['is_valid']:
            raise ValueError(f"密码强度不足: {', '.join(result['errors'])}")
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError("密码不匹配")
        return v


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., min_length=6, max_length=100, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")
    confirm_password: str = Field(..., min_length=8, max_length=100, description="确认新密码")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        result = password_handler.validate_password_strength(v)
        if not result['is_valid']:
            raise ValueError(f"密码强度不足: {', '.join(result['errors'])}")
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError("密码不匹配")
        return v


class UserProfile(BaseModel):
    """用户资料模型"""
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class AuthResponse(BaseModel):
    """认证响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserProfile


# 模拟用户数据库
class MockUserDB:
    """模拟用户数据库"""
    
    def __init__(self):
        self.users = {
            "admin": {
                "id": "admin_001",
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": password_handler.hash_password("admin123"),
                "role": UserRole.ADMIN,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "last_login": None
            },
            "testuser": {
                "id": "user_001",
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": password_handler.hash_password("password123"),
                "role": UserRole.USER,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "last_login": None
            }
        }
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        return self.users.get(username)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        for user in self.users.values():
            if user.get("email") == email:
                return user
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        username = user_data["username"]
        self.users[username] = user_data
        return user_data
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新用户"""
        if username in self.users:
            self.users[username].update(updates)
            return self.users[username]
        return None
    
    def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        return username in self.users
    
    def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return any(user.get("email") == email for user in self.users.values())


user_db = MockUserDB()


@router.post("/login", response_model=StandardResponse)
async def login(request: LoginRequest) -> StandardResponse:
    """用户登录"""
    try:
        # 查找用户
        user = user_db.get_user_by_username(request.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        if not password_handler.verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 检查用户状态
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        # 创建令牌
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
        
        tokens = create_token_pair(token_data)
        
        # 更新最后登录时间
        user_db.update_user(request.username, {"last_login": datetime.now(timezone.utc)})
        
        # 构建用户资料
        user_profile = UserProfile(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
            last_login=user.get("last_login")
        )
        
        auth_response = AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_profile
        )
        
        return StandardResponse(
            success=True,
            data=auth_response.model_dump(),
            message="登录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.post("/register", response_model=StandardResponse)
async def register(request: RegisterRequest) -> StandardResponse:
    """用户注册"""
    try:
        # 检查用户名是否已存在
        if user_db.username_exists(request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if user_db.email_exists(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建用户
        user_data = {
            "id": SecurityHelper.generate_secure_token(8),
            "username": request.username,
            "email": request.email,
            "password_hash": password_handler.hash_password(request.password),
            "role": request.role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None
        }
        
        created_user = user_db.create_user(user_data)
        
        # 创建令牌
        token_data = {
            "sub": created_user["id"],
            "username": created_user["username"],
            "email": created_user["email"],
            "role": created_user["role"]
        }
        
        tokens = create_token_pair(token_data)
        
        # 构建用户资料
        user_profile = UserProfile(
            id=created_user["id"],
            username=created_user["username"],
            email=created_user["email"],
            role=created_user["role"],
            is_active=created_user["is_active"],
            created_at=created_user["created_at"],
            last_login=None
        )
        
        auth_response = AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_profile
        )
        
        return StandardResponse(
            success=True,
            data=auth_response.model_dump(),
            message="注册成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )


@router.post("/refresh", response_model=StandardResponse)
async def refresh_token(request: RefreshTokenRequest) -> StandardResponse:
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = verify_refresh_token(request.refresh_token)
        
        # 创建新的访问令牌
        user_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
        
        new_access_token = jwt_handler.create_access_token(user_data)
        
        return StandardResponse(
            success=True,
            data={
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": jwt_handler.access_token_expire_minutes * 60
            },
            message="令牌刷新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.post("/logout", response_model=StandardResponse)
async def logout(
    refresh_token: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """用户登出"""
    try:
        # 将刷新令牌加入黑名单
        invalidate_token(refresh_token)
        
        return StandardResponse(
            success=True,
            data=None,
            message="登出成功"
        )
        
    except Exception as e:
        logger.error(f"登出失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/profile", response_model=StandardResponse)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """获取用户资料"""
    try:
        # 从数据库获取完整用户信息
        username = current_user.get("username")
        user = user_db.get_user_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 构建用户资料
        user_profile = UserProfile(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
            last_login=user.get("last_login")
        )
        
        return StandardResponse(
            success=True,
            data=user_profile.model_dump(),
            message="获取用户资料成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )


@router.put("/profile", response_model=StandardResponse)
async def update_profile(
    email: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """更新用户资料"""
    try:
        username = current_user.get("username")
        
        # 验证邮箱格式
        if email and not SecurityHelper.validate_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱格式不正确"
            )
        
        # 检查邮箱是否已被其他用户使用
        if email and email != current_user.get("email"):
            if user_db.email_exists(email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被使用"
                )
        
        # 更新用户信息
        updates = {}
        if email:
            updates["email"] = email
        
        if updates:
            updated_user = user_db.update_user(username, updates)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
        
        # 返回更新后的用户资料
        user = user_db.get_user_by_username(username)
        user_profile = UserProfile(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
            last_login=user.get("last_login")
        )
        
        return StandardResponse(
            success=True,
            data=user_profile.model_dump(),
            message="用户资料更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败"
        )


@router.post("/change-password", response_model=StandardResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """修改密码"""
    try:
        username = current_user.get("username")
        user = user_db.get_user_by_username(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证当前密码
        if not password_handler.verify_password(request.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 更新密码
        new_password_hash = password_handler.hash_password(request.new_password)
        user_db.update_user(username, {"password_hash": new_password_hash})
        
        return StandardResponse(
            success=True,
            data=None,
            message="密码修改成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )


@router.get("/permissions", response_model=StandardResponse)
async def get_user_permissions(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """获取用户权限"""
    try:
        role_value = current_user.get("role", "guest")
        # 将字符串角色转换为枚举
        if isinstance(role_value, str):
            user_role = UserRole(role_value)
        else:
            user_role = role_value
        
        # 获取用户权限
        permissions = rbac_manager.get_user_permissions(user_role)
        
        # 格式化权限数据
        formatted_permissions = {}
        for resource, perms in permissions.items():
            formatted_permissions[resource.value] = [perm.value for perm in perms]
        
        return StandardResponse(
            success=True,
            data={
                "role": user_role.value,
                "permissions": formatted_permissions
            },
            message="获取用户权限成功"
        )
        
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户权限失败"
        )


@router.delete("/account", response_model=StandardResponse)
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> StandardResponse:
    """删除用户账户"""
    try:
        username = current_user.get("username")
        
        # 这里应该实现真正的删除逻辑
        # 为了安全，通常只是标记为删除而不是真正删除
        
        logger.info(f"用户 {username} 请求删除账户")
        
        return StandardResponse(
            success=True,
            data=None,
            message="账户删除请求已提交"
        )
        
    except Exception as e:
        logger.error(f"删除账户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除账户失败"
        )