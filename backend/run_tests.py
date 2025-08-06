#!/usr/bin/env python3
"""
测试运行脚本
"""
import subprocess
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 切换到后端目录
os.chdir(project_root / 'backend')


def run_tests(test_type='all'):
    """运行测试
    
    Args:
        test_type: 测试类型 ('all', 'unit', 'integration', 'api')
    """
    print(f"🧪 运行 {test_type} 测试...")
    
    # 基础 pytest 命令
    cmd = ['python', '-m', 'pytest']
    
    # 根据测试类型添加选项
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'api':
        cmd.extend(['-m', 'api'])
    elif test_type == 'config':
        cmd.extend(['-m', 'config'])
    
    # 添加通用选项
    cmd.extend([
        '-v',
        '--tb=short',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html',
        'tests/'
    ])
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ {test_type} 测试通过!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {test_type} 测试失败: {e}")
        return False


def run_linting():
    """运行代码检查"""
    print("🔍 运行代码检查...")
    
    # 运行 ruff
    try:
        subprocess.run(['python', '-m', 'ruff', 'check', 'src/'], check=True)
        print("✅ Ruff 检查通过!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ruff 检查失败: {e}")
        return False
    
    # 运行 mypy
    try:
        subprocess.run(['python', '-m', 'mypy', 'src/'], check=True)
        print("✅ MyPy 检查通过!")
    except subprocess.CalledProcessError as e:
        print(f"❌ MyPy 检查失败: {e}")
        return False
    
    return True


def run_format_check():
    """运行代码格式检查"""
    print("📝 检查代码格式...")
    
    try:
        subprocess.run(['python', '-m', 'black', '--check', 'src/'], check=True)
        print("✅ 代码格式正确!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 代码格式不正确: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行测试和代码检查')
    parser.add_argument('--test-type', choices=['all', 'unit', 'integration', 'api', 'config'], 
                       default='all', help='测试类型')
    parser.add_argument('--lint', action='store_true', help='运行代码检查')
    parser.add_argument('--format', action='store_true', help='检查代码格式')
    parser.add_argument('--all', action='store_true', help='运行所有检查')
    
    args = parser.parse_args()
    
    success = True
    
    if args.all or args.test_type:
        if not run_tests(args.test_type):
            success = False
    
    if args.all or args.lint:
        if not run_linting():
            success = False
    
    if args.all or args.format:
        if not run_format_check():
            success = False
    
    if not args.all and not args.test_type and not args.lint and not args.format:
        # 默认运行所有检查
        success = run_tests('all') and run_linting() and run_format_check()
    
    if success:
        print("\n🎉 所有检查通过!")
        sys.exit(0)
    else:
        print("\n💥 部分检查失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()