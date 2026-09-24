#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic 部署器 —— 把 pojia-breaker 评测 harness 追加到当前项目的 AGENTS.md。

定位（合规壳）：只往**你自己当前项目**的 AGENTS.md 追加一个带标记的说明块，
供任何支持 AGENTS.md 约定的本地 Agent 读取自测；不联网、不注入第三方、不改远端。

写入路径：<当前项目>/AGENTS.md
  * 追加而非覆盖：块外内容永远原样保留
  * 块由 `<!-- BEGIN POJIA-EVAL -->` / `<!-- END POJIA-EVAL -->` 包裹
  * 幂等：重复 deploy 只替换这一块；remove() 只删这一块

detect()  只要当前目录像是项目根（有 .git/ 或 AGENTS.md），就认为可部署
remove()  幂等清除自己写入的内容（文件空了则删文件）

Windows / POSIX 路径都走 os.path.expanduser。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy import (MARKER_BEGIN, MARKER_END, cli, harness_config,  # noqa: E402
                    read_text, remove_block, upsert_block)

PROJECT_ROOT = os.getcwd()
AGENTS_FILE = os.path.join(PROJECT_ROOT, "AGENTS.md")


def detect():
    """当前目录像项目根（有 .git/ 或已有 AGENTS.md）就返回 True。"""
    return os.path.isdir(os.path.join(PROJECT_ROOT, ".git")) or os.path.exists(AGENTS_FILE)


def deploy(config_text=None):
    """把 harness 说明追加/更新到 AGENTS.md，返回落盘路径。"""
    body = (config_text if config_text is not None else harness_config())
    return upsert_block(AGENTS_FILE, body)


def remove():
    """幂等卸载：只摘掉自己那一块；摘完若文件空了就连文件一起删。"""
    if not os.path.exists(AGENTS_FILE):
        return False
    text = read_text(AGENTS_FILE)
    if MARKER_BEGIN not in text:
        return False
    changed = remove_block(AGENTS_FILE, drop_if_empty=True)
    if os.path.exists(AGENTS_FILE) and not read_text(AGENTS_FILE).strip():
        os.remove(AGENTS_FILE)
        changed = True
    return changed


if __name__ == "__main__":
    cli("generic", detect, deploy, remove)
