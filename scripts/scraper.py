#!/usr/bin/env python3
"""
GitHub Trending & Awesome List Scraper
自动收集 GitHub Trending 项目和 Awesome 列表
"""

import json
import re
import time
import os
import requests
from datetime import datetime
from pathlib import Path

# 数据存储目录
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 需要过滤的无用 topic
USELESS_TOPICS = {
    "awesome", "awesome-list", "awesome-lists",
    "list", "lists", "collection", "collections", "resources", "resource",
    "hacktoberfest", "hacktoberfest-accepted", "first-contributions",
    "handbook", "guide", "curated", "awesome-repo", "tutorial",
    "python", "go", "javascript", "java", "c++", "cpp", "typescript",
    "rust", "shell", "html", "css", "php",
    "programming", "dev", "developer", "coding", "code",
    "tool", "tools", "library", "libraries",
    "example", "examples", "demo", "demos", "sample", "samples",
    "cli", "terminal", "command-line", "command-line-tools",
    "opensource", "open-source", "oss",
    "beginner", "beginners", "beginner-friendly",
    "ajax", "xml", "json", "rest", "api", "rest-api",
}

# 精选种子源: Go Web Framework Stars (mingrammer/go-web-framework-stars)
CURATED_GO_WEB_REPOS = [
    "beego/beego", "gobuffalo/buffalo", "labstack/echo", "gofiber/fiber",
    "gin-gonic/gin", "NYTimes/gizmo", "ant0ine/go-json-rest", "goadesign/goa",
    "go-macaron/macaron", "revel/revel", "go-martini/martini", "gorilla/mux",
    "goji/goji", "gocraft/web", "pilu/traffic", "lunny/tango",
    "emicklei/go-restful", "go-chi/chi", "julienschmidt/httprouter", "ivpusic/neo",
    "valyala/fasthttp", "tideland/gorest", "bnkamalesh/webgo", "go-swagger/go-swagger",
    "labstack/armor", "devfeel/dotweb", "go-kit/kit", "tmaiaroto/aegis",
    "rs/rest-layer", "vardius/gorouter", "go-aah/aah", "ponzu-cms/ponzu",
    "gramework/gramework", "gogf/gf", "tusharsoni/copper",
    "go-goyave/goyave", "abahmed/gearbox", "yoyofx/yoyogo", "go-kratos/kratos",
    "zeromicro/go-zero", "encoredev/encore", "gofr-dev/gofr", "apex/up",
    "go-zoo/bone",
]

# 精选种子源: 安全/黑客工具 (热门安全工具)
CURATED_SECURITY_REPOS = [
    "sqlmapproject/sqlmap", "rapid7/metasploit-framework", "nmap/nmap",
    "openwall/john", "hashcat/hashcat", "aircrack-ng/aircrack-ng",
    "sullo/nikto", "vanhauser-thc/thc-hydra", "bettercap/bettercap",
    "OJ/gobuster", "VirusTotal/yara",
    "volatilityfoundation/volatility", "BC-SECURITY/Empire",
    "BloodHoundAD/BloodHound", "laramies/theHarvester",
    "n1nj4sec/pupy", "nmap/ncrack",
    "wpscanteam/wpscan", "urbanadventurer/WhatWeb",
    "sherlock-project/sherlock", "twintproject/twint",
    "smicallef/spiderfoot", "projectdiscovery/nuclei",
    "projectdiscovery/subfinder", "projectdiscovery/httpx",
    "projectdiscovery/naabu", "lanmaster53/recon-ng",
    "darkoperator/dnsrecon", "cuckoosandbox/cuckoo",
    "NationalSecurityAgency/ghidra", "radareorg/radare2",
    "ReFirmLabs/binwalk", "longld/peda", "pwndbg/pwndbg",
    "hugsy/gef", "x64dbg/x64dbg",
    "mandiant/flare-vm", "mandiant/red_team_tool_countermeasures",
    "OWASP/CheatSheetSeries",
    "OWASP/wstg", "OWASP/owasp-mstg",
    "zaproxy/zaproxy",
    "b374k/b374k", "epinna/weevely3", "byt3bl33d3r/CrackMapExec",
    "trustedsec/social-engineer-toolkit", "trustedsec/ptf",
    "mubix/post-exploitation", "sleuthkit/sleuthkit",
    "gentilkiwi/mimikatz", "PowerShellMafia/PowerSploit",
    "samratashok/nishang", "Veil-Framework/Veil",
    "TheKingOfDuck/fuzzDicts", "danielmiessler/SecLists",
    "bregman-arie/devops-exercises", "andrew-d/static-binaries",
    "jivoi/awesome-osint",
    "drduh/macOS-Security-and-Privacy-Guide",
    "OWASP/Amass", "digininja/DVWA", "webpwnized/mutillidae",
    "juice-shop/juice-shop", "maurosoria/dirsearch",
    "ffuf/ffuf", "tomnomnom/httprobe", "tomnomnom/waybackurls",
    "lc/gau", "EdOverflow/bugbounty-cheatsheet",
    "nahamsec/recon_profile",
    "swisskyrepo/PayloadsAllTheThings",
    "nettitude/PoshC2", "fuzzdb-project/fuzzdb",
]

# 分类关键词映射
CATEGORY_KEYWORDS = {
    "AI/机器学习": ["ai", "machine-learning", "deep-learning", "neural", "llm", "gpt", "transformer", "pytorch", "tensorflow", "model", "nlp", "computer-vision", "reinforcement-learning", "rag", "agent"],
    "Web开发": ["web", "frontend", "backend", "javascript", "typescript", "react", "vue", "node", "django", "flask", "fastapi", "nextjs", "svelte", "angular"],
    "DevOps/工具": ["docker", "kubernetes", "ci", "cd", "devops", "monitoring", "logging", "automation", "terraform", "ansible", "jenkins", "github-actions", "ci-cd"],
    "数据科学": ["data", "analytics", "visualization", "pandas", "numpy", "jupyter", "notebook", "database", "sql", "etl", "data-engineering"],
    "移动开发": ["mobile", "android", "ios", "flutter", "react-native", "swift", "kotlin", "app", "mobile-app"],
    "区块链/Web3": ["blockchain", "web3", "crypto", "ethereum", "bitcoin", "defi", "nft", "solidity", "smart-contract"],
    "游戏开发": ["game", "game-engine", "unity", "unreal", "godot", "pixel", "2d", "3d", "gaming"],
    "系统/底层": ["system", "kernel", "os", "compiler", "virtualization", "performance", "memory", "rust", "c++", "c"],
    "安全/黑客工具": ["security", "crypto", "cipher", "vulnerability", "audit", "pentest", "hacking", "encryption", "exploit", "penetration", "payload", "crack", "hash", "recon", "osint", "forensic", "malware", "trojan", "backdoor", "injection", "xss", "sqlmap", "nmap", "wireshark", "metasploit", "burpsuite", "hydra", "john", "ghidra", "radare", "mimikatz"],
    "教育/学习": ["tutorial", "course", "education", "learning", "study", "learn", "practice", "interview"],
}


def filter_topics(topics):
    """过滤无用的 topic"""
    if not topics:
        return []
    filtered = [t for t in topics if t.lower() not in USELESS_TOPICS]
    return filtered[:10]  # 最多保留 10 个有用的


def get_github_headers():
    """获取 GitHub API 请求头 (支持 token 认证以提升限额)"""
    import os
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AutoWiki-Bot/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def scrape_github_trending(language="", since="daily"):
    """爬取 GitHub Trending 页面"""
    url = f"https://github.com/trending/{language}?since={since}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        # 简单解析 HTML 提取项目信息
        repos = []
        # 匹配 repo 链接
        repo_pattern = r'<h2 class="h3 lh-condensed">.*?<a href="/([^"]+)"'
        matches = re.findall(repo_pattern, resp.text, re.DOTALL)
        
        for match in matches[:25]:  # 取前25个
            parts = match.strip("/").split("/")
            if len(parts) == 2:
                repos.append({
                    "full_name": f"{parts[0]}/{parts[1]}",
                    "owner": parts[0],
                    "name": parts[1],
                    "source": "trending",
                    "language": language or "all"
                })
        
        return repos
    except Exception as e:
        print(f"  ❌ 爬取 Trending 失败 ({language}): {e}")
        return []

def scrape_github_awesome(category="awesome"):
    """爬取 Awesome 列表"""
    url = f"https://github.com/search?q={category}&type=repositories&sort=stars&order=desc"
    headers = get_github_headers()
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        repos = []
        # 匹配 repo 链接
        repo_pattern = r'href="/([^"]+?/[^"]+?)"\s+class="Link"'
        matches = re.findall(repo_pattern, resp.text)
        
        for match in matches[:20]:
            parts = match.strip("/").split("/")
            if len(parts) == 2:
                repos.append({
                    "full_name": f"{parts[0]}/{parts[1]}",
                    "owner": parts[0],
                    "name": parts[1],
                    "source": "awesome-search",
                })
        
        return repos
    except Exception as e:
        print(f"  ❌ 爬取 Awesome 失败 ({category}): {e}")
        return []

def get_repo_details(owner, name):
    """获取仓库详细信息"""
    url = f"https://api.github.com/repos/{owner}/{name}"
    headers = get_github_headers()
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # 更好的 License 提取
        license_str = "未知"
        if data.get("license"):
            lic = data["license"]
            raw = lic.get("spdx_id", "") or lic.get("name", "")
            if raw and raw not in ("NOASSERTION", "NONE", "null", "None"):
                license_str = raw

        # 更好的 Homepage 提取
        homepage = data.get("homepage", "") or data.get("website", "") or ""
        
        return {
            "description": data.get("description", "") or "暂无描述",
            "stars": data.get("stargazers_count", 0) or 0,
            "forks": data.get("forks_count", 0) or 0,
            "language": data.get("language", "") or "未知",
            "topics": filter_topics(data.get("topics", [])),
            "updated_at": data.get("updated_at", ""),
            "homepage": homepage,
            "license": license_str,
            "size": data.get("size", 0),
            "archived": data.get("archived", False),
            "default_branch": data.get("default_branch", ""),
            "pushed_at": data.get("pushed_at", ""),
            "created_at": data.get("created_at", ""),
            "open_issues": data.get("open_issues_count", 0) or 0,
        }
    except Exception as e:
        print(f"  ❌ 获取仓库详情失败 ({owner}/{name}): {e}")
        return {}

def get_readme_content(owner, name, max_bytes=2000):
    """获取仓库 README 内容"""
    url = f"https://api.github.com/repos/{owner}/{name}/readme"
    headers = get_github_headers()
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        import base64
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
        
        # 取前 max_bytes 字符
        content = content[:max_bytes].strip()
        return content
    except Exception as e:
        print(f"  ⚠️ 获取 README 失败 ({owner}/{name}): {e}")
        return ""

def categorize_repo(repo):
    """根据描述和主题自动分类"""
    text = f"{repo.get('description', '')} {' '.join(repo.get('topics', []))} {repo.get('language', '')}".lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "其他"

def scrape_curated_repos(source="all"):
    """爬取精选种子源列表中的仓库
    source: "go-web" | "security" | "all"
    """
    repos = []
    lists = []
    if source in ("go-web", "all"):
        lists.append(("curated-go-web", CURATED_GO_WEB_REPOS))
    if source in ("security", "all"):
        lists.append(("curated-security", CURATED_SECURITY_REPOS))
    for src_name, repo_list in lists:
        for full_name in repo_list:
            parts = full_name.split("/")
            if len(parts) == 2:
                repos.append({
                    "full_name": full_name,
                    "owner": parts[0],
                    "name": parts[1],
                    "source": src_name,
                })
    return repos

def run_full_scrape():
    """完整爬取流程"""
    print("🔍 开始爬取 GitHub 数据...")
    seen_names = set()
    all_repos = []
    
    # 1. 爬取 Trending
    print("  📊 步骤 1: 爬取 Trending")
    for lang in ["", "python", "javascript", "typescript", "go", "rust", "java", "c++", "shell"]:
        trending = scrape_github_trending(lang)
        print(f"    {lang or 'all'}: {len(trending)} projects")
        for repo in trending:
            key = repo["full_name"].lower()
            if key not in seen_names:
                seen_names.add(key)
                all_repos.append(repo)
    
    # 2. 爬取 Awesome 列表
    print("  📊 步骤 2: 爬取 Awesome 列表")
    awesome_categories = [
        "awesome", "machine learning", "python", "javascript", "go", "rust",
        "devops", "data science", "ai", "web development", "frontend",
        "backend", "mobile", "blockchain", "security", "tools",
    ]
    for cat in awesome_categories:
        awesome = scrape_github_awesome(cat)
        print(f"    {cat}: {len(awesome)} projects")
        for repo in awesome:
            key = repo["full_name"].lower()
            if key not in seen_names:
                seen_names.add(key)
                all_repos.append(repo)
    
    # 3. 爬取精选种子源
    print("  📊 步骤 3: 爬取精选种子源")
    curated_go = scrape_curated_repos("go-web")
    print(f"    go-web-framework-stars: {len(curated_go)} projects")
    for repo in curated_go:
        key = repo["full_name"].lower()
        if key not in seen_names:
            seen_names.add(key)
            all_repos.append(repo)
    curated_sec = scrape_curated_repos("security")
    print(f"    security-tools: {len(curated_sec)} projects")
    for repo in curated_sec:
        key = repo["full_name"].lower()
        if key not in seen_names:
            seen_names.add(key)
            all_repos.append(repo)

    # 4. 获取详情
    print(f"  📊 步骤 4: 获取 {len(all_repos)} 个仓库详情")
    results = []
    for i, repo in enumerate(all_repos):
        if i % 10 == 0:
            print(f"    进度: {i}/{len(all_repos)}")
        details = get_repo_details(repo["owner"], repo["name"])
        if details:
            repo.update(details)
            repo["category"] = categorize_repo(repo)
            results.append(repo)
        time.sleep(0.5)  # GitHub API 限速
    
    # 按 stars 排序
    results.sort(key=lambda x: x.get("stars", 0), reverse=True)
    
    print(f"\n✅ 爬取完成: {len(results)} 个仓库")
    return results

if __name__ == "__main__":
    repos = run_full_scrape()
    
    # 保存
    data_file = DATA_DIR / "latest.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"💾 已保存到 {data_file}")
