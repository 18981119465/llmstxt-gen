"""
配置回滚功能和版本管理机制
"""

import json
import shutil
import logging
import hashlib
import gzip
import base64
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from .loader import ConfigLoader, ConfigManager
from .exceptions import ConfigError
import os

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """版本状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    CORRUPTED = "corrupted"


class VersionType(Enum):
    """版本类型"""
    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULED = "scheduled"
    ROLLBACK = "rollback"
    MIGRATION = "migration"


@dataclass
class VersionMetadata:
    """版本元数据"""
    version_id: str
    config_hash: str
    file_size: int
    compressed_size: int
    status: VersionStatus
    version_type: VersionType
    tags: List[str]
    environment: str
    service_version: str
    checksum: str


class ConfigVersion:
    """配置版本"""
    
    def __init__(self, version: int, config: Dict[str, Any], timestamp: datetime, 
                 changed_by: str = "system", change_reason: str = "",
                 version_type: VersionType = VersionType.AUTO,
                 metadata: Optional[VersionMetadata] = None):
        self.version = version
        self.config = config
        self.timestamp = timestamp
        self.changed_by = changed_by
        self.change_reason = change_reason
        self.backup_path: Optional[Path] = None
        self.version_type = version_type
        self.metadata = metadata
        self.parent_version: Optional[int] = None
        self.child_versions: List[int] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "config": self.config,
            "timestamp": self.timestamp.isoformat(),
            "changed_by": self.changed_by,
            "change_reason": self.change_reason,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "version_type": self.version_type.value,
            "metadata": asdict(self.metadata) if self.metadata else None,
            "parent_version": self.parent_version,
            "child_versions": self.child_versions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigVersion':
        """从字典创建版本对象"""
        version = cls(
            version=data["version"],
            config=data["config"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            changed_by=data.get("changed_by", "system"),
            change_reason=data.get("change_reason", ""),
            version_type=VersionType(data.get("version_type", "auto"))
        )
        version.backup_path = Path(data["backup_path"]) if data.get("backup_path") else None
        if data.get("metadata"):
            version.metadata = VersionMetadata(**data["metadata"])
        version.parent_version = data.get("parent_version")
        version.child_versions = data.get("child_versions", [])
        return version


class ConfigRollbackManager:
    """配置回滚管理器"""
    
    def __init__(self, config_loader: ConfigLoader, backup_dir: str = "config/backups"):
        self.config_loader = config_loader
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.versions: Dict[str, List[ConfigVersion]] = {}  # config_id -> versions
        self.max_versions = 50  # 最大保留版本数
        self.auto_backup = True
        self.compression_enabled = True
        self.retention_days = 30
        self.version_index: Dict[str, ConfigVersion] = {}  # version_id -> version
        self.config_hashes: Dict[str, List[str]] = {}  # config_hash -> version_ids
        self._load_versions()
    
    def _load_versions(self):
        """加载版本信息"""
        try:
            version_file = self.backup_dir / "versions.json"
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                
                for config_id, versions in versions_data.items():
                    self.versions[config_id] = []
                    for version_data in versions:
                        version = ConfigVersion.from_dict(version_data)
                        self.versions[config_id].append(version)
                        
                        # 构建索引
                        version_id = self._generate_version_id(config_id, version.version)
                        self.version_index[version_id] = version
                        
                        # 构建哈希索引
                        if version.metadata:
                            config_hash = version.metadata.config_hash
                            if config_hash not in self.config_hashes:
                                self.config_hashes[config_hash] = []
                            self.config_hashes[config_hash].append(version_id)
                
                # 构建版本关系
                self._build_version_relationships()
                logger.info(f"加载了 {len(self.versions)} 个配置的版本信息")
        except Exception as e:
            logger.error(f"加载版本信息失败: {e}")
    
    def _save_versions(self):
        """保存版本信息"""
        try:
            version_file = self.backup_dir / "versions.json"
            versions_data = {}
            
            for config_id, versions in self.versions.items():
                versions_data[config_id] = [v.to_dict() for v in versions]
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, indent=2, ensure_ascii=False)
            
            logger.info("版本信息保存成功")
        except Exception as e:
            logger.error(f"保存版本信息失败: {e}")
    
    def _generate_version_id(self, config_id: str, version: int) -> str:
        """生成版本ID"""
        return f"{config_id}_v{version}"
    
    def _build_version_relationships(self):
        """构建版本关系"""
        for config_id, versions in self.versions.items():
            # 按版本号排序
            versions.sort(key=lambda v: v.version)
            
            # 建立父子关系
            for i in range(1, len(versions)):
                versions[i].parent_version = versions[i-1].version
                versions[i-1].child_versions.append(versions[i].version)
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        config_str = json.dumps(config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()
    
    def _compress_config(self, config: Dict[str, Any]) -> bytes:
        """压缩配置数据"""
        config_str = json.dumps(config, ensure_ascii=False)
        if self.compression_enabled:
            return gzip.compress(config_str.encode('utf-8'))
        return config_str.encode('utf-8')
    
    def _decompress_config(self, compressed_data: bytes) -> Dict[str, Any]:
        """解压缩配置数据"""
        if self.compression_enabled:
            config_str = gzip.decompress(compressed_data).decode('utf-8')
        else:
            config_str = compressed_data.decode('utf-8')
        return json.loads(config_str)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """计算校验和"""
        return hashlib.md5(data).hexdigest()
    
    def create_backup(self, config_id: str, config: Dict[str, Any], 
                    changed_by: str = "system", change_reason: str = "auto_backup",
                    version_type: VersionType = VersionType.AUTO,
                    tags: List[str] = None) -> ConfigVersion:
        """创建配置备份"""
        try:
            # 获取当前版本号
            current_versions = self.versions.get(config_id, [])
            next_version = len(current_versions) + 1
            
            # 计算配置哈希
            config_hash = self._calculate_config_hash(config)
            
            # 检查是否已存在相同配置的版本
            if config_hash in self.config_hashes:
                existing_versions = self.config_hashes[config_hash]
                for version_id in existing_versions:
                    existing_version = self.version_index.get(version_id)
                    if existing_version and existing_version.metadata:
                        existing_version.metadata.status = VersionStatus.ACTIVE
                        logger.info(f"配置哈希已存在，复用版本: {version_id}")
                        return existing_version
            
            # 压缩配置数据
            compressed_data = self._compress_config(config)
            checksum = self._calculate_checksum(compressed_data)
            
            # 创建版本元数据
            metadata = VersionMetadata(
                version_id=self._generate_version_id(config_id, next_version),
                config_hash=config_hash,
                file_size=len(json.dumps(config, ensure_ascii=False).encode('utf-8')),
                compressed_size=len(compressed_data),
                status=VersionStatus.ACTIVE,
                version_type=version_type,
                tags=tags or [],
                environment=os.getenv("ENVIRONMENT", "development"),
                service_version=os.getenv("APP_VERSION", "1.0.0"),
                checksum=checksum
            )
            
            # 创建版本对象
            version = ConfigVersion(
                version=next_version,
                config=config,
                timestamp=datetime.now(),
                changed_by=changed_by,
                change_reason=change_reason,
                version_type=version_type,
                metadata=metadata
            )
            
            # 创建备份文件
            backup_filename = f"{config_id}_v{next_version}_{int(datetime.now().timestamp())}.dat"
            backup_path = self.backup_dir / backup_filename
            
            with open(backup_path, 'wb') as f:
                f.write(compressed_data)
            
            version.backup_path = backup_path
            
            # 添加到版本列表
            current_versions.append(version)
            self.versions[config_id] = current_versions
            
            # 构建索引
            version_id = self._generate_version_id(config_id, next_version)
            self.version_index[version_id] = version
            self.config_hashes[config_hash] = self.config_hashes.get(config_hash, []) + [version_id]
            
            # 构建版本关系
            self._build_version_relationships()
            
            # 清理旧版本
            self._cleanup_old_versions(config_id)
            
            # 保存版本信息
            self._save_versions()
            
            logger.info(f"创建配置备份: {config_id} v{next_version}")
            return version
            
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
            raise ConfigError(f"创建配置备份失败: {e}")
    
    def rollback_to_version(self, config_id: str, target_version: int, 
                           changed_by: str = "system", change_reason: str = "rollback") -> Dict[str, Any]:
        """回滚到指定版本"""
        try:
            if config_id not in self.versions:
                raise ConfigError(f"配置 {config_id} 不存在")
            
            versions = self.versions[config_id]
            target_version_obj = None
            
            # 查找目标版本
            for version in versions:
                if version.version == target_version:
                    target_version_obj = version
                    break
            
            if not target_version_obj:
                raise ConfigError(f"版本 {target_version} 不存在")
            
            # 检查备份文件是否存在
            if not target_version_obj.backup_path or not target_version_obj.backup_path.exists():
                raise ConfigError(f"版本 {target_version} 的备份文件不存在")
            
            # 验证备份文件完整性
            if target_version_obj.metadata:
                with open(target_version_obj.backup_path, 'rb') as f:
                    compressed_data = f.read()
                
                checksum = self._calculate_checksum(compressed_data)
                if checksum != target_version_obj.metadata.checksum:
                    raise ConfigError(f"版本 {target_version} 的备份文件校验失败")
                
                # 解压配置
                backup_config = self._decompress_config(compressed_data)
            else:
                # 兼容旧格式
                with open(target_version_obj.backup_path, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
            
            # 创建当前版本的备份（用于记录回滚操作）
            current_config = self.config_loader.get_merged_config()
            self.create_backup(
                config_id,
                current_config,
                changed_by=changed_by,
                change_reason=f"回滚前备份: {change_reason}",
                version_type=VersionType.ROLLBACK,
                tags=[f"rollback_from:v{target_version}"]
            )
            
            # 恢复配置
            if config_id == "main":
                # 主配置，需要恢复到配置文件
                self._restore_main_config(backup_config)
            else:
                # 服务配置，只恢复到内存
                pass
            
            logger.info(f"配置 {config_id} 已回滚到版本 {target_version}")
            return backup_config
            
        except Exception as e:
            logger.error(f"配置回滚失败: {e}")
            raise ConfigError(f"配置回滚失败: {e}")
    
    def _restore_main_config(self, config: Dict[str, Any]):
        """恢复主配置文件"""
        try:
            # 恢复默认配置文件
            default_config_path = self.config_loader.config_dir / "default.yaml"
            if default_config_path.exists():
                shutil.copy2(default_config_path, default_config_path.with_suffix(".yaml.backup"))
            
            import yaml
            with open(default_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info("主配置文件恢复成功")
        except Exception as e:
            logger.error(f"恢复主配置文件失败: {e}")
            raise ConfigError(f"恢复主配置文件失败: {e}")
    
    def get_versions(self, config_id: str) -> List[ConfigVersion]:
        """获取配置的所有版本"""
        return self.versions.get(config_id, [])
    
    def get_latest_version(self, config_id: str) -> Optional[ConfigVersion]:
        """获取最新版本"""
        versions = self.versions.get(config_id, [])
        return versions[-1] if versions else None
    
    def get_version_info(self, config_id: str, version: int) -> Optional[ConfigVersion]:
        """获取指定版本信息"""
        versions = self.versions.get(config_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def get_version_details(self, config_id: str, version: int) -> Optional[Dict[str, Any]]:
        """获取版本详细信息"""
        version_obj = self.get_version_info(config_id, version)
        if not version_obj:
            return None
        
        details = {
            "version": version_obj.version,
            "timestamp": version_obj.timestamp.isoformat(),
            "changed_by": version_obj.changed_by,
            "change_reason": version_obj.change_reason,
            "version_type": version_obj.version_type.value,
            "parent_version": version_obj.parent_version,
            "child_versions": version_obj.child_versions,
            "backup_path": str(version_obj.backup_path) if version_obj.backup_path else None,
            "backup_exists": version_obj.backup_path.exists() if version_obj.backup_path else False,
        }
        
        if version_obj.metadata:
            details["metadata"] = asdict(version_obj.metadata)
        
        # 获取版本谱系
        lineage = self.get_version_lineage(config_id, version)
        details["lineage"] = {
            "ancestors": [v.version for v in lineage if v.version < version],
            "descendants": [v.version for v in lineage if v.version > version]
        }
        
        return details
    
    def _cleanup_old_versions(self, config_id: str):
        """清理旧版本"""
        if config_id not in self.versions:
            return
        
        versions = self.versions[config_id]
        if len(versions) > self.max_versions:
            # 删除最旧的版本
            versions_to_remove = versions[:-self.max_versions]
            
            for version in versions_to_remove:
                # 删除备份文件
                if version.backup_path and version.backup_path.exists():
                    version.backup_path.unlink()
            
            # 更新版本列表
            self.versions[config_id] = versions[-self.max_versions:]
    
    def delete_version(self, config_id: str, version: int) -> bool:
        """删除指定版本"""
        try:
            if config_id not in self.versions:
                return False
            
            versions = self.versions[config_id]
            version_to_delete = None
            
            for v in versions:
                if v.version == version:
                    version_to_delete = v
                    break
            
            if not version_to_delete:
                return False
            
            # 删除备份文件
            if version_to_delete.backup_path and version_to_delete.backup_path.exists():
                version_to_delete.backup_path.unlink()
            
            # 从版本列表中删除
            versions.remove(version_to_delete)
            
            # 重新编号版本
            for i, v in enumerate(versions):
                v.version = i + 1
            
            # 保存版本信息
            self._save_versions()
            
            logger.info(f"删除版本: {config_id} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"删除版本失败: {e}")
            return False
    
    def get_backup_info(self) -> Dict[str, Any]:
        """获取备份信息"""
        info = {
            "backup_dir": str(self.backup_dir),
            "total_configs": len(self.versions),
            "total_versions": sum(len(versions) for versions in self.versions.values()),
            "max_versions": self.max_versions,
            "auto_backup": self.auto_backup,
            "configs": {}
        }
        
        for config_id, versions in self.versions.items():
            info["configs"][config_id] = {
                "version_count": len(versions),
                "latest_version": versions[-1].version if versions else 0,
                "latest_timestamp": versions[-1].timestamp.isoformat() if versions else None,
                "total_backup_size": self._calculate_backup_size(versions)
            }
        
        return info
    
    def _calculate_backup_size(self, versions: List[ConfigVersion]) -> int:
        """计算备份文件总大小"""
        total_size = 0
        for version in versions:
            if version.backup_path and version.backup_path.exists():
                total_size += version.backup_path.stat().st_size
        return total_size
    
    def cleanup_backups(self, keep_versions: int = None):
        """清理备份文件"""
        if keep_versions is None:
            keep_versions = self.max_versions
        
        cleaned_count = 0
        
        for config_id, versions in self.versions.items():
            if len(versions) > keep_versions:
                versions_to_remove = versions[:-keep_versions]
                
                for version in versions_to_remove:
                    if version.backup_path and version.backup_path.exists():
                        version.backup_path.unlink()
                        cleaned_count += 1
                
                # 更新版本列表
                self.versions[config_id] = versions[-keep_versions:]
                
                # 重新编号版本
                for i, v in enumerate(self.versions[config_id]):
                    v.version = i + 1
        
        # 保存版本信息
        self._save_versions()
        
        logger.info(f"清理了 {cleaned_count} 个备份文件")
        return cleaned_count
    
    def auto_backup_config(self, config_id: str, config: Dict[str, Any], 
                         changed_by: str = "system", change_reason: str = "auto_backup"):
        """自动备份配置"""
        if self.auto_backup:
            return self.create_backup(config_id, config, changed_by, change_reason)
        return None
    
    # 高级版本管理功能
    
    def get_version_by_id(self, version_id: str) -> Optional[ConfigVersion]:
        """根据版本ID获取版本"""
        return self.version_index.get(version_id)
    
    def get_versions_by_hash(self, config_hash: str) -> List[ConfigVersion]:
        """根据配置哈希获取版本"""
        version_ids = self.config_hashes.get(config_hash, [])
        return [self.version_index[vid] for vid in version_ids if vid in self.version_index]
    
    def get_version_lineage(self, config_id: str, version: int) -> List[ConfigVersion]:
        """获取版本谱系（包括祖先和后代）"""
        lineage = []
        versions = self.versions.get(config_id, [])
        
        # 查找指定版本
        target_version = None
        for v in versions:
            if v.version == version:
                target_version = v
                break
        
        if not target_version:
            return lineage
        
        # 收集祖先版本
        current = target_version
        while current.parent_version:
            for v in versions:
                if v.version == current.parent_version:
                    lineage.insert(0, v)
                    current = v
                    break
        
        # 添加目标版本
        lineage.append(target_version)
        
        # 收集后代版本
        current = target_version
        while current.child_versions:
            for v in versions:
                if v.version in current.child_versions:
                    lineage.append(v)
                    current = v
                    break
        
        return lineage
    
    def compare_versions(self, config_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """比较两个版本的差异"""
        v1 = self.get_version_info(config_id, version1)
        v2 = self.get_version_info(config_id, version2)
        
        if not v1 or not v2:
            raise ConfigError("版本不存在")
        
        # 计算配置差异
        config1 = v1.config
        config2 = v2.config
        
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }
        
        # 简单的键值比较
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            if key not in config1:
                diff["added"][key] = config2[key]
            elif key not in config2:
                diff["removed"][key] = config1[key]
            elif config1[key] != config2[key]:
                diff["modified"][key] = {
                    "old": config1[key],
                    "new": config2[key]
                }
            else:
                diff["unchanged"][key] = config1[key]
        
        return {
            "version1": v1.to_dict(),
            "version2": v2.to_dict(),
            "diff": diff,
            "timestamp_diff": (v2.timestamp - v1.timestamp).total_seconds()
        }
    
    def create_branch(self, config_id: str, base_version: int, branch_name: str, 
                     new_config: Dict[str, Any], changed_by: str = "system") -> ConfigVersion:
        """创建版本分支"""
        try:
            base_version_obj = self.get_version_info(config_id, base_version)
            if not base_version_obj:
                raise ConfigError(f"基础版本 {base_version} 不存在")
            
            # 创建分支版本
            branch_version = self.create_backup(
                config_id=config_id,
                config=new_config,
                changed_by=changed_by,
                change_reason=f"创建分支: {branch_name}",
                version_type=VersionType.MANUAL,
                tags=[f"branch:{branch_name}", f"base:v{base_version}"]
            )
            
            # 设置分支关系
            branch_version.parent_version = base_version
            base_version_obj.child_versions.append(branch_version.version)
            
            # 保存版本信息
            self._save_versions()
            
            logger.info(f"创建分支: {branch_name} 基于版本 {base_version}")
            return branch_version
            
        except Exception as e:
            logger.error(f"创建分支失败: {e}")
            raise ConfigError(f"创建分支失败: {e}")
    
    def merge_versions(self, config_id: str, source_version: int, target_version: int, 
                      merged_config: Dict[str, Any], changed_by: str = "system") -> ConfigVersion:
        """合并版本"""
        try:
            source = self.get_version_info(config_id, source_version)
            target = self.get_version_info(config_id, target_version)
            
            if not source or not target:
                raise ConfigError("源版本或目标版本不存在")
            
            # 创建合并版本
            merged_version = self.create_backup(
                config_id=config_id,
                config=merged_config,
                changed_by=changed_by,
                change_reason=f"合并版本: v{source_version} + v{target_version}",
                version_type=VersionType.MANUAL,
                tags=[f"merge:v{source_version}", f"merge:v{target_version}"]
            )
            
            # 设置合并关系
            merged_version.parent_version = target_version
            target.child_versions.append(merged_version.version)
            
            # 保存版本信息
            self._save_versions()
            
            logger.info(f"合并版本: v{source_version} + v{target_version} -> v{merged_version.version}")
            return merged_version
            
        except Exception as e:
            logger.error(f"合并版本失败: {e}")
            raise ConfigError(f"合并版本失败: {e}")
    
    def tag_version(self, config_id: str, version: int, tags: List[str]) -> bool:
        """为版本添加标签"""
        try:
            version_obj = self.get_version_info(config_id, version)
            if not version_obj:
                return False
            
            if version_obj.metadata:
                version_obj.metadata.tags.extend(tags)
                version_obj.metadata.tags = list(set(version_obj.metadata.tags))  # 去重
            
            # 保存版本信息
            self._save_versions()
            
            logger.info(f"为版本 {config_id} v{version} 添加标签: {tags}")
            return True
            
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    def search_versions(self, config_id: str = None, 
                        tags: List[str] = None, 
                        version_type: VersionType = None,
                        start_date: datetime = None,
                        end_date: datetime = None) -> List[ConfigVersion]:
        """搜索版本"""
        results = []
        
        # 确定搜索范围
        if config_id:
            search_versions = self.versions.get(config_id, [])
        else:
            search_versions = []
            for versions in self.versions.values():
                search_versions.extend(versions)
        
        for version in search_versions:
            # 检查版本类型
            if version_type and version.version_type != version_type:
                continue
            
            # 检查标签
            if tags and version.metadata:
                if not any(tag in version.metadata.tags for tag in tags):
                    continue
            
            # 检查时间范围
            if start_date and version.timestamp < start_date:
                continue
            if end_date and version.timestamp > end_date:
                continue
            
            results.append(version)
        
        # 按时间排序
        results.sort(key=lambda v: v.timestamp, reverse=True)
        return results
    
    def cleanup_expired_versions(self) -> int:
        """清理过期版本"""
        expired_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for config_id, versions in self.versions.items():
            versions_to_remove = []
            
            for version in versions:
                if (version.timestamp < cutoff_date and 
                    version.metadata and 
                    version.metadata.status == VersionStatus.ACTIVE and
                    version.version_type == VersionType.AUTO):
                    versions_to_remove.append(version)
            
            # 标记为已归档而不是删除
            for version in versions_to_remove:
                if version.metadata:
                    version.metadata.status = VersionStatus.ARCHIVED
                    expired_count += 1
        
        if expired_count > 0:
            self._save_versions()
            logger.info(f"归档了 {expired_count} 个过期版本")
        
        return expired_count
    
    def get_version_statistics(self, config_id: str = None) -> Dict[str, Any]:
        """获取版本统计信息"""
        stats = {
            "total_versions": 0,
            "active_versions": 0,
            "archived_versions": 0,
            "by_type": {},
            "by_environment": {},
            "total_size": 0,
            "compressed_size": 0,
            "compression_ratio": 0.0
        }
        
        versions = []
        if config_id:
            versions = self.versions.get(config_id, [])
        else:
            for v_list in self.versions.values():
                versions.extend(v_list)
        
        for version in versions:
            stats["total_versions"] += 1
            
            # 按状态统计
            if version.metadata:
                if version.metadata.status == VersionStatus.ACTIVE:
                    stats["active_versions"] += 1
                elif version.metadata.status == VersionStatus.ARCHIVED:
                    stats["archived_versions"] += 1
                
                # 按类型统计
                vtype = version.metadata.version_type.value
                stats["by_type"][vtype] = stats["by_type"].get(vtype, 0) + 1
                
                # 按环境统计
                env = version.metadata.environment
                stats["by_environment"][env] = stats["by_environment"].get(env, 0) + 1
                
                # 统计大小
                stats["total_size"] += version.metadata.file_size
                stats["compressed_size"] += version.metadata.compressed_size
        
        # 计算压缩比
        if stats["total_size"] > 0:
            stats["compression_ratio"] = (1 - stats["compressed_size"] / stats["total_size"]) * 100
        
        return stats
    
    def export_version_metadata(self, output_path: str = None) -> str:
        """导出版本元数据"""
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "total_configs": len(self.versions),
            "total_versions": sum(len(versions) for versions in self.versions.values()),
            "configurations": {}
        }
        
        for config_id, versions in self.versions.items():
            metadata["configurations"][config_id] = {
                "version_count": len(versions),
                "latest_version": versions[-1].version if versions else 0,
                "latest_timestamp": versions[-1].timestamp.isoformat() if versions else None,
                "versions": [v.to_dict() for v in versions]
            }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"版本元数据已导出到: {output_path}")
        
        return json.dumps(metadata, indent=2, ensure_ascii=False)
    
    def get_history(self, config_id: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """获取配置历史"""
        history = []
        
        if config_id:
            versions = self.versions.get(config_id, [])
        else:
            versions = []
            for v_list in self.versions.values():
                versions.extend(v_list)
        
        # 按时间排序
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        
        # 限制数量
        if limit:
            versions = versions[:limit]
        
        for version in versions:
            history_entry = {
                "config_id": config_id or "unknown",
                "version": version.version,
                "version_id": self._generate_version_id(config_id or "unknown", version.version),
                "timestamp": version.timestamp.isoformat(),
                "changed_by": version.changed_by,
                "change_reason": version.change_reason,
                "version_type": version.version_type.value,
                "backup_exists": version.backup_path.exists() if version.backup_path else False,
            }
            
            if version.metadata:
                history_entry["metadata"] = {
                    "status": version.metadata.status.value,
                    "environment": version.metadata.environment,
                    "service_version": version.metadata.service_version,
                    "tags": version.metadata.tags,
                    "file_size": version.metadata.file_size,
                    "compressed_size": version.metadata.compressed_size,
                }
            
            history.append(history_entry)
        
        return history