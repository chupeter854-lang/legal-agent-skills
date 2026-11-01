#!/usr/bin/env python3
"""案件体检：每次打开案件先跑一遍，只报需要注意的事。

检查：
  1. 期限：已过期、7 日内、30 日内届满的未完成期限；尚未人工核对的期限
  2. 材料：未登记的新材料、登记了但未入卷的材料、登记了却找不到的文件
  3. 未结事项：登记超过 30 天仍未结的待办、争点、矛盾、待核实
  4. 编号：索引和议题里引用了、但各表里不存在的编号
  5. 索引篇幅：超过上限时提示压缩
  6. 下一个可用编号

用法：python3 case_check.py <工作台文件夹> [--today 2026-11-01]
"""
import argparse
import datetime
import os
import re

import casekit

OPEN_DEADLINE = {'', '未完成', '进行中'}
CLOSED_ITEM = {'已结', '已完成', '已解决', '已放弃', '已核实', '不再跟进'}


def parse_date(s):
    m = re.search(r'(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})', s or '')
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tracker')
    ap.add_argument('--today')
    a = ap.parse_args()

    s = casekit.load_settings(a.tracker)
    tracker = s['_tracker']
    today = parse_date(a.today) if a.today else datetime.date.today()
    out = [f'# 案件体检：{s.get("案件名称", "")}（{today.isoformat()}）', '']

    # 1. 期限
    overdue, week, month, unverified, undated = [], [], [], [], []
    for r in casekit.ledger_rows(tracker, 'D'):
        if r.get('状态', '') not in OPEN_DEADLINE:
            continue
        label = f'{r["编号"]} {r.get("事项", "")}（{r.get("届满日", "")}）'
        if '须人工' in r.get('核对', ''):
            unverified.append(label)
        d = parse_date(r.get('届满日'))
        if d is None:
            undated.append(label)
            continue
        left = (d - today).days
        if left < 0:
            overdue.append(f'{label}，已过 {-left} 天')
        elif left <= 7:
            week.append(f'{label}，剩 {left} 天')
        elif left <= 30:
            month.append(f'{label}，剩 {left} 天')
    out.append('## 期限')
    if not (overdue or week or month or undated):
        out.append('30 日内没有届满的未完成期限。')
    for title, items in [('已过期（请确认是否已处理或补救）', overdue), ('7 日内届满', week),
                         ('30 日内届满', month), ('届满日未填或无法识别', undated)]:
        if items:
            out.append(f'**{title}**')
            out += [f'- {x}' for x in items]
    if unverified:
        out.append(f'**尚未人工核对的期限 {len(unverified)} 项**（AI 推算的期限一律须律师核对起算日和期间）')
        out += [f'- {x}' for x in unverified]
    out.append('')

    # 2. 材料
    out.append('## 材料')
    mrows = casekit.ledger_rows(tracker, 'M')
    known = {r.get('指纹') for r in mrows}
    mdir = s['_materials']
    if os.path.isdir(mdir):
        files = casekit.material_files(mdir)
        new = [f for f in files if casekit.sha256(os.path.join(mdir, f))[:12] not in known]
        missing = [r['编号'] for r in mrows if r.get('路径') and r['路径'] not in set(files)]
    else:
        new, missing = [], []
        out.append(f'材料目录不存在：{mdir}')
    pending = [r['编号'] for r in mrows if r.get('状态') == '待入卷']
    out.append(f'已登记 {len(mrows)} 份；未登记的新文件 {len(new)} 份；待入卷 {len(pending)} 份'
               + (f'（{"、".join(pending)}）' if pending else '') + '。')
    if new:
        out += [f'- 新文件：{f}' for f in new[:10]] + ([f'- ……另有 {len(new) - 10} 份'] if len(new) > 10 else [])
    if missing:
        out.append('登记过但找不到文件：' + '、'.join(missing))
    out.append('')

    # 3. 未结事项
    out.append('## 未结事项')
    qrows = [r for r in casekit.ledger_rows(tracker, 'Q') if r.get('状态', '') not in CLOSED_ITEM]
    stale = []
    for r in qrows:
        d = parse_date(r.get('登记日'))
        if d and (today - d).days > 30:
            stale.append(f'{r["编号"]} [{r.get("类型", "")}] {r.get("内容", "")[:40]}（{(today - d).days} 天）')
    kinds = {}
    for r in qrows:
        kinds[r.get('类型') or '未分类'] = kinds.get(r.get('类型') or '未分类', 0) + 1
    out.append(f'未结 {len(qrows)} 项' + ('：' + '，'.join(f'{k} {v}' for k, v in kinds.items()) if kinds else '') + '。')
    if stale:
        out.append('**超过 30 天未结**')
        out += [f'- {x}' for x in stale]
    out.append('')

    # 4. 编号一致性
    defined = {r['编号'] for k in 'MEDQ' for r in casekit.ledger_rows(tracker, k)} | set(casekit.topic_ids(tracker))
    refs = {}
    sources = [casekit.INDEX]
    topic_dir = os.path.join(tracker, casekit.TOPIC_DIR)
    if os.path.isdir(topic_dir):
        sources += [os.path.join(casekit.TOPIC_DIR, f) for f in sorted(os.listdir(topic_dir)) if f.endswith('.md')]
    for src in sources:
        for m in casekit.ID_RE.finditer(casekit.read(os.path.join(tracker, src))):
            rid = f'{m.group(1)}-{m.group(2)}'
            if rid not in defined:
                refs.setdefault(rid, set()).add(src)
    if refs:
        out.append('## 悬空编号（被引用但各表里没有）')
        out += [f'- {k}：见 {"、".join(sorted(v))}' for k, v in sorted(refs.items())]
        out.append('')

    # 5. 索引篇幅
    idx = casekit.read(os.path.join(tracker, casekit.INDEX))
    n, limit = len(idx.splitlines()), int(s.get('索引行数上限', 150))
    if n > limit:
        out += ['## 索引篇幅', f'案件索引.md 有 {n} 行，超过上限 {limit} 行，建议压缩（见技能“压缩索引”一节）。', '']

    # 6. 下一个编号
    all_ids = list(defined)
    out.append('## 下一个可用编号')
    out.append('　'.join(casekit.next_id(all_ids, k) for k in 'MEDQT'))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
