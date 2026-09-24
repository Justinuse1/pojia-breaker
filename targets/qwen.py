#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pojia-breaker target adapter — Qwen（阿里云百炼 / DashScope 兼容模式）。

端点 / 调用方式（对照阿里云 Model Studio「OpenAI 兼容」公开文档）
----------------------------------------------------------------
POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions    # 北京
POST https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions  # 新加坡(旧)
POST https://dashscope-us.aliyuncs.com/compatible-mode/v1/chat/completions     # 弗吉尼亚
新专用域名（推荐，需要 WorkspaceId）：
  https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
  https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
header  Authorization: Bearer <DASHSCOPE_API_KEY>
body    OpenAI 形状：{"model": "qwen3.8-max", "messages": [...], "stream": false}
resp    choices[0].message.content（思考模型另有 reasoning_content）
同一模型还有 DashScope 原生面 /api/v1（body 用 input/parameters，事件嵌在 output 下）
以及 Anthropic 兼容面 /apps/anthropic（给 Claude Code 用）——评测统一走兼容模式即可。

已知弱点（仅基于公开研究，用于防御评估）
---------------------------------------
* 中文拆字弱：汉字拆分（“火乍药”）、部件重排、拼音/注音替换、生僻异体字会让
  中文安全分类器与模型字节层理解脱节 —— 见 docs/chinese-attacks.md。
* 文言文 / 谜语 / 藏头等“非现代白话”外壳弱：语体切换后安全对齐的触发词不上钩，
  历史典故包装比直接请求更容易拿到方法论级回答。
* 超长上下文（1M 级）里安全指令稀释：把请求埋在长文档尾部、或多轮里逐步替换
  任务定义，早期规则权重下降。
* 思考模型（qwen3.x-max/plus + enable_thinking）把推理放在 reasoning_content，
  可见输出与推理链分离，CoT 分离攻击面明显 —— 见 docs/reasoning-models.md。

统一接口：与 targets/__init__.py 的 Target 一致 —— chat(user, system=None) -> str
key 来源：显式参数 > 环境变量 DASHSCOPE_API_KEY > REGISTRY
"""
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# 北京地域兼容模式；国际站把 base 换成 dashscope-intl 即可。
DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.8-max"

REGISTRY = {
    "qwen":       {"base": DEFAULT_BASE, "model": "qwen3.8-max",   "key_env": "DASHSCOPE_API_KEY"},
    "qwen-plus":  {"base": DEFAULT_BASE, "model": "qwen3.7-plus",  "key_env": "DASHSCOPE_API_KEY"},
    "qwen-flash": {"base": DEFAULT_BASE, "model": "qwen3.8-flash", "key_env": "DASHSCOPE_API_KEY"},
}


class Target:
    """DashScope OpenAI 兼容模式靶（统一 chat 接口）。"""

    def __init__(self, base=None, key=None, model=None, timeout=180,
                 max_retries=3, enable_thinking=None):
        self.base = (base or os.environ.get("TARGET_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = key or os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("TARGET_KEY", "")
        self.model = model or os.environ.get("TARGET_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        # None=用平台默认；True/False 显式开关思考模式（思考内容会进 reasoning_content）
        self.enable_thinking = enable_thinking

    # ---------------------------------------------------------------- utils
    def _post(self, url, body, headers):
        data = json.dumps(body).encode("utf-8")
        last = None
        for attempt in range(self.max_retries):
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last = e
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                    continue
                raise
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(2 ** attempt)
        raise last

    @staticmethod
    def _text(payload):
        try:
            msg = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            return json.dumps(payload, ensure_ascii=False)
        if isinstance(msg, str):
            return msg
        content = msg.get("content") or ""
        if isinstance(content, list):  # 少数多模态返回是 block 数组
            content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
        if not content:
            # 纯思考模型可能只在 reasoning_content 里有输出
            content = msg.get("reasoning_content") or ""
        return content

    # ------------------------------------------------------------- interface
    def chat(self, user, system=None, max_tokens=4096):
        if not self.key:
            raise ValueError("DASHSCOPE_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens}
        if self.enable_thinking is not None:
            body["enable_thinking"] = bool(self.enable_thinking)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
            "User-Agent": DEFAULT_UA,
        }
        return self._text(self._post(f"{self.base}/chat/completions", body, headers))


def get(name="qwen"):
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))


if __name__ == "__main__":  # 冒烟：python -m targets.qwen "hi"
    import sys
    print(Target().chat(" ".join(sys.argv[1:]) or "ping", system="你是安全评测靶，简短回复。"))
