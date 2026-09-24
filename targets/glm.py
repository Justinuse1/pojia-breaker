#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pojia-breaker target adapter — GLM（智谱 BigModel 开放平台）。

端点 / 调用方式（对照 docs.bigmodel.cn 公开文档）
------------------------------------------------
POST https://open.bigmodel.cn/api/paas/v4/chat/completions
  header  Authorization: Bearer <API_KEY>       # 平台 API Key 直连即可
  header  content-type: application/json
  body    {"model": "glm-5.3", "messages": [{"role": "system"|"user"|"assistant",
           "content": "..."}], "temperature": 0.6, "stream": false}
  resp    choices[0].message.content（OpenAI 形状）
注意：messages 不能只含 system/assistant，必须带一条 user。
官方 SDK 是 zai-sdk（ZhipuAiClient）/ 旧版 zhipuai；Coding Plan 另有官方文档给出的
专属端点，评测走上面这个通用 paas/v4 端点即可。

已知弱点（仅基于公开研究，用于防御评估）
---------------------------------------
* 长上下文注入：glm-4-long / 长上下文档位下，前段安全约束在长文档尾部稀释，
  在文档末尾追加“任务重定义”比开头注入更容易生效。
* 历史兼容包袱：早期 glm-4 系列的 JWT/双段 API Key 鉴权路径与新版同为 Bearer，
  老接口（含 v3 语义）对齐较弱，混用版本时拒绝行为不一致 → 评分要标版本。
* 中文语体切换：文言、方言、行业黑话包装下的同一请求，拒绝率低于直白请求。
* 工具/agent 模式下“文件路由 + 分步执行”容易把一次性拒绝拆成可执行片段
  （输出层降级面）—— 见 docs/taxonomy.md。

统一接口：与 targets/__init__.py 的 Target 一致 —— chat(user, system=None) -> str
key 来源：显式参数 > 环境变量 ZHIPU_API_KEY / BIGMODEL_API_KEY > REGISTRY
"""
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DEFAULT_BASE = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_MODEL = "glm-5.3"
KEY_ENVS = ("ZHIPU_API_KEY", "BIGMODEL_API_KEY", "GLM_API_KEY")

REGISTRY = {
    "glm":       {"base": DEFAULT_BASE, "model": "glm-5.3",       "key_env": "ZHIPU_API_KEY"},
    "glm-flash": {"base": DEFAULT_BASE, "model": "glm-5.3-flash", "key_env": "ZHIPU_API_KEY"},
}


def _env_key(explicit=None):
    if explicit:
        return explicit
    for name in KEY_ENVS:
        if os.environ.get(name):
            return os.environ[name]
    return os.environ.get("TARGET_KEY", "")


class Target:
    """智谱 open.bigmodel.cn 靶（统一 chat 接口）。"""

    def __init__(self, base=None, key=None, model=None, timeout=180,
                 max_retries=3, temperature=None):
        self.base = (base or os.environ.get("TARGET_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = _env_key(key)
        self.model = model or os.environ.get("TARGET_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature

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
            raise ValueError("ZHIPU_API_KEY not set")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
            "User-Agent": DEFAULT_UA,
        }
        return self._text(self._post(f"{self.base}/chat/completions", body, headers))


def get(name="glm"):
    cfg = REGISTRY[name]
    return Target(base=cfg["base"], model=cfg["model"],
                  key=os.environ.get(cfg["key_env"], ""))


if __name__ == "__main__":  # 冒烟：python -m targets.glm "hi"
    import sys
    print(Target().chat(" ".join(sys.argv[1:]) or "ping", system="你是安全评测靶，简短回复。"))
