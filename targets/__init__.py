#!/usr/bin/env python3
"""pojia-breaker target adapter — OpenAI-compatible unified interface."""
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
    "gpt":      {"base": "https://supeai.cc/v1",  "model": "gpt-5.2-codex",       "key_env": "SUPEAI_CC_KEY"},
}


def get(name: str) -> Target:
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))
