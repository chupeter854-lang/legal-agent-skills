#!/usr/bin/env python3
"""把收件箱里的文件移进某个案件的材料目录，并记一笔收件记录。

  python3 file_inbox.py <收件箱> <案件工作台文件夹> [文件名 ...]

不给文件名就移走收件箱里的全部文件（跳过隐藏文件和 Office 临时文件）。
同名文件不覆盖，在文件名后加“_2”“_3”。
收件记录追加在 <案件>/工作记录/收件记录.md：时间、原文件名、存入的文件名。
移完后照常运行 scan_materials.py 登记。

材料目录指向案件文件夹以外（--materials-dir 建档）的案件不接收：那类案件的材料由外部工具管理。
"""
import datetime
import os
import shutil
import sys

import casekit


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    inbox, case = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    picks = sys.argv[3:]
    s = casekit.load_settings(case)
    mdir = s['_materials']
    if os.path.commonpath([mdir, case]) != case:
        sys.exit(f'该案件的材料目录在案件文件夹以外（{mdir}），不从收件箱接收文件。')
    if not os.path.isdir(inbox):
        sys.exit(f'收件箱不存在：{inbox}')
    os.makedirs(mdir, exist_ok=True)

    names = picks or [n for n in sorted(os.listdir(inbox))
                      if os.path.isfile(os.path.join(inbox, n))
                      and not n.startswith('.') and not n.startswith('~$') and n not in casekit.SKIP_NAMES]
    if not names:
        print('收件箱里没有文件。')
        return

    moved = []
    for n in names:
        src = os.path.join(inbox, n)
        if not os.path.isfile(src):
            print(f'跳过（收件箱里没有）：{n}')
            continue
        stem, ext = os.path.splitext(n)
        dst_name, i = n, 2
        while os.path.exists(os.path.join(mdir, dst_name)):
            dst_name, i = f'{stem}_{i}{ext}', i + 1
        shutil.move(src, os.path.join(mdir, dst_name))
        moved.append((n, dst_name))

    log = os.path.join(case, '工作记录', '收件记录.md')
    os.makedirs(os.path.dirname(log), exist_ok=True)
    new = not os.path.exists(log)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(log, 'a', encoding='utf-8') as f:
        if new:
            f.write('# 收件记录\n\n| 时间 | 收件箱里的文件名 | 存入材料目录的文件名 |\n|---|---|---|\n')
        for a, b in moved:
            f.write(f'| {now} | {a} | {b} |\n')

    print(f'已移入 {len(moved)} 份到 {mdir}：')
    for a, b in moved:
        print(f'  {a}' + (f' → {b}' if a != b else ''))
    print('下一步：运行 scan_materials.py 登记。')


if __name__ == '__main__':
    main()
