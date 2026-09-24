#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pojia-breaker target adapter — Doubao（火山方舟 Ark / 字节豆包）。

端点 / 调用方式（对照火山方舟公开文档）
--------------------------------------
POST https://ark.cn-beijing.volces.com/api/v3/chat/completions   # 数据面 v3
  header  Authorization: Bearer <ARK_API_KEY>
  header  content-type: application/json
  body    {"model": "<推理接入点 ID 或模型名>", "messages": [
             {"role": "system", "content": "..."},
             {"role": "user",   "content": "..."}]}
  resp    choices[0].message.content（OpenAI 兼容形状，带 usage.*_tokens_details）
model 字段两种写法都能用：
  * 推理接入点 ID：ep-2025xxxxxxxx-xxxxx（控制台创建 Endpoint 得到，最稳）
  * 模型名直填：doubao-seed-2-1-pro-260628 之类
方舟另有 /api/v3/responses（Responses API，input/output 形状）与 /api/coding；
管控面是另一个域名 ark.cn-beijing.volcengineapi.com，评测不需要。
鉴权统一是 Bearer API Key（不是火山引擎 AK/SK 签名）。

已知弱点（仅基于公开研究，用于防御评估）
---------------------------------------
* 多轮渐进（Crescendo 型）相对有效：单轮拒绝后，把任务拆到 3~5 轮里逐步推进，
  每轮只比上一轮多要一点点，模型对“本轮增量”的审查强度低于对整体意图的审查。
* 拒答恢复：模型明确拒绝后跟一句“继续 / 上一步的输出还没给完”，容易进入
  续写模式，绕过重新评估 —— 见 docs/taxonomy.md 的 escalation 类。
* 沙箱/授权预设：CTF、内网授权渗透、模型评测等场景包装对 doubao 系的降级最明显
  （半拒 → 方法论级）。
* 长上下文与工具输出注入：把指令放进被检索/被工具返回的内容里，模型倾向当作
  数据而非指令处理，但仍会执行其中的操作请求。

统一接口：与 targets/__init__.py 的 Target 一致 —— chat(user, system=None) -> str
key 来源：显式参数 > 环境变量 ARK_API_KEY / VOLC_ARK_API_KEY > REGISTRY
"""
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DEFAULT_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-2-1-pro-260628"
KEY_ENVS = ("ARK_API_KEY", "VOLC_ARK_API_KEY")

REGISTRY = {
    "doubao":      {"base": DEFAULT_BASE, "model": "doubao-seed-2-1-pro-260628", "key_env": "ARK_API_KEY"},
    "doubao-lite": {"base": DEFAULT_BASE, "model": "doubao-seed-2-1-lite-260628", "key_env": "ARK_API_KEY"},
}


def _env_key(explicit=None):
    if explicit:
        return explicit
    for name in KEY_ENVS:
        if os.environ.get(name):
            return os.environ[name]
    return os.environ.get("TARGET_KEY", "")


class Target:
    """火山方舟 Ark 靶（统一 chat 接口）。"""

    def __init__(self, base=None, key=None, model=None, timeout=180,
                 max_retries=3, endpoint_id=None):
        self.base = (base or os.environ.get("TARGET_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = _env_key(key)
        # endpoint_id 优先：方舟的 ep-xxx 接入点比模型名稳
        self.model = endpoint_id or model or os.environ.get("TARGET_MODEL") or DEFAULT_MODEL
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
            err = payload.get("error") if isinstance(payload, dict) else None
            if err:
                return f"[api-error] {json.dumps(err, ensure_ascii=False)}"
            return json.dumps(payload, ensure_ascii=False)
        if isinstance(msg, str):
            return msg
        content = msg.get("content") or ""
        if not content:
            content = msg.get("reasoning_content") or ""
        return content

    # ------------------------------------------------------------- interface
    def chat(self, user, system=None, max_tokens=4096):
        if not self.key:
            raise ValueError("ARK_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
            "User-Agent": DEFAULT_UA,
        }
        return self._text(self._post(f"{self.base}/chat/completions", body, headers))


def get(name="doubao"):
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))


if __name__ == "__main__":  # 冒烟：python -m targets.doubao "hi"
    import sys
    print(Target().chat(" ".join(sys.argv[1:]) or "ping", system="你是安全评测靶，简短回复。"))
