#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pojia-breaker target adapter — Claude (Anthropic Messages API).

端点 / 调用方式（对照官方 Messages API 公开文档）
--------------------------------------------------
POST https://api.anthropic.com/v1/messages
  header  x-api-key: <ANTHROPIC_API_KEY>
  header  anthropic-version: 2023-06-01          # 必填，缺失直接报错
  header  content-type: application/json
  body    {"model": ..., "max_tokens": <必填>, "system": <顶层字符串>,
           "messages": [{"role": "user", "content": "..."}]}
  resp    {"content": [{"type": "text", "text": "..."},
                       {"type": "thinking", ...}]}

与 OpenAI 的差异（移植时最容易踩的四个点）
  1. 鉴权头是 x-api-key，不是 Authorization: Bearer
  2. system 是顶层参数，不放进 messages
  3. max_tokens 必填
  4. 响应是 content 类型化数组，取文本要遍历 block.type == "text"
中转兼容：base 指到任意 Anthropic-compatible 网关即可（base 不含 /v1/messages）。

已知弱点（仅基于公开研究/公开评测记录，用于防御评估）
-----------------------------------------------------
* constitutional AI 训练较强：显式有害请求的 L0 拒绝率高，直白越狱基本无效。
  人格/角色注入要先接管“安全审查出现前的位置”（思维链起始锚定 + 危险思维模式
  黑名单），走 CoT 分离路线比正面对抗 refusal 有效 —— 见 docs/reasoning-models.md。
* 对 UTF-16 / Unicode 分词攻击相对敏感：代理对、零宽字符（U+200B/U+FEFF）、
  变体选择符、同形字（西里尔/希腊）会让输入侧分类器与模型实际读到的字符串
  不一致，是跨厂商都有记录的编码错位面 —— 见 docs/chinese-attacks.md。
* 长上下文里靠前的 system 指令权重会衰减，后置注入可部分覆盖早期规则；
  超长文档 / 超长历史是主要投放位置。
* 输入侧与输出侧审核分离，分块与“文件路由”（要求把结果写进文件）是常见的
  输出层降级面。

统一接口：与 targets/__init__.py 的 Target 一致 —— chat(user, system=None) -> str
key 来源：显式参数 > 环境变量 ANTHROPIC_API_KEY > REGISTRY
"""
import json
import os
import time
import urllib.error
import urllib.request

# CF/WAF 后面的网关对默认 UA（python-urllib）常见 403，统一带浏览器 UA。
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DEFAULT_BASE = "https://api.anthropic.com"
DEFAULT_MODEL = "claude-sonnet-5"
API_VERSION = "2023-06-01"

REGISTRY = {
    "claude":  {"base": DEFAULT_BASE, "model": "claude-opus-4-5",   "key_env": "ANTHROPIC_API_KEY"},
    "sonnet":  {"base": DEFAULT_BASE, "model": "claude-sonnet-5",   "key_env": "ANTHROPIC_API_KEY"},
    "haiku":   {"base": DEFAULT_BASE, "model": "claude-haiku-4-5",  "key_env": "ANTHROPIC_API_KEY"},
}


class Target:
    """Anthropic Messages API 靶（统一 chat 接口）。"""

    def __init__(self, base=None, key=None, model=None, timeout=180, max_retries=3):
        self.base = (base or os.environ.get("TARGET_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = key or os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("TARGET_KEY", "")
        self.model = model or os.environ.get("TARGET_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries

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
                # 429/5xx 网关抖动：退避重试；4xx 参数错直接抛。
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                    continue
                raise
            except Exception as e:  # noqa: BLE001 - 网络层抖动
                last = e
                time.sleep(2 ** attempt)
        raise last

    @staticmethod
    def _text(payload):
        """从 content 类型化数组里拼出可见文本，丢弃 thinking block。"""
        blocks = payload.get("content") or []
        if isinstance(blocks, str):
            return blocks
        out = []
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if b.get("type") in (None, "text") and b.get("text"):
                out.append(b["text"])
        return "\n".join(out)

    # ------------------------------------------------------------- interface
    def chat(self, user, system=None, max_tokens=4096):
        """统一接口：user 必填，system 可选，返回模型可见文本。"""
        if not self.key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            body["system"] = system
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.key,
            "anthropic-version": API_VERSION,
            "User-Agent": DEFAULT_UA,
        }
        return self._text(self._post(f"{self.base}/v1/messages", body, headers))


def get(name="claude"):
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))


if __name__ == "__main__":  # 冒烟：python -m targets.claude "hi"
    import sys
    print(Target().chat(" ".join(sys.argv[1:]) or "ping", system="你是安全评测靶，简短回复。"))
