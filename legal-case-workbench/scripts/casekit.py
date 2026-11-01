"""案件工作台脚本共用的小工具：读设置、解析 Markdown 表格、算文件指纹。

只用标准库，兼容 Python 3.9。
"""
import hashlib
import json
import os
import re

SETTINGS = '工作台设置.json'
LEDGER_FILES = {
    'M': '材料登记.md',
    'E': '时间线.md',
    'D': '期限表.md',
    'Q': '待办与争点.md',
}
INDEX = '案件索引.md'
TOPIC_DIR = '议题'
ID_RE = re.compile(r'\b([MEDQT])-(\d{3,})\b')
SKIP_NAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}


def load_settings(tracker):
    path = os.path.join(tracker, SETTINGS)
    if not os.path.exists(path):
        raise SystemExit(f'找不到 {path}：这个文件夹还没有建立案件工作台（先运行 init_case.py）。')
    with open(path, encoding='utf-8') as f:
        s = json.load(f)
    s['_tracker'] = os.path.abspath(tracker)
    md = s.get('材料目录', '材料')
    s['_materials'] = md if os.path.isabs(md) else os.path.normpath(os.path.join(s['_tracker'], md))
    return s


def read(path):
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read()


def _cells(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c.strip() for c in line.split('|')]


def parse_tables(text):
    """返回文件里所有表格：[{'header': [...], 'rows': [dict, ...]}]。"""
    tables, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        if lines[i].lstrip().startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|?\s*:?-{2,}', lines[i + 1]):
            header = _cells(lines[i])
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                cells = _cells(lines[i])
                cells += [''] * (len(header) - len(cells))
                rows.append(dict(zip(header, cells)))
                i += 1
            tables.append({'header': header, 'rows': rows})
        else:
            i += 1
    return tables


def ledger_rows(tracker, kind):
    """某张登记表里编号以 kind- 开头的行（跳过模板里的空行）。"""
    text = read(os.path.join(tracker, LEDGER_FILES[kind]))
    out = []
    for t in parse_tables(text):
        if '编号' not in t['header']:
            continue
        for r in t['rows']:
            if re.fullmatch(rf'{kind}-\d{{3,}}', r.get('编号', '')):
                out.append(r)
    return out


def topic_ids(tracker):
    d = os.path.join(tracker, TOPIC_DIR)
    if not os.path.isdir(d):
        return []
    ids = []
    for name in sorted(os.listdir(d)):
        m = re.match(r'(T-\d{3,})', name)
        if m:
            ids.append(m.group(1))
    return ids


def next_id(existing, kind):
    nums = [int(x.split('-')[1]) for x in existing if x.startswith(kind + '-')]
    return f'{kind}-{(max(nums) if nums else 0) + 1:03d}'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def material_files(materials_dir):
    """材料目录下的全部文件（相对路径），跳过隐藏文件和 Office 临时文件。"""
    out = []
    for root, dirs, files in os.walk(materials_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for name in sorted(files):
            if name.startswith('.') or name.startswith('~$') or name in SKIP_NAMES:
                continue
            out.append(os.path.relpath(os.path.join(root, name), materials_dir))
    return out
