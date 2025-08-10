"""
JWT认证模块
"""

import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.constants import ALGORITHMS

logger = logging.getLogger(__name__)


class JWTHandler:
    """JWT处理器"""
    
    def __init__(self, 
                 secret_key: str = "your-secret-key-here",
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌"
            )
        except Exception as e:
            logger.error(f"JWT处理异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌验证失败"
            )
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌（不验证）"""
        try:
            payload = jwt.decode(token, self.secret_key, options={"verify_signature": False})
            return payload
        except Exception as e:
            logger.warning(f"JWT解码失败: {e}")
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """检查令牌是否过期"""
        try:
            payload = self.decode_token(token)
            if not payload:
                return True
            
            exp = payload.get("exp")
            if not exp:
                return True
            
            return datetime.now(timezone.utc) > datetime.fromtimestamp(exp, timezone.utc)
        except Exception:
            return True
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """使用刷新令牌获取新的访问令牌"""
        try:
            payload = self.verify_token(refresh_token)
            
            # 检查是否为刷新令牌
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
            
            # 提取用户信息
            user_data = {
                "sub": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
            
            # 创建新的访问令牌
            return self.create_access_token(user_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刷新令牌失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌失败"
            )


class PasswordHandler:
    """密码处理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        result = {
            "is_valid": True,
            "errors": [],
            "score": 0,
            "suggestions": []
        }
        
        # 检查长度
        if len(password) < 8:
            result["errors"].append("密码长度至少8位")
            result["score"] -= 2
        else:
            result["score"] += 1
        
        # 检查复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        complexity = sum([has_upper, has_lower, has_digit, has_special])
        result["score"] += complexity
        
        if complexity < 3:
            result["errors"].append("密码应包含大小写字母、数字和特殊字符")
        
        # 检查常见弱密码
        common_passwords = [
            "password", "123456", "qwerty", "abc123",
            "password123", "admin", "root", "letmein"
        ]
        
        if password.lower() in common_passwords:
            result["errors"].append("密码过于常见")
            result["score"] -= 3
        
        # 检查重复字符
        if len(set(password)) < len(password) / 2:
            result["suggestions"].append("建议使用更多不同的字符")
        
        # 设置有效性
        result["is_valid"] = len(result["errors"]) == 0 and result["score"] >= 3
        
        # 添加建议
        if result["score"] < 5:
            result["suggestions"].append("建议使用更复杂的密码")
        
        return result


class TokenBlacklist:
    """令牌黑名单"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.blacklist_key = "token_blacklist"
    
    def add_to_blacklist(self, token: str, expire_time: Optional[int] = None):
        """添加令牌到黑名单"""
        if not self.redis_client:
            return
        
        try:
            # 解码令牌获取过期时间
            jwt_handler = JWTHandler()
            payload = jwt_handler.decode_token(token)
            
            if payload:
                exp = payload.get("exp")
                if exp:
                    # 计算剩余时间
                    remaining_time = int(exp - datetime.now(timezone.utc).timestamp())
                    if remaining_time > 0:
                        self.redis_client.setex(
                            f"{self.blacklist_key}:{token}",
                            remaining_time,
                            "1"
                        )
                        logger.info(f"令牌已添加到黑名单: {token[:20]}...")
        except Exception as e:
            logger.error(f"添加令牌到黑名单失败: {e}")
    
    def is_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"{self.blacklist_key}:{token}")
        except Exception as e:
            logger.error(f"检查令牌黑名单失败: {e}")
            return False
    
    def remove_from_blacklist(self, token: str):
        """从黑名单中移除令牌"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(f"{self.blacklist_key}:{token}")
            logger.info(f"令牌已从黑名单中移除: {token[:20]}...")
        except Exception as e:
            logger.error(f"从黑名单移除令牌失败: {e}")


# 全局实例
jwt_handler = JWTHandler()
password_handler = PasswordHandler()
token_blacklist = TokenBlacklist()


def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """创建令牌对（访问令牌和刷新令牌）"""
    access_token = jwt_handler.create_access_token(user_data)
    refresh_token = jwt_handler.create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": jwt_handler.access_token_expire_minutes * 60
    }


def verify_access_token(token: str) -> Dict[str, Any]:
    """验证访问令牌"""
    # 检查黑名单
    if token_blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已被注销"
        )
    
    # 验证令牌
    payload = jwt_handler.verify_token(token)
    
    # 检查令牌类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌类型"
        )
    
    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """验证刷新令牌"""
    # 检查黑名单
    if token_blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已被注销"
        )
    
    # 验证令牌
    payload = jwt_handler.verify_token(token)
    
    # 检查令牌类型
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌类型"
        )
    
    return payload


def invalidate_token(token: str):
    """使令牌失效"""
    token_blacklist.add_to_blacklist(token)


def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """获取令牌信息"""
    return jwt_handler.decode_token(token)