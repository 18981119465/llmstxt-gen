"""
配置系统数据模型和验证规则
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re


class EnvironmentType(str, Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StorageType(str, Enum):
    """存储类型枚举"""
    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class SystemConfig(BaseModel):
    """系统配置"""
    name: str = Field(..., description="系统名称")
    version: str = Field(..., description="系统版本")
    debug: bool = Field(False, description="调试模式")
    env: EnvironmentType = Field(EnvironmentType.DEVELOPMENT, description="环境类型")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = Field(..., description="数据库主机")
    port: int = Field(5432, description="数据库端口")
    name: str = Field(..., description="数据库名称")
    user: str = Field(..., description="数据库用户")
    password: str = Field(..., description="数据库密码")
    pool_size: int = Field(10, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(20, ge=0, le=50, description="最大溢出连接数")
    pool_timeout: int = Field(30, ge=1, le=300, description="连接池超时时间")
    pool_recycle: int = Field(3600, ge=300, description="连接池回收时间")


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = Field(..., description="Redis主机")
    port: int = Field(6379, description="Redis端口")
    db: int = Field(0, ge=0, le=15, description="Redis数据库")
    password: str = Field("", description="Redis密码")
    max_connections: int = Field(10, ge=1, le=100, description="最大连接数")


class ApiConfig(BaseModel):
    """API配置"""
    host: str = Field("0.0.0.0", description="API主机")
    port: int = Field(8000, ge=1, le=65535, description="API端口")
    workers: int = Field(4, ge=1, le=32, description="工作进程数")
    reload: bool = Field(False, description="是否重载")
    cors_origins: List[str] = Field(["*"], description="CORS允许的源")
    cors_methods: List[str] = Field(["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="CORS允许的方法")
    cors_headers: List[str] = Field(["*"], description="CORS允许的头部")


class AIServiceConfig(BaseModel):
    """AI服务配置"""
    enabled: bool = Field(True, description="是否启用")
    model: str = Field("gpt-3.5-turbo", description="AI模型")
    max_tokens: int = Field(1000, ge=1, le=8000, description="最大令牌数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    timeout: int = Field(30, ge=1, le=300, description="超时时间")
    retry_attempts: int = Field(3, ge=0, le=10, description="重试次数")


class DocumentProcessorConfig(BaseModel):
    """文档处理服务配置"""
    enabled: bool = Field(True, description="是否启用")
    max_file_size: int = Field(10485760, ge=1, description="最大文件大小(字节)")
    supported_formats: List[str] = Field(["txt", "md", "pdf", "docx"], description="支持的文件格式")
    processing_timeout: int = Field(300, ge=1, le=3600, description="处理超时时间")
    max_concurrent_processes: int = Field(3, ge=1, le=20, description="最大并发处理数")


class WebCrawlerConfig(BaseModel):
    """网站爬取服务配置"""
    enabled: bool = Field(True, description="是否启用")
    max_pages: int = Field(100, ge=1, le=10000, description="最大页面数")
    delay: int = Field(1, ge=0, le=60, description="请求延迟(秒)")
    timeout: int = Field(30, ge=1, le=300, description="超时时间")
    user_agent: str = Field("llmstxt-gen/1.0.0", description="用户代理")
    follow_redirects: bool = Field(True, description="是否跟随重定向")
    max_concurrent_crawls: int = Field(1, ge=1, le=20, description="最大并发爬取数")
    respect_robots_txt: bool = Field(True, description="是否遵守robots.txt")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: LogLevel = Field(LogLevel.INFO, description="日志级别")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    file: str = Field("logs/app.log", description="日志文件路径")
    max_file_size: int = Field(10485760, ge=1, description="最大文件大小(字节)")
    backup_count: int = Field(5, ge=1, le=100, description="备份文件数量")
    rotation: str = Field("midnight", description="日志轮转策略")


class MonitoringConfig(BaseModel):
    """监控配置"""
    enabled: bool = Field(True, description="是否启用")
    metrics_port: int = Field(9090, ge=1, le=65535, description="指标端口")
    health_check_interval: int = Field(30, ge=1, le=300, description="健康检查间隔")
    performance_tracking: bool = Field(True, description="是否启用性能跟踪")


class SecurityConfig(BaseModel):
    """安全配置"""
    secret_key: str = Field(..., description="密钥")
    jwt_secret: str = Field(..., description="JWT密钥")
    jwt_algorithm: str = Field("HS256", description="JWT算法")
    jwt_expiration: int = Field(3600, ge=300, le=86400, description="JWT过期时间")
    bcrypt_rounds: int = Field(12, ge=4, le=16, description="bcrypt轮数")


class StorageConfig(BaseModel):
    """存储配置"""
    type: StorageType = Field(StorageType.LOCAL, description="存储类型")
    local_path: str = Field("data/storage", description="本地存储路径")
    max_storage_size: int = Field(1073741824, ge=1, description="最大存储大小(字节)")
    allowed_extensions: List[str] = Field(["txt", "md", "pdf", "docx", "png", "jpg", "jpeg"], description="允许的文件扩展名")


class AppConfig(BaseModel):
    """应用配置"""
    system: SystemConfig
    database: DatabaseConfig
    redis: RedisConfig
    api: ApiConfig
    ai_service: AIServiceConfig
    document_processor: DocumentProcessorConfig
    web_crawler: WebCrawlerConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    security: SecurityConfig
    storage: StorageConfig

    @field_validator('system')
    def validate_system_config(cls, v):
        """验证系统配置"""
        if not v.name:
            raise ValueError("系统名称不能为空")
        if not re.match(r'^\d+\.\d+\.\d+$', v.version):
            raise ValueError("版本号格式不正确，应为 x.y.z")
        return v

    @field_validator('database')
    def validate_database_config(cls, v):
        """验证数据库配置"""
        if not v.host:
            raise ValueError("数据库主机不能为空")
        if not v.name:
            raise ValueError("数据库名称不能为空")
        if not v.user:
            raise ValueError("数据库用户不能为空")
        return v

    @field_validator('security')
    def validate_security_config(cls, v):
        """验证安全配置"""
        if len(v.secret_key) < 32:
            raise ValueError("密钥长度不能少于32位")
        if len(v.jwt_secret) < 32:
            raise ValueError("JWT密钥长度不能少于32位")
        return v

    @field_validator('storage')
    def validate_storage_config(cls, v):
        """验证存储配置"""
        if v.type == StorageType.LOCAL and not v.local_path:
            raise ValueError("本地存储路径不能为空")
        return v


class ConfigTemplate(BaseModel):
    """配置模板"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    config: Dict[str, Any] = Field(..., description="配置内容")
    extends: Optional[str] = Field(None, description="继承的模板")
    environment: EnvironmentType = Field(EnvironmentType.DEVELOPMENT, description="适用环境")


class ConfigPreset(BaseModel):
    """配置预设"""
    name: str = Field(..., description="预设名称")
    description: str = Field(..., description="预设描述")
    config: Dict[str, Any] = Field(..., description="配置内容")
    extends: Optional[str] = Field(None, description="继承的配置")
    use_case: str = Field(..., description="使用场景")


class ConfigHistory(BaseModel):
    """配置历史"""
    id: str = Field(..., description="历史ID")
    config_id: str = Field(..., description="配置ID")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    version: int = Field(..., description="版本号")
    changed_by: str = Field(..., description="修改人")
    change_reason: str = Field(..., description="修改原因")
    created_at: str = Field(..., description="创建时间")


class ConfigValidationResult(BaseModel):
    """配置验证结果"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    config: Optional[Dict[str, Any]] = Field(None, description="配置内容")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    service_name: str = Field(..., description="服务名称")
    config_key: Optional[str] = Field(None, description="配置键")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    reason: str = Field(..., description="更新原因")


class ConfigReloadRequest(BaseModel):
    """配置重载请求"""
    service_name: Optional[str] = Field(None, description="服务名称")
    force: bool = Field(False, description="是否强制重载")


class ConfigRollbackRequest(BaseModel):
    """配置回滚请求"""
    config_id: str = Field(..., description="配置ID")
    version: int = Field(..., description="目标版本")
    reason: str = Field(..., description="回滚原因")