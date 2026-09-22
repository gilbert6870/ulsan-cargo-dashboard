# 흥아라인 울산항 물동량 대시보드 — CLAUDE.md

> 이 파일은 Claude 세션이 바뀌어도 프로젝트 맥락을 유지하기 위한 파일입니다.
> 새 세션에서 이 파일을 읽으면 지금까지의 작업 내용과 구조를 파악할 수 있습니다.

---

## 프로젝트 개요

**목적**: 프리즘(PRISM) 수출입 신고 승인 데이터를 자동 수집하여 울산항 물동량을 실시간 모니터링  
**담당자**: 흥아라인 울산사무소  
**이메일**: jhopark@heungaline.com  
**배포 목표**: GitHub Pages (무료 웹 호스팅)

---

## 폴더 구조

```
흥아라인 울산항 물동량 확인/
├── index.html            ← 메인 대시보드 (GitHub Pages 진입점)
├── CLAUDE.md             ← 이 파일 (세션 컨텍스트)
├── README.md             ← 사용자용 설명서
├── fetch_prism.py        ← 프리즘 자동 로그인 & 데이터 수집 스크립트
├── requirements.txt      ← Python 패키지 목록
├── setup.bat             ← Windows 환경 설치 (더블클릭)
├── run_fetch.bat         ← 1회 데이터 수집 실행
├── run_watch.bat         ← 30분마다 자동 수집
├── .env                  ← 프리즘 로그인 정보 (Git에 올리지 않음!)
├── .env.example          ← .env 템플릿 (Git에 올림)
├── .gitignore            ← .env 제외 설정
├── data/
│   ├── sample_prism.csv  ← 샘플 데이터 (울산항 기준)
│   └── prism_data.csv    ← 실제 수집 데이터 (fetch_prism.py 실행 후 생성)
└── docs/                 ← 추가 문서 폴더
```

---

## 대시보드 기능 현황

### ✅ 완료된 기능
- [x] CSV 파일 업로드 (프리즘 내보내기 파일 직접 로드)
- [x] 샘플 데이터 미리보기
- [x] **KPI 타일**: 총 TEU, 수출, 수입, 모선 수, 화주 수, FULL 비율
- [x] **일별 TEU 추이** 바 차트 (수출/수입 스택)
- [x] **수출/수입 비율** 도넛 차트
- [x] **모선별 TEU** 수평 바 차트
- [x] **FULL/EMPTY 구분** 도넛 차트
- [x] **20'/40' 사이즈 구분** 도넛 차트
- [x] **화주별 실적 테이블** (전체/수출/수입 탭 전환, 순위, 비중)
- [x] **모선 목록** (항차별 TEU 집계)
- [x] 기간/수출입구분/모선 필터
- [x] CSV 내보내기
- [x] 프리즘 자동 로그인 & 데이터 수집 (`fetch_prism.py`)
- [x] `.env` 파일 기반 자격증명 관리

### 🔧 추가 개발 예정
- [ ] GitHub Actions 자동화 (스케줄 실행 → CSV 커밋)
- [ ] 전월/전년 동기 대비 증감율
- [ ] 항로별 물동량 분석
- [ ] PDF 보고서 자동 생성
- [ ] 알림 기능 (특정 화주 물동량 급변 시)

---

## 데이터 컬럼 구조 (프리즘 표준)

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| 신고번호 | 수출입 신고 고유번호 | 41291-26-0001234 |
| 신고일자 | 신고 날짜 | 2026-09-01 |
| 수출입구분 | 수출 / 수입 | 수출 |
| 화주명 | 화주 또는 수입자 | 현대자동차㈜ |
| 모선명 | 선박명 | HEUNG-A HOCHIMINH |
| 항차 | 항차 번호 | 026E |
| 컨테이너번호 | 컨테이너 일련번호 | HDMU1234567 |
| 컨테이너규격 | 20 또는 40 | 40 |
| 풀엠티구분 | FULL 또는 EMPTY | FULL |
| 수량 | 컨테이너 개수 | 2 |
| TEU | Twenty-foot Equivalent Unit | 4 |
| 신고금액(USD) | 신고 금액 | 85000 |

---

## 프리즘 자동화 설정

### .env 파일 편집 방법
1. 프로젝트 폴더에서 `.env` 파일을 메모장으로 열기
2. `PRISM_USER_ID=` 뒤에 프리즘 아이디 입력
3. `PRISM_PASSWORD=` 뒤에 비밀번호 입력
4. `PRISM_COMPANY_BRN=` 뒤에 사업자번호 입력 (흥아라인)
5. 저장 후 `run_fetch.bat` 더블클릭

### fetch_prism.py 셀렉터 조정
프리즘 화면 구조에 맞게 아래 항목을 조정해야 합니다:
- 로그인 페이지 URL: `PRISM_URL` 환경변수
- 아이디 필드: `#userId` (실제 프리즘 ID 속성으로 변경)
- 비밀번호 필드: `#userPw`
- 조회 메뉴 URL: `/decls/expImpDclrList.do`
- 날짜 필드: `#startDate`, `#endDate`
- 다운로드 버튼: `.btn-excel`

---

## GitHub 배포 방법

```bash
# 1. GitHub에서 새 리포지토리 생성
# 2. 로컬에서 연결
git remote add origin https://github.com/[계정]/ulsan-cargo-dashboard.git
git branch -M main
git push -u origin main

# 3. GitHub Pages 활성화
# GitHub 리포 → Settings → Pages → Source: main 브랜치 선택
```

배포 후 URL: `https://[계정].github.io/ulsan-cargo-dashboard/`

---

## 다음 세션에서 Claude에게 전달할 메시지

새 세션 시작 시 아래 내용을 Claude에게 붙여넣으세요:

```
이 프로젝트는 흥아라인 울산항 물동량 대시보드입니다.
CLAUDE.md 파일을 읽어서 현재까지의 작업 내용을 파악하고 이어서 작업해주세요.
프로젝트 폴더: D:\[0]USER\Desktop\바이브코드\프로젝트\흥아라인 울산항 물동량 확인
```

---

## 변경 이력

| 날짜 | 작업 내용 |
|------|-----------|
| 2026-09-22 | 프로젝트 초기 생성, 대시보드 v1.0, 프리즘 자동화 스크립트 |


## 2026-09-22 세션 2 완료 내용

### 완료된 작업
- **fetch_prism.py 완전 재작성** (수출+수입):
  - 수출: `/plism3/oks/cms/mng/selectKmcsExpMrnList.do` → `/oks/doc/mng/selectExpMblList.do` → `/oks/doc/mng/selectExpCntrList.do`
  - 수입: `/iks/doc/mng/selectImpMrnList.do` → `/iks/doc/mng/selectImpMblDtlList.do` → `/iks/doc/mng/selectImpCntrList.do`
  - PLISM 3.0 인증: Playwright 브라우저 세션 활용
  
- **index.html 대시보드 업데이트** (PLISM 컬럼 형식 적용):
  - `신고일자` → `출발일자`
  - `풀엠티구분` 값: FULL/EMPTY + F/E 모두 인식
  - 인라인 샘플 데이터: PLISM 컬럼 형식으로 교체
  - 데이터 파일: `sample_prism.csv` → `prism_data.csv`

- **.env 업데이트**:
  - `PRISM_URL=https://www.plism.com` (unipass → plism)
  - `PRISM_KLNET_ID=HASMT010` 추가

### 새 CSV 컬럼 형식 (PLISM 3.0)
```
수출입구분,모선명,항차,출발일자,MBL번호,화주명,컨테이너번호,컨테이너규격,컨테이너코드,풀엠티구분,TEU,수량,MRN,수집일시
```

### git commit 방법 (index.lock 있는 경우)
1. `git_setup.bat` 실행 (index.lock 자동 제거)
2. 또는 수동:
   ```
   del .git\index.lock
   git add fetch_prism.py index.html git_setup.bat
   git commit -m "feat: PLISM 3.0 수출+수입 연동 및 대시보드 업데이트"
   git push
   ```

### 다음 단계
- GitHub repository 생성 후 push: `git remote add origin <URL>` → `git push -u origin master`
- GitHub Pages 활성화: Settings → Pages → Source: master branch
- fetch_prism.py 테스트: `python fetch_prism.py --days 7`
