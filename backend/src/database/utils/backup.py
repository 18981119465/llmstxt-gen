"""
数据库备份工具
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import subprocess
import shutil
import gzip
import hashlib

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """数据库备份类"""
    
    def __init__(self, config=None):
        """初始化数据库备份"""
        self.config = config or {}
        self.backup_dir = Path(self.config.get('backup_dir', 'backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, backup_type='full', backup_name=None) -> Dict[str, Any]:
        """创建数据库备份"""
        try:
            backup_name = backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            # 构建备份命令
            db_url = self.config.get('database_url', 'postgresql://postgres:password@localhost:5432/llms_txt_gen')
            
            if backup_type == 'full':
                cmd = [
                    'pg_dump',
                    db_url,
                    '--file', str(backup_file),
                    '--verbose'
                ]
            elif backup_type == 'schema':
                cmd = [
                    'pg_dump',
                    db_url,
                    '--schema-only',
                    '--file', str(backup_file),
                    '--verbose'
                ]
            else:
                raise ValueError(f"不支持的备份类型: {backup_type}")
            
            # 执行备份
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 计算文件哈希
                file_hash = self._calculate_file_hash(backup_file)
                file_size = backup_file.stat().st_size
                
                # 压缩备份文件
                compressed_file = self._compress_file(backup_file)
                
                backup_info = {
                    'backup_name': backup_name,
                    'backup_type': backup_type,
                    'file_path': str(compressed_file),
                    'file_size': file_size,
                    'compressed_size': compressed_file.stat().st_size,
                    'file_hash': file_hash,
                    'created_at': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                logger.info(f"数据库备份创建成功: {backup_name}")
                return backup_info
            else:
                error_msg = f"备份失败: {result.stderr}"
                logger.error(error_msg)
                return {
                    'backup_name': backup_name,
                    'backup_type': backup_type,
                    'status': 'failed',
                    'error_message': error_msg,
                    'created_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = f"备份创建异常: {str(e)}"
            logger.error(error_msg)
            return {
                'backup_name': backup_name or 'unknown',
                'backup_type': backup_type,
                'status': 'failed',
                'error_message': error_msg,
                'created_at': datetime.now().isoformat()
            }
    
    def restore_backup(self, backup_file: str) -> Dict[str, Any]:
        """恢复数据库备份"""
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            # 解压文件（如果是压缩文件）
            if backup_path.suffix == '.gz':
                backup_path = self._decompress_file(backup_path)
            
            db_url = self.config.get('database_url', 'postgresql://postgres:password@localhost:5432/llms_txt_gen')
            
            # 构建恢复命令
            cmd = [
                'psql',
                db_url,
                '--file', str(backup_path),
                '--verbose'
            ]
            
            # 执行恢复
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"数据库恢复成功: {backup_file}")
                return {
                    'backup_file': backup_file,
                    'status': 'completed',
                    'restored_at': datetime.now().isoformat()
                }
            else:
                error_msg = f"恢复失败: {result.stderr}"
                logger.error(error_msg)
                return {
                    'backup_file': backup_file,
                    'status': 'failed',
                    'error_message': error_msg,
                    'restored_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = f"备份恢复异常: {str(e)}"
            logger.error(error_msg)
            return {
                'backup_file': backup_file,
                'status': 'failed',
                'error_message': error_msg,
                'restored_at': datetime.now().isoformat()
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob('*.sql.gz'):
                stat = backup_file.stat()
                backups.append({
                    'file_name': backup_file.name,
                    'file_path': str(backup_file),
                    'file_size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
        
        return backups
    
    def delete_backup(self, backup_file: str) -> Dict[str, Any]:
        """删除备份"""
        try:
            backup_path = Path(backup_file)
            
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"备份删除成功: {backup_file}")
                return {
                    'backup_file': backup_file,
                    'status': 'completed',
                    'deleted_at': datetime.now().isoformat()
                }
            else:
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
                
        except Exception as e:
            error_msg = f"备份删除异常: {str(e)}"
            logger.error(error_msg)
            return {
                'backup_file': backup_file,
                'status': 'failed',
                'error_message': error_msg,
                'deleted_at': datetime.now().isoformat()
            }
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """清理旧备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_backups = []
            
            for backup_file in self.backup_dir.glob('*.sql.gz'):
                if datetime.fromtimestamp(backup_file.stat().st_ctime) < cutoff_date:
                    backup_file.unlink()
                    deleted_backups.append(backup_file.name)
            
            logger.info(f"清理了 {len(deleted_backups)} 个旧备份")
            
            return {
                'retention_days': retention_days,
                'deleted_count': len(deleted_backups),
                'deleted_backups': deleted_backups,
                'cleaned_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"清理备份异常: {str(e)}"
            logger.error(error_msg)
            return {
                'retention_days': retention_days,
                'deleted_count': 0,
                'error_message': error_msg,
                'cleaned_at': datetime.now().isoformat()
            }
    
    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """验证备份完整性"""
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            # 解压文件（如果是压缩文件）
            if backup_path.suffix == '.gz':
                backup_path = self._decompress_file(backup_path)
            
            # 检查文件是否为空
            if backup_path.stat().st_size == 0:
                raise ValueError("备份文件为空")
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(backup_path)
            
            # 检查SQL文件的基本语法
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 基本检查
                if not content.strip():
                    raise ValueError("备份文件内容为空")
                
                if 'CREATE TABLE' not in content and 'INSERT INTO' not in content:
                    raise ValueError("备份文件格式不正确")
            
            logger.info(f"备份验证成功: {backup_file}")
            
            return {
                'backup_file': backup_file,
                'file_hash': file_hash,
                'file_size': backup_path.stat().st_size,
                'status': 'verified',
                'verified_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"备份验证异常: {str(e)}"
            logger.error(error_msg)
            return {
                'backup_file': backup_file,
                'status': 'failed',
                'error_message': error_msg,
                'verified_at': datetime.now().isoformat()
            }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _compress_file(self, file_path: Path) -> Path:
        """压缩文件"""
        compressed_path = file_path.with_suffix('.sql.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除原文件
        file_path.unlink()
        
        return compressed_path
    
    def _decompress_file(self, file_path: Path) -> Path:
        """解压文件"""
        decompressed_path = file_path.with_suffix('')
        
        with gzip.open(file_path, 'rb') as f_in:
            with open(decompressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return decompressed_path


# 全局备份管理器实例
backup_manager = DatabaseBackup()