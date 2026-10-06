#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prism_data.csv -> data/monthly_YYYYMM.csv, data/index.json, data/summary.json

집계 기준 (PLISM API 원본 필드 기준):
  - 중복제거 : 수출입구분 + MRN + 컨테이너번호  (한 컨테이너에 MBL이 여러 개여도 1회만 집계)
  - 선사     : MBL번호 앞 4자리 (예: HASLJ0126... -> HASL)  ← 물동량 집계 기준
  - 운항선사 : MRN 앞 4자리 (모선 운항사, 참고용)
  - 신고세관 : MRN 목록 customs 앞 3자리 (110=울산세관 ...). 구버전 수집분은 공란
  - 선박명   : MRN 목록 vessel_name
  - FULL/EMPTY : MBL bl_type == 'E' 이면 EMPTY. 구버전 수집분은 공란
"""
import csv, json, sys, os
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
SRC = BASE / 'data' / 'prism_data.csv'
OUT = BASE / 'data'
# --only 202607,202608 : 해당 월 CSV만 다시 씀 (index/summary는 항상 전체)
ONLY = None
if '--only' in sys.argv:
    ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(','))

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
        if ONLY is None or ym in ONLY:
          tmp = OUT / f'.tmp_monthly_{ym}.csv'
          with open(tmp, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=headers, restval='', extrasaction='ignore')
            w.writeheader(); w.writerows(rs)
          os.replace(tmp, OUT / f'monthly_{ym}.csv')   # 중간에 끊겨도 기존 파일 보존
        t = lambda r: float(r.get('TEU') or 0)
        index[ym] = {
            'rows': len(rs),
            'teu': round(sum(t(r) for r in rs)),
            'exp_teu': round(sum(t(r) for r in rs if r.get('수출입구분') == '수출')),
            'imp_teu': round(sum(t(r) for r in rs if r.get('수출입구분') == '수입')),
            'vessels': len({r.get('모선명') for r in rs}),
        }
        for r in rs:
            key = (ym, r.get('운항선사코드', ''), (r.get('세관', '') or '')[:3], r.get('수출입구분', ''),
                   r.get('FE', ''), r.get('화물구분', '') or r.get('풀엠티구분', ''),
                   (r.get('MBL번호', '') or '')[:4], r.get('모선명', ''))
            summ[key][0] += t(r); summ[key][1] += 1
        print(f'  {ym}: {len(rs):,}행  {index[ym]["teu"]:,} TEU')

    from datetime import datetime
    last_col = max((r.get('수집일시', '') or '' for r in dedup), default='')
    meta = {'updated': datetime.now().strftime('%Y-%m-%d %H:%M'), 'last_collected': last_col[:16]}
    (OUT / 'index.json').write_text(json.dumps({'months': index, **meta}, ensure_ascii=False, indent=1), encoding='utf-8')
    summary = {'cols': ['ym', 'operator', 'customs', 'dir', 'fe', 'cls', 'teu', 'cnt', 'bl_carrier', 'vessel'],
               'rows': [list(k[:6]) + [round(v[0]), v[1], k[6], k[7]] for k, v in sorted(summ.items())]}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False), encoding='utf-8')
    print(f'index.json / summary.json ({len(summary["rows"])}행) 저장 완료')

if __name__ == '__main__':
    main()
