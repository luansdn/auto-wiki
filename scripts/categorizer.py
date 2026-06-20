#!/usr/bin/env python3
"""
LLM Categorizer & Summarizer
使用本地 LLM 对项目进行智能分类和摘要
"""

import json
import requests
import time
from pathlib import Path
import re

LLM_API_URL = "http://localhost:8000/v1/chat/completions"
LLM_MODEL = "Qwen3.6-35B-A3B-UD-IQ3_S.gguf"
CN_RE = re.compile(r"[\u4e00-\u9fff]")

# 过滤英文干扰文本
SKIP_PATTERNS = [
    r"Only Chinese", r"Let['s]?\s", r"Count", r"remove the English",
    r"need to make sure", r"would be", r"keeping", r"ensure t",
    r"Total is", r"aim for", r"per typical", r"Fits perfectly",
    r"Strictly speaking", r"[\d]+\s*(chars|characters)", r"Note:",
    r"I['\u2019]ll", r"Neutral", r"keep it as",
    r"Formulate Features", r"Determine Features",
    r"Mental Draft", r"Mental Refinement",
]

ENG_PATTERN = re.compile(r"(?:^|\s)\([A-Za-z][A-Za-z0-9\s/&,;.\-']+\)")


def _clean_text(text):
    """清理文本中的英文注解"""
    text = ENG_PATTERN.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def call_llm(prompt, max_tokens=500):
    """调用本地 LLM，支持自动提取 reasoning_content 中的答案"""
    headers = {"Content-Type": "application/json"}
    system_prompt = "请直接输出答案，不要推理过程，不要计数。只输出中文文字。"

    data = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "top_p": 0.9,
    }

    try:
        resp = requests.post(LLM_API_URL, headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        message = result["choices"][0]["message"]
        content = message.get("content", "").strip()
        reasoning = message.get("reasoning_content", "").strip()

        if content and len(content) > 10:
            return _clean_text(content)

        if reasoning:
            extracted = _extract_from_reasoning(reasoning)
            if extracted:
                return extracted

        return content if content else None
    except Exception as e:
        print(f"  LLM 调用失败: {e}")
        return None


def _extract_from_reasoning(reasoning):
    """从 reasoning_content 中提取中文答案"""
    for marker in ["**Draft", "Draft Generation", "Refinement):", "Formulate Features", "Determine Features"]:
        if marker in reasoning:
            pos = reasoning.find(marker)
            after = reasoning[pos:]
            skip_line = after.find("\n")
            block = after[skip_line:].strip() if skip_line > 0 else after.strip()
            next_sec = re.search(r"\n\d+\.\s+\*\*", block)
            cc = re.search(r"\n\s*\*?\(?Count", block)
            end = len(block)
            if next_sec:
                end = min(end, next_sec.start())
            if cc:
                end = min(end, cc.start())
            text = block[:end].strip()
            parts = []
            for l in text.split("\n"):
                l = l.strip()
                l = re.sub(r"^-\s+\*.*?\*\s*", "", l)
                l = re.sub(r"^-\s+", "", l)
                l = re.sub(r"^`[^`]+`\s*", "", l)
                l = re.sub(r"^[A-Za-z\s/&]+:\s*", "", l)
                l = l.strip()
                cn = len(CN_RE.findall(l))
                if cn >= 10 and not any(re.search(p, l) for p in SKIP_PATTERNS):
                    parts.append(l)
            if parts:
                result = " ".join(parts)
                if len(CN_RE.findall(result)) >= 15:
                    return _clean_text(result)

    bullet_lines = []
    for l in reasoning.split("\n"):
        l = l.strip()
        if l.startswith("•") and any(re.search(p, l) for p in SKIP_PATTERNS):
            continue
        if l.startswith("•"):
            cn = len(CN_RE.findall(l))
            if cn >= 5:
                bullet_lines.append(l)
    if bullet_lines:
        return "\n".join(bullet_lines)

    paragraphs = reasoning.split("\n\n")
    best = ""
    for p in reversed(paragraphs):
        p = p.strip()
        if re.match(r"^\d+\..*:\s*$", p):
            continue
        if any(re.search(pat, p) for pat in SKIP_PATTERNS):
            continue
        cn = len(CN_RE.findall(p))
        if cn >= 50:
            clean = re.sub(r"^-\s+\*.*?\*\s*", "", p)
            clean = re.sub(r"^-\s+", "", clean)
            clean = re.sub(r"^`[^`]+`\s*", "", clean)
            clean = re.sub(r"^[A-Za-z\s/&]+:\s*", "", clean)
            clean = re.sub(r"\s*\*?\(Count.*?\)", "", clean)
            if len(clean) > len(best):
                best = clean
    return _clean_text(best) if best else None


CATEGORIZE_PROMPT = """根据项目信息，选择最合适的分类。只输出分类名称，不要任何解释。

项目: {name}
描述: {description}
标签: {topics}
语言: {language}
Stars: {stars}

可选分类:
- AI/机器学习
- Web开发
- DevOps/工具
- 数据科学
- 移动开发
- 区块链/Web3
- 游戏开发
- 系统/底层
- 安全/密码学
- 教育/学习
- 其他

分类:"""

DETAILED_INTRO_PROMPT = """为以下 GitHub 项目写一段详细的项目介绍（150-300字）。直接输出中文介绍文字，不要其他格式。

要求:
1. 第一句话概括项目是什么
2. 然后说明核心功能和主要特点
3. 最后说明适用场景和受众

项目: {name}
GitHub: https://github.com/{full_name}
描述: {description}
Stars: {stars:,}
Forks: {forks:,}
语言: {language}
标签: {topics}
License: {license}

介绍:"""

FEATURES_PROMPT = """为以下 GitHub 项目列出主要特性（5-8个）。直接输出列表，用"• "开头，不要其他内容。

项目: {name}

特性:"""


def categorize_with_llm(repo):
    prompt = CATEGORIZE_PROMPT.format(
        name=repo.get("full_name", ""),
        description=repo.get("description", "无描述"),
        topics=", ".join(repo.get("topics", [])),
        language=repo.get("language", "未知"),
        stars=repo.get("stars", 0),
    )
    result = call_llm(prompt, max_tokens=100)
    if result and len(result) < 50:
        return result
    return repo.get("category", "其他")


def generate_detailed_intro(repo):
    prompt = DETAILED_INTRO_PROMPT.format(
        name=repo.get("full_name", ""),
        full_name=repo.get("full_name", ""),
        description=repo.get("description", "无描述"),
        stars=repo.get("stars", 0),
        forks=repo.get("forks", 0),
        language=repo.get("language", "未知"),
        topics=", ".join(repo.get("topics", [])) or "无",
        license=repo.get("license", "未知"),
    )
    result = call_llm(prompt, max_tokens=1000)
    return result if result and len(result) > 20 else None


def generate_features(repo):
    prompt = FEATURES_PROMPT.format(name=repo.get("full_name", ""))
    result = call_llm(prompt, max_tokens=800)
    return result if result else None


def process_repos(repos, use_llm=True):
    print(f"\nLLM 处理 ({len(repos)} 个项目)...")
    for i, repo in enumerate(repos):
        if i % 10 == 0:
            print(f"  进度: {i}/{len(repos)}")
        if use_llm:
            intro = generate_detailed_intro(repo)
            if intro:
                repo["summary"] = intro
                print(f"    {repo['full_name']}: 已生成简介 ({len(intro)}字)")
            else:
                repo["summary"] = repo.get("description", "暂无描述")

            features = generate_features(repo)
            if features:
                repo["features"] = features

            time.sleep(1.0)
        else:
            repo["summary"] = repo.get("description", "暂无描述")
    print("LLM 处理完成")
    return repos


if __name__ == "__main__":
    import sys
    test_result = call_llm("用50字介绍 vinta/awesome-python 是什么")
    if test_result:
        print(f"LLM 连接正常: {test_result[:80]}")
    else:
        print("LLM 连接失败")
