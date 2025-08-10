"""
数据库连接和配置管理
"""

import os
from typing import Optional, Generator, Dict, Any
from contextlib import contextmanager
import logging
from urllib.parse import urlparse

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:password@localhost:5432/llms_txt_gen"
        )
        self.async_database_url = self._convert_to_async_url(self.database_url)
        
        # 连接池配置
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
        # 连接配置
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        self.command_timeout = int(os.getenv("DB_COMMAND_TIMEOUT", "30"))
        
        # SSL配置
        self.ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
        self.ssl_root_cert = os.getenv("DB_SSL_ROOT_CERT")
        self.ssl_cert = os.getenv("DB_SSL_CERT")
        self.ssl_key = os.getenv("DB_SSL_KEY")
        
        # 调试配置
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("DB_ECHO_POOL", "false").lower() == "true"
        
    def _convert_to_async_url(self, url: str) -> str:
        """将同步URL转换为异步URL"""
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    
    def get_sync_engine_kwargs(self) -> Dict[str, Any]:
        """获取同步引擎参数"""
        kwargs = {
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
            "poolclass": QueuePool,
        }
        
        # 添加连接参数
        connect_args = {}
        
        # SSL配置
        if self.ssl_mode and self.ssl_mode != "disable":
            connect_args["sslmode"] = self.ssl_mode
            if self.ssl_root_cert:
                connect_args["sslrootcert"] = self.ssl_root_cert
            if self.ssl_cert:
                connect_args["sslcert"] = self.ssl_cert
            if self.ssl_key:
                connect_args["sslkey"] = self.ssl_key
        
        # 超时配置
        connect_args["connect_timeout"] = self.connect_timeout
        
        if connect_args:
            kwargs["connect_args"] = connect_args
            
        return kwargs
    
    def get_async_engine_kwargs(self) -> Dict[str, Any]:
        """获取异步引擎参数"""
        kwargs = self.get_sync_engine_kwargs()
        
        # 异步特定的配置
        kwargs["future"] = True
        
        return kwargs


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        
    @property
    def engine(self):
        """获取同步引擎"""
        if self._engine is None:
            self._engine = create_engine(
                self.config.database_url,
                **self.config.get_sync_engine_kwargs()
            )
        return self._engine
    
    @property
    def async_engine(self):
        """获取异步引擎"""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.config.async_database_url,
                **self.config.get_async_engine_kwargs()
            )
        return self._async_engine
    
    @property
    def session_factory(self):
        """获取同步会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                autoflush=False
            )
        return self._session_factory
    
    @property
    def async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                expire_on_commit=False,
                autoflush=False,
                class_=AsyncSession
            )
        return self._async_session_factory
    
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_session_context(self) -> Session:
        """获取数据库会话上下文"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    async def get_async_session(self) -> AsyncSession:
        """获取异步数据库会话"""
        return self.async_session_factory()
    
    async def get_async_session_context(self) -> AsyncSession:
        """获取异步数据库会话上下文"""
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()
    
    def create_tables(self):
        """创建数据库表"""
        try:
            from ..models.base import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除数据库表"""
        try:
            from ..models.base import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.get_session_context() as session:
                session.execute("SELECT 1")
            logger.info("数据库连接正常")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    async def check_async_connection(self) -> bool:
        """检查异步数据库连接"""
        try:
            async with self.get_async_session() as session:
                await session.execute("SELECT 1")
            logger.info("异步数据库连接正常")
            return True
        except Exception as e:
            logger.error(f"异步数据库连接失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with self.get_session_context() as session:
                # 获取数据库版本
                result = session.execute("SELECT version()")
                version = result.scalar()
                
                # 获取数据库大小
                result = session.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                size = result.scalar()
                
                # 获取连接数
                result = session.execute("SELECT count(*) FROM pg_stat_activity")
                connections = result.scalar()
                
                return {
                    "version": version,
                    "size": size,
                    "connections": connections,
                    "url": self.config.database_url,
                    "pool_size": self.config.pool_size,
                    "max_overflow": self.config.max_overflow,
                    "pool_timeout": self.config.pool_timeout,
                    "pool_recycle": self.config.pool_recycle,
                }
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {"error": str(e)}
    
    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        if self._async_engine:
            self._async_engine.dispose()
            self._async_engine = None
        logger.info("数据库连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 便捷函数
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的便捷函数"""
    return db_manager.get_session()


def get_db_session_context() -> Session:
    """获取数据库会话上下文的便捷函数"""
    return db_manager.get_session_context()


async def get_async_db_session() -> AsyncSession:
    """获取异步数据库会话的便捷函数"""
    return await db_manager.get_async_session()


def get_async_db_session_context() -> AsyncSession:
    """获取异步数据库会话上下文的便捷函数"""
    return db_manager.get_async_session_context()


def check_db_connection() -> bool:
    """检查数据库连接的便捷函数"""
    return db_manager.check_connection()


async def check_async_db_connection() -> bool:
    """检查异步数据库连接的便捷函数"""
    return await db_manager.check_async_connection()


def get_db_info() -> Dict[str, Any]:
    """获取数据库信息的便捷函数"""
    return db_manager.get_database_info()


def close_db_connections():
    """关闭数据库连接的便捷函数"""
    db_manager.close()