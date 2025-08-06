#!/usr/bin/env python3
"""
配置管理命令行工具
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.core import ConfigManager, ConfigWatcher, ConfigValidator
from src.config.rollback import ConfigRollbackManager
from src.config.management import get_config_manager


class ConfigCLI:
    """配置管理命令行工具"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self.config_manager = None
        self.validator = None
        self.watcher = None
        self.rollback_manager = None
        
    async def initialize(self):
        """初始化配置管理器"""
        try:
            self.config_manager = ConfigManager(self.config_path)
            self.validator = ConfigValidator()
            self.watcher = ConfigWatcher(self.config_path, self.config_manager)
            self.rollback_manager = ConfigRollbackManager(self.config_path)
            
            # 加载配置
            self.config_manager.load_config()
            print(f"✅ 配置管理器初始化成功")
            print(f"📁 配置文件: {self.config_path}")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            sys.exit(1)
    
    async def show_config(self, section: Optional[str] = None, output_format: str = "yaml"):
        """显示配置"""
        try:
            config = self.config_manager.load_config()
            
            if section:
                if section in config:
                    config = {section: config[section]}
                else:
                    print(f"❌ 配置部分 '{section}' 不存在")
                    return
            
            if output_format == "json":
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                print(yaml.dump(config, default_flow_style=False, allow_unicode=True))
                
        except Exception as e:
            print(f"❌ 显示配置失败: {e}")
    
    async def set_config(self, key: str, value: str, section: Optional[str] = None):
        """设置配置值"""
        try:
            # 解析值
            try:
                # 尝试解析为 JSON
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                # 如果不是 JSON，直接使用字符串
                parsed_value = value
            
            # 构建配置路径
            if section:
                config_path = f"{section}.{key}"
            else:
                config_path = key
            
            # 更新配置
            success = self.config_manager.update_config_value(config_path, parsed_value)
            
            if success:
                print(f"✅ 配置更新成功: {config_path} = {parsed_value}")
            else:
                print(f"❌ 配置更新失败: {config_path}")
                
        except Exception as e:
            print(f"❌ 设置配置失败: {e}")
    
    async def validate_config(self):
        """验证配置"""
        try:
            config = self.config_manager.load_config()
            result = self.validator.validate_config(config)
            
            if result.valid:
                print("✅ 配置验证通过")
            else:
                print("❌ 配置验证失败:")
                for error in result.errors:
                    print(f"   - {error}")
            
            if result.warnings:
                print("⚠️  警告:")
                for warning in result.warnings:
                    print(f"   - {warning}")
                    
        except Exception as e:
            print(f"❌ 验证配置失败: {e}")
    
    async def reload_config(self):
        """重新加载配置"""
        try:
            success = self.config_manager.reload_config()
            
            if success:
                print("✅ 配置重新加载成功")
            else:
                print("❌ 配置重新加载失败")
                
        except Exception as e:
            print(f"❌ 重新加载配置失败: {e}")
    
    async def watch_config(self):
        """监视配置文件变化"""
        try:
            print(f"👀 开始监视配置文件: {self.config_path}")
            print("按 Ctrl+C 停止监视")
            
            # 设置回调函数
            def on_config_change():
                print("🔄 配置文件已更改")
            
            self.watcher.set_callback(on_config_change)
            self.watcher.start_watching()
            
            # 保持运行
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 停止监视")
                self.watcher.stop_watching()
                
        except Exception as e:
            print(f"❌ 监视配置失败: {e}")
    
    async def export_config(self, output_file: str, output_format: str = "yaml"):
        """导出配置"""
        try:
            config = self.config_manager.load_config()
            
            if output_format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 配置导出成功: {output_file}")
            
        except Exception as e:
            print(f"❌ 导出配置失败: {e}")
    
    async def import_config(self, input_file: str):
        """导入配置"""
        try:
            # 读取配置文件
            if input_file.endswith('.json'):
                with open(input_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                with open(input_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            
            # 保存配置
            success = self.config_manager.save_config(config)
            
            if success:
                print(f"✅ 配置导入成功: {input_file}")
            else:
                print(f"❌ 配置导入失败: {input_file}")
                
        except Exception as e:
            print(f"❌ 导入配置失败: {e}")
    
    async def show_history(self):
        """显示配置历史"""
        try:
            history = self.rollback_manager.get_history()
            
            if not history:
                print("📝 暂无配置历史")
                return
            
            print("📝 配置历史:")
            for i, version in enumerate(history, 1):
                print(f"{i}. {version['timestamp']} - {version['version_id']}")
                print(f"   描述: {version.get('description', '无描述')}")
                print(f"   文件大小: {version.get('file_size', 0)} bytes")
                print()
                
        except Exception as e:
            print(f"❌ 显示历史失败: {e}")
    
    async def rollback(self, version_id: Optional[str] = None):
        """回滚配置"""
        try:
            if version_id:
                success = self.rollback_manager.rollback(version_id)
            else:
                # 回滚到上一个版本
                history = self.rollback_manager.get_history()
                if len(history) > 1:
                    success = self.rollback_manager.rollback(history[1]['version_id'])
                else:
                    print("❌ 没有可回滚的版本")
                    return
            
            if success:
                print("✅ 配置回滚成功")
            else:
                print("❌ 配置回滚失败")
                
        except Exception as e:
            print(f"❌ 回滚配置失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="配置管理命令行工具")
    parser.add_argument("--config", "-c", help="配置文件路径", default="config/config.yaml")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 显示配置
    show_parser = subparsers.add_parser("show", help="显示配置")
    show_parser.add_argument("--section", "-s", help="显示特定部分")
    show_parser.add_argument("--format", "-f", choices=["yaml", "json"], default="yaml", help="输出格式")
    
    # 设置配置
    set_parser = subparsers.add_parser("set", help="设置配置值")
    set_parser.add_argument("key", help="配置键")
    set_parser.add_argument("value", help="配置值")
    set_parser.add_argument("--section", "-s", help="配置部分")
    
    # 验证配置
    validate_parser = subparsers.add_parser("validate", help="验证配置")
    
    # 重新加载配置
    reload_parser = subparsers.add_parser("reload", help="重新加载配置")
    
    # 监视配置
    watch_parser = subparsers.add_parser("watch", help="监视配置文件变化")
    
    # 导出配置
    export_parser = subparsers.add_parser("export", help="导出配置")
    export_parser.add_argument("output", help="输出文件")
    export_parser.add_argument("--format", "-f", choices=["yaml", "json"], default="yaml", help="输出格式")
    
    # 导入配置
    import_parser = subparsers.add_parser("import", help="导入配置")
    import_parser.add_argument("input", help="输入文件")
    
    # 显示历史
    history_parser = subparsers.add_parser("history", help="显示配置历史")
    
    # 回滚配置
    rollback_parser = subparsers.add_parser("rollback", help="回滚配置")
    rollback_parser.add_argument("--version", "-v", help="版本ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建 CLI 实例
    cli = ConfigCLI(args.config)
    await cli.initialize()
    
    # 执行命令
    if args.command == "show":
        await cli.show_config(args.section, args.format)
    elif args.command == "set":
        await cli.set_config(args.key, args.value, args.section)
    elif args.command == "validate":
        await cli.validate_config()
    elif args.command == "reload":
        await cli.reload_config()
    elif args.command == "watch":
        await cli.watch_config()
    elif args.command == "export":
        await cli.export_config(args.output, args.format)
    elif args.command == "import":
        await cli.import_config(args.input)
    elif args.command == "history":
        await cli.show_history()
    elif args.command == "rollback":
        await cli.rollback(args.version)


if __name__ == "__main__":
    asyncio.run(main())