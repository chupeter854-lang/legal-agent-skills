#!/usr/bin/env python3
"""为一个案件建立工作台文件夹：案件索引、四张登记表、议题、材料卡、法律检索、草稿、工作记录。

用法：
  python3 init_case.py <案件文件夹> --name 案件名称 [--type 民事] [--code 代号] [--materials-dir 目录]
  python3 init_case.py --root <案件根目录> --party 当事人简称 --cause 案由 [...]
      不用自己选路径：在案件根目录下建“<当事人简称><案由>案件_<建立日期>”文件夹，
      例如 --party 徐某某 --cause 买卖合同纠纷 → “徐某某买卖合同纠纷案件_20261101”。
      案由以“案”或“案件”结尾的不重复加。--name 不给时，案件名称就用“当事人简称＋案由”。
      根目录里已有同一当事人、同一案由的案件文件夹（日期不同）时停下，确认是新案件再加 --new。
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


def clean(text):
    """去掉路径里不能用的字符。"""
    return re.sub(r'[\\/:*?"<>|\n\r\t ]', '', text).strip('.')


def case_stem(party, cause):
    """<当事人简称><案由>案件，不含日期。"""
    cause = re.sub(r'(案件|案)$', '', clean(cause)) or clean(cause)
    return f'{clean(party)}{cause}案件'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', nargs='?', help='案件文件夹（与 --root 二选一）')
    ap.add_argument('--root', help='案件根目录：在其下按“当事人简称＋案由”建文件夹')
    ap.add_argument('--party', help='当事人简称，例如 徐某某（已脱敏的用代号）')
    ap.add_argument('--cause', help='案由，例如 买卖合同纠纷')
    ap.add_argument('--name', help='案件名称；不给时用“当事人简称＋案由”')
    ap.add_argument('--new', action='store_true', help='根目录里已有同名案件时，确认这是另一个新案件')
    ap.add_argument('--type', default='未填')
    ap.add_argument('--code', default='')
    ap.add_argument('--materials-dir', help='材料所在目录（已存在、只读）；不给就用 <案件文件夹>/材料')
    a = ap.parse_args()

    if bool(a.folder) == bool(a.root):
        sys.exit('案件文件夹和 --root 要给且只给一个')
    if not a.name and not (a.party and a.cause):
        sys.exit('需要 --name，或者 --party 和 --cause')
    if a.root:
        if not (a.party and a.cause):
            sys.exit('用 --root 建档时需要 --party（当事人简称）和 --cause（案由）')
        root = os.path.abspath(a.root)
        if not os.path.isdir(root):
            sys.exit(f'案件根目录不存在：{root}')
        stem = case_stem(a.party, a.cause)
        folder = f'{stem}_{datetime.date.today().strftime("%Y%m%d")}'
        same = [n for n in sorted(os.listdir(root)) if n.startswith(stem + '_') and n != folder]
        if same and not a.new:
            sys.exit('根目录里已有同一当事人、同一案由的案件：' + '、'.join(same)
                     + '\n是同一个案件就用已有的文件夹；确认是另一个新案件，加 --new 再运行。')
        tracker = os.path.join(root, folder)
    else:
        tracker = os.path.abspath(a.folder)
    name = a.name or case_stem(a.party, a.cause)[:-2]
    code = a.code
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
                '当事人简称': a.party or '',
                '案由': a.cause or '',
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
