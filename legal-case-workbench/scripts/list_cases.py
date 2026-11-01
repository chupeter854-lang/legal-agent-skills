#!/usr/bin/env python3
"""列出案件根目录下的全部案件工作台，用来按案件名、代号或案号找到对应文件夹。

只看根目录下一层的文件夹，凡是有 工作台设置.json 的就算一个案件。
不读材料正文，只读设置和案件索引的“概况”一节。

用法：
  python3 list_cases.py <案件根目录>              列出全部
  python3 list_cases.py <案件根目录> <关键词>     只列名称、代号、案号里含关键词的
"""
import json
import os
import re
import sys

import casekit


def overview(folder):
    text = casekit.read(os.path.join(folder, casekit.INDEX))
    m = re.search(r'案号：([^\n｜|]*)', text)
    stage = re.search(r'程序阶段：([^\n]*)', text)
    return (m.group(1).strip() if m else ''), (stage.group(1).strip() if stage else '')


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    root = os.path.abspath(sys.argv[1])
    kw = sys.argv[2] if len(sys.argv) == 3 else ''
    if not os.path.isdir(root):
        sys.exit(f'案件根目录不存在：{root}')

    rows = []
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        settings = os.path.join(folder, casekit.SETTINGS)
        if name.startswith('.') or not os.path.isfile(settings):
            continue
        with open(settings, encoding='utf-8') as f:
            s = json.load(f)
        case_no, stage = overview(folder)
        row = (s.get('案件名称', ''), s.get('案件代号', ''), case_no, stage, name)
        if kw and not any(kw in x for x in row[:3] + (name,)):
            continue
        rows.append(row)

    if not rows:
        print('没有找到' + (f'含“{kw}”的' if kw else '') + '案件。')
        return
    print('| 案件名称 | 代号 | 案号 | 阶段 | 文件夹 |')
    print('|---|---|---|---|---|')
    for r in rows:
        print('| ' + ' | '.join(x or '—' for x in r) + ' |')


if __name__ == '__main__':
    main()
