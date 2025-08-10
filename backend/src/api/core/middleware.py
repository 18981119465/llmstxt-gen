"""
API框架中间件模块
"""

import time
import uuid
import json
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 在响应头中添加请求ID
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """请求计时中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        # 计算请求处理时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录慢请求
        if process_time > 1.0:  # 超过1秒的请求
            logger.warning(
                f"慢请求: {request.method} {request.url.path} - {process_time:.3f}s",
                extra={
                    "request_id": getattr(request.state, 'request_id', 'unknown'),
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time
                }
            )
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 记录请求开始
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else "unknown"
            }
        )
        
        try:
            response = await call_next(request)
            
            # 记录请求完成
            logger.info(
                f"请求完成: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "process_time": response.headers.get("X-Process-Time", "unknown")
                }
            )
            
            return response
            
        except Exception as e:
            # 记录请求异常
            logger.error(
                f"请求异常: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头部中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头部
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """请求限流中间件"""
    
    def __init__(self, app, rate_limit: int = 100, time_window: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit  # 请求数量限制
        self.time_window = time_window  # 时间窗口（秒）
        self.requests: Dict[str, list] = {}  # 存储请求时间戳
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期的请求记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.time_window
            ]
        else:
            self.requests[client_ip] = []
        
        # 检查是否超过限流
        if len(self.requests[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "RATE_LIMIT_ERROR",
                    "message": "请求频率过高，请稍后再试",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )
        
        # 记录当前请求
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)


class RequestBodyMiddleware(BaseHTTPMiddleware):
    """请求体中间件 - 用于记录和验证请求体"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 如果是JSON请求，记录请求体
        if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.body()
                if body:
                    body_data = json.loads(body.decode())
                    # 只记录非敏感信息
                    safe_body = self._sanitize_body(body_data)
                    
                    logger.debug(
                        f"请求体: {request.method} {request.url.path}",
                        extra={
                            "request_id": request_id,
                            "path": request.url.path,
                            "method": request.method,
                            "body": safe_body
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"无法解析请求体: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
        
        return await call_next(request)
    
    def _sanitize_body(self, body: Any) -> Dict[str, Any]:
        """清理请求体中的敏感信息"""
        if isinstance(body, dict):
            sanitized = {}
            sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
            
            for key, value in body.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = "***"
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return body


class ResponseBodyMiddleware(BaseHTTPMiddleware):
    """响应体中间件 - 用于记录响应数据"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        response = await call_next(request)
        
        # 如果是JSON响应，记录响应体
        if isinstance(response, JSONResponse):
            try:
                body_data = json.loads(response.body.decode())
                # 只记录非敏感信息和部分响应
                safe_body = self._sanitize_response(body_data)
                
                logger.debug(
                    f"响应体: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method,
                        "response": safe_body
                    }
                )
            except Exception as e:
                logger.warning(
                    f"无法解析响应体: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
        
        return response
    
    def _sanitize_response(self, response: Any) -> Dict[str, Any]:
        """清理响应中的敏感信息"""
        if isinstance(response, dict):
            sanitized = {}
            sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
            
            for key, value in response.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = "***"
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return response