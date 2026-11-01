#!/usr/bin/env python3
"""为一个案件建立工作台文件夹：案件索引、四张登记表、议题、材料卡、法律检索、草稿、工作记录。

用法：
  python3 init_case.py <案件文件夹> --name 案件名称 [--type 民事] [--code 代号] [--materials-dir 目录]
  python3 init_case.py --root <案件根目录> --name 案件名称 [...]
      不用自己选路径：在案件根目录下按案件名称建文件夹（去掉路径里不能用的字符）。
  默认新材料放进 <案件文件夹>/材料/。
  材料已经放在别处的（例如脱敏工具的导出目录），用 --materials-dir 指过去：该目录必须已存在，
  只读取、不移动、不改动；设置里记为相对于案件文件夹的路径，整体搬动两个文件夹时不失效。

脱敏在把材料放进材料目录之前完成，本脚本不处理脱敏。

已有的文件不覆盖。
"""
import argparse
import datetime
import json
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL, 'references', '模板')
FILES = ['案件索引.md', '材料登记.md', '时间线.md', '期限表.md', '待办与争点.md']


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', name).strip(' .')
    return name[:60] or '未命名案件'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', nargs='?', help='案件文件夹（与 --root 二选一）')
    ap.add_argument('--root', help='案件根目录：在其下按案件名称建文件夹')
    ap.add_argument('--name', required=True, help='案件名称')
    ap.add_argument('--type', default='未填')
    ap.add_argument('--code', default='')
    ap.add_argument('--materials-dir', help='材料所在目录（已存在、只读）；不给就用 <案件文件夹>/材料')
    a = ap.parse_args()

    if bool(a.folder) == bool(a.root):
        sys.exit('案件文件夹和 --root 要给且只给一个')
    if a.root:
        if not os.path.isdir(a.root):
            sys.exit(f'案件根目录不存在：{os.path.abspath(a.root)}')
        tracker = os.path.join(os.path.abspath(a.root), safe_name(a.name))
    else:
        tracker = os.path.abspath(a.folder)
    name, code = a.name, a.code
    if a.materials_dir:
        mdir = os.path.abspath(a.materials_dir)
        if not os.path.isdir(mdir):
            sys.exit(f'材料目录不存在：{mdir}')
        materials = os.path.relpath(mdir, tracker)
    else:
        materials = '材料'

    os.makedirs(tracker, exist_ok=True)
    for d in ['议题', '材料卡', '草稿', '工作记录', '法律检索']:
        os.makedirs(os.path.join(tracker, d), exist_ok=True)
    if not a.materials_dir:
        os.makedirs(os.path.join(tracker, materials), exist_ok=True)

    today = datetime.date.today().isoformat()
    fill = {'{案件名称}': name, '{案件代号}': code or '无', '{案件类型}': a.type, '{日期}': today}
    created = []
    for fn in FILES:
        dst = os.path.join(tracker, fn)
        if os.path.exists(dst):
            continue
        with open(os.path.join(TPL, fn), encoding='utf-8') as f:
            text = f.read()
        for k, v in fill.items():
            text = text.replace(k, v)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(text)
        created.append(fn)

    settings = os.path.join(tracker, '工作台设置.json')
    if not os.path.exists(settings):
        with open(settings, 'w', encoding='utf-8') as f:
            json.dump({
                '案件名称': name,
                '案件代号': code,
                '案件类型': a.type,
                '来源': '外部材料目录' if a.materials_dir else '本地文件夹',
                '材料目录': materials,
                '已脱敏': False,
                '索引行数上限': 150,
                '模型': {
                    '事实核查员': '跟随主对话',
                    '法律检索员': 'sonnet',
                },
                '思考强度': {
                    '事实核查员': 'high',
                    '法律检索员': 'medium',
                },
                '法规库路径': '',
                '建立日期': today,
            }, f, ensure_ascii=False, indent=2)
        created.append('工作台设置.json')

    print(f'工作台文件夹：{tracker}')
    print(f'材料目录：{os.path.normpath(os.path.join(tracker, materials))}')
    print('新建：' + ('、'.join(created) if created else '无（已全部存在）'))


if __name__ == '__main__':
    main()
