"""
API工具模块 - 安全工具
"""

import hashlib
import secrets
import re
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import ipaddress
import logging

logger = logging.getLogger(__name__)


class SecurityHelper:
    """安全助手类"""
    
    # 常见的安全相关正则表达式
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    )
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    USERNAME_PATTERN = re.compile(
        r'^[a-zA-Z0-9_]{3,20}$'
    )
    
    # IP地址白名单和黑名单
    IP_WHITELIST = [
        "127.0.0.1",
        "::1",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16"
    ]
    
    IP_BLACKLIST = [
        # 恶意IP地址
    ]
    
    # 常见的攻击模式
    SQL_INJECTION_PATTERNS = [
        r"(?i)\b(select|insert|update|delete|drop|alter|create|exec|execute)\b",
        r"(?i)\b(union|join|where|having|group by|order by)\b",
        r"(?i)\b(or|and)\s+\d+\s*=\s*\d+",
        r"(?i)\b('|--|;|/\*|\*/|@@)\b"
    ]
    
    XSS_PATTERNS = [
        r"(?i)<script[^>]*>.*?</script>",
        r"(?i)javascript:",
        r"(?i)on\w+\s*=",
        r"(?i)<iframe[^>]*>",
        r"(?i)<object[^>]*>",
        r"(?i)<embed[^>]*>"
    ]
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """生成API密钥"""
        prefix = "llms_"
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}{random_part}"
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, salt: str, password_hash: str) -> bool:
        """验证密码"""
        computed_hash, _ = SecurityHelper.hash_password(password, salt)
        return computed_hash == password_hash
    
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
        has_special = any(c in string.punctuation for c in password)
        
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
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        return bool(SecurityHelper.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """验证用户名格式"""
        return bool(SecurityHelper.USERNAME_PATTERN.match(username))
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """清理输入字符串"""
        if not isinstance(input_string, str):
            return ""
        
        # 截断超长字符串
        if len(input_string) > max_length:
            input_string = input_string[:max_length]
        
        # 移除危险字符
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        
        return input_string.strip()
    
    @staticmethod
    def detect_sql_injection(input_string: str) -> bool:
        """检测SQL注入"""
        if not isinstance(input_string, str):
            return False
        
        for pattern in SecurityHelper.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string):
                logger.warning(f"检测到SQL注入尝试: {input_string}")
                return True
        
        return False
    
    @staticmethod
    def detect_xss(input_string: str) -> bool:
        """检测XSS攻击"""
        if not isinstance(input_string, str):
            return False
        
        for pattern in SecurityHelper.XSS_PATTERNS:
            if re.search(pattern, input_string):
                logger.warning(f"检测到XSS攻击尝试: {input_string}")
                return True
        
        return False
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """验证IP地址"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_ip_allowed(ip: str) -> bool:
        """检查IP是否允许访问"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # 检查黑名单
            for blacklisted_ip in SecurityHelper.IP_BLACKLIST:
                if ip_obj in ipaddress.ip_network(blacklisted_ip, strict=False):
                    logger.warning(f"IP {ip} 在黑名单中")
                    return False
            
            # 检查白名单
            for whitelisted_ip in SecurityHelper.IP_WHITELIST:
                if ip_obj in ipaddress.ip_network(whitelisted_ip, strict=False):
                    return True
            
            # 默认允许
            return True
            
        except ValueError:
            logger.warning(f"无效的IP地址: {ip}")
            return False
    
    @staticmethod
    def generate_request_id() -> str:
        """生成请求ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4)
        return f"{timestamp}_{random_part}"
    
    @staticmethod
    def mask_sensitive_data(data: Any, mask_fields: List[str] = None) -> Any:
        """屏蔽敏感数据"""
        if mask_fields is None:
            mask_fields = ['password', 'token', 'secret', 'key', 'auth', 'credit_card']
        
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in mask_fields):
                    masked_data[key] = "***"
                else:
                    masked_data[key] = SecurityHelper.mask_sensitive_data(value, mask_fields)
            return masked_data
        elif isinstance(data, list):
            return [SecurityHelper.mask_sensitive_data(item, mask_fields) for item in data]
        else:
            return data
    
    @staticmethod
    def validate_request_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """验证请求头"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查User-Agent
        user_agent = headers.get('user-agent', '')
        if not user_agent:
            validation_result["warnings"].append("缺少User-Agent头")
        
        # 检查Content-Type
        content_type = headers.get('content-type', '')
        if content_type and 'application/json' not in content_type:
            validation_result["warnings"].append("建议使用application/json内容类型")
        
        # 检查可疑头
        suspicious_headers = [
            'x-forwarded-for',
            'x-real-ip',
            'x-forwarded-host'
        ]
        
        for header in suspicious_headers:
            if header in headers:
                validation_result["warnings"].append(f"检测到可疑头: {header}")
        
        return validation_result
    
    @staticmethod
    def rate_limit_key(identifier: str, window_type: str = "minute") -> str:
        """生成限流键"""
        timestamp = datetime.now()
        
        if window_type == "minute":
            time_key = timestamp.strftime("%Y%m%d%H%M")
        elif window_type == "hour":
            time_key = timestamp.strftime("%Y%m%d%H")
        elif window_type == "day":
            time_key = timestamp.strftime("%Y%m%d")
        else:
            time_key = timestamp.strftime("%Y%m%d%H%M")
        
        return f"rate_limit:{identifier}:{time_key}"
    
    @staticmethod
    def is_valid_jwt_token(token: str) -> bool:
        """验证JWT令牌格式"""
        if not token:
            return False
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # 检查各部分是否为有效的Base64
            import base64
            
            for part in parts:
                # 添加填充如果需要
                padding = len(part) % 4
                if padding:
                    part += '=' * (4 - padding)
                
                base64.b64decode(part)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract_client_info(request) -> Dict[str, Any]:
        """提取客户端信息"""
        client_info = {
            "ip": getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown',
            "user_agent": request.headers.get('user-agent', 'unknown'),
            "referer": request.headers.get('referer', 'unknown'),
            "accept_language": request.headers.get('accept-language', 'unknown'),
            "accept_encoding": request.headers.get('accept-encoding', 'unknown'),
        }
        
        # 提取X-Forwarded-For
        x_forwarded_for = request.headers.get('x-forwarded-for')
        if x_forwarded_for:
            client_info["forwarded_for"] = x_forwarded_for.split(',')[0].strip()
        
        return client_info