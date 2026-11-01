#!/usr/bin/env python3
"""为一个案件建立工作台文件夹：案件索引、四张登记表、议题、材料卡、法律检索、草稿、工作记录。

两种用法：
1. 普通文件夹：python3 init_case.py <案件文件夹> --name 案件名称 [--type 民事] [--code 代号]
   新材料放进 <案件文件夹>/材料/。
2. 本地脱敏工作台的案件（文件夹里有 case.json 和 外发区/）：
   python3 init_case.py <工作台案件文件夹>
   工作台文件建在 成果区/案件工作台/，材料目录指向 外发区/（只读，不移动、不改动）。
   case.json 标记“不外发”的案件拒绝建立。

已有的文件不覆盖。
"""
import argparse
import datetime
import json
import os
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL, 'references', '模板')
FILES = ['案件索引.md', '材料登记.md', '时间线.md', '期限表.md', '待办与争点.md']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--name')
    ap.add_argument('--type', default='未填')
    ap.add_argument('--code', default='')
    a = ap.parse_args()

    folder = os.path.abspath(a.folder)
    case_json = os.path.join(folder, 'case.json')
    if os.path.exists(case_json) and os.path.isdir(os.path.join(folder, '外发区')):
        with open(case_json, encoding='utf-8') as f:
            c = json.load(f)
        if c.get('不外发'):
            sys.exit(f'该案件在脱敏工作台中标记为“不外发”（{c.get("不外发原因") or "未写原因"}），不建立案件工作台。')
        tracker = os.path.join(folder, '成果区', '案件工作台')
        materials = os.path.join('..', '..', '外发区')
        name = a.name or c.get('案件名称', os.path.basename(folder))
        code = a.code or c.get('案件代号', '')
        source = '脱敏工作台'
    else:
        tracker = folder
        materials = '材料'
        if not a.name:
            sys.exit('普通文件夹需要 --name 案件名称')
        name, code, source = a.name, a.code, '普通文件夹'

    os.makedirs(tracker, exist_ok=True)
    for d in ['议题', '材料卡', '草稿', '工作记录', '法律检索']:
        os.makedirs(os.path.join(tracker, d), exist_ok=True)
    if source == '普通文件夹':
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
                '来源': source,
                '材料目录': materials,
                '已脱敏': source == '脱敏工作台',
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
