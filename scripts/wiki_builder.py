#!/usr/bin/env python3
"""
Wiki Builder
将收集的项目数据生成 Markdown Wiki
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Wiki 输出目录
WIKI_DIR = Path(__file__).parent.parent / "wiki"
WIKI_DIR.mkdir(exist_ok=True)

# 分类描述
CATEGORY_DESCRIPTIONS = {
    "AI/机器学习": "人工智能、机器学习、深度学习、LLM 相关项目",
    "Web开发": "前端、后端、框架、全栈 Web 开发",
    "DevOps/工具": "运维工具、CI/CD、命令行工具、效率工具",
    "数据科学": "数据分析、可视化、数据库、数据工程",
    "移动开发": "Android、iOS、Flutter、React Native",
    "区块链/Web3": "加密货币、DeFi、NFT、Web3 基础设施",
    "游戏开发": "游戏引擎、游戏工具、2D/3D 开发",
    "系统/底层": "操作系统、编译器、系统工具、性能优化",
    "安全/密码学": "安全工具、密码学、审计、渗透测试",
    "教育/学习": "教程、学习资源、文档、Awesome 列表",
    "其他": "其他未分类项目"
}

def load_repos(data_file=None):
    """加载项目数据"""
    if data_file is None:
        data_file = Path(__file__).parent.parent / "data" / "latest.json"
    
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_main_index(repos):
    """生成主索引页"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 统计分类
    categories = {}
    for repo in repos:
        cat = repo.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(repo)
    
    # 生成 Markdown
    content = f"""# 📚 Auto-Wiki 知识库

> 自动收集 GitHub 优质项目，智能分类整理
> 
> 最后更新: {now}
> 项目总数: {len(repos)}

---

## 📊 分类导航

"""
    
    for cat, cat_repos in sorted(categories.items(), key=lambda x: -len(x[1])):
        desc = CATEGORY_DESCRIPTIONS.get(cat, "")
        safe_cat_name = cat.replace("/", "_")
        content += f"### [{cat}](categories/{safe_cat_name}.md)\n"
        content += f"{desc} ({len(cat_repos)} 个项目)\n\n"
    
    content += """---

## 🔥 热门项目 (按 Stars 排序)

"""
    
    # 按 Stars 排序取前20
    top_repos = sorted(repos, key=lambda x: x.get("stars", 0), reverse=True)[:20]
    for i, repo in enumerate(top_repos, 1):
        stars = repo.get("stars", 0)
        stars_display = f"⭐ {stars:,}" if stars > 0 else ""
        gh_link = f"https://github.com/{repo['full_name']}"
        intro = repo.get("summary", repo.get("description", "暂无描述"))[:80]
        content += f"{i}. **[{repo['full_name']}](repos/{repo['owner']}_{repo['name']}.md)** [{repo['full_name']}]({gh_link}) {stars_display}\n"
        content += f"   {intro}\n\n"
    
    content += """---

## 📖 使用说明

- 点击分类查看该类别下所有项目
- 点击项目名称查看详细信息
- 数据每日自动更新

"""
    
    output_file = WIKI_DIR / "README.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 主索引生成: {output_file}")
    return output_file

def generate_category_pages(repos):
    """生成分类页面"""
    categories_dir = WIKI_DIR / "categories"
    categories_dir.mkdir(exist_ok=True)
    
    # 按分类分组
    categories = {}
    for repo in repos:
        cat = repo.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(repo)
    
    for cat, cat_repos in categories.items():
        content = f"""# {cat}

> {CATEGORY_DESCRIPTIONS.get(cat, '')}
> 
> 项目数量: {len(cat_repos)}

---

"""
        
        # 按 Stars 排序
        sorted_repos = sorted(cat_repos, key=lambda x: x.get("stars", 0), reverse=True)
        
        for repo in sorted_repos:
            stars = repo.get("stars", 0)
            stars_display = f"⭐ {stars:,}" if stars > 0 else ""
            lang = repo.get("language", "")
            lang_display = f"🌐 {lang}" if lang else ""
            
            gh_link = f"https://github.com/{repo['full_name']}"
            intro = repo.get("summary", repo.get("description", "暂无描述"))[:100]
            content += f"## [{repo['full_name']}]({gh_link}) [详细](../repos/{repo['owner']}_{repo['name']}.md)\n\n"
            content += f"{stars_display} {lang_display}\n\n"
            content += f"{intro}\n\n"
            content += "---\n\n"
        
        # 将分类名中的 / 替换为 _ 以避免路径问题
        safe_cat_name = cat.replace("/", "_")
        output_file = categories_dir / f"{safe_cat_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"  📄 分类页面: {cat} ({len(cat_repos)} 个项目)")

def generate_repo_pages(repos):
    """生成项目详情页"""
    repos_dir = WIKI_DIR / "repos"
    repos_dir.mkdir(exist_ok=True)
    
    for repo in repos:
        owner = repo.get("owner", "unknown")
        name = repo.get("name", "unknown")
        
        # 构建基本信息行
        info_rows = ""
        info_rows += f"| ⭐ Stars | {repo.get('stars', 0):,} |\n"
        info_rows += f"| 🍴 Forks | {repo.get('forks', 0):,} |\n"
        info_rows += f"| 🌐 Language | {repo.get('language', '未知')} |\n"
        info_rows += f"| 📜 License | {repo.get('license', '未知')} |\n"
        
        if repo.get("updated_at"):
            info_rows += f"| 📅 Updated | {repo['updated_at'][:10]} |\n"
        
        if repo.get("pushed_at"):
            info_rows += f"| 📅 最近推送 | {repo['pushed_at'][:10]} |\n"
        
        topics = repo.get("topics", [])
        if topics:
            topics_str = ", ".join(topics)
        else:
            topics_str = "无"
        
        content = f"""# {repo['full_name']}

> {repo.get('description', '暂无描述')}

---

## 基本信息

| 属性 | 值 |
|------|-----|
{info_rows.rstrip()}

## 项目介绍

{repo.get('summary', repo.get('description', '暂无详细介绍'))}
"""
        
        # 加入特性列表
        if repo.get("features"):
            content += f"""

## 主要特性

{repo['features']}
"""
        
        # 加入链接
        content += f"""

## 相关链接

- 🔗 GitHub: https://github.com/{repo['full_name']}
"""
        
        if repo.get("homepage"):
            content += f"- 🌐 Homepage: {repo['homepage']}\n"
        
        content += f"""

---

*数据收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        
        output_file = repos_dir / f"{owner}_{name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    print(f"  📄 项目页面: {len(repos)} 个")

def build_wiki(data_file=None):
    """构建完整 Wiki"""
    print("📚 开始构建 Wiki...")
    
    repos = load_repos(data_file)
    print(f"  📊 加载项目: {len(repos)} 个")
    
    generate_main_index(repos)
    generate_category_pages(repos)
    generate_repo_pages(repos)
    
    print("\n✅ Wiki 构建完成!")
    print(f"📁 输出目录: {WIKI_DIR}")
    return WIKI_DIR

if __name__ == "__main__":
    build_wiki()
