# 개발 과정 기록

이 문서는 `ctx_get_data` 프로젝트의 주요 변경 과정과 운영 규칙을 기록합니다.
기능 변경이 완료되면 변경 이유, 영향 범위, 검증 결과, Git 커밋을 이 문서에 추가합니다.

## 현재 구조

```text
app.py                    Flask 앱 진입점, 앱 설정, DB/업무 로직
routes/
  auth.py                 로그인, 로그아웃, 전역 인증 훅
  collect.py              CTX 수집 및 외부 상세 조회 API
  pages.py                HTML 페이지 라우트
templates/pages/
  dashboard/index.html    메인 대시보드
  ctx/single-collection.html
  channel-configs/index.html
static/                   이미지 등 정적 파일
```

`app.py`는 `app:app` 진입점을 유지합니다. 페이지와 CTX 수집 라우트는 Blueprint로 분리했으며, 기존 URL은 그대로 유지합니다.

## 변경 이력

### 2026-08-15

- 메뉴별 HTML을 `templates/pages/` 아래로 정리했습니다.
- 사용하지 않는 루트 HTML, 기본 Flask 샘플 템플릿, `백업/` 복사본을 제거했습니다.
- 페이지 라우트를 `routes/pages.py` Blueprint로 분리했습니다.
- CTX 수집, 외부 조회, 상세 페이지 프록시를 `routes/collect.py` Blueprint로 분리했습니다.
- 로그인, 로그아웃, 전역 인증 처리를 `routes/auth.py` Blueprint로 분리했습니다.
- 각 단계마다 문법 검사와 Flask 테스트 클라이언트 검증 후 별도 커밋했습니다.

관련 커밋:

- `1935293` `chore: remove obsolete template copies`
- `81fe183` `refactor: extract page routes`
- `8a49541` `refactor: extract collection routes`
- `ad30bd5` `refactor: extract authentication routes`

## 안전한 개발 절차

1. 변경 전 `git status --short`로 작업 트리를 확인합니다.
2. 의존성이 적은 기능 하나만 선택해 분리하거나 수정합니다.
3. 수정 직후 해당 기능의 최소 검증을 실행합니다.
4. `get_errors` 또는 Python 문법 검사를 실행합니다.
5. Flask 테스트 클라이언트로 기존 URL과 응답 상태를 확인합니다.
6. 검증된 변경만 기능 단위로 커밋합니다.
7. `git push origin main`으로 GitHub와 동기화합니다.
8. 이 문서의 변경 이력에 변경 이유, 검증 결과, 커밋을 기록합니다.

## 기본 검증 명령

```powershell
python -m py_compile .\app.py .\routes\*.py
```

인증 환경을 설정한 뒤 주요 페이지를 확인합니다.

```powershell
$env:APP_ACCESS_PASSWORD = 'test-password'
python -m pytest
```

현재 별도 pytest 모음이 없는 경우에는 Flask 테스트 클라이언트로 다음 경로를 확인합니다.

```text
/health
/
/index.html
/ctx-single-collection.html
/channel-configs.html
/login
/collect
/lookup-proino
/item-detail
```

## 다음 분리 대상

DB와 통계, 채널 설정 기능은 여러 공통 함수와 `pymysql` 연결 로직을 공유하므로 다음 순서로 분리합니다.

1. DB 설정과 연결 공통 함수
2. 채널 설정 서비스 및 라우트
3. 통계 조회와 상품 수정/삭제 라우트
4. 상품 등록 및 대상 DB 전송 서비스

각 단계는 기존 URL과 API 응답 형식을 유지한 상태에서 진행합니다.
