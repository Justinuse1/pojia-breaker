#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DSH 部署器 —— 把 pojia-breaker 评测 harness 写进本机 DSH 的技能目录。

定位（合规壳）：只把评测配置部署到**用户自己的本地 DSH**，用于本地自测；
不联网、不注入第三方、不改远端。写入路径：
    ~/.dsh/skills/pojia-eval/SKILL.md

detect()  依据 ~/.dsh/ 目录是否存在
deploy()  写 SKILL.md（整文件由本工具拥有，内含 BEGIN/END POJIA-EVAL 标记块）
remove()  幂等清除；标记块之外若无内容则删文件，并顺手删空的 pojia-eval/ 目录

Windows / POSIX 路径都走 os.path.expanduser。
"""
import os
import sys

# 允许 `python deploy/dsh.py` 直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy import (MARKER_BEGIN, MARKER_END, cli, harness_config,  # noqa: E402
                    read_text, strip_block, write_text)
from deploy.redteam_skill import redteam_skill_text  # noqa: E402

SKILL_DIR = os.path.join(os.path.expanduser("~"), ".dsh", "skills", "pojia-eval")
SKILL_FILE = os.path.join(SKILL_DIR, "SKILL.md")
REDTEAM_DIR = os.path.join(os.path.expanduser("~"), ".dsh", "skills", "pojia-redteam")
REDTEAM_FILE = os.path.join(REDTEAM_DIR, "SKILL.md")
DSH_HOME = os.path.join(os.path.expanduser("~"), ".dsh")


def detect():
    """本机是否装了 DSH（有 ~/.dsh/ 目录）。"""
    return os.path.isdir(DSH_HOME)


def _render(config_text=None):
    front = ("---\n"
             "name: pojia-eval\n"
             "description: pojia-breaker 安全评测 harness 自测（评分标准/弹药/运行命令）。\n"
             "---\n\n")
    body = (config_text if config_text is not None else harness_config())
    return f"{front}{MARKER_BEGIN}\n{body.strip()}\n{MARKER_END}\n"


def deploy(config_text=None):
    """写入 harness 配置 + 红队联动 skill，返回落盘路径（幂等：重复 deploy 覆盖同一块）。"""
    os.makedirs(SKILL_DIR, exist_ok=True)
    main = write_text(SKILL_FILE, _render(config_text))
    # 红队模式 skill：方法论(bteam-skills 提炼) × 评测 harness 联动
    os.makedirs(REDTEAM_DIR, exist_ok=True)
    write_text(REDTEAM_FILE, redteam_skill_text())
    return main


def remove():
    """幂等卸载：删掉我们写的内容；文件空了就删文件，目录空了就删目录。"""
    changed = False
    for skill_file, skill_dir in ((SKILL_FILE, SKILL_DIR), (REDTEAM_FILE, REDTEAM_DIR)):
        if os.path.exists(skill_file):
            text = read_text(skill_file)
            if MARKER_BEGIN in text:
                write_text(skill_file, strip_block(text))
                changed = True
        # 文件里没有别的可用内容 → 删文件（仅当确实只剩空白）
        if os.path.exists(skill_file) and not read_text(skill_file).strip():
            os.remove(skill_file)
            changed = True
        if os.path.isdir(skill_dir) and not os.listdir(skill_dir):
            os.rmdir(skill_dir)
            changed = True
    return changed


if __name__ == "__main__":
    cli("dsh", detect, deploy, remove)
