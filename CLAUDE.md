# 흥아라인 울산항 물동량 대시보드 — CLAUDE.md

> Claude 세션이 바뀌어도 맥락을 이어가기 위한 파일입니다. 새 세션은 이 파일부터 읽고 시작합니다.
> 최종 갱신: 2026-10-27 · 관련 문서: `docs/PRD.md`(제품 요구사항), `docs/BRD.md`(비즈니스 요구사항)

---

## 1. 한눈에 보기

| 항목 | 내용 |
|---|---|
| 목적 | PLISM(KL-Net) 적하목록 신고 데이터를 매일 자동 수집해 울산항 물동량을 실시간으로 보는 웹 대시보드 |
| 운영 | 흥아라인 울산사무소 |
| 대시보드 | https://gilbert6870.github.io/ulsan-cargo-dashboard/ |
| 저장소 | github.com/gilbert6870/ulsan-cargo-dashboard (**공개 저장소**, 브랜치 master) |
| 로컬 폴더 | `D:\[0]USER\Desktop\바이브코드\프로젝트\흥아라인 울산항 물동량 확인` (Windows PC) |
| 상태 | 운영 중. 매일 09:00 자동 업데이트(실패 시 18시까지 매시 재시도) |

---

## 2. 작업 규칙 (반드시 지킬 것)

1. **보안**: PLISM 로그인 ID·비밀번호·KL-Net ID는 `.env`에만 둔다. 코드·로그·커밋·문서(이 파일 포함)에 적지 않는다. 저장소가 공개이므로 이 파일에도 계정 정보를 쓰지 않는다.
2. **실행 위치**: PLISM 접속과 Playwright 수집은 **Windows PC에서 .bat로만** 실행된다. Claude의 작업 환경(Linux VM, 클라우드)에서는 PLISM 접속과 Chromium 실행이 안 된다. 수집이 필요하면 .bat를 만들어 사용자에게 실행을 요청하고, "실행완료" 후 로그를 확인한다.
3. **.bat 파일은 CRLF 줄바꿈 + ASCII**로 저장한다. LF로 저장하면 실행되지 않는다.
4. **경로의 `[0]`**: PowerShell에서 대괄호가 와일드카드로 해석된다. `-LiteralPath`/`$PSScriptRoot`를 쓰고 `Resolve-Path`·`Split-Path -LiteralPath -Parent` 조합은 쓰지 않는다(PS 5.1 오류).
5. **git 잠금 파일**: Claude 쪽에서 git을 실행하면 `.git/*.lock`이 남을 수 있다. 커밋 후 `find .git -name "*.lock"`으로 확인하고 지운다(삭제 권한 필요). 남겨두면 다음날 자동 push가 실패한다.
6. **파일 수정 후 검증**: index.html은 `<script>` 추출 → `node --check`로 문법 확인, 가능하면 실제 데이터로 화면을 띄워 확인 후 커밋한다.
7. **커밋 대상**: 원본 `data/prism_data.csv`, `logs/`, `.env`, `browser_profile/`는 커밋하지 않는다. 대시보드용 집계 파일(`data/monthly_*.csv`, `*.json`)만 올린다.

---

## 3. 시스템 구성과 데이터 흐름

```
[Windows 작업 스케줄러 09:00~18:00 매시]
   └─ daily_update.bat
        1) fetch_prism_v31.py --days 7   PLISM 자동 로그인 → API 호출 → data/prism_data.csv 증분 병합
        2) build_data.py                  중복제거 → 월별 CSV + 요약 JSON 생성
        3) git add/commit/push            GitHub Pages 자동 배포 (1~2분)
        4) logs/last_success.txt = 오늘   (같은 날 재실행은 건너뜀)
[브라우저] index.html → data/index.json → 최신월 monthly CSV + summary/voyages/sizes.json (shippers.json은 필요 시)
```

### 주요 파일 (운영 중)

| 파일 | 역할 |
|---|---|
| `index.html` | 대시보드 단일 파일 (Chart.js 4.4.0, 다크 테마) |
| `fetch_prism_v31.py` | PLISM 수집 (Playwright, 증분 병합, 절전 방지, 25분 멈춤 감시, 실패 시 종료코드 1) |
| `build_data.py` | 중복제거·월별 분할·요약 JSON 생성 (`--only YYYYMM,...` 지원, `--only none`이면 JSON만) |
| `daily_update.bat` | 매일 자동 실행 본체 (`force` 인자로 강제 실행) |
| `register_task.bat` / `.ps1` | 작업 스케줄러 등록 (관리자 권한 불필요) + `logs/task_status.txt` 기록 |
| `recollect_2026_all.bat` | 2026년 1~9월 월 단위 일괄 재수집 |
| `test_fields_1day.bat` | 하루치 테스트 수집 (필드 확인) |
| `docs/울산항_물동량_대시보드_프롬프트.xlsx` | 타 선사 재현용 단계별 프롬프트 |
| `.env` | PRISM_USER_ID / PRISM_PASSWORD / PRISM_KLNET_ID (git 제외) |

구버전·임시 파일(정리 대상, 운영에 쓰지 않음): `fetch_prism.py`, `fetch_prism_v3.py`, `fetch_prism_v31_backup.py`, `daily_update_old.bat`, `register_task_old.ps1`, `run_*.bat`, `fetch_august_full.bat`, `fetch_history_2026.bat`, `add_carrier.py`, `fix_carrier*.py`, `test_write.py`, `push_now.bat`, `setup_github_auth.bat`.

---

## 4. 집계 기준 (PLISM 원본 필드 기준 — 바꾸지 말 것)

PLISM '모선별 현황' 조회조건(ETD · 신고세관 · 선사부호 · 선박명)과 같은 기준이다.

| 항목 | 기준 |
|---|---|
| 기간 | 수출 = MRN 목록 `dpt_date`(ETD), 수입 = `arv_date`(ETA) → CSV `출발일자` |
| 신고세관 | MRN 목록 `customs` 앞 3자리. 110 울산, 030 부산, 062 광양, 020 인천, 016 평택, 100 옥계, 122 포항. **대시보드 기본값 = 울산세관(110)** |
| 선사부호 | **MBL번호 앞 4자리** (= customs_line_code, 예 HASL) |
| 선박명 | MRN 목록 `vessel_name` |
| 운항선사 | MRN 3~6번째 글자(예 26SNKO… → SNKO, 장금상선). 참고용. 항구·선사부호가 아님 |
| 중복제거 | `수출입구분 + MRN + 컨테이너번호` 가 같으면 1개 (한 컨테이너에 MBL이 여러 개면 TEU 1회) |
| 환적 | 수입 `cargo_class`=T → 환적 양하, 수출 `cargo_class`=R → 환적 적하. 양하·적하 각각 집계 + 합계 |
| FULL/EMPTY | MBL `bl_type`=E → EMPTY, 그 외 FULL. (`풀엠티구분` 컬럼은 화물구분 값이라 쓰지 않음) |
| 사이즈 | `cntr_code` 첫 자리 2=20', 4·L=40', 둘째 자리 5=40'HC |
| TEU / VAN | 20'=1, 40'·40'HC=2 TEU / VAN=컨테이너 개수 |

자사 KL-Net 계정으로는 **자사 신고 B/L만** 조회된다(다른 선사 물량은 안 보임). 계정은 전국 세관 물량을 모두 돌려주므로 반드시 신고세관으로 걸러야 한다.

---

## 5. 데이터 파일 스키마

**`data/prism_data.csv` / `monthly_YYYYMM.csv`** (utf-8-sig, 컨테이너 1개 = 1행, 20컬럼)
`수출입구분, 모선명, 항차, 출발일자, MBL번호, 화주명, 컨테이너번호, 컨테이너규격, 컨테이너코드, 풀엠티구분, TEU, 수량, MRN, 수집일시, 운항선사코드, 항구, 세관, BL구분, FE, 화물구분`
- 증분 병합 키: 수출입구분+MRN+MBL번호+컨테이너번호 / 수집일시는 UTC

| JSON | 컬럼 | 용도 |
|---|---|---|
| `index.json` | months{ym: rows, teu, exp_teu, imp_teu, vessels}, `updated`(KST), `last_collected` | 월 목록, 헤더 업데이트 시각 |
| `summary.json` | ym, operator, customs, dir, fe, cls, teu, cnt, bl_carrier, vessel | 월별 추이(필터 연동) |
| `voyages.json` | ym, vessel, voyage, dir, customs, bl_carrier, date, van, teu, full, ts | 모선 월별 조회 |
| `sizes.json` | ym, dir, customs, bl_carrier, size, fe, ts, van, teu | 규격 월별 조회 |
| `shippers.json` (약 7.7MB, 지연 로딩) | ym, shipper, dir, customs, bl_carrier, ts, van, teu, full | 화주 월별 조회 |

PLISM API(POST JSON, 로그인한 페이지 안에서 fetch):
수출 `/plism3/oks/cms/mng/selectKmcsExpMrnList.do` → `/oks/doc/mng/selectExpMblDtlList.do` → `/oks/doc/mng/selectExpCntrList.do`
수입 `/plism3/iks/cms/mng/selectKmcsImpMrnList.do` → `/iks/doc/mng/selectImpMblDtlList.do` → `/iks/doc/mng/selectImpCntrList.do`

---

## 6. 대시보드 기능 (2026-10-27 기준)

- **헤더**: 데이터 업데이트 시각 배지(26시간 이내 초록 / 이후 주황), 건수, CSV 업로드·내보내기
- **필터(모든 항목 연동)**: 월 다중선택 + 날짜 범위 / 구분(전체·수출·수입) / 화물(전체·로컬·환적) / 신고세관 / 선사부호 / 선박명(선사부호 연동)
- **KPI 7개**: 총 TEU, 수출(로컬·환적), 수입(로컬·환적), 환적(양하·적하·비율), 모선 수(항차), 화주 수, FULL 비율
- **월별 TEU 추이**: 누적 막대(수출로컬/수출환적/수입로컬/수입환적, FULL/EMPTY 탭), 구간값 + 월 합계 숫자, 막대 클릭 시 해당 월 선택
- **수출/수입 도넛**, **FULL/EMPTY 도넛 + 수출·수입 막대**: 조각·막대 안에 TEU와 비율
- **모선·항차별 TEU**: 모선+항차 단위, 수출·수입 TEU + 합계(점유율), 클릭 → **모선 월별 조회**(월별 차트 + 항차별 표)
- **컨테이너 규격**: 전체/EMPTY × 20'/40'/40'HC VAN·TEU, **규격 월별 조회**
- **화주별 물동량**: 전체/수출/수입 탭, 행 클릭 → **화주 월별 조회**
- 각 카드 ⛶ 확대 모달, 데이터 캐시 방지(`?v=타임스탬프`, no-store)
- 삭제된 기능: 선사별 물동량(울산항 전체) 카드, 툴바 모선 필터(선박명 필터로 대체)

---

## 7. 자동화 운영과 점검

- 작업 이름 `HeungalineDailyUpdate`: 매일 09:00 시작, 1시간 간격 9시간 반복(~18:00) + 로그온 10분 후. PC가 꺼져 있으면 켜질 때 실행, 절전 중이면 깨워서 실행. 실행 제한 1시간.
- 성공하면 `logs/last_success.txt`에 날짜 기록 → 같은 날 나머지 시도는 즉시 종료.
- 매번 최근 7일을 다시 수집하므로 하루 이틀 누락돼도 다음 실행에서 채워진다.

점검 순서
1. 대시보드 헤더 업데이트 시각
2. `logs/daily_update.log` (수집 건수, `[ERROR]`, `[OK] GitHub Pages updated`)
3. `logs/last_success.txt`, `logs/task_status.txt`(등록·다음 실행 시각)
4. `git log -3` 와 `git ls-remote origin master` 일치 여부, `.git/*.lock` 잔존 여부
5. 화면이 예전 그대로면 GitHub Pages 배포(1~2분) 대기 후 Ctrl+F5

---

## 8. 알려진 이슈 · 주의

- **공개 저장소 노출**: 월별 CSV·shippers.json에 화주명이 포함돼 누구나 내려받을 수 있다. 과거 커밋에 원본 `data/prism_data.csv`(초기 6.3만 행)와 구버전 CLAUDE.md(KL-Net ID 기재)가 남아 있다. 공개 범위를 회사와 협의 필요(비공개 저장소 + 유료 Pages 또는 화주명 제외 등).
- 2026-10-27 10:00 시도에서 Chromium `Target crashed`로 로그인 실패 → 매시 재시도로 처리. 반복되면 Playwright/Chromium 재설치 검토.
- 2026-10-25(일)은 업데이트 기록 없음(PC 꺼짐 추정). 7일 재수집으로 데이터는 보완됨.
- 로그에 로그인 ID가 그대로 찍히던 부분을 2026-10-27에 앞 2자리만 보이도록 수정.
- PACIFIC BUSAN처럼 항차 번호가 기항마다 바뀌는 선박은 월 항차 수가 많게 보인다(1~10월 54항차).

---

## 9. 변경 이력

| 날짜 | 내용 |
|---|---|
| 09-22 | 프로젝트 생성, PLISM 3.0 수출·수입 API 연동, 대시보드 v1 |
| 09-29 | 증분 수집 v3.1, 1~9월 소급 수집, 월별 CSV 지연 로딩, 모선 필터 → 선사 필터 → 운항선사, 중복제거, **집계 기준 확정**(MRN 앞 4자리 = 운항선사, 신고세관·선사부호(MBL 앞 4자리)·선박명 기준), 환적 양하·적하 분리, FULL/EMPTY = bl_type, 월 단위 재수집, 기본 세관 울산(110), 옥계·포항 코드, 선사별 카드 삭제, 월별 추이 숫자, EMPTY 사이즈 구분 |
| 10-02 | 타 선사 재현용 프롬프트 엑셀 작성(docs/) |
| 10-06 | 매일 09:00 자동 업데이트 수정(작업 경로 `[0]` 오류, 비관리자 등록), git 잠금 파일 정리, 헤더 업데이트 시각, 모선·항차별 TEU + 모선/규격/화주 월별 조회, 그래프 안 TEU·비율 표시 |
| 10-07 | 실패 시 매시 재시도·로그온 실행·절전 방지·멈춤 감시, 데이터 캐시 방지 |
| 10-11~ | 매일 자동 업데이트 정상 운영 |
| 10-27 | 로그 ID 마스킹, CLAUDE.md 전면 개정, PRD/BRD 작성 |

---

## 10. 다음 할 일 (백로그)

- 공개 범위 결정(화주명 노출) 및 저장소 정리(과거 원본 CSV·계정 정보 이력 제거)
- 구버전·임시 파일 정리
- 전월·전년 동월 대비 증감률, 항로(POL/POD)별 분석
- 월간 보고서(PDF/엑셀) 자동 생성
- 화주 물동량 급변 알림
- 타 선사 버전 지원(프롬프트 엑셀 활용)

## 새 세션 시작 문구

```
흥아라인 울산항 물동량 대시보드 프로젝트입니다. 프로젝트 폴더의 CLAUDE.md를 먼저 읽고
작업 규칙과 집계 기준을 지켜서 이어서 작업해 주세요.
```
