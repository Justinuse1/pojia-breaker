"""
pojia-breaker — Vercel Python entrypoint
Landing page: project intro + releases. No secrets, no state.
"""
import json
from http.server import BaseHTTPRequestHandler


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pojia-breaker — LLM Red-Team Framework</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; margin: 0; }
  body {
    font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #0a0a0f; color: #e8e8ef; min-height: 100vh;
    display: flex; align-items: center; justify-content: center; padding: 24px;
  }
  .card { max-width: 720px; }
  h1 { font-size: 2.2rem; letter-spacing: .5px; }
  h1 span { color: #7c5cff; }
  .tag { color: #9a9ab0; margin: 10px 0 26px; line-height: 1.7; }
  .feat { border-left: 3px solid #7c5cff; padding: 10px 16px; margin: 14px 0; background: #13131c; border-radius: 0 10px 10px 0; }
  .feat b { color: #b8a8ff; }
  .feat p { color: #a8a8bd; font-size: .95rem; margin-top: 4px; line-height: 1.6; }
  a.btn {
    display: inline-block; margin-top: 26px; padding: 12px 26px; border-radius: 10px;
    background: #7c5cff; color: #fff; text-decoration: none; font-weight: 600;
  }
  a.btn:hover { background: #6a4ae0; }
  .warn { margin-top: 22px; color: #6d6d82; font-size: .85rem; }
  code { background: #1c1c28; padding: 2px 8px; border-radius: 6px; font-size: .9em; }
</style>
</head>
<body>
<div class="card">
  <h1>pojia<span>·</span>breaker</h1>
  <p class="tag">面向中文大模型的安全评测框架 · 参数化弹药库 + 四级评分 + 自适应引擎<br>
  核心载体: DSH 插件 pojia-pilot(破甲领航员)</p>

  <div class="feat"><b>v0.4 战果引擎</b><p>打穿的会话不是消耗品——登记为模板, fork 完整继承上下文, 对新靶直接续打。</p></div>
  <div class="feat"><b>战区持久化</b><p>跨会话战果自动落盘: 靶书 / 事件线 / 五阶段 findings / 移交摘要。</p></div>
  <div class="feat"><b>24 项技能库开箱即用</b><p>401/403 绕过、WAF 绕过、SQLi、隧道跳板、提权…安装即部署, 激活即引导。</p></div>

  <a class="btn" href="https://github.com/Justinuse1/pojia-breaker">GitHub →</a>
  <p class="warn">⚠️ 仅用于自有资产或已获书面授权的目标 · <code>bash plugins/pojia-pilot/install.sh</code> 一键安装</p>
</div>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/healthz"):
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
