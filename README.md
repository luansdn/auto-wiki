# Auto-Wiki

自动收集 GitHub 优质项目，智能分类整理到本地 Wiki。

## 功能

- 📊 自动爬取 GitHub Trending 和 Awesome 列表
- 🤖 使用本地 LLM 进行智能分类和摘要
- 📚 生成结构化的 Markdown Wiki
- 🌐 轻量级 Web 浏览器

## 快速开始

```bash
# 启动完整流程（爬取 + LLM分类 + 生成Wiki）
python3 run.py

# 或者只启动 Wiki 浏览器
python3 scripts/server.py 8888
```

访问 http://localhost:8888 查看 Wiki

## 项目结构

```
auto-wiki/
├── scripts/
│   ├── scraper.py       # GitHub 爬虫
│   ├── categorizer.py   # LLM 分类器
│   ├── wiki_builder.py  # Wiki 生成器
│   └── server.py        # Web 服务器
├── data/                # 爬取的数据
├── wiki/                # 生成的 Wiki
└── run.py               # 主程序
```

## 依赖

- Python 3.8+
- requests
- llama-server (本地 LLM，可选)

## 配置

编辑 `scripts/categorizer.py` 中的 `CATEGORY_KEYWORDS` 可自定义分类规则。

## 定时更新

添加 crontab 定时任务：

```bash
# 每天凌晨 2 点更新
0 2 * * * cd /home/luan/auto-wiki && python3 run.py >> /tmp/auto-wiki.log 2>&1
```
