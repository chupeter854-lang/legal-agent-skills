#!/usr/bin/env python3
"""给一个工作区文件夹写入 Claude Code 的读写边界设置（.claude/settings.json）。

在这个文件夹里打开的 Claude Code 会话（包括它派出的子代理）：
  - 文件工具（Read、Grep、Glob）只能读工作区本身和 --read 列出的目录；
  - Shell 命令在沙箱里运行，只能读同样这些目录，写入只限工作区；
  - 不允许命令绕过沙箱运行。

用法：
  python3 setup_workspace.py <工作区> [--read 目录 ...] [--skills 技能目录 ...] [--dry-run]

  <工作区>    会话的工作文件夹，例如一个案件工作台文件夹。
  --read      额外允许读取的目录（只读），例如脱敏工具的导出目录。
  --skills    会话要用到的技能目录。不给时自动加入 ~/.claude/skills 下的全部技能
              （软链接同时加入链接本身和实际位置）。

已有的 settings.json 会合并而不是覆盖：数组去重追加，其他设置保留。
只用标准库，兼容 Python 3.9。
"""
import argparse
import json
import os
import sys

HOME = os.path.expanduser('~')


def default_skill_dirs():
    root = os.path.join(HOME, '.claude', 'skills')
    out = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if name.startswith('.') or not os.path.isdir(p):
                continue
            out.append(p)
    return out


def with_real(paths):
    """路径本身加上它解析软链接后的实际位置，去重保序。"""
    out = []
    for p in paths:
        for q in (os.path.abspath(p), os.path.realpath(p)):
            if q not in out:
                out.append(q)
    return out


def merge_list(d, key, items):
    cur = d.get(key) or []
    for x in items:
        if x not in cur:
            cur.append(x)
    d[key] = cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workspace')
    ap.add_argument('--read', nargs='*', default=[], help='额外只读目录')
    ap.add_argument('--skills', nargs='*', help='技能目录（不给则用 ~/.claude/skills 下全部）')
    ap.add_argument('--dry-run', action='store_true', help='只打印将写入的设置，不改文件')
    a = ap.parse_args()

    ws = os.path.realpath(a.workspace)
    if not os.path.isdir(ws):
        sys.exit(f'工作区不存在：{ws}')
    if ws in (HOME, '/', os.path.realpath(HOME)):
        sys.exit('不要把家目录或根目录当作工作区，那等于没有边界。')

    reads = []
    for r in a.read:
        rp = os.path.realpath(r)
        if not os.path.isdir(rp):
            sys.exit(f'--read 目录不存在：{rp}')
        reads.append(rp)
    skills = with_real(a.skills if a.skills is not None else default_skill_dirs())

    path = os.path.join(ws, '.claude', 'settings.json')
    cfg = {}
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                cfg = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f'{path} 不是合法 JSON，先修好再运行：{e}')

    perm = cfg.setdefault('permissions', {})
    perm['blockReadsOutsideWorkingDirectories'] = True
    merge_list(perm, 'additionalDirectories', reads + skills)

    sb = cfg.setdefault('sandbox', {})
    sb['enabled'] = True
    sb['allowUnsandboxedCommands'] = False
    fs = sb.setdefault('filesystem', {})
    merge_list(fs, 'denyRead', ['~/'])
    merge_list(fs, 'allowRead', [ws] + reads + skills)

    text = json.dumps(cfg, ensure_ascii=False, indent=2) + '\n'
    if a.dry_run:
        print(text)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f'已写入：{path}')
    print(f'工作区（可读写）：{ws}')
    for r in reads:
        print(f'只读目录：{r}')
    print(f'技能目录：{len(skills)} 个（只读）')
    print('提醒：设置在下一个新开的会话生效；已经打开的会话不会自动套用。')


if __name__ == '__main__':
    main()
