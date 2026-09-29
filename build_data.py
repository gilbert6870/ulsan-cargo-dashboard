#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prism_data.csv -> data/monthly_YYYYMM.csv, data/index.json, data/summary.json

집계 기준 (PLISM API 원본 필드 기준):
  - 중복제거 : 수출입구분 + MRN + 컨테이너번호  (한 컨테이너에 MBL이 여러 개여도 1회만 집계)
  - 운항선사 : MRN 앞 4자리 선사부호 (예: 26SNKO2349I -> SNKO)
  - 항구     : MRN 목록의 국내항 UN/LOCODE (KRUSN=울산 ...). 구버전 수집분은 공란
  - FULL/EMPTY : MBL bl_type == 'E' 이면 EMPTY. 구버전 수집분은 공란
"""
import csv, json, sys
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
SRC = BASE / 'data' / 'prism_data.csv'
OUT = BASE / 'data'

def main():
    if not SRC.exists():
        print(f'[ERROR] {SRC} 없음'); sys.exit(1)
    with open(SRC, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        rows = list(reader)
    for h in ['운항선사코드', '항구', '세관', 'BL구분', 'FE', '화물구분']:
        if h not in headers: headers.append(h)

    seen, dedup = set(), []
    for r in rows:
        mrn = r.get('MRN', '')
        if not r.get('운항선사코드'): r['운항선사코드'] = mrn[2:6] if len(mrn) >= 6 else ''
        k = (r.get('수출입구분', ''), mrn, r.get('컨테이너번호', ''))
        if k in seen: continue
        seen.add(k); dedup.append(r)
    print(f'원본 {len(rows):,}행 -> 중복제거 {len(dedup):,}행 (-{len(rows)-len(dedup):,})')

    by_month = defaultdict(list)
    for r in dedup:
        ym = (r.get('출발일자', '') or '').replace('.', '').replace('-', '')[:6]
        if len(ym) == 6 and ym >= '202601': by_month[ym].append(r)

    index, summ = {}, defaultdict(lambda: [0.0, 0])
    for ym, rs in sorted(by_month.items()):
        with open(OUT / f'monthly_{ym}.csv', 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=headers, restval='', extrasaction='ignore')
            w.writeheader(); w.writerows(rs)
        t = lambda r: float(r.get('TEU') or 0)
        index[ym] = {
            'rows': len(rs),
            'teu': round(sum(t(r) for r in rs)),
            'exp_teu': round(sum(t(r) for r in rs if r.get('수출입구분') == '수출')),
            'imp_teu': round(sum(t(r) for r in rs if r.get('수출입구분') == '수입')),
            'vessels': len({r.get('모선명') for r in rs}),
        }
        for r in rs:
            key = (ym, r.get('운항선사코드', ''), r.get('항구', ''), r.get('수출입구분', ''),
                   r.get('FE', ''), r.get('화물구분', '') or r.get('풀엠티구분', ''))
            summ[key][0] += t(r); summ[key][1] += 1
        print(f'  {ym}: {len(rs):,}행  {index[ym]["teu"]:,} TEU')

    (OUT / 'index.json').write_text(json.dumps({'months': index}, ensure_ascii=False, indent=1), encoding='utf-8')
    summary = {'cols': ['ym', 'carrier', 'port', 'dir', 'fe', 'cls', 'teu', 'cnt'],
               'rows': [list(k) + [round(v[0]), v[1]] for k, v in sorted(summ.items())]}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False), encoding='utf-8')
    print(f'index.json / summary.json ({len(summary["rows"])}행) 저장 완료')

if __name__ == '__main__':
    main()
