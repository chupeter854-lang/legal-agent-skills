#!/usr/bin/env python3
"""找出材料目录里还没登记的新材料，可选直接登记并分配 M 编号。

用文件指纹（SHA256 前 12 位）判断新旧：改了名的同一份文件不会重复登记；
内容变了的同名文件算新材料（例如对方补充提交的新版本）。

用法：
  python3 scan_materials.py <工作台文件夹>             只列出，不改文件
  python3 scan_materials.py <工作台文件夹> --register  新材料写入 材料登记.md，状态“待入卷”

编号在这里一次分好，再交给并行的入卷子代理，避免各自编号撞车。
"""
import argparse
import datetime
import os

import casekit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tracker')
    ap.add_argument('--register', action='store_true')
    a = ap.parse_args()

    s = casekit.load_settings(a.tracker)
    tracker, mdir = s['_tracker'], s['_materials']
    if not os.path.isdir(mdir):
        raise SystemExit(f'材料目录不存在：{mdir}')

    rows = casekit.ledger_rows(tracker, 'M')
    known = {r.get('指纹', ''): r for r in rows}
    ids = [r['编号'] for r in rows]

    new, dup = [], []
    seen_now = {}
    for rel in casekit.material_files(mdir):
        fp = casekit.sha256(os.path.join(mdir, rel))[:12]
        if fp in known:
            if known[fp].get('路径') != rel:
                dup.append((rel, known[fp]['编号'], known[fp].get('路径')))
            continue
        if fp in seen_now:
            dup.append((rel, '本次新材料', seen_now[fp]))
            continue
        seen_now[fp] = rel
        new.append((rel, fp))

    on_disk = set(casekit.material_files(mdir))
    missing = [r for r in rows if r.get('路径') and r['路径'] not in on_disk]
    pending = [r for r in rows if r.get('状态') == '待入卷']

    assigned = []
    for rel, fp in new:
        nid = casekit.next_id(ids, 'M')
        ids.append(nid)
        assigned.append((nid, rel, fp))

    if a.register and assigned:
        path = os.path.join(tracker, casekit.LEDGER_FILES['M'])
        text = casekit.read(path).rstrip('\n') + '\n'
        today = datetime.date.today().isoformat()
        for nid, rel, fp in assigned:
            name = os.path.splitext(os.path.basename(rel))[0].replace('|', '／')
            text += f'| {nid} | {name} | {rel.replace("|", "／")} | {fp} | {today} | 待入卷 |  |  |\n'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    print(f'材料目录：{mdir}')
    if assigned:
        print(f'\n新材料 {len(assigned)} 份' + ('（已登记为“待入卷”）' if a.register else '（未登记，加 --register 登记）') + '：')
        for nid, rel, _ in assigned:
            print(f'  {nid}  {rel}')
    else:
        print('\n没有新材料。')
    if pending:
        print(f'\n此前登记但尚未入卷 {len(pending)} 份：' + '、'.join(r['编号'] for r in pending))
    if dup:
        print('\n内容与已登记材料相同（只是改名或重复放置），不另登记：')
        for rel, nid, old in dup:
            print(f'  {rel}  = {nid}（{old}）')
    if missing:
        print('\n登记过但在材料目录里找不到（可能被移动或改名后内容也变了）：')
        for r in missing:
            print(f'  {r["编号"]}  {r["路径"]}')


if __name__ == '__main__':
    main()
