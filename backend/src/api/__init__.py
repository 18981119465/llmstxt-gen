"""
FastAPI应用主入口
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入API框架
from src.api.core import get_app, get_api_framework, APIException
from src.api.routers import system_router, auth_router
from src.api.schemas import create_success_response, create_error_response
from src.api.utils import SecurityHelper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def create_application() -> FastAPI:
    """创建FastAPI应用"""
    # 创建API框架实例
    api_framework = get_api_framework()
    app = get_app()
    
    # 配置应用信息
    app.title = "llms.txt-gen API"
    app.description = "API for llms.txt generation service"
    app.version = "1.0.0"
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )
    
    # 注册异常处理器
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        request_id = getattr(request.state, 'request_id', 'unknown')
        response_data = create_error_response(
            error=exc.error_code,
            message=exc.message,
            request_id=request_id,
            details=exc.details
        ).model_dump()
        
        return JSONResponse(
            status_code=exc.status_code,
            content=json.loads(json.dumps(response_data, cls=CustomJSONEncoder))
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 格式化验证错误
        validation_errors = []
        for error in exc.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        response_data = create_error_response(
            error="VALIDATION_ERROR",
            message="数据验证失败",
            request_id=request_id,
            details={"validation_errors": validation_errors}
        ).model_dump()
        
        return JSONResponse(
            status_code=422,
            content=json.loads(json.dumps(response_data, cls=CustomJSONEncoder))
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        error_code = "HTTP_ERROR"
        if exc.status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
        elif exc.status_code == 403:
            error_code = "AUTHORIZATION_ERROR"
        elif exc.status_code == 404:
            error_code = "RESOURCE_NOT_FOUND"
        elif exc.status_code == 422:
            error_code = "VALIDATION_ERROR"
        elif exc.status_code == 429:
            error_code = "RATE_LIMIT_ERROR"
        elif exc.status_code >= 500:
            error_code = "INTERNAL_SERVER_ERROR"
        
        response_data = create_error_response(
            error=error_code,
            message=str(exc.detail),
            request_id=request_id
        ).model_dump()
        
        return JSONResponse(
            status_code=exc.status_code,
            content=json.loads(json.dumps(response_data, cls=CustomJSONEncoder))
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            f"未处理的异常: {exc}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            },
            exc_info=True
        )
        
        response_data = create_error_response(
            error="INTERNAL_SERVER_ERROR",
            message="服务器内部错误",
            request_id=request_id
        ).model_dump()
        
        return JSONResponse(
            status_code=500,
            content=json.loads(json.dumps(response_data, cls=CustomJSONEncoder))
        )
    
    # 请求ID中间件
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = SecurityHelper.generate_request_id()
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    # 注册路由
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    
    # 根路径
    @app.get("/")
    async def root():
        return create_success_response(
            data={
                "service": "llms.txt-gen API",
                "version": "1.0.0",
                "status": "running",
                "docs": "/api/docs",
                "redoc": "/api/redoc"
            },
            message="API服务正在运行"
        )
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return create_success_response(
            data={
                "service": "llms.txt-gen API",
                "version": "1.0.0",
                "status": "healthy",
                "timestamp": "2025-01-07T10:00:00Z"
            },
            message="健康检查通过"
        )
    
    # API信息
    @app.get("/api/v1/info")
    async def api_info():
        return create_success_response(
            data={
                "name": "llms.txt-gen API",
                "version": "1.0.0",
                "description": "API for llms.txt generation service",
                "endpoints": {
                    "system": "/api/v1/system",
                    "docs": "/api/docs",
                    "redoc": "/api/redoc",
                    "openapi": "/api/openapi.json"
                }
            },
            message="API信息获取成功"
        )
    
    logger.info("FastAPI应用创建成功")
    return app


# 创建应用实例
app = create_application()


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("API服务启动中...")
    
    # 初始化服务
    try:
        # 这里可以添加其他服务的初始化
        logger.info("API服务启动成功")
    except Exception as e:
        logger.error(f"API服务启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("API服务关闭中...")
    
    # 清理资源
    try:
        # 这里可以添加资源的清理
        logger.info("API服务关闭成功")
    except Exception as e:
        logger.error(f"API服务关闭失败: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "True").lower() == "true",
        log_level="info"
    )