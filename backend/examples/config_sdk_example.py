"""
配置管理SDK使用示例
"""

import asyncio
import json
from pathlib import Path
from src.config.sdk import ConfigClient, LocalConfigManager, ConfigClientOptions


async def remote_config_example():
    """远程配置管理示例"""
    print("=== 远程配置管理示例 ===")
    
    # 创建配置客户端
    options = ConfigClientOptions(
        api_base_url="http://localhost:8000/api/v1/config",
        timeout=10
    )
    
    try:
        async with ConfigClient(options) as client:
            # 1. 获取当前配置
            print("\n1. 获取当前配置:")
            config = await client.get_config()
            print(f"应用名称: {config.get('app', {}).get('name', 'Unknown')}")
            print(f"调试模式: {config.get('app', {}).get('debug', False)}")
            
            # 2. 更新配置值
            print("\n2. 更新配置值:")
            success = await client.set_value("app.debug", True)
            print(f"更新调试模式: {'成功' if success else '失败'}")
            
            # 3. 获取特定部分
            print("\n3. 获取数据库配置:")
            db_config = await client.get_section("database")
            print(f"数据库URL: {db_config.get('url', 'Unknown')}")
            
            # 4. 验证配置
            print("\n4. 验证配置:")
            validation_result = await client.validate_config()
            print(f"配置有效: {validation_result['valid']}")
            if validation_result['errors']:
                print("错误:")
                for error in validation_result['errors']:
                    print(f"  - {error}")
            
            # 5. 导出配置
            print("\n5. 导出配置:")
            yaml_config = await client.export_config("yaml")
            print("YAML格式配置:")
            print(yaml_config[:200] + "..." if len(yaml_config) > 200 else yaml_config)
            
            # 6. 获取历史记录
            print("\n6. 获取历史记录:")
            history = await client.get_history()
            print(f"历史记录数量: {len(history)}")
            for i, version in enumerate(history[:3]):  # 显示前3条
                print(f"  {i+1}. {version['version_id']} - {version['timestamp']}")
            
            # 7. 监视配置变化
            print("\n7. 监视配置变化:")
            def on_config_change(new_config):
                print(f"配置已变化! 新的调试模式: {new_config.get('app', {}).get('debug')}")
            
            # 注意：这是一个简化的监视实现，实际使用时可能需要使用WebSocket
            # await client.watch_config(on_config_change)
            
    except Exception as e:
        print(f"远程配置示例出错: {e}")


def local_config_example():
    """本地配置管理示例"""
    print("\n=== 本地配置管理示例 ===")
    
    # 创建测试配置文件
    test_config = {
        "app": {
            "name": "test-app",
            "version": "1.0.0",
            "debug": True
        },
        "database": {
            "url": "sqlite:///test.db",
            "pool_size": 10
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8000
        }
    }
    
    # 保存测试配置
    config_path = "test_config.yaml"
    import yaml
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
    
    try:
        # 创建本地配置管理器
        manager = LocalConfigManager(config_path)
        
        # 1. 加载配置
        print("\n1. 加载配置:")
        config = manager.load_config()
        print(f"配置内容: {json.dumps(config, indent=2, ensure_ascii=False)}")
        
        # 2. 获取配置信息
        print("\n2. 获取配置信息:")
        info = manager.get_config_info()
        print(f"配置文件: {info['config_path']}")
        print(f"文件大小: {info['file_size']} bytes")
        
        # 3. 获取配置值
        print("\n3. 获取配置值:")
        app_name = manager.get_value("app.name")
        print(f"应用名称: {app_name}")
        
        # 4. 设置配置值
        print("\n4. 设置配置值:")
        success = manager.set_value("app.debug", False)
        print(f"更新调试模式: {'成功' if success else '失败'}")
        
        # 5. 获取配置部分
        print("\n5. 获取数据库配置:")
        db_config = manager.get_section("database")
        print(f"数据库配置: {db_config}")
        
        # 6. 更新配置部分
        print("\n6. 更新API配置:")
        new_api_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "debug": False
        }
        success = manager.update_section("api", new_api_config)
        print(f"更新API配置: {'成功' if success else '失败'}")
        
        # 7. 验证配置
        print("\n7. 验证配置:")
        validation_result = manager.validate_config()
        print(f"配置有效: {validation_result['valid']}")
        if validation_result['warnings']:
            print("警告:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        
        # 8. 导出配置
        print("\n8. 导出配置:")
        yaml_export = manager.export_config("yaml")
        print("YAML导出:")
        print(yaml_export)
        
        json_export = manager.export_config("json")
        print("\nJSON导出:")
        print(json_export)
        
        # 9. 导入配置
        print("\n9. 导入配置:")
        new_config = {
            "app": {
                "name": "imported-app",
                "version": "2.0.0",
                "debug": True
            },
            "database": {
                "url": "postgresql://localhost:5432/testdb",
                "pool_size": 20
            }
        }
        
        # 先导出为YAML，然后导入
        import yaml
        yaml_data = yaml.dump(new_config, default_flow_style=False, allow_unicode=True)
        success = manager.import_config(yaml_data, "yaml")
        print(f"导入YAML配置: {'成功' if success else '失败'}")
        
        # 验证导入结果
        if success:
            imported_config = manager.load_config()
            print(f"导入后的配置: {json.dumps(imported_config, indent=2, ensure_ascii=False)}")
        
        # 10. 获取历史记录
        print("\n10. 获取历史记录:")
        history = manager.get_history()
        print(f"历史记录数量: {len(history)}")
        for i, version in enumerate(history):
            print(f"  {i+1}. {version['version_id']} - {version['timestamp']}")
        
    except Exception as e:
        print(f"本地配置示例出错: {e}")
    finally:
        # 清理测试文件
        try:
            Path(config_path).unlink()
        except:
            pass


async def batch_operations_example():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    try:
        async with ConfigClient() as client:
            # 批量更新配置
            updates = [
                ("app.debug", True),
                ("app.version", "1.0.1"),
                ("database.pool_size", 15),
                ("api.port", 8080)
            ]
            
            print("批量更新配置:")
            for key, value in updates:
                success = await client.set_value(key, value)
                print(f"  {key} = {value}: {'成功' if success else '失败'}")
            
            # 批量获取配置
            keys = ["app.name", "app.debug", "database.url", "api.host"]
            print("\n批量获取配置:")
            for key in keys:
                try:
                    value = await client.get_value(key)
                    print(f"  {key} = {value}")
                except Exception as e:
                    print(f"  {key} = 错误: {e}")
            
            # 批量验证不同配置
            test_configs = [
                {"app": {"name": "test", "version": "1.0.0"}},
                {"app": {"name": "", "version": "invalid"}},
                {"database": {"url": "sqlite:///test.db", "pool_size": -1}}
            ]
            
            print("\n批量验证配置:")
            for i, config in enumerate(test_configs):
                try:
                    result = await client.validate_config(config)
                    print(f"  配置 {i+1}: {'有效' if result['valid'] else '无效'}")
                    if result['errors']:
                        print(f"    错误: {result['errors']}")
                except Exception as e:
                    print(f"  配置 {i+1}: 验证失败 - {e}")
    
    except Exception as e:
        print(f"批量操作示例出错: {e}")


async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    try:
        async with ConfigClient() as client:
            # 尝试获取不存在的配置
            print("1. 尝试获取不存在的配置:")
            try:
                value = await client.get_value("nonexistent.key")
                print(f"  值: {value}")
            except Exception as e:
                print(f"  错误: {e}")
            
            # 尝试设置无效配置
            print("\n2. 尝试验证无效配置:")
            try:
                invalid_config = {"app": {"name": "", "version": "invalid"}}
                result = await client.validate_config(invalid_config)
                print(f"  验证结果: {result}")
            except Exception as e:
                print(f"  错误: {e}")
            
            # 尝试回滚到不存在的版本
            print("\n3. 尝试回滚到不存在的版本:")
            try:
                success = await client.rollback("nonexistent-version")
                print(f"  回滚结果: {success}")
            except Exception as e:
                print(f"  错误: {e}")
    
    except Exception as e:
        print(f"错误处理示例出错: {e}")


async def main():
    """主函数"""
    print("配置管理SDK使用示例")
    print("=" * 50)
    
    # 本地配置示例
    local_config_example()
    
    # 远程配置示例（需要服务器运行）
    print("\n提示: 远程配置示例需要运行配置管理服务器")
    try:
        await remote_config_example()
    except Exception as e:
        print(f"远程配置示例跳过（服务器未运行）: {e}")
    
    # 批量操作示例
    try:
        await batch_operations_example()
    except Exception as e:
        print(f"批量操作示例跳过: {e}")
    
    # 错误处理示例
    try:
        await error_handling_example()
    except Exception as e:
        print(f"错误处理示例跳过: {e}")
    
    print("\n示例运行完成!")


if __name__ == "__main__":
    asyncio.run(main())