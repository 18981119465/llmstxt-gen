#!/usr/bin/env python3
"""
配置管理命令行工具入口点
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.cli import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())