"""
数据模型验证测试脚本
"""

import sys
import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import (
    Base, User, Role, Permission, Project, Document, Task,
    SystemConfig, SystemLog, AuditLog
)
from src.database.utils.connection import DatabaseConfig, DatabaseManager
from src.database.schemas.user import UserCreate, UserRole
from src.database.schemas.project import ProjectCreate, ProjectStatus
from src.database.schemas.document import DocumentCreate
from src.database.schemas.task import TaskCreate


def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        # 创建数据库配置
        config = DatabaseConfig()
        print(f"📊 数据库URL: {config.database_url}")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(config)
        
        # 测试连接
        if db_manager.check_connection():
            print("✅ 数据库连接成功")
            
            # 获取数据库信息
            db_info = db_manager.get_database_info()
            print(f"📊 数据库信息: {json.dumps(db_info, indent=2, default=str)}")
            
            return True
        else:
            print("❌ 数据库连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return False


def test_model_creation():
    """测试模型创建"""
    print("\n🔍 测试数据模型创建...")
    
    try:
        # 创建数据库引擎
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        # 创建表
        db_manager.create_tables()
        print("✅ 数据库表创建成功")
        
        # 测试模型实例化
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        print("✅ 用户模型创建成功")
        
        project = Project(
            name="Test Project",
            description="Test project description",
            slug="test-project",
            owner_id=user.id
        )
        print("✅ 项目模型创建成功")
        
        document = Document(
            project_id=project.id,
            name="Test Document",
            type="pdf",
            file_size=1024
        )
        print("✅ 文档模型创建成功")
        
        task = Task(
            project_id=project.id,
            document_id=document.id,
            task_type="document_process",
            name="Test Task",
            created_by_id=user.id
        )
        print("✅ 任务模型创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型创建错误: {e}")
        return False


def test_schema_validation():
    """测试schema验证"""
    print("\n🔍 测试Pydantic schema验证...")
    
    try:
        # 测试用户schema
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "full_name": "Test User"
        }
        
        user_schema = UserCreate(**user_data)
        print("✅ 用户schema验证成功")
        
        # 测试密码强度验证
        try:
            weak_password_data = user_data.copy()
            weak_password_data["password"] = "weak"
            weak_password_data["confirm_password"] = "weak"
            UserCreate(**weak_password_data)
            print("❌ 密码强度验证失败")
            return False
        except Exception:
            print("✅ 密码强度验证成功")
        
        # 测试项目schema
        project_data = {
            "name": "Test Project",
            "description": "Test project description",
            "visibility": "private"
        }
        
        from src.database.schemas.project import ProjectCreate
        project_schema = ProjectCreate(**project_data)
        print("✅ 项目schema验证成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema验证错误: {e}")
        return False


def test_database_operations():
    """测试数据库操作"""
    print("\n🔍 测试数据库操作...")
    
    try:
        # 创建数据库会话
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        with db_manager.get_session_context() as session:
            # 创建测试用户
            user = User(
                username="testuser_ops",
                email="test_ops@example.com",
                password_hash="hashed_password",
                full_name="Test User Ops"
            )
            session.add(user)
            session.commit()
            
            # 创建测试角色
            role = Role(
                name="test_role",
                display_name="Test Role",
                description="Test role description"
            )
            session.add(role)
            session.commit()
            
            # 创建测试权限
            permission = Permission(
                code="test_permission",
                name="Test Permission",
                description="Test permission description",
                resource="test",
                action="read"
            )
            session.add(permission)
            session.commit()
            
            # 创建测试项目
            project = Project(
                name="Test Project Ops",
                description="Test project description",
                slug="test-project-ops",
                owner_id=user.id
            )
            session.add(project)
            session.commit()
            
            # 创建测试文档
            document = Document(
                project_id=project.id,
                name="Test Document Ops",
                type="pdf",
                file_size=2048,
                file_hash="test_hash_123"
            )
            session.add(document)
            session.commit()
            
            # 创建测试任务
            task = Task(
                project_id=project.id,
                document_id=document.id,
                task_type="document_process",
                name="Test Task Ops",
                created_by_id=user.id
            )
            session.add(task)
            session.commit()
            
            # 测试查询
            queried_user = session.query(User).filter(User.username == "testuser_ops").first()
            if queried_user:
                print("✅ 用户查询成功")
                print(f"📊 用户信息: {queried_user.to_dict()}")
            else:
                print("❌ 用户查询失败")
                return False
            
            # 测试更新
            queried_user.full_name = "Updated Test User"
            session.commit()
            print("✅ 用户更新成功")
            
            # 测试删除
            session.delete(queried_user)
            session.commit()
            print("✅ 用户删除成功")
            
            # 清理测试数据
            session.query(Task).filter(Task.name == "Test Task Ops").delete()
            session.query(Document).filter(Document.name == "Test Document Ops").delete()
            session.query(Project).filter(Project.name == "Test Project Ops").delete()
            session.query(Role).filter(Role.name == "test_role").delete()
            session.query(Permission).filter(Permission.code == "test_permission").delete()
            session.commit()
            
            print("✅ 测试数据清理成功")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库操作错误: {e}")
        return False


def test_model_relationships():
    """测试模型关系"""
    print("\n🔍 测试模型关系...")
    
    try:
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        with db_manager.get_session_context() as session:
            # 创建用户
            user = User(
                username="testuser_rel",
                email="test_rel@example.com",
                password_hash="hashed_password",
                full_name="Test User Relations"
            )
            session.add(user)
            session.commit()
            
            # 创建角色
            role = Role(
                name="test_role_rel",
                display_name="Test Role Relations",
                description="Test role description"
            )
            session.add(role)
            session.commit()
            
            # 创建权限
            permission = Permission(
                code="test_permission_rel",
                name="Test Permission Relations",
                description="Test permission description",
                resource="test",
                action="read"
            )
            session.add(permission)
            session.commit()
            
            # 建立关系
            user.roles.append(role)
            role.permissions.append(permission)
            session.commit()
            
            # 测试关系查询
            queried_user = session.query(User).filter(User.username == "testuser_rel").first()
            if queried_user and len(queried_user.roles) > 0:
                print("✅ 用户角色关系成功")
                if len(queried_user.roles[0].permissions) > 0:
                    print("✅ 角色权限关系成功")
                else:
                    print("❌ 角色权限关系失败")
                    return False
            else:
                print("❌ 用户角色关系失败")
                return False
            
            # 测试权限检查
            if queried_user.has_permission("test_permission_rel"):
                print("✅ 权限检查成功")
            else:
                print("❌ 权限检查失败")
                return False
            
            # 清理测试数据
            session.delete(queried_user)
            session.delete(role)
            session.delete(permission)
            session.commit()
            
            print("✅ 关系测试数据清理成功")
            
            return True
            
    except Exception as e:
        print(f"❌ 模型关系错误: {e}")
        return False


def test_json_serialization():
    """测试JSON序列化"""
    print("\n🔍 测试JSON序列化...")
    
    try:
        # 创建用户实例
        user = User(
            username="testuser_json",
            email="test_json@example.com",
            password_hash="hashed_password",
            full_name="Test User JSON"
        )
        
        # 转换为字典
        user_dict = user.to_dict()
        print("✅ 用户模型转换为字典成功")
        
        # 序列化为JSON
        json_str = json.dumps(user_dict, indent=2, default=str)
        print("✅ 用户模型JSON序列化成功")
        
        # 反序列化
        parsed_dict = json.loads(json_str)
        print("✅ 用户模型JSON反序列化成功")
        
        # 验证数据完整性
        if parsed_dict.get("username") == "testuser_json":
            print("✅ JSON序列化数据完整性验证成功")
        else:
            print("❌ JSON序列化数据完整性验证失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ JSON序列化错误: {e}")
        return False


def generate_test_report(results):
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    report = {
        "test_summary": {
            "total_tests": len(results),
            "passed_tests": len([r for r in results if r["status"] == "PASS"]),
            "failed_tests": len([r for r in results if r["status"] == "FAIL"]),
            "success_rate": (len([r for r in results if r["status"] == "PASS"]) / len(results)) * 100
        },
        "test_results": results,
        "generated_at": datetime.now().isoformat(),
        "database_info": {
            "version": "PostgreSQL",
            "orm": "SQLAlchemy",
            "schema_validation": "Pydantic"
        }
    }
    
    # 保存报告
    with open("database_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📊 测试报告已保存到: database_test_report.json")
    return report


def main():
    """主测试函数"""
    print("🚀 开始数据模型验证测试...")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    test_functions = [
        ("数据库连接测试", test_database_connection),
        ("模型创建测试", test_model_creation),
        ("Schema验证测试", test_schema_validation),
        ("数据库操作测试", test_database_operations),
        ("模型关系测试", test_model_relationships),
        ("JSON序列化测试", test_json_serialization)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n🔍 运行 {test_name}...")
        try:
            if test_func():
                results.append({"name": test_name, "status": "PASS"})
                print(f"✅ {test_name} 通过")
            else:
                results.append({"name": test_name, "status": "FAIL"})
                print(f"❌ {test_name} 失败")
        except Exception as e:
            results.append({"name": test_name, "status": "FAIL", "error": str(e)})
            print(f"❌ {test_name} 错误: {e}")
    
    print("\n" + "=" * 60)
    
    # 生成报告
    report = generate_test_report(results)
    
    # 显示总结
    summary = report["test_summary"]
    print(f"📊 测试总结:")
    print(f"   总测试数: {summary['total_tests']}")
    print(f"   通过测试: {summary['passed_tests']}")
    print(f"   失败测试: {summary['failed_tests']}")
    print(f"   成功率: {summary['success_rate']:.1f}%")
    
    if summary["success_rate"] == 100:
        print("\n🎉 所有测试通过！数据模型实现成功！")
    else:
        print(f"\n⚠️  有 {summary['failed_tests']} 个测试失败，需要修复。")
    
    return summary["success_rate"] == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)