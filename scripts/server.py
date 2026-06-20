#!/usr/bin/env python3
"""
Wiki Web Server
轻量级 Wiki 浏览器
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path
from urllib.parse import unquote

# Wiki 目录
WIKI_DIR = Path(__file__).parent.parent / "wiki"

class WikiHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WIKI_DIR), **kwargs)
    
    def do_GET(self):
        # 解析路径
        path = unquote(self.path)
        
        # 默认跳转到 README
        if path == "/":
            self.path = "/README.md"
            path = "/README.md"
        
        # 如果请求 .md 文件，返回渲染后的 HTML
        if path.endswith(".md"):
            self.serve_markdown(path)
        else:
            super().do_GET()
    
    def serve_markdown(self, path):
        """将 Markdown 渲染为简单 HTML"""
        md_file = WIKI_DIR / path.lstrip("/")
        
        if not md_file.exists():
            self.send_error(404, "File not found")
            return
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 简单的 Markdown -> HTML 转换
        html = self.md_to_html(content, path)
        
        # 编码为 UTF-8
        html_bytes = html.encode("utf-8")
        
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)
    
    def md_to_html(self, md_content, current_path):
        """简单的 Markdown 转 HTML"""
        lines = md_content.split("\n")
        html_lines = []
        in_table = False
        in_list = False
        
        for line in lines:
            # 标题
            if line.startswith("# "):
                html_lines.append(f"<h1>{self.process_inline(line[2:])}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{self.process_inline(line[3:])}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{self.process_inline(line[4:])}</h3>")
            # 水平线
            elif line.strip() == "---":
                html_lines.append("<hr>")
            # 表格
            elif line.startswith("|"):
                if not in_table:
                    html_lines.append("<table>")
                    in_table = True
                if "---" in line:
                    continue
                cells = [c.strip() for c in line.split("|")[1:-1]]
                row = "".join(f"<td>{self.process_inline(c)}</td>" for c in cells)
                html_lines.append(f"<tr>{row}</tr>")
            else:
                if in_table:
                    html_lines.append("</table>")
                    in_table = False
                # 列表
                if line.startswith("- "):
                    if not in_list:
                        html_lines.append("<ul>")
                        in_list = True
                    html_lines.append(f"<li>{self.process_inline(line[2:])}</li>")
                else:
                    if in_list:
                        html_lines.append("</ul>")
                        in_list = False
                    # 普通段落
                    if line.strip():
                        processed = self.process_inline(line)
                        html_lines.append(f"<p>{processed}</p>")
        
        if in_table:
            html_lines.append("</table>")
        if in_list:
            html_lines.append("</ul>")
        
        body = "\n".join(html_lines)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Wiki</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.8;
            color: #333;
            background: #fafafa;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        td {{ border: 1px solid #ddd; padding: 8px; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
        .nav {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        blockquote {{ border-left: 4px solid #3498db; margin: 0; padding: 10px 20px; color: #555; background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">&#128218; 首页</a>
    </div>
    {body}
</body>
</html>"""
    
    def process_inline(self, text):
        """处理行内格式"""
        import re
        from urllib.parse import quote
        # 链接 [text](url) -> <a href="url">text</a>
        def encode_link(m):
            url = m.group(2).strip()
            # 只对相对路径（非 http/https/mailto 开头）进行 URL 编码
            if not url.startswith(("http://", "https://", "mailto:", "#")):
                url = quote(url, safe='/:@!$&\'()*+,;=-._~')
            return f'<a href="{url}">{m.group(1)}</a>'
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', encode_link, text)
        # 粗体
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # 行内代码
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        return text
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[Wiki] {args[0]}")

def run_server(port=8888):
    """启动 Wiki 服务"""
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), WikiHandler) as httpd:
        print(f"📚 Wiki 服务器启动")
        print(f"🌐 地址: http://localhost:{port}")
        print(f"📁 Wiki 目录: {WIKI_DIR}")
        print("按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️ 服务已停止")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    run_server(port)
