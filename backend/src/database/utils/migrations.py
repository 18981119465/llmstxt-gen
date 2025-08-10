"""
数据库迁移工具
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self, database_url: str = None, alembic_ini_path: str = None):
        """初始化迁移管理器"""
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/llms_txt_gen"
        )
        
        # 设置Alembic配置文件路径
        self.alembic_ini_path = alembic_ini_path or "alembic.ini"
        
        # 创建Alembic配置
        self.alembic_cfg = Config(self.alembic_ini_path)
        
        # 设置数据库URL
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
        
        # 创建数据库引擎
        self.engine = create_engine(self.database_url)
        
    def create_migration(self, message: str, revision_id: str = None) -> Dict[str, Any]:
        """创建新的迁移"""
        try:
            # 构建迁移命令参数
            kwargs = {
                "message": message,
                "autogenerate": True
            }
            
            if revision_id:
                kwargs["rev_id"] = revision_id
            
            # 执行迁移创建命令
            command.revision(self.alembic_cfg, **kwargs)
            
            logger.info(f"迁移创建成功: {message}")
            
            return {
                "status": "success",
                "message": message,
                "revision_id": revision_id,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"迁移创建失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "message": message,
                "error": error_msg,
                "created_at": datetime.now().isoformat()
            }
    
    def upgrade(self, revision: str = "head") -> Dict[str, Any]:
        """升级数据库到指定版本"""
        try:
            # 执行升级命令
            command.upgrade(self.alembic_cfg, revision)
            
            logger.info(f"数据库升级成功: {revision}")
            
            # 获取当前版本
            current_version = self.get_current_version()
            
            return {
                "status": "success",
                "revision": revision,
                "current_version": current_version,
                "upgraded_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据库升级失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "revision": revision,
                "error": error_msg,
                "upgraded_at": datetime.now().isoformat()
            }
    
    def downgrade(self, revision: str = "-1") -> Dict[str, Any]:
        """降级数据库到指定版本"""
        try:
            # 执行降级命令
            command.downgrade(self.alembic_cfg, revision)
            
            logger.info(f"数据库降级成功: {revision}")
            
            # 获取当前版本
            current_version = self.get_current_version()
            
            return {
                "status": "success",
                "revision": revision,
                "current_version": current_version,
                "downgraded_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据库降级失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "revision": revision,
                "error": error_msg,
                "downgraded_at": datetime.now().isoformat()
            }
    
    def get_current_version(self) -> str:
        """获取当前数据库版本"""
        try:
            # 执行当前命令
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                
            return version or "None"
            
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return "None"
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史"""
        try:
            # 获取迁移历史
            history = command.history(self.alembic_cfg, verbose=True)
            
            # 解析历史信息
            migrations = []
            for line in history.split('\n'):
                if line.strip() and '->' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        revision = parts[0]
                        migrations.append({
                            "revision": revision,
                            "message": " ".join(parts[2:]),
                            "line": line.strip()
                        })
            
            return migrations
            
        except Exception as e:
            logger.error(f"获取迁移历史失败: {e}")
            return []
    
    def get_heads(self) -> List[str]:
        """获取所有头部版本"""
        try:
            # 获取头部版本
            heads = command.heads(self.alembic_cfg, verbose=True)
            
            # 解析头部版本
            head_list = []
            for line in heads.split('\n'):
                if line.strip():
                    head_list.append(line.strip())
            
            return head_list
            
        except Exception as e:
            logger.error(f"获取头部版本失败: {e}")
            return []
    
    def check_database(self) -> Dict[str, Any]:
        """检查数据库状态"""
        try:
            # 检查数据库连接
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.scalar()
            
            # 获取当前版本
            current_version = self.get_current_version()
            
            # 获取头部版本
            heads = self.get_heads()
            
            # 检查是否需要升级
            needs_upgrade = current_version not in heads and current_version != "None"
            
            return {
                "status": "healthy",
                "connection": "ok",
                "current_version": current_version,
                "heads": heads,
                "needs_upgrade": needs_upgrade,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据库检查失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "error",
                "connection": "failed",
                "error": error_msg,
                "checked_at": datetime.now().isoformat()
            }
    
    def init_database(self) -> Dict[str, Any]:
        """初始化数据库"""
        try:
            # 创建Alembic版本表
            with self.engine.connect() as connection:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    )
                """))
                
                # 检查是否已有版本
                result = connection.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                
                if not version:
                    # 插入初始版本
                    connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('None')"))
                    logger.info("数据库初始化完成")
                else:
                    logger.info(f"数据库已初始化，当前版本: {version}")
            
            return {
                "status": "success",
                "initialized_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据库初始化失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "error": error_msg,
                "initialized_at": datetime.now().isoformat()
            }
    
    def stamp(self, revision: str = "head") -> Dict[str, Any]:
        """标记数据库版本"""
        try:
            # 执行标记命令
            command.stamp(self.alembic_cfg, revision)
            
            logger.info(f"数据库版本标记成功: {revision}")
            
            # 获取当前版本
            current_version = self.get_current_version()
            
            return {
                "status": "success",
                "revision": revision,
                "current_version": current_version,
                "stamped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"数据库版本标记失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "revision": revision,
                "error": error_msg,
                "stamped_at": datetime.now().isoformat()
            }
    
    def create_alembic_config(self, config_path: str = None) -> Dict[str, Any]:
        """创建Alembic配置文件"""
        try:
            config_path = config_path or self.alembic_ini_path
            
            # 配置文件内容
            config_content = f"""[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = {self.database_url}

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
"""
            
            # 写入配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logger.info(f"Alembic配置文件创建成功: {config_path}")
            
            return {
                "status": "success",
                "config_path": config_path,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Alembic配置文件创建失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "error": error_msg,
                "created_at": datetime.now().isoformat()
            }
    
    def create_alembic_directory(self, directory: str = "alembic") -> Dict[str, Any]:
        """创建Alembic目录结构"""
        try:
            # 创建目录
            alembic_dir = Path(directory)
            alembic_dir.mkdir(exist_ok=True)
            
            # 创建版本目录
            versions_dir = alembic_dir / "versions"
            versions_dir.mkdir(exist_ok=True)
            
            # 创建env.py文件
            env_content = f"""from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from src.database.models import Base
# target_metadata = Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    context.configure(
        url={repr(self.database_url)},
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
            
            with open(alembic_dir / "env.py", 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            logger.info(f"Alembic目录结构创建成功: {directory}")
            
            return {
                "status": "success",
                "directory": directory,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Alembic目录结构创建失败: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "failed",
                "error": error_msg,
                "created_at": datetime.now().isoformat()
            }


# 全局迁移管理器实例
migration_manager = MigrationManager()