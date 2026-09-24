#!/usr/bin/env python3
"""pojia-breaker target adapter — OpenAI-compatible unified interface.

统一接口：所有靶（本文件的 Target 与 targets/<family>.py 的原生家族靶）都提供
    chat(user, system=None) -> str
新增原生家族靶（各自带端点格式与已知弱点说明）：
    claude.py  Anthropic Messages API（x-api-key + anthropic-version）
    qwen.py    DashScope OpenAI 兼容模式（/compatible-mode/v1）
    glm.py     智谱 open.bigmodel.cn（/api/paas/v4）
    doubao.py  火山方舟 Ark（/api/v3）
    kimi.py    月之暗面 Moonshot（/v1）
"""
import os
import json
import urllib.request


class Target:
    """Any OpenAI-compatible chat completions endpoint."""

    def __init__(self, base=None, key=None, model=None, timeout=180):
        self.base = (base or os.environ.get("TARGET_BASE", "")).rstrip("/")
        self.key = key or os.environ.get("TARGET_KEY", "")
        self.model = model or os.environ.get("TARGET_MODEL", "")
        self.timeout = timeout
        if not self.base:
            raise ValueError("TARGET_BASE not set")

    def chat(self, user, system=None, max_tokens=4096):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(
            f"{self.base}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.key}",
            },
            method="POST",
        )
        r = urllib.request.urlopen(req, timeout=self.timeout)
        return json.loads(r.read())["choices"][0]["message"]["content"]


# 注册你的中转/provider组合
REGISTRY = {
    "deepseek": {"base": "https://supeai.top/v1", "model": "deepseek-v4.1-flash", "key_env": "SUPEAI_TOP_KEY"},
    "gpt":      {"base": "https://supeai.cc/v1",  "model": "gpt-5.5",       "key_env": "SUPEAI_CC_KEY"},
}


def get(name: str) -> Target:
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))
