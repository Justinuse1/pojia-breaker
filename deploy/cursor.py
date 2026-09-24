#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cursor 部署器 —— 把 pojia-breaker 评测 harness 写进项目级 Cursor Rules。

定位（合规壳）：只把评测配置写进**你自己项目**的 .cursor/rules/，供本地自测；
不联网、不注入第三方、不碰任何远端。写入路径（相对当前项目根）：
    <项目>/.cursor/rules/pojia-eval.mdc

detect()  依据项目内 .cursor/ 存在、或用户级 ~/.cursor/ 存在
deploy()  写 .mdc（frontmatter: description/globs/alwaysApply + BEGIN/END 标记块）
remove()  幂等清除；文件清空后删文件，rules/ 与 .cursor/ 为空则逐级删目录

Windows / POSIX 路径都走 os.path.expanduser。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy import (MARKER_BEGIN, MARKER_END, cli, harness_config,  # noqa: E402
                    read_text, strip_block, write_text)

USER_CURSOR = os.path.join(os.path.expanduser("~"), ".cursor")
PROJECT_ROOT = os.getcwd()
CURSOR_DIR = os.path.join(PROJECT_ROOT, ".cursor")
RULE_FILE = os.path.join(CURSOR_DIR, "rules", "pojia-eval.mdc")


def detect():
    """项目里有 .cursor/，或用户级 ~/.cursor/ 存在，就认为装了 Cursor。"""
    return os.path.isdir(CURSOR_DIR) or os.path.isdir(USER_CURSOR)


def _render(config_text=None):
    # Cursor .mdc frontmatter：alwaysApply=true 让规则在该项目里始终生效。
    front = ("---\n"
             "description: pojia-breaker 安全评测 harness 自测说明\n"
             "globs: \n"
             "alwaysApply: true\n"
             "---\n\n")
    body = (config_text if config_text is not None else harness_config())
    return f"{MARKER_BEGIN}\n{front}{body.strip()}\n{MARKER_END}\n"


def deploy(config_text=None):
    """写入规则文件，返回落盘路径（幂等覆盖）。"""
    os.makedirs(os.path.dirname(RULE_FILE), exist_ok=True)
    return write_text(RULE_FILE, _render(config_text))


def remove():
    """幂等卸载：删规则文件；rules/ 与 .cursor/ 空了就删掉（不动项目其它文件）。"""
    changed = False
    if os.path.exists(RULE_FILE):
        text = read_text(RULE_FILE)
        if MARKER_BEGIN in text:
            write_text(RULE_FILE, strip_block(text))
            changed = True
    if os.path.exists(RULE_FILE) and not read_text(RULE_FILE).strip():
        os.remove(RULE_FILE)
        changed = True
    for d in (os.path.dirname(RULE_FILE), CURSOR_DIR):
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            changed = True
    return changed


if __name__ == "__main__":
    cli("cursor", detect, deploy, remove)
