#!/usr/bin/env python3
"""
Auto-Wiki 主程序
自动收集、分类、整理 GitHub 优质资源
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scraper import run_full_scrape
from categorizer import process_repos
from wiki_builder import build_wiki

def main():
    print("=" * 60)
    print("📚 Auto-Wiki - GitHub 资源自动收集系统")
    print("=" * 60)
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 爬取数据
    print("📊 步骤 1/3: 爬取 GitHub 资源")
    print("-" * 40)
    repos = run_full_scrape()
    
    # 2. LLM 分类和摘要
    print("\n🤖 步骤 2/3: LLM 智能分类")
    print("-" * 40)
    repos = process_repos(repos, use_llm=True)
    
    # 保存处理后的数据
    data_file = Path(__file__).parent / "data" / "latest.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    
    # 3. 生成 Wiki
    print("\n📚 步骤 3/3: 生成 Wiki")
    print("-" * 40)
    wiki_dir = build_wiki(data_file)
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ Auto-Wiki 更新完成!")
    print("=" * 60)
    print(f"📊 收集项目: {len(repos)} 个")
    print(f"📁 Wiki 目录: {wiki_dir}")
    print()
    print("🌐 启动 Wiki 服务器:")
    print(f"   python3 {Path(__file__).parent / 'scripts' / 'server.py'}")
    print()

if __name__ == "__main__":
    main()
