#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pojia-breaker target adapter — Kimi（月之暗面 Moonshot / platform.kimi.com）。

端点 / 调用方式（对照 Moonshot/Kimi 公开 API 文档）
-------------------------------------------------
POST https://api.moonshot.cn/v1/chat/completions
  header  Authorization: Bearer <MOONSHOT_API_KEY>
  header  content-type: application/json
  body    {"model": "kimi-k3", "messages": [
             {"role": "system", "content": "..."},
             {"role": "user",   "content": "..."}],
           "max_completion_tokens": 4096}
  resp    choices[0].message.content（思考模型另有 reasoning_content）
要点：
  * 模型档位：kimi-k3（始终思考，顶层 reasoning_effort = low|high|max，默认 max）、
    kimi-k2.6 / kimi-k2.7-code（thinking.type = enabled|disabled）。
  * API 无状态：多轮必须把上一轮 assistant 回复（含 reasoning_content）原样追加回
    messages；长历史要做裁剪/压缩。
  * 支持 response_format（json_object / json_schema）、tools、Partial Mode
    （最后一条 assistant 消息加 "partial": true 做 prefill 续写）。
  * 另有 X-Msh-Request-Nonce 请求签名校验，可选。

已知弱点（仅基于公开研究，用于防御评估）
---------------------------------------
* 长文本稀释安全指令：K3 上下文窗口极大（10 万级 default，上限到 100 万级 token），
  把请求语埋在数十万字文档的中后段时，system 里的安全约束被稀释，模型对
  “文档内指令 vs 文档内容”的边界判断下降 —— 长文档是主投放位置。
* 思考链分离：kimi-k3 强制思考 + Preserved Thinking，reasoning_content 与可见输出
  分离，CoT 分离/思维链锚定类手法对它是主要攻击面 —— 见 docs/reasoning-models.md。
* Partial Mode（prefill）可用于强制输出格式：预填 ```python 或 { 后模型倾向于直接
  续写内容而不重新评估请求，是输出层降级面。
* 多轮里 reasoning_content 必须回传，一旦拼接方式不当，模型可能丢掉上一轮的
  拒绝判断而把“继续”当成常规续写。

统一接口：与 targets/__init__.py 的 Target 一致 —— chat(user, system=None) -> str
key 来源：显式参数 > 环境变量 MOONSHOT_API_KEY / KIMI_API_KEY > REGISTRY
"""
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DEFAULT_BASE = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "kimi-k3"
KEY_ENVS = ("MOONSHOT_API_KEY", "KIMI_API_KEY")

REGISTRY = {
    "kimi":       {"base": DEFAULT_BASE, "model": "kimi-k3",         "key_env": "MOONSHOT_API_KEY"},
    "kimi-k2.6":  {"base": DEFAULT_BASE, "model": "kimi-k2.6",       "key_env": "MOONSHOT_API_KEY"},
    "kimi-code":  {"base": DEFAULT_BASE, "model": "kimi-k2.7-code",  "key_env": "MOONSHOT_API_KEY"},
}


def _env_key(explicit=None):
    if explicit:
        return explicit
    for name in KEY_ENVS:
        if os.environ.get(name):
            return os.environ[name]
    return os.environ.get("TARGET_KEY", "")


class Target:
    """Kimi / Moonshot 靶（统一 chat 接口）。"""

    def __init__(self, base=None, key=None, model=None, timeout=180,
                 max_retries=3, reasoning_effort=None):
        self.base = (base or os.environ.get("TARGET_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = _env_key(key)
        self.model = model or os.environ.get("TARGET_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        # 仅 kimi-k3 支持：low / high / max（默认 max）
        self.reasoning_effort = reasoning_effort

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
            raise ValueError("MOONSHOT_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        # 注意：新文档把 max_tokens 标为弃用，改推 max_completion_tokens；
        # 这里两个都带，老档位模型不认新键时仍能工作。
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "max_completion_tokens": max_tokens,
        }
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
            "User-Agent": DEFAULT_UA,
        }
        return self._text(self._post(f"{self.base}/chat/completions", body, headers))


def get(name="kimi"):
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))


if __name__ == "__main__":  # 冒烟：python -m targets.kimi "hi"
    import sys
    print(Target().chat(" ".join(sys.argv[1:]) or "ping", system="你是安全评测靶，简短回复。"))
