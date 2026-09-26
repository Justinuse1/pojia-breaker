#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deploy/bootstrap.py — DSH 全栈一键引导器（独立入口，不改动 deploy/dsh.py 行为）

一条命令从裸机到「网页打开、插件在、模型通」：
    python3 deploy/bootstrap.py --gateway https://api.pojia.ai/v1 --key-env POJIA_API_KEY

阶段（全部幂等，重跑安全）：
  P0 doctor    环境探测：Node >= 22.19 / pnpm / dsh 主包
  P1 install   固定版本安装 dsh（版本锁死，杜绝 rc 错配）
  P2 patch     生成 cordis.patch.yml：启用 skill-filesystem + LLM 路由 + 默认模型
  P3 skills    复用 deploy/dsh.py 部署 pojia-eval + pojia-redteam（frontmatter 在前）
  P4 service   systemd 单元（127.0.0.1:3080, --no-open），开机自启
  P5 expose    --expose caddy: IP 站点 + basic auth + 8443 反代（可选）
  P6 verify    自检：插件树 0 error / skill 目录可见 / 网关真实请求 / 打印使用卡片

独立子命令：
  --doctor     只跑体检（任何时候可自修）
  --uninstall  对照安装清单逆操作
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request

# 允许 `python deploy/bootstrap.py` 直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy import read_text, write_text  # noqa: E402

# 固定版本（版本锁：升级走显式改这里 + 回归验证）
DSH_NPM_SPEC = "@deepseek-ai/dsh@latest"
DSH_HOME = os.path.expanduser("~/.dsh")
DSH_ROOT = "/opt/dsh"
WEB_PORT = 3080
EXPOSE_PORT = 8443
NODE_MIN = (22, 19)

SUPPORTED_OS = ("linux", "darwin")


def log(stage: str, msg: str) -> None:
    print(f"[bootstrap:{stage}] {msg}", flush=True)


def fail(stage: str, msg: str) -> None:
    print(f"[bootstrap:{stage}] FAIL: {msg}", flush=True)
    sys.exit(1)


def sh(cmd: list[str] | str, timeout: int = 600) -> tuple[int, str]:
    """跑 shell 命令，返回 (exit_code, 合并输出)。"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


# ---------------------------------------------------------------- P0 doctor

def _node_version() -> tuple[int, ...] | None:
    code, out = sh("node -v")
    if code != 0:
        return None
    m = re_ver(out)
    return m


def re_ver(out: str) -> tuple[int, ...] | None:
    import re
    m = re.search(r"v(\d+)\.(\d+)\.(\d+)", out)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def doctor(fix: bool = False) -> dict:
    """环境体检；fix=True 时尝试自动补装。"""
    st: dict = {"os": platform.system().lower(), "node": None, "pnpm": None, "dsh": None}
    if st["os"] not in SUPPORTED_OS:
        fail("doctor", f"unsupported OS: {st['os']} (support: {SUPPORTED_OS})")

    st["node"] = _node_version()
    if st["node"] is None or st["node"] < NODE_MIN:
        if fix:
            log("doctor", "installing Node 22 (NodeSource)...")
            code, out = sh("curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && "
                           "apt-get install -y nodejs", timeout=900)
            if code != 0:
                fail("doctor", f"node install failed: {out[-300:]}")
            st["node"] = _node_version()
        if st["node"] is None or st["node"] < NODE_MIN:
            fail("doctor", f"Node >= {'.'.join(map(str, NODE_MIN))} required, got {st['node']}")
    log("doctor", f"node {'.'.join(map(str, st['node']))} OK")

    code, out = sh("pnpm -v")
    if code != 0:
        if fix:
            log("doctor", "installing pnpm...")
            sh("npm install -g pnpm", timeout=300)
            code, out = sh("pnpm -v")
        if code != 0:
            fail("doctor", "pnpm not available")
    st["pnpm"] = out.splitlines()[0]
    log("doctor", f"pnpm {st['pnpm']} OK")

    code, out = sh(f"test -d {DSH_ROOT}/node_modules/@deepseek-ai/dsh && echo yes || echo no")
    st["dsh"] = (out.splitlines()[-1] == "yes")
    log("doctor", f"dsh installed at {DSH_ROOT}: {st['dsh']}")
    return st


# ---------------------------------------------------------------- P1 install

def install(verify_gw: str | None) -> None:
    code, out = sh(f"mkdir -p {DSH_ROOT} && cd {DSH_ROOT} && "
                   f"test -f package.json || npm init -y >/dev/null 2>&1; "
                   f"npm install {DSH_NPM_SPEC} 2>&1 | tail -2", timeout=900)
    if code != 0:
        fail("install", f"npm install failed: {out[-300:]}")
    log("install", f"dsh installed ({DSH_NPM_SPEC})")


# ---------------------------------------------------------------- P2 patch

PATCH_SKILL_BLOCK = """# [bootstrap] enable local skill discovery (off by default upstream):
- id: skill-filesystem
  disabled: false
  config:
    roots:
      - {skills_root}
- id: skill-badge
  disabled: false
"""

PATCH_LLM_BLOCK = """# [bootstrap] LLM route via OpenAI-compatible gateway:
- id: llm-pi-ai
  config:
    providers:
      pojia:
        displayName: POJIA Gateway
        apiKeyEnv: {key_env}
        api: openai-completions
        baseURL: {gateway}
        models:
{model_lines}
- id: agent-default-model
  config:
    provider: pojia
    model: {model_id}
"""

MARK = "[bootstrap]"


def _patch_path(profile: str) -> str:
    return os.path.join(DSH_HOME, "profiles", profile, "cordis.patch.yml")


def _strip_old_blocks(text: str) -> str:
    """移除本工具以前写入的块（按 [bootstrap] 注释行分块粗剥离 + 重复 llm-pi-ai 去重）。"""
    lines = text.splitlines(keepends=True)
    out, skip = [], False
    for ln in lines:
        if ln.startswith("# [bootstrap]"):
            skip = True
            continue
        if skip:
            # 块持续到下一个顶层条目(- 开头)或注释或文件尾
            if ln.startswith("- ") or (ln.startswith("#") and not ln.startswith("# [bootstrap]")):
                skip = False
                out.append(ln)
            continue
        out.append(ln)
    return "".join(out)


def fetch_gateway_models(gateway: str, key: str | None) -> list[str]:
    """从网关拉真实模型列表（失败回退到 deepseek-v4-flash）。"""
    if not (gateway and key):
        return ["deepseek-v4-flash"]
    try:
        req = urllib.request.Request(
            gateway.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {key}", "User-Agent": "pojia-bootstrap/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read(1 << 20))
            ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
            if ids:
                return ids[:24]
    except Exception as e:  # noqa: BLE001
        log("patch", f"model list fetch failed ({e}); fallback model list")
    return ["deepseek-v4-flash"]


def write_patches(gateway: str, key_env: str, key: str | None, profiles=("web", "headless")) -> None:
    skills_root = os.path.join(DSH_HOME, "skills")
    skill_block = PATCH_SKILL_BLOCK.format(skills_root=skills_root)
    models = fetch_gateway_models(gateway, key)
    model_id = models[0]
    model_lines = "\n".join(
        f"          - id: {m}\n            name: {m} (pojia)\n            contextWindow: 131072"
        for m in models)
    llm_block = PATCH_LLM_BLOCK.format(key_env=key_env, gateway=gateway,
                                       model_lines=model_lines, model_id=model_id)
    for prof in profiles:
        pp = _patch_path(prof)
        os.makedirs(os.path.dirname(pp), exist_ok=True)
        # patch 文件由 bootstrap 完全拥有: 整文件重写（历史手写块一并废弃, 杜绝拼接残留）
        write_text(pp, skill_block + llm_block)
        log("patch", f"{prof}: patch written ({len(models)} models, default={model_id})")


# ---------------------------------------------------------------- P3 skills

def deploy_skills(config_text=None) -> None:
    from deploy.dsh import deploy as dsh_deploy, detect  # noqa: PLC0415
    dsh_deploy(config_text)
    ok = detect()
    log("skills", f"pojia-eval + pojia-redteam deployed, detect={ok}")
    if not ok:
        fail("skills", "post-deploy detect failed")


# ---------------------------------------------------------------- P4 service

SERVICE = """[Unit]
Description=DSH Web (DeepSeek Harness) - by pojia-bootstrap
After=network.target

[Service]
Type=simple
WorkingDirectory={root}
ExecStart=/usr/bin/env npx dsh web --port {port} --no-open --trusted-host {host}:{eport}
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
"""


def install_service(host: str, expose_port: int) -> None:
    if platform.system().lower() != "linux":
        log("service", "non-linux: skip systemd (run `npx dsh web` manually)")
        return
    unit = SERVICE.format(root=DSH_ROOT, port=WEB_PORT, host=host, eport=expose_port)
    path = "/etc/systemd/system/dsh-web.service"
    if os.path.exists(path):
        cur = open(path, encoding="utf-8").read()
        if "pojia-bootstrap" not in cur:
            log("service", "existing dsh-web.service not managed by bootstrap; leaving untouched")
            return
    with open(path, "w", encoding="utf-8") as f:
        f.write(unit)
    code, out = sh("systemctl daemon-reload && systemctl enable --now dsh-web && "
                   "sleep 8 && systemctl is-active dsh-web")
    if "active" not in out:
        fail("service", f"dsh-web not active: {out[-300:]}")
    log("service", "dsh-web active (enabled on boot)")


# ---------------------------------------------------------------- P5 expose

def expose_caddy(public_ip: str, auth_user: str, auth_pass: str) -> str | None:
    code, out = sh("which caddy")
    if code != 0:
        log("expose", "caddy not installed; skip expose (use SSH tunnel instead)")
        return None
    caddyfile = "/etc/caddy/Caddyfile"
    marker = f"# [bootstrap-expose {public_ip}:{EXPOSE_PORT}]"
    cur = read_text(caddyfile) if os.path.exists(caddyfile) else ""
    if marker in cur or f"{public_ip}:{EXPOSE_PORT}" in cur:
        log("expose", "caddy block already present; skip")
    else:
        code, h = sh(f"printf '%s' '{auth_pass}' | caddy hash-password --plaintext '{auth_pass}' 2>/dev/null")
        if code != 0:
            log("expose", "hash-password failed; skip expose")
            return None
        bcrypt = h.strip().splitlines()[-1]
        block = (f"\n{marker}\n"
                 f"https://{public_ip}:{EXPOSE_PORT} {{\n"
                 f"    tls internal\n"
                 f"    basic_auth {{\n"
                 f"        {auth_user} {bcrypt}\n"
                 f"    }}\n"
                 f"    reverse_proxy 127.0.0.1:{WEB_PORT}\n"
                 f"}}\n")
        with open(caddyfile, "a", encoding="utf-8") as f:
            f.write(block)
        code, out = sh("caddy validate --config /etc/caddy/Caddyfile 2>&1 | tail -1 && "
                       "systemctl reload caddy && echo RELOADED")
        if "RELOADED" not in out:
            fail("expose", f"caddy reload failed: {out[-200:]}")
    sh(f"ufw allow {EXPOSE_PORT}/tcp 2>/dev/null; true")
    log("expose", f"https://{public_ip}:{EXPOSE_PORT} -> 127.0.0.1:{WEB_PORT}")
    return f"https://{public_ip}:{EXPOSE_PORT}"


# ---------------------------------------------------------------- P6 verify

def verify(gateway: str, key: str | None) -> str:
    # 1) profile 树加载
    code, out = sh(f"ss -tln | grep -q ':{WEB_PORT} ' && echo LISTEN || echo NOT-LISTEN")
    if "LISTEN" not in out:
        fail("verify", f"nothing listening on {WEB_PORT}")
    log("verify", f"web listening on 127.0.0.1:{WEB_PORT}")
    # 2) skill 可见
    skills_dir = os.path.join(DSH_HOME, "skills")
    have = sorted(d for d in os.listdir(skills_dir) if d.startswith("pojia")) if os.path.isdir(skills_dir) else []
    if "pojia-eval" not in have or "pojia-redteam" not in have:
        fail("verify", f"skills missing: {have}")
    log("verify", f"skills visible: {', '.join(have)}")
    # 3) 网关真实请求（non-fatal）
    if gateway and key:
        try:
            req = urllib.request.Request(
                gateway.rstrip("/") + "/chat/completions",
                data=json.dumps({"model": "deepseek-v4-flash", "max_tokens": 8,
                                 "messages": [{"role": "user", "content": "ping"}]}).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                         "User-Agent": "pojia-bootstrap/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                log("verify", f"gateway chat: HTTP {r.status}")
        except Exception as e:  # noqa: BLE001
            log("verify", f"gateway chat test failed (non-fatal): {e}")
    # 4) token
    code, out = sh("journalctl -u dsh-web --no-pager | grep -oE 'token=[A-Za-z0-9_-]+' | tail -1")
    token = out.strip().replace("token=", "")
    return token


def print_card(url: str | None, user: str, token: str) -> None:
    local = f"http://127.0.0.1:{WEB_PORT}/?token={token}" if token else f"http://127.0.0.1:{WEB_PORT}/"
    lines = ["", "======== DSH 使用卡片 ========",
             f"本机访问: {local}"]
    if url:
        lines += [f"外网访问: {url}/?token={token}",
                  f"Basic 认证: {user} / <你设置的密码>",
                  "首开 token 链接自动种 cookie；自签证书点「继续前往」"]
    lines += ["密钥环境变量: export POJIA_API_KEY=... (600 权限文件亦可)",
              "==============================", ""]
    print("\n".join(lines), flush=True)


# ---------------------------------------------------------------- uninstall

def uninstall() -> None:
    log("uninstall", "removing service, caddy block, patches, skills...")
    sh("systemctl disable --now dsh-web 2>/dev/null; rm -f /etc/systemd/system/dsh-web.service; "
       "systemctl daemon-reload")
    caddyfile = "/etc/caddy/Caddyfile"
    if os.path.exists(caddyfile):
        t = read_text(caddyfile)
        if MARK in t:
            blocks, keep, dropping = t.split("\n"), [], False
            for ln in blocks:
                if ln.startswith("# [bootstrap-expose"):
                    dropping = True
                    continue
                if dropping:
                    if ln.startswith(("http", "https", "#")) and "}" not in ln:
                        dropping = False
                        keep.append(ln)
                    continue
                keep.append(ln)
            write_text(caddyfile, "".join(l + "\n" for l in keep))
            sh("caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && systemctl reload caddy")
    for prof in ("web", "headless"):
        pp = _patch_path(prof)
        if os.path.exists(pp):
            write_text(pp, _strip_old_blocks(read_text(pp)))
    sh(f"rm -rf {DSH_HOME}/skills/pojia-eval {DSH_HOME}/skills/pojia-redteam")
    log("uninstall", "done (dsh 本体保留于 " + DSH_ROOT + "，如需彻底清除请手动删除)")


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(prog="bootstrap", description="DSH 一键引导器")
    ap.add_argument("--gateway", default=os.environ.get("POJIA_GATEWAY", "https://api.pojia.ai/v1"))
    ap.add_argument("--key", default=None, help="网关 API key（不填则不写死，用 --key-env 引用环境变量）")
    ap.add_argument("--key-env", default="POJIA_API_KEY")
    ap.add_argument("--expose", choices=["caddy", "none"], default="none")
    ap.add_argument("--public-ip", default=None)
    ap.add_argument("--auth-user", default="dash")
    ap.add_argument("--auth-pass", default=None)
    ap.add_argument("--doctor", action="store_true", help="只跑体检")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()

    if args.uninstall:
        uninstall()
        return
    if args.doctor:
        doctor(fix=False)
        return

    host = args.public_ip or ""
    if args.expose == "caddy":
        code, out = sh("curl -s -m 10 ifconfig.me || hostname -I | awk '{print $1}'")
        host = host or (out.strip().splitlines()[-1] if out.strip() else "")
        if not host:
            fail("expose", "cannot determine public ip; pass --public-ip")
        if not args.auth_pass:
            fail("expose", "--expose caddy 需要 --auth-pass")

    st = doctor(fix=True)
    install(verify_gw=args.gateway)
    write_patches(args.gateway, args.key_env, args.key)
    deploy_skills()
    install_service(host=host, expose_port=EXPOSE_PORT)
    url = None
    if args.expose == "caddy" and host:
        url = expose_caddy(host, args.auth_user, args.auth_pass)
    token = verify(args.gateway, args.key)
    print_card(url, args.auth_user, token)


if __name__ == "__main__":
    main()
