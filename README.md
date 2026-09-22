# 흥아라인 울산항 물동량 대시보드

울산항 수출입 물동량을 실시간으로 확인하는 웹 대시보드입니다.

## 🚀 빠른 시작

### 1단계: 설치
```bash
# setup.bat 더블클릭 또는
pip install -r requirements.txt
playwright install chromium
```

### 2단계: 로그인 정보 입력
`.env` 파일을 메모장으로 열어서 프리즘 아이디/비번 입력

### 3단계: 데이터 수집
```bash
# run_fetch.bat 더블클릭 또는
python fetch_prism.py
```

### 4단계: 대시보드 확인
`index.html`을 브라우저로 열거나 GitHub Pages URL 접속

## 📊 주요 기능

- **실시간 TEU 모니터링** — 수출/수입/누적
- **모선별 물동량** — 항차별 집계
- **FULL/EMPTY 구분** — 비율 및 TEU
- **20'/40' 사이즈 분석**
- **화주별 실적 랭킹** — 전체/수출/수입 탭

## 🔒 보안

`.env` 파일은 절대 GitHub에 올리지 마세요! (`.gitignore`에 이미 설정됨)

## 📁 파일 구조

- `index.html` — 대시보드 메인
- `fetch_prism.py` — 프리즘 자동 수집 스크립트
- `data/sample_prism.csv` — 샘플 데이터
- `CLAUDE.md` — AI 세션 컨텍스트 파일

---
흥아라인 울산사무소 | jhopark@heungaline.com
