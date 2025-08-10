"""
FastAPI应用核心模块
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uuid
from typing import Optional, Dict, Any
import logging

from .exceptions import APIException, http_exception_handler, validation_exception_handler
from .middleware import RequestIDMiddleware, TimingMiddleware, LoggingMiddleware
from .dependencies import get_config_manager, get_logger
from ..schemas.response import StandardResponse, ErrorResponse

logger = logging.getLogger(__name__)


class APIFramework:
    """API框架核心类"""
    
    def __init__(self, 
                 title: str = "llms.txt-gen API",
                 description: str = "API for llms.txt generation service",
                 version: str = "1.0.0",
                 debug: bool = False):
        self.title = title
        self.description = description
        self.version = version
        self.debug = debug
        self.app = None
        self.config_manager = None
        self.logger = None
        
    def create_app(self) -> FastAPI:
        """创建FastAPI应用实例"""
        self.app = FastAPI(
            title=self.title,
            description=self.description,
            version=self.version,
            debug=self.debug,
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json"
        )
        
        # 注册中间件
        self._register_middleware()
        
        # 注册异常处理器
        self._register_exception_handlers()
        
        # 注册基础路由
        self._register_base_routes()
        
        logger.info("FastAPI应用创建成功")
        return self.app
    
    def _register_middleware(self):
        """注册中间件"""
        # 请求ID中间件
        self.app.add_middleware(RequestIDMiddleware)
        
        # 计时中间件
        self.app.add_middleware(TimingMiddleware)
        
        # 日志中间件
        self.app.add_middleware(LoggingMiddleware)
        
        # 可信主机中间件
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # 在生产环境中应该限制
        )
        
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 在生产环境中应该限制
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"]
        )
    
    def _register_exception_handlers(self):
        """注册异常处理器"""
        self.app.add_exception_handler(APIException, http_exception_handler)
        self.app.add_exception_handler(RequestValidationError, validation_exception_handler)
        self.app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        self.app.add_exception_handler(Exception, self._general_exception_handler)
    
    def _register_base_routes(self):
        """注册基础路由"""
        
        @self.app.get("/")
        async def root() -> StandardResponse:
            """根路径"""
            return StandardResponse(
                success=True,
                data={
                    "service": self.title,
                    "version": self.version,
                    "status": "running"
                },
                message="API服务正在运行"
            )
        
        @self.app.get("/health")
        async def health_check() -> StandardResponse:
            """健康检查"""
            health_status = {
                "service": self.title,
                "version": self.version,
                "status": "healthy",
                "timestamp": time.time()
            }
            
            # 检查配置管理器
            if self.config_manager:
                health_status["config_manager"] = "connected"
            else:
                health_status["config_manager"] = "disconnected"
            
            return StandardResponse(
                success=True,
                data=health_status,
                message="健康检查通过"
            )
    
    def _general_exception_handler(self, request: Request, exc: Exception) -> JSONResponse:
        """通用异常处理器"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            f"未处理的异常: {exc}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                error="INTERNAL_SERVER_ERROR",
                message="服务器内部错误",
                request_id=request_id
            ).dict()
        )
    
    def include_router(self, router, **kwargs):
        """包含路由器"""
        if self.app:
            self.app.include_router(router, **kwargs)
    
    def set_config_manager(self, config_manager):
        """设置配置管理器"""
        self.config_manager = config_manager
    
    def set_logger(self, logger):
        """设置日志记录器"""
        self.logger = logger


# 全局API框架实例
api_framework = APIFramework()


def get_app() -> FastAPI:
    """获取FastAPI应用实例"""
    return api_framework.create_app()


def get_api_framework() -> APIFramework:
    """获取API框架实例"""
    return api_framework