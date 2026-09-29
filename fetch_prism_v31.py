#!/usr/bin/env python3
"""
흥아라인 울산항 물동량 - PLISM 3.1 자동 수집 (자동 로그인 + 증분 업데이트)
=========================================================
변경 사항 (v3.1):
  - .env의 PRISM_USER_ID / PRISM_PASSWORD로 자동 로그인
  - 기존 CSV와 병합 (증분 업데이트 - 변동사항만 수정)
  - --full-replace 시 전체 교체

사용법:
  python fetch_prism_v31.py                        # 최근 7일 증분 업데이트
  python fetch_prism_v31.py --days 30              # 최근 30일 증분 업데이트
  python fetch_prism_v31.py --full-replace         # 최근 30일 전체 교체
  python fetch_prism_v31.py --date-from 20260901 --date-to 20260929
  python fetch_prism_v31.py --watch                # 30분마다 자동 반복
"""

import os, sys, time, json, csv, argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. pip install python-dotenv")

# ─── 설정 ────────────────────────────────────────────────
PLISM_BASE   = os.getenv("PRISM_URL", "https://www.plism.com")
KLNET_ID     = os.getenv("PRISM_KLNET_ID", "HASMT010")
USER_ID      = os.getenv("PRISM_USER_ID", "")
PASSWORD     = os.getenv("PRISM_PASSWORD", "")
OUTPUT_PATH  = os.getenv("DATA_OUTPUT_PATH", "./data/prism_data.csv")
INTERVAL_MIN = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))
PROFILE_DIR  = os.getenv("CHROME_PROFILE_PATH", "./browser_profile")

PROJECT_DIR = Path(__file__).parent.resolve()
DATA_DIR    = (PROJECT_DIR / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
if not Path(OUTPUT_PATH).is_absolute():
    OUTPUT_PATH = str((PROJECT_DIR / OUTPUT_PATH).resolve())

LOG_PATH = str(DATA_DIR / "run_debug.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ─── 데이터 수집 JavaScript ──────────────────────────────
COLLECTION_JS = """
async (args) => {
  const { klnetId, dateFrom, dateTo } = args;

  const fetchAllPages = async (url, bodyBuilder) => {
    let allResults = [], pageIndex = 1, total = null;
    while (true) {
      const body = bodyBuilder(pageIndex);
      const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json;charset=UTF-8'},
        body: JSON.stringify(body)
      });
      if (!resp.ok) break;
      const data = await resp.json();
      const results = data.result || [];
      if (total === null) total = data.totCnt || results.length;
      if (!results.length) break;
      allResults = allResults.concat(results);
      if (allResults.length >= total) break;
      pageIndex++;
    }
    return allResults;
  };

  const batchAsync = async (items, fn, concurrency = 30) => {
    const res = [];
    for (let i = 0; i < items.length; i += concurrency) {
      const chunk = items.slice(i, i + concurrency);
      const cr = await Promise.all(chunk.map(fn));
      res.push(...cr);
    }
    return res;
  };

  const parseCntr = (code) => {
    if (!code) return { size: "20'", teu: 1 };
    return code.substring(0, 1) === '4' ? { size: "40'", teu: 2 } : { size: "20'", teu: 1 };
  };

  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  const expMrnList = await fetchAllPages(
    '/plism3/oks/cms/mng/selectKmcsExpMrnList.do',
    (p) => ({ reqMap: { etd_date_fr: dateFrom, etd_date_to: dateTo, sKlnetId: klnetId, pageIndex: p, pageRowCount: 100 } })
  );

  const expMblList = (await batchAsync(expMrnList, async (mrn) => {
    try {
      const r = await fetch('/oks/doc/mng/selectExpMblDtlList.do', {
        method: 'POST', headers: {'Content-Type': 'application/json;charset=UTF-8'},
        body: JSON.stringify({ req: { mrn: mrn.mrn, customs_line_code: mrn.customs_line_code, pageIndex: 1, pageRowCount: 200 } })
      });
      const d = await r.json();
      return (d.result || []).map(m => ({ ...m, dpt_date: mrn.dpt_date, vessel_name: mrn.vessel_name, voyage_no: mrn.voyage_no }));
    } catch (e) { return []; }
  }, 30)).flat();

  const expRows = (await batchAsync(expMblList, async (mbl) => {
    try {
      const r = await fetch('/oks/doc/mng/selectExpCntrList.do', {
        method: 'POST', headers: {'Content-Type': 'application/json;charset=UTF-8'},
        body: JSON.stringify({ req: { mrn: mbl.mrn, mbl_no: mbl.mbl_no, customs_line_code: mbl.customs_line_code, pageIndex: 1, pageRowCount: 200 } })
      });
      const d = await r.json();
      return (d.result || []).map(c => {
        const sz = parseCntr(c.cntr_code);
        return {
          type: '수출', vessel: mbl.vessel_name || '', voyage: mbl.voyage_no || '',
          date: mbl.dpt_date ? mbl.dpt_date.substring(0, 8) : '',
          mbl_no: mbl.mbl_no, shipper: mbl.shipper || '',
          cntr_no: c.cntr_no, cntr_size: sz.size, cntr_code: c.cntr_code,
          fm: mbl.cargo_character || '', teu: sz.teu, qty: 1, mrn: mbl.mrn, collected: now
        };
      });
    } catch (e) { return []; }
  }, 30)).flat();

  const impMrnList = await fetchAllPages(
    '/plism3/iks/cms/mng/selectKmcsImpMrnList.do',
    (p) => ({ reqMap: { arv_date_fr: dateFrom, arv_date_to: dateTo, sKlnetId: klnetId, pageIndex: p, pageRowCount: 100 } })
  );

  const impMblList = (await batchAsync(impMrnList, async (mrn) => {
    try {
      const r = await fetch('/iks/doc/mng/selectImpMblDtlList.do', {
        method: 'POST', headers: {'Content-Type': 'application/json;charset=UTF-8'},
        body: JSON.stringify({ req: { mrn: mrn.mrn, customs_line_code: mrn.customs_line_code, pageIndex: 1, pageRowCount: 200 } })
      });
      const d = await r.json();
      return (d.result || []).map(m => ({ ...m, arv_date: mrn.arv_date, vessel_name: mrn.vessel_name, voyage_no: mrn.voyage_no }));
    } catch (e) { return []; }
  }, 30)).flat();

  const impRows = (await batchAsync(impMblList, async (mbl) => {
    try {
      const r = await fetch('/iks/doc/mng/selectImpCntrList.do', {
        method: 'POST', headers: {'Content-Type': 'application/json;charset=UTF-8'},
        body: JSON.stringify({ req: { mrn: mbl.mrn, mbl_no: mbl.mbl_no, customs_line_code: mbl.customs_line_code, pageIndex: 1, pageRowCount: 200 } })
      });
      const d = await r.json();
      return (d.result || []).map(c => {
        const sz = parseCntr(c.cntr_code);
        return {
          type: '수입', vessel: mbl.vessel_name || '', voyage: mbl.voyage_no || '',
          date: mbl.arv_date || '',
          mbl_no: mbl.mbl_no, shipper: mbl.consignee || '',
          cntr_no: c.cntr_no, cntr_size: sz.size, cntr_code: c.cntr_code,
          fm: mbl.cargo_class || '', teu: sz.teu, qty: 1, mrn: mbl.mrn, collected: now
        };
      });
    } catch (e) { return []; }
  }, 30)).flat();

  return {
    rows: [...expRows, ...impRows],
    stats: {
      exp_mrn: expMrnList.length, exp_mbl: expMblList.length, exp_cntr: expRows.length,
      imp_mrn: impMrnList.length, imp_mbl: impMblList.length, imp_cntr: impRows.length,
      exp_teu: expRows.reduce((s, r) => s + r.teu, 0),
      imp_teu: impRows.reduce((s, r) => s + r.teu, 0),
    }
  };
}
"""

CSV_HEADERS = ['수출입구분','모선명','항차','출발일자','MBL번호','화주명',
               '컨테이너번호','컨테이너규격','컨테이너코드','풀엠티구분','TEU','수량','MRN','수집일시']

ROW_KEY_MAP = {
    '수출입구분':'type','모선명':'vessel','항차':'voyage','출발일자':'date',
    'MBL번호':'mbl_no','화주명':'shipper','컨테이너번호':'cntr_no',
    '컨테이너규격':'cntr_size','컨테이너코드':'cntr_code','풀엠티구분':'fm',
    'TEU':'teu','수량':'qty','MRN':'mrn','수집일시':'collected'
}

# 고유 키: 수출입구분 + MRN + MBL번호 + 컨테이너번호
UNIQUE_KEYS = ['수출입구분', 'MRN', 'MBL번호', '컨테이너번호']
# 비교에서 제외할 컬럼 (수집일시는 매번 바뀌므로 변동 판단에서 제외)
SKIP_COMPARE = {'수집일시'}


def incremental_update(new_rows, output_path):
    """기존 CSV와 병합 - 변동사항만 수정, 신규만 추가"""
    # 기존 데이터 로드
    existing = {}
    if Path(output_path).exists():
        try:
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = tuple(row.get(k, '') for k in UNIQUE_KEYS)
                    existing[key] = dict(row)
            log(f"기존 데이터 로드: {len(existing)}행")
        except Exception as e:
            log(f"기존 CSV 읽기 실패 (새로 생성): {e}")

    added = updated = unchanged = 0

    for r in new_rows:
        new_row = {h: str(r.get(ROW_KEY_MAP[h], '')) for h in CSV_HEADERS}
        key = tuple(new_row.get(k, '') for k in UNIQUE_KEYS)

        if key not in existing:
            existing[key] = new_row
            added += 1
        else:
            # 변동 확인 (수집일시 제외)
            changed = any(
                existing[key].get(h, '') != new_row.get(h, '')
                for h in CSV_HEADERS if h not in SKIP_COMPARE
            )
            if changed:
                new_row['수집일시'] = existing[key].get('수집일시', new_row['수집일시'])  # 최초 수집일시 유지
                existing[key] = new_row
                updated += 1
            else:
                unchanged += 1

    log(f"증분 결과 → 신규: {added}행, 변경: {updated}행, 유지: {unchanged}행")

    # 저장 (출발일자 기준 정렬)
    all_rows = list(existing.values())
    try:
        all_rows.sort(key=lambda r: (r.get('출발일자',''), r.get('수출입구분',''), r.get('모선명','')))
    except Exception:
        pass

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_rows)

    return len(all_rows), added, updated, unchanged


def rows_to_csv(rows, output_path):
    """전체 교체 저장"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(ROW_KEY_MAP[h], '') for h in CSV_HEADERS})
    return len(rows)


def _try_fill_and_click(frame, page_ref):
    """주어진 frame에서 ID/PW 입력 후 로그인 버튼 클릭. 성공 시 True."""
    pw_els = frame.query_selector_all('input[type="password"]')
    if not pw_els:
        return False

    log(f"패스워드 필드 {len(pw_els)}개 발견 (frame: {frame.url[:60]})")

    id_el = None
    for sel in ['input[type="text"]', '#userId', '#user_id',
                'input[name="userId"]', 'input[name="user_id"]',
                'input[placeholder*="ID"]', 'input[placeholder*="아이디"]']:
        try:
            el = frame.query_selector(sel)
            if el:
                id_el = el
                log(f"ID 필드 발견: {sel}")
                break
        except Exception:
            pass

    pw_el = pw_els[0]

    try:
        if id_el:
            id_el.fill(USER_ID)
            page_ref.wait_for_timeout(300)
            log("ID 입력 완료")
        pw_el.fill(PASSWORD)
        page_ref.wait_for_timeout(300)
        log("PW 입력 완료")
    except Exception as e:
        log(f"입력 오류: {e}")
        return False

    clicked = False
    for btn_text in ['로그인', 'LOGIN', 'Login', 'login']:
        try:
            btn = frame.get_by_role('button', name=btn_text)
            if btn.count() > 0:
                btn.first.click()
                clicked = True
                log(f"'{btn_text}' 버튼 클릭")
                break
        except Exception:
            pass

    if not clicked:
        try:
            btns = frame.query_selector_all('button, input[type="submit"], a')
            for btn in btns:
                try:
                    txt = (btn.text_content() or btn.get_attribute('value') or '')
                    if '로그인' in txt or 'LOGIN' in txt.upper():
                        btn.click()
                        clicked = True
                        log(f"로그인 버튼 텍스트 매칭 클릭: {txt[:30]}")
                        break
                except Exception:
                    pass
        except Exception as e:
            log(f"버튼 탐색 오류: {e}")

    if not clicked:
        try:
            btns = frame.query_selector_all('[onclick*="login"],[onclick*="Login"],[onclick*="LOGIN"]')
            if btns:
                btns[0].click()
                clicked = True
                log("onclick 버튼 클릭")
        except Exception:
            pass

    if not clicked:
        log("버튼 미발견 → Enter 시도")
        try:
            pw_el.press('Return')
            clicked = True
        except Exception as e:
            log(f"Enter 실패: {e}")

    return clicked


def auto_login(page):
    """자동 로그인 - Playwright frames 탐색 + JS evaluate fallback"""
    if not USER_ID or not PASSWORD:
        log("ERROR: .env에 PRISM_USER_ID / PRISM_PASSWORD 없음")
        return False

    log(f"자동 로그인 시도 (ID: {USER_ID})")
    page.wait_for_timeout(2000)

    ss_start = str(DATA_DIR / f"login_start_{datetime.now().strftime('%H%M%S')}.png")
    try:
        page.screenshot(path=ss_start)
        log(f"로그인 전 스크린샷: {ss_start}")
    except Exception:
        pass

    # 방법 1: Playwright frames 반복 탐색
    try:
        all_frames = page.frames
        log(f"총 frame 수: {len(all_frames)}")
        for frame in all_frames:
            try:
                log(f"Frame 탐색: {frame.url[:80]}")
                if _try_fill_and_click(frame, page):
                    page.wait_for_timeout(5000)
                    log("로그인 완료 (Playwright frame 방식)")
                    return True
            except Exception as e:
                log(f"Frame 오류: {e}")
                continue
    except Exception as e:
        log(f"frames 탐색 오류: {e}")

    # 방법 2: JS evaluate fallback
    log("방법 2: JS evaluate 시도")
    try:
        result = page.evaluate("""
async (args) => {
  const { userId, password } = args;
  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
  ).set;
  const fillField = (el, val) => {
    nativeSetter.call(el, val);
    el.dispatchEvent(new Event('input',  {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
  };
  const tryRoot = (root) => {
    if (!root) return false;
    const pws = root.querySelectorAll('input[type="password"]');
    let pwEl = pws.length > 0 ? pws[0] : null;
    if (!pwEl) return false;
    const idSels = ['#userId','#user_id','[name="userId"]','input[type="text"]'];
    let idEl = null;
    for (const s of idSels) {
      try { idEl = root.querySelector(s); if (idEl) break; } catch(e){}
    }
    if (idEl) fillField(idEl, userId);
    fillField(pwEl, password);
    const allEls = [...root.querySelectorAll('button,input[type="submit"],a,[onclick]')];
    for (const el of allEls) {
      const t = (el.textContent||el.value||el.getAttribute('onclick')||'');
      if (/로그인|login/i.test(t)) { el.click(); return { ok: true, msg: '버튼클릭' }; }
    }
    pwEl.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));
    return { ok: true, msg: 'Enter전송' };
  };
  const r = tryRoot(document);
  if (r) return r;
  for (const fr of document.querySelectorAll('iframe')) {
    try { const r2 = tryRoot(fr.contentDocument); if (r2) return r2; } catch(e) {}
  }
  return { ok: false, msg: '폼 미발견' };
}
""", {'userId': USER_ID, 'password': PASSWORD})

        log(f"JS 결과: {result}")
        if result and result.get('ok'):
            page.wait_for_timeout(5000)
            log("로그인 완료 (JS 방식)")
            return True
    except Exception as e:
        log(f"JS evaluate 오류: {e}")

    ss_fail = str(DATA_DIR / f"login_fail_{datetime.now().strftime('%H%M%S')}.png")
    try:
        page.screenshot(path=ss_fail)
        log(f"로그인 실패 스크린샷: {ss_fail}")
    except Exception:
        pass
    return False


def detect_login_needed(page):
    """로그인 필요 여부 감지"""
    url   = page.url
    title = page.title()
    log(f"접속 URL: {url}")
    log(f"타이틀: {title}")

    if 'login' in url.lower() or 'login' in title.lower():
        log("URL/title에 login 포함 → 로그인 필요")
        return True

    try:
        has_pw = page.evaluate("""() => {
            const check = (root) => {
                if (!root) return false;
                return root.querySelectorAll('input[type="password"]').length > 0;
            };
            if (check(document)) return true;
            for (const fr of document.querySelectorAll('iframe')) {
                try { if (check(fr.contentDocument)) return true; } catch(e) {}
            }
            return false;
        }""")
        if has_pw:
            log("JS: 패스워드 필드 감지 → 로그인 필요")
            return True
    except Exception as e:
        log(f"JS 감지 오류: {e}")

    try:
        for frame in page.frames:
            try:
                if frame.query_selector_all('input[type="password"]'):
                    log(f"Playwright frame에서 패스워드 필드 감지")
                    return True
            except Exception:
                pass
    except Exception as e:
        log(f"frame 감지 오류: {e}")

    return False


def collect(date_from, date_to, full_replace=False):
    from playwright.sync_api import sync_playwright

    mode = "전체교체" if full_replace else "증분업데이트"
    log(f"수집 시작: {date_from} ~ {date_to} ({mode})")
    log(f"출력: {OUTPUT_PATH}")

    with sync_playwright() as p:
        profile_path = Path(PROFILE_DIR) if Path(PROFILE_DIR).is_absolute() else PROJECT_DIR / PROFILE_DIR
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage',
                  '--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page()
        log("PLISM 접속 중...")
        page.goto(
            f"{PLISM_BASE}/websquare/websquare.html?w2xPath=/sq5/com/uat/Main.xml&menu_no=1",
            wait_until='networkidle', timeout=30000
        )

        if detect_login_needed(page):
            log("로그인 페이지 감지 → 자동 로그인 시도")
            if not auto_login(page):
                log("로그인 실패. .env 아이디/비밀번호 확인 후 재시도하세요.")
                browser.close()
                return None
            log("로그인 후 페이지 안정화 대기 (3초)...")
            page.wait_for_timeout(3000)
        else:
            log("로그인 불필요 (기존 세션 유효)")

        log("데이터 수집 중... (수분 소요)")
        result = page.evaluate(COLLECTION_JS, {
            'klnetId': KLNET_ID,
            'dateFrom': date_from,
            'dateTo': date_to
        })
        browser.close()

    stats = result.get('stats', {})
    rows  = result.get('rows', [])
    log(f"수출 MRN:{stats.get('exp_mrn')} MBL:{stats.get('exp_mbl')} CNTR:{stats.get('exp_cntr')} TEU:{stats.get('exp_teu')}")
    log(f"수입 MRN:{stats.get('imp_mrn')} MBL:{stats.get('imp_mbl')} CNTR:{stats.get('imp_cntr')} TEU:{stats.get('imp_teu')}")
    log(f"수집 합계: {len(rows)}행 / {stats.get('exp_teu',0)+stats.get('imp_teu',0)} TEU")

    if full_replace:
        n = rows_to_csv(rows, OUTPUT_PATH)
        log(f"CSV 전체 저장 완료: {OUTPUT_PATH} ({n}행)")
    else:
        total, added, updated, unchanged = incremental_update(rows, OUTPUT_PATH)
        log(f"CSV 증분 저장 완료: {OUTPUT_PATH} (전체 {total}행 | 신규 {added} | 변경 {updated} | 유지 {unchanged})")

    return stats


def main():
    parser = argparse.ArgumentParser(description='PLISM 물동량 자동 수집 v3.1 (증분 업데이트)')
    parser.add_argument('--days', type=int, default=7, help='최근 N일 (기본 7일, 증분모드)')
    parser.add_argument('--date-from', help='시작일 YYYYMMDD')
    parser.add_argument('--date-to',   help='종료일 YYYYMMDD')
    parser.add_argument('--full-replace', action='store_true', help='기존 CSV 전체 교체 (기본: 증분)')
    parser.add_argument('--watch', action='store_true', help=f'{INTERVAL_MIN}분마다 반복')
    args = parser.parse_args()

    # --full-replace 시 기본 30일
    default_days = 30 if args.full_replace else args.days

    today = datetime.now()
    date_to   = args.date_to   or today.strftime('%Y%m%d')
    date_from = args.date_from or (today - timedelta(days=default_days)).strftime('%Y%m%d')

    if args.watch:
        while True:
            collect(date_from, date_to, full_replace=args.full_replace)
            log(f"{INTERVAL_MIN}분 후 재실행...")
            time.sleep(INTERVAL_MIN * 60)
    else:
        collect(date_from, date_to, full_replace=args.full_replace)


if __name__ == '__main__':
    main()
