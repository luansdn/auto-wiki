#!/bin/bash
# Auto-Wiki 快速启动脚本

echo "📚 Auto-Wiki - GitHub 资源自动收集系统"
echo "========================================"
echo ""

# 检查 Python 依赖
echo "🔍 检查依赖..."
python3 -c "import requests" 2>/dev/null || {
    echo "❌ 缺少 requests 库，正在安装..."
    pip3 install requests -q
}

# 检查 LLM 连接
echo "🔍 检查 LLM 连接..."
curl -s http://localhost:8000/v1/models > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ LLM 服务正常"
else
    echo "⚠️  LLM 服务未启动，将使用简单分类"
fi

echo ""
echo "🚀 启动 Auto-Wiki..."
echo ""

python3 /home/luan/auto-wiki/run.py
