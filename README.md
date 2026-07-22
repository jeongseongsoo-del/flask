<br/>
<br/>

<p align="center">
<img src="https://files.cloudtype.io/logo/cloudtype-logo-horizontal-black.png" width="50%" alt="Cloudtype"/>
</p>

<br/>
<br/>

# Flask

Python으로 구현된 Flask 어플리케이션 템플릿입니다.

## 🖇️ 준비 및 확인사항

### 지원 Python 버전
- 3.7, 3.8, 3.9, 3.10, 3.11
- Flask는 최소 3.7 버전의 Python를 필요로 합니다.
- ⚠️ 로컬/테스트 환경과 클라우드타입에서 설정한 Python 버전이 상이한 경우 정상적으로 빌드되지 않을 수 있습니다.

### 패키지 명세
- 빌드 시 어플리케이션에 사용된 패키지를 설치하기 위해서는 `requirements.txt` 파일이 반드시 필요합니다.

## ⌨️ 명령어

### Start

```bash
gunicorn -b 0.0.0.0:${PORT:-5000} app:app
```

- `flask --app [app 모듈명] run` 은 개발 서버 실행 명령어이므로 사용을 지양합니다.

## Cloudtype 배포 체크리스트

1. 저장소 연결
- GitHub 저장소 `main` 브랜치를 Cloudtype 서비스에 연결합니다.

2. 런타임 확인
- Python 런타임을 선택합니다. (권장: Python 3.11)

3. 의존성 설치 파일 확인
- 루트 경로에 `requirements.txt` 가 존재하는지 확인합니다.

4. 시작 명령 확인
- Procfile을 사용하거나 아래 명령으로 설정합니다.

```bash
gunicorn -b 0.0.0.0:${PORT:-5000} app:app
```

5. 포트 설정
- 별도 고정 포트를 강제하지 않고 Cloudtype가 주입하는 `PORT` 값을 사용합니다.

6. 배포 트리거
- `main` 에 푸시 후 자동 배포 로그에서 install/start 단계 성공 여부를 확인합니다.

## 배포 후 헬스체크 시나리오

서비스 URL을 `https://<your-service>.app.cloudtype.io` 라고 가정합니다.

1. 기본 상태 확인
```bash
curl -i https://<your-service>.app.cloudtype.io/health
```
- 기대 결과: HTTP 200, JSON에 `status: ok` 포함

2. 앱 실행 상태 전환 확인
```bash
curl -i -X POST https://<your-service>.app.cloudtype.io/run-app
curl -i https://<your-service>.app.cloudtype.io/health
```
- 기대 결과: `appState` 가 `running`

3. 수집 API 기본 동작 확인
```bash
curl -i -X POST https://<your-service>.app.cloudtype.io/collect \
	-H "Content-Type: application/json" \
	-d '{"target":"1234567","type":"단건 조회"}'
```
- 기대 결과: HTTP 200, `success: true`

4. 상세 페이지 프록시 확인
```bash
curl -i "https://<your-service>.app.cloudtype.io/item-detail?itemCd=1297571"
```
- 기대 결과: HTTP 200, HTML 본문 반환


## 🏷️ 환경변수

- `FLASK_ENV`: 배포 환경 설정
- `APP_ACCESS_PASSWORD`: 접속 비밀번호(미설정 시 서비스는 503 반환)
- `FLASK_SECRET_KEY`: 세션 암호화 키(강력한 임의 문자열 권장)


## 💬 문제해결

- [클라우드타입 Docs](https://docs.cloudtype.io/)

- [클라우드타입 FAQ](https://help.cloudtype.io/guide/faq)

- [Discord](https://discord.gg/U7HX4BA6hu)


## 📄 License

[BSD 3-Clause](https://github.com/pallets/flask/blob/main/LICENSE.rst)

