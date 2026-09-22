#!/usr/bin/env python3
"""
흥아라인 울산항 물동량 - PLISM 3.0 자동 데이터 수집
======================================================
PLISM 3.0 (www.plism.com) - KL-Net 운영 시스템
수출 MFCS + 수입 적하목록 데이터 수집

사용법:
  1. .env 파일에 로그인 정보 입력 (메모장으로 편집)
  2. python fetch_prism.py              # 오늘 기준 최근 30일
  3. python fetch_prism.py --days 7     # 최근 7일
  4. python fetch_prism.py --watch      # 30분마다 자동 반복
  5. python fetch_prism.py --date-from 20260901 --date-to 20260922

필요 패키지:
  pip install playwright python-dotenv pandas requests
  playwright install chromium
"""

import os
import sys
import time
import json
import argparse
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path

# ─── .env 로드 ───────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 로드 완료")
except ImportError:
    print("⚠️  python-dotenv 없음. pip install python-dotenv")

# ─── 설정값 ───────────────────────────────────────────────
PLISM_BASE    = "https://www.plism.com"
USER_ID       = os.getenv("PRISM_USER_ID", "")
PASSWORD      = os.getenv("PRISM_PASSWORD", "")
KLNET_ID      = os.getenv("PRISM_KLNET_ID", "HASMT010")   # 흥아라인 KL-Net ID
OUTPUT_PATH   = os.getenv("DATA_OUTPUT_PATH", "./data/prism_data.csv")
INTERVAL_MIN  = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))

# ─── CSV 컬럼 (대시보드 index.html과 일치) ───────────────
CSV_COLUMNS = [
    "수출입구분", "모선명", "항차", "출발일자",
    "MBL번호", "화주명", "컨테이너번호", "컨테이너규격",
    "컨테이너코드", "풀엠티구분", "TEU", "수량",
    "MRN", "수집일시"
]

# ─── 컨테이너 코드 → 사이즈/TEU 변환 ────────────────────
def parse_container_code(cntr_code):
    """
    cntr_code 예: 22GP, 42GP, 45GP, 22RE, 42RE
    앞 두 자리로 사이즈 결정:
      22xx → 20' (1 TEU)
      42xx, 45xx → 40' (2 TEU)
    """
    if not cntr_code:
        return "20'", 1
    code = str(cntr_code).strip().upper()
    prefix = code[:2] if len(code) >= 2 else code
    if prefix.startswith('2'):
        return "20'", 1
    elif prefix.startswith('4'):
        return "40'", 2
    return "20'", 1


def check_credentials():
    if not USER_ID:
        print("❌ .env 파일에 PRISM_USER_ID 입력 필요")
        return False
    if not PASSWORD:
        print("❌ .env 파일에 PRISM_PASSWORD 입력 필요")
        return False
    return True


# ─── PLISM 3.0 로그인 ─────────────────────────────────────
def login_plism(page):
    """Playwright page로 PLISM 3.0 로그인"""
    print(f"  🌐 PLISM 3.0 접속: {PLISM_BASE}")
    page.goto(f"{PLISM_BASE}/uat/uia/plism3Main.do", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    # 로그인 폼 찾기
    # PLISM 3.0 로그인: id/pw 입력 후 로그인 버튼 클릭
    try:
        # 아이디 입력
        id_field = page.locator("input[name='user_id'], input[id*='userId'], input[id*='id'], #id, #user_id").first
        id_field.fill(USER_ID)
        page.wait_for_timeout(300)

        # 비밀번호 입력
        pw_field = page.locator("input[type='password']").first
        pw_field.fill(PASSWORD)
        page.wait_for_timeout(300)

        # 로그인 버튼 클릭
        login_btn = page.locator("button[type='submit'], input[type='submit'], a:has-text('로그인'), button:has-text('로그인')").first
        login_btn.click()
        page.wait_for_timeout(3000)

        # 로그인 성공 확인
        if "plism3Sub" in page.url or "plism3Main" in page.url:
            print(f"  ✅ 로그인 성공")
            return True
        else:
            print(f"  ⚠️  로그인 후 URL: {page.url}")
            return True  # URL 확인 없이 진행
    except Exception as e:
        print(f"  ❌ 로그인 오류: {e}")
        return False


# ─── API 호출 유틸 ────────────────────────────────────────
def api_get_all_pages(page, url, body_builder, page_row=100):
    """
    페이지네이션으로 전체 데이터 수집
    page: Playwright page (쿠키 세션 포함)
    url: API endpoint URL
    body_builder: fn(page_index) → dict (request body)
    """
    all_results = []
    page_index = 1
    total = None

    while True:
        body = body_builder(page_index)
        body_json = json.dumps(body, ensure_ascii=False)

        try:
            response = page.evaluate(f"""
                async () => {{
                    const r = await fetch('{url}', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json;charset=UTF-8'}},
                        body: {json.dumps(body_json)}
                    }});
                    const text = await r.text();
                    return {{status: r.status, text: text}};
                }}
            """)

            if response['status'] != 200:
                print(f"    ⚠️  API 오류 {response['status']}: {url}")
                break

            data = json.loads(response['text'])
            results = data.get('result', [])

            if total is None:
                total = data.get('totCnt', len(results))
                print(f"    📊 총 {total}건 수집 중...")

            if not results:
                break

            all_results.extend(results)

            if len(all_results) >= total:
                break

            page_index += 1
            time.sleep(0.3)  # API 부하 방지

        except Exception as e:
            print(f"    ❌ API 오류: {e}")
            break

    return all_results


# ─── 수출 데이터 수집 ─────────────────────────────────────
def fetch_export_data(page, date_from, date_to):
    """
    수출 MFCS: MRN → MBL → 컨테이너 순으로 수집
    """
    print(f"\n  📦 수출 데이터 수집 ({date_from} ~ {date_to})")
    rows = []

    # 1. 수출 MRN 목록 (vessel/voyage 단위)
    exp_mrn_url = f"{PLISM_BASE}/plism3/oks/cms/mng/selectKmcsExpMrnList.do"
    mrn_list = api_get_all_pages(
        page, exp_mrn_url,
        lambda pi: {"reqMap": {
            "etd_date_fr": date_from,
            "etd_date_to": date_to,
            "sKlnetId": KLNET_ID,
            "pageIndex": pi,
            "pageRowCount": 100
        }}
    )
    print(f"    🚢 수출 MRN: {len(mrn_list)}건")

    for mrn_info in mrn_list:
        mrn = mrn_info.get('mrn', '')
        cls = mrn_info.get('customs_line_code', '')
        vessel = mrn_info.get('vessel_name', '')
        voyage = mrn_info.get('voyage_no', '')
        dep_date = mrn_info.get('dpt_date', '') or mrn_info.get('dpt_date_excel', '')
        # 날짜 정규화 (YYYY-MM-DD → YYYYMMDD)
        dep_date_str = dep_date.replace('-', '')[:8] if dep_date else date_from

        # 2. 수출 MBL 목록
        exp_mbl_url = f"{PLISM_BASE}/oks/doc/mng/selectExpMblList.do"
        mbl_list = api_get_all_pages(
            page, exp_mbl_url,
            lambda pi, m=mrn, c=cls: {"req": {
                "mrn": m, "customs_line_code": c,
                "sKlnetId": KLNET_ID,
                "pageIndex": pi, "pageRowCount": 100
            }}
        )

        for mbl in mbl_list:
            mbl_no = mbl.get('mbl_no', '')
            shipper = mbl.get('shipper', '') or mbl.get('shipper1', '')
            cntr_num = int(mbl.get('cntr_num', 0) or 0)

            # 3. 컨테이너 목록
            exp_cntr_url = f"{PLISM_BASE}/oks/doc/mng/selectExpCntrList.do"
            cntr_list = api_get_all_pages(
                page, exp_cntr_url,
                lambda pi, m=mrn, c=cls, bn=mbl_no: {"req": {
                    "mrn": m, "customs_line_code": c, "mbl_no": bn,
                    "sKlnetId": KLNET_ID,
                    "pageIndex": pi, "pageRowCount": 200
                }}
            )

            if cntr_list:
                for cntr in cntr_list:
                    size, teu = parse_container_code(cntr.get('cntr_code', ''))
                    rows.append({
                        "수출입구분": "수출",
                        "모선명": vessel,
                        "항차": voyage,
                        "출발일자": dep_date_str,
                        "MBL번호": mbl_no,
                        "화주명": shipper,
                        "컨테이너번호": cntr.get('cntr_no', ''),
                        "컨테이너규격": size,
                        "컨테이너코드": cntr.get('cntr_code', ''),
                        "풀엠티구분": "F",  # 수출 적하목록 = Full
                        "TEU": teu,
                        "수량": 1,
                        "MRN": mrn,
                        "수집일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            elif cntr_num > 0:
                # 컨테이너 상세 없으면 MBL 단위로 집계
                rows.append({
                    "수출입구분": "수출",
                    "모선명": vessel,
                    "항차": voyage,
                    "출발일자": dep_date_str,
                    "MBL번호": mbl_no,
                    "화주명": shipper,
                    "컨테이너번호": "",
                    "컨테이너규격": "",
                    "컨테이너코드": "",
                    "풀엠티구분": "F",
                    "TEU": cntr_num,
                    "수량": cntr_num,
                    "MRN": mrn,
                    "수집일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        time.sleep(0.2)

    print(f"    ✅ 수출 {len(rows)}개 컨테이너 수집 완료")
    return rows


# ─── 수입 데이터 수집 ─────────────────────────────────────
def fetch_import_data(page, date_from, date_to):
    """
    수입 적하목록: MRN → MBL → 컨테이너 순으로 수집
    """
    print(f"\n  📦 수입 데이터 수집 ({date_from} ~ {date_to})")
    rows = []

    # 1. 수입 MRN 목록
    imp_mrn_url = f"{PLISM_BASE}/iks/doc/mng/selectImpMrnList.do"
    mrn_list = api_get_all_pages(
        page, imp_mrn_url,
        lambda pi: {"req": {
            "from_date": date_from,
            "to_date": date_to,
            "sKlnetId": KLNET_ID,
            "pageIndex": pi,
            "pageRowCount": 100
        }}
    )
    print(f"    🚢 수입 MRN: {len(mrn_list)}건")

    for mrn_info in mrn_list:
        mrn = mrn_info.get('mrn', '')
        cls = mrn_info.get('customs_line_code', '')
        vessel = mrn_info.get('vessel_name', '')
        voyage = mrn_info.get('voyage_no', '')
        arv_date = mrn_info.get('arv_date', '') or mrn_info.get('eta', '')
        arv_date_str = arv_date.replace('-', '')[:8] if arv_date else date_from

        # 2. 수입 MBL 목록
        imp_mbl_url = f"{PLISM_BASE}/iks/doc/mng/selectImpMblDtlList.do"
        mbl_list = api_get_all_pages(
            page, imp_mbl_url,
            lambda pi, m=mrn, c=cls: {"req": {
                "mrn": m, "customs_line_code": c,
                "sKlnetId": KLNET_ID,
                "pageIndex": pi, "pageRowCount": 100
            }}
        )

        for mbl in mbl_list:
            mbl_no = mbl.get('mbl_no', '')
            consignee = mbl.get('consignee', '') or mbl.get('consignee1', '')
            cntr_cnt = int(mbl.get('cntr_cnt', 0) or 0)

            # 3. 컨테이너 목록
            imp_cntr_url = f"{PLISM_BASE}/iks/doc/mng/selectImpCntrList.do"
            cntr_list = api_get_all_pages(
                page, imp_cntr_url,
                lambda pi, m=mrn, c=cls, bn=mbl_no: {"req": {
                    "mrn": m, "customs_line_code": c, "mbl_no": bn,
                    "sKlnetId": KLNET_ID,
                    "pageIndex": pi, "pageRowCount": 200
                }}
            )

            if cntr_list:
                for cntr in cntr_list:
                    size, teu = parse_container_code(cntr.get('cntr_code', ''))
                    rows.append({
                        "수출입구분": "수입",
                        "모선명": vessel,
                        "항차": voyage,
                        "출발일자": arv_date_str,
                        "MBL번호": mbl_no,
                        "화주명": consignee,
                        "컨테이너번호": cntr.get('cntr_no', ''),
                        "컨테이너규격": size,
                        "컨테이너코드": cntr.get('cntr_code', ''),
                        "풀엠티구분": "F",  # 수입 적하목록 = Full
                        "TEU": teu,
                        "수량": int(cntr.get('pack_num', 0) or 0),
                        "MRN": mrn,
                        "수집일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            elif cntr_cnt > 0:
                rows.append({
                    "수출입구분": "수입",
                    "모선명": vessel,
                    "항차": voyage,
                    "출발일자": arv_date_str,
                    "MBL번호": mbl_no,
                    "화주명": consignee,
                    "컨테이너번호": "",
                    "컨테이너규격": "",
                    "컨테이너코드": "",
                    "풀엠티구분": "F",
                    "TEU": cntr_cnt,
                    "수량": int(mbl.get('pack_num', 0) or 0),
                    "MRN": mrn,
                    "수집일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        time.sleep(0.2)

    print(f"    ✅ 수입 {len(rows)}개 컨테이너 수집 완료")
    return rows


# ─── CSV 저장 ─────────────────────────────────────────────
def save_to_csv(rows, output_path):
    """데이터를 CSV로 저장"""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  💾 저장 완료: {out} ({len(rows)}건)")
    return True


# ─── 메인 실행 ────────────────────────────────────────────
def run_once(date_from=None, date_to=None, days=30):
    """1회 데이터 수집 실행"""
    if not check_credentials():
        return False

    # 날짜 범위 설정
    if not date_to:
        date_to = datetime.now().strftime('%Y%m%d')
    if not date_from:
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

    print(f"\n{'='*55}")
    print(f"🚀 PLISM 3.0 데이터 수집 시작")
    print(f"   기간: {date_from} ~ {date_to}")
    print(f"   KL-Net ID: {KLNET_ID}")
    print(f"{'='*55}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright 미설치:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return False

    all_rows = []
    success = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            # 로그인
            if not login_plism(page):
                print("❌ 로그인 실패")
                return False

            # 메인 페이지 로드 대기
            page.wait_for_timeout(2000)

            # 수출 데이터 수집
            export_rows = fetch_export_data(page, date_from, date_to)
            all_rows.extend(export_rows)

            # 수입 데이터 수집
            import_rows = fetch_import_data(page, date_from, date_to)
            all_rows.extend(import_rows)

            # CSV 저장
            if all_rows:
                save_to_csv(all_rows, OUTPUT_PATH)
                success = True
            else:
                print("⚠️  수집된 데이터 없음")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            # 스크린샷 저장
            try:
                page.screenshot(path="./data/error_screenshot.png")
                print("   📸 오류 스크린샷: ./data/error_screenshot.png")
            except:
                pass
        finally:
            browser.close()

    # 결과 요약
    if all_rows:
        exp_cnt = sum(1 for r in all_rows if r['수출입구분'] == '수출')
        imp_cnt = sum(1 for r in all_rows if r['수출입구분'] == '수입')
        exp_teu = sum(r['TEU'] for r in all_rows if r['수출입구분'] == '수출')
        imp_teu = sum(r['TEU'] for r in all_rows if r['수출입구분'] == '수입')
        print(f"\n{'='*55}")
        print(f"📊 수집 결과 요약")
        print(f"   수출: {exp_cnt}건 / {exp_teu} TEU")
        print(f"   수입: {imp_cnt}건 / {imp_teu} TEU")
        print(f"   합계: {len(all_rows)}건 / {exp_teu + imp_teu} TEU")
        print(f"{'='*55}\n")

    return success


def run_watch(date_from=None, date_to=None, days=30):
    """주기적 반복 실행"""
    print(f"⏰ 감시 모드: {INTERVAL_MIN}분마다 자동 수집")
    while True:
        run_once(date_from, date_to, days)
        next_run = datetime.now() + timedelta(minutes=INTERVAL_MIN)
        print(f"⏳ 다음 수집: {next_run.strftime('%H:%M:%S')}")
        time.sleep(INTERVAL_MIN * 60)


# ─── 진입점 ───────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PLISM 3.0 흥아라인 울산항 물동량 수집')
    parser.add_argument('--watch', action='store_true', help='자동 반복 실행')
    parser.add_argument('--days', type=int, default=30, help='조회 기간 (기본 30일)')
    parser.add_argument('--date-from', type=str, default=None, help='시작일 (YYYYMMDD)')
    parser.add_argument('--date-to',   type=str, default=None, help='종료일 (YYYYMMDD)')
    args = parser.parse_args()

    if args.watch:
        run_watch(args.date_from, args.date_to, args.days)
    else:
        ok = run_once(args.date_from, args.date_to, args.days)
        sys.exit(0 if ok else 1)
