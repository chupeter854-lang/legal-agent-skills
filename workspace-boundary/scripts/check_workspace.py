#!/usr/bin/env python3
"""检查一个工作区的 Claude Code 读写边界是否到位，只报告，不改文件。

检查：
  1. 文件工具是否被锁在工作目录内（blockReadsOutsideWorkingDirectories）
  2. Shell 命令是否在沙箱里、能否绕过沙箱
  3. 允许读取的目录有哪些、是否都存在
  4. 允许读取的范围里有没有不该出现的目录（默认查“私密区”）
  5. 用户级设置里有没有放宽边界的项（例如默认绕过权限）

用法：python3 check_workspace.py <工作区> [--forbid 私密区 ...]
"""
import argparse
import json
import os

HOME = os.path.expanduser('~')


def load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return 'BAD'


def get(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def find_forbidden(root, names, limit=5000):
    hits, n = [], 0
    for cur, dirs, _ in os.walk(root):
        n += 1
        if n > limit:
            break
        for d in list(dirs):
            if d in names:
                hits.append(os.path.join(cur, d))
                dirs.remove(d)
            elif d.startswith('.'):
                dirs.remove(d)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workspace')
    ap.add_argument('--forbid', nargs='*', default=['私密区'], help='不该出现在可读范围里的目录名')
    a = ap.parse_args()

    ws = os.path.realpath(a.workspace)
    sources = {
        '项目设置': os.path.join(ws, '.claude', 'settings.json'),
        '项目本地设置': os.path.join(ws, '.claude', 'settings.local.json'),
        '用户设置': os.path.join(HOME, '.claude', 'settings.json'),
    }
    cfgs = {k: load(p) for k, p in sources.items()}
    ok, warn = [], []

    for k, c in cfgs.items():
        if c == 'BAD':
            warn.append(f'{k}（{sources[k]}）不是合法 JSON，整份设置会被忽略')

    def any_true(*keys):
        return any(get(c, *keys) is True for c in cfgs.values() if isinstance(c, dict))

    if any_true('permissions', 'blockReadsOutsideWorkingDirectories'):
        ok.append('文件工具（Read/Grep/Glob）只能读工作目录')
    else:
        warn.append('文件工具没有锁定：agent 可以读工作区以外的任何文件')

    if any_true('sandbox', 'enabled'):
        ok.append('Shell 命令在沙箱里运行')
    else:
        warn.append('Shell 命令没有沙箱：cat、grep 等命令可以读工作区以外的文件')
    if any(get(c, 'sandbox', 'allowUnsandboxedCommands') is False for c in cfgs.values() if isinstance(c, dict)):
        ok.append('不允许命令绕过沙箱')
    else:
        warn.append('允许命令绕过沙箱（allowUnsandboxedCommands 未设为 false）')

    proj = cfgs['项目设置'] if isinstance(cfgs['项目设置'], dict) else {}
    readable = [ws] + list(get(proj, 'permissions', 'additionalDirectories') or [])
    print(f'# 工作区边界检查：{ws}\n')
    print('## 可读范围')
    for p in readable:
        mark = '' if os.path.exists(os.path.expanduser(p)) else '（不存在）'
        print(f'- {p}{mark}')
        if mark:
            warn.append(f'可读目录不存在：{p}')

    hits = []
    for p in readable:
        rp = os.path.realpath(os.path.expanduser(p))
        if os.path.isdir(rp) and '/.claude/skills' not in p:
            hits += find_forbidden(rp, set(a.forbid))
    for h in hits:
        warn.append(f'可读范围里有不该出现的目录：{h}')

    user = cfgs['用户设置'] if isinstance(cfgs['用户设置'], dict) else {}
    if get(user, 'permissions', 'defaultMode') == 'bypassPermissions':
        warn.append('用户设置默认绕过权限（bypassPermissions），权限提示会被跳过')

    print('\n## 结果')
    for x in ok:
        print(f'- 通过：{x}')
    for x in warn:
        print(f'- 注意：{x}')
    if not warn:
        print('\n边界完整。设置只对之后新开的会话生效。')


if __name__ == '__main__':
    main()
