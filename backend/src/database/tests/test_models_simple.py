"""
简单的数据模型测试
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """测试导入"""
    print("测试数据模型导入...")
    
    try:
        # 测试基础模型导入
        from src.database.models.base import Base
        print("✓ 基础模型导入成功")
        
        # 测试用户模型导入
        from src.database.models.user import User, Role, Permission
        print("✓ 用户模型导入成功")
        
        # 测试项目模型导入
        from src.database.models.project import Project
        print("✓ 项目模型导入成功")
        
        # 测试文档模型导入
        from src.database.models.document import Document
        print("✓ 文档模型导入成功")
        
        # 测试任务模型导入
        from src.database.models.task import Task
        print("✓ 任务模型导入成功")
        
        # 测试系统模型导入
        from src.database.models.system import SystemConfig
        print("✓ 系统模型导入成功")
        
        # 测试schemas导入
        from src.database.schemas.user import UserCreate, UserResponse
        print("✓ 用户schemas导入成功")
        
        from src.database.schemas.project import ProjectCreate, ProjectResponse
        print("✓ 项目schemas导入成功")
        
        from src.database.schemas.document import DocumentCreate, DocumentResponse
        print("✓ 文档schemas导入成功")
        
        from src.database.schemas.task import TaskCreate, TaskResponse
        print("✓ 任务schemas导入成功")
        
        from src.database.schemas.system import SystemConfigCreate, SystemConfigResponse
        print("✓ 系统schemas导入成功")
        
        # 测试工具导入
        from src.database.utils.connection import DatabaseConfig, DatabaseManager
        print("✓ 数据库连接工具导入成功")
        
        from src.database.utils.session import SessionManager
        print("✓ 会话管理工具导入成功")
        
        from src.database.utils.backup import DatabaseBackup
        print("✓ 备份工具导入成功")
        
        from src.database.utils.migrations import MigrationManager
        print("✓ 迁移工具导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_model_creation():
    """测试模型创建"""
    print("\n🔍 测试模型创建...")
    
    try:
        from src.database.models.user import User, Role, Permission
        from src.database.models.project import Project
        from src.database.models.document import Document
        from src.database.models.task import Task
        
        # 创建用户实例
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        print("✓ 用户实例创建成功")
        
        # 创建角色实例
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="Test role description"
        )
        print("✓ 角色实例创建成功")
        
        # 创建权限实例
        permission = Permission(
            code="test_permission",
            name="Test Permission",
            description="Test permission description",
            resource="test",
            action="read"
        )
        print("✓ 权限实例创建成功")
        
        # 创建项目实例
        project = Project(
            name="Test Project",
            description="Test project description",
            slug="test-project",
            owner_id=user.id
        )
        print("✓ 项目实例创建成功")
        
        # 创建文档实例
        document = Document(
            project_id=project.id,
            name="Test Document",
            type="pdf",
            file_size=1024
        )
        print("✓ 文档实例创建成功")
        
        # 创建任务实例
        task = Task(
            project_id=project.id,
            document_id=document.id,
            task_type="document_process",
            name="Test Task",
            created_by_id=user.id
        )
        print("✓ 任务实例创建成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 模型创建失败: {e}")
        return False


def test_schema_validation():
    """测试schema验证"""
    print("\n🔍 测试schema验证...")
    
    try:
        from src.database.schemas.user import UserCreate
        
        # 测试有效数据
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "full_name": "Test User"
        }
        
        user_schema = UserCreate(**user_data)
        print("✓ 用户schema验证成功")
        
        # 测试密码强度验证
        try:
            weak_password_data = user_data.copy()
            weak_password_data["password"] = "weak"
            weak_password_data["confirm_password"] = "weak"
            UserCreate(**weak_password_data)
            print("✗ 密码强度验证失败")
            return False
        except Exception:
            print("✓ 密码强度验证成功")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema验证失败: {e}")
        return False


def test_json_serialization():
    """测试JSON序列化"""
    print("\n🔍 测试JSON序列化...")
    
    try:
        from src.database.models.user import User
        import json
        
        # 创建用户实例
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        
        # 转换为字典
        user_dict = user.to_dict()
        print("✓ 用户模型转换为字典成功")
        
        # 序列化为JSON
        json_str = json.dumps(user_dict, indent=2, default=str)
        print("✓ 用户模型JSON序列化成功")
        
        # 反序列化
        parsed_dict = json.loads(json_str)
        print("✓ 用户模型JSON反序列化成功")
        
        # 验证数据完整性
        if parsed_dict.get("username") == "testuser":
            print("✓ JSON序列化数据完整性验证成功")
        else:
            print("✗ JSON序列化数据完整性验证失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ JSON序列化失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始数据模型验证测试...")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    test_functions = [
        ("导入测试", test_imports),
        ("模型创建测试", test_model_creation),
        ("Schema验证测试", test_schema_validation),
        ("JSON序列化测试", test_json_serialization)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n运行 {test_name}...")
        try:
            if test_func():
                results.append({"name": test_name, "status": "PASS"})
                print(f"✓ {test_name} 通过")
            else:
                results.append({"name": test_name, "status": "FAIL"})
                print(f"✗ {test_name} 失败")
        except Exception as e:
            results.append({"name": test_name, "status": "FAIL", "error": str(e)})
            print(f"✗ {test_name} 错误: {e}")
    
    print("\n" + "=" * 60)
    
    # 显示总结
    total_tests = len(results)
    passed_tests = len([r for r in results if r["status"] == "PASS"])
    failed_tests = len([r for r in results if r["status"] == "FAIL"])
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"测试总结:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过测试: {passed_tests}")
    print(f"   失败测试: {failed_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有测试通过！数据模型实现成功！")
    else:
        print(f"\n⚠️  有 {failed_tests} 个测试失败，需要修复。")
    
    return success_rate == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)