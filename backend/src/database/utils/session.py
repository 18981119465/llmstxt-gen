"""
数据库会话管理
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta
from threading import Lock
import threading
import weakref

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SessionInfo:
    """会话信息类"""
    
    def __init__(self, session: Session, session_id: str, created_by: str = "unknown"):
        self.session = session
        self.session_id = session_id
        self.created_by = created_by
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.query_count = 0
        self.is_active = True
        self.transaction_count = 0
        self.rollback_count = 0
        self.error_count = 0
        
    def update_usage(self):
        """更新使用信息"""
        self.last_used = datetime.now()
        self.query_count += 1
        
    def record_transaction(self):
        """记录事务"""
        self.transaction_count += 1
        
    def record_rollback(self):
        """记录回滚"""
        self.rollback_count += 1
        
    def record_error(self):
        """记录错误"""
        self.error_count += 1
        
    def get_age(self) -> timedelta:
        """获取会话年龄"""
        return datetime.now() - self.created_at
        
    def get_idle_time(self) -> timedelta:
        """获取空闲时间"""
        return datetime.now() - self.last_used
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "query_count": self.query_count,
            "transaction_count": self.transaction_count,
            "rollback_count": self.rollback_count,
            "error_count": self.error_count,
            "is_active": self.is_active,
            "age_seconds": self.get_age().total_seconds(),
            "idle_seconds": self.get_idle_time().total_seconds()
        }


class SessionManager:
    """数据库会话管理器"""
    
    def __init__(self, max_sessions: int = 100, session_timeout: int = 3600):
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout  # 秒
        self.sessions: Dict[str, SessionInfo] = {}
        self.lock = Lock()
        self._cleanup_thread = None
        self._running = False
        
        # 启动清理线程
        self.start_cleanup_thread()
        
    def create_session(self, session_id: Optional[str] = None, created_by: str = "unknown") -> str:
        """创建新的数据库会话"""
        with self.lock:
            # 检查会话数量限制
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_expired_sessions()
                if len(self.sessions) >= self.max_sessions:
                    raise Exception(f"会话数量超过限制: {self.max_sessions}")
            
            # 生成会话ID
            if session_id is None:
                session_id = f"session_{datetime.now().timestamp()}_{threading.get_ident()}"
            
            # 创建会话
            from .connection import db_manager
            session = db_manager.session_factory()
            
            # 存储会话信息
            session_info = SessionInfo(session, session_id, created_by)
            self.sessions[session_id] = session_info
            
            logger.info(f"创建数据库会话: {session_id} by {created_by}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取数据库会话"""
        with self.lock:
            session_info = self.sessions.get(session_id)
            if session_info and session_info.is_active:
                session_info.update_usage()
                return session_info.session
            return None
    
    def close_session(self, session_id: str) -> bool:
        """关闭数据库会话"""
        with self.lock:
            session_info = self.sessions.get(session_id)
            if session_info:
                try:
                    session_info.session.close()
                    session_info.is_active = False
                    del self.sessions[session_id]
                    logger.info(f"关闭数据库会话: {session_id}")
                    return True
                except Exception as e:
                    logger.error(f"关闭会话失败 {session_id}: {e}")
                    session_info.is_active = False
                    return False
            return False
    
    def close_all_sessions(self):
        """关闭所有会话"""
        with self.lock:
            for session_id, session_info in list(self.sessions.items()):
                try:
                    session_info.session.close()
                    session_info.is_active = False
                except Exception as e:
                    logger.error(f"关闭会话失败 {session_id}: {e}")
            
            self.sessions.clear()
            logger.info("关闭所有数据库会话")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        with self.lock:
            session_info = self.sessions.get(session_id)
            if session_info:
                return session_info.to_dict()
            return None
    
    def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """获取所有会话信息"""
        with self.lock:
            return [info.to_dict() for info in self.sessions.values()]
    
    def get_active_sessions_count(self) -> int:
        """获取活跃会话数量"""
        with self.lock:
            return len([info for info in self.sessions.values() if info.is_active])
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        with self.lock:
            active_sessions = [info for info in self.sessions.values() if info.is_active]
            
            if not active_sessions:
                return {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "total_queries": 0,
                    "total_transactions": 0,
                    "total_rollbacks": 0,
                    "total_errors": 0,
                    "average_age": 0,
                    "average_idle": 0
                }
            
            total_queries = sum(info.query_count for info in active_sessions)
            total_transactions = sum(info.transaction_count for info in active_sessions)
            total_rollbacks = sum(info.rollback_count for info in active_sessions)
            total_errors = sum(info.error_count for info in active_sessions)
            
            total_age = sum(info.get_age().total_seconds() for info in active_sessions)
            total_idle = sum(info.get_idle_time().total_seconds() for info in active_sessions)
            
            return {
                "total_sessions": len(active_sessions),
                "active_sessions": len(active_sessions),
                "total_queries": total_queries,
                "total_transactions": total_transactions,
                "total_rollbacks": total_rollbacks,
                "total_errors": total_errors,
                "average_age": total_age / len(active_sessions),
                "average_idle": total_idle / len(active_sessions)
            }
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = []
        
        for session_id, session_info in self.sessions.items():
            if session_info.get_idle_time().total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.close_session(session_id)
        
        if expired_sessions:
            logger.info(f"清理过期会话: {len(expired_sessions)} 个")
    
    def start_cleanup_thread(self):
        """启动清理线程"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._running = True
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
            logger.info("启动会话清理线程")
    
    def stop_cleanup_thread(self):
        """停止清理线程"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
            logger.info("停止会话清理线程")
    
    def _cleanup_worker(self):
        """清理工作线程"""
        while self._running:
            try:
                self._cleanup_expired_sessions()
                
                # 每5分钟清理一次
                for _ in range(300):
                    if not self._running:
                        break
                    threading.Event().wait(1)
                    
            except Exception as e:
                logger.error(f"会话清理线程错误: {e}")
                threading.Event().wait(60)  # 错误时等待1分钟
    
    @contextmanager
    def session_context(self, session_id: Optional[str] = None, created_by: str = "unknown"):
        """会话上下文管理器"""
        session_id = self.create_session(session_id, created_by)
        session = self.get_session(session_id)
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            
            # 记录错误
            session_info = self.sessions.get(session_id)
            if session_info:
                session_info.record_error()
                session_info.record_rollback()
            
            logger.error(f"会话操作失败 {session_id}: {e}")
            raise
        finally:
            self.close_session(session_id)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            stats = self.get_session_stats()
            
            # 检查会话数量
            session_status = "healthy"
            if stats["active_sessions"] > self.max_sessions * 0.8:
                session_status = "warning"
            if stats["active_sessions"] >= self.max_sessions:
                session_status = "critical"
            
            # 检查错误率
            error_rate = stats["total_errors"] / max(stats["total_queries"], 1)
            error_status = "healthy"
            if error_rate > 0.1:  # 10%错误率
                error_status = "warning"
            if error_rate > 0.2:  # 20%错误率
                error_status = "critical"
            
            # 检查回滚率
            rollback_rate = stats["total_rollbacks"] / max(stats["total_transactions"], 1)
            rollback_status = "healthy"
            if rollback_rate > 0.2:  # 20%回滚率
                rollback_status = "warning"
            if rollback_rate > 0.4:  # 40%回滚率
                rollback_status = "critical"
            
            overall_status = "healthy"
            if any(status == "warning" for status in [session_status, error_status, rollback_status]):
                overall_status = "warning"
            if any(status == "critical" for status in [session_status, error_status, rollback_status]):
                overall_status = "critical"
            
            return {
                "status": overall_status,
                "session_status": session_status,
                "error_status": error_status,
                "rollback_status": rollback_status,
                "stats": stats,
                "max_sessions": self.max_sessions,
                "session_timeout": self.session_timeout,
                "cleanup_thread_running": self._running
            }
            
        except Exception as e:
            logger.error(f"会话管理器健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# 全局会话管理器实例
session_manager = SessionManager()