# Persephone Backend

Flask 기반 Persephone 웹페이지 백엔드 서버입니다.

## 실행 방법

### 1. 가상환경 생성

```bash
python -m venv venv
```

### 2. 가상환경 실행

Windows PowerShell 기준:

```bash
.\venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install flask flask-cors pymysql python-dotenv
```

### 4. .env 파일 생성

백엔드 폴더 안에 `.env` 파일을 만들고 아래 형식으로 작성합니다.

```env
DB_HOST=127.0.0.1
DB_PORT=13306
DB_USER=admin
DB_PASSWORD=Qlalfqjsgh2@
```

### 5. DB 터널 실행

별도 PowerShell 창에서 아래 명령어를 실행합니다.

```bash
cloudflared access tcp --hostname db.demeter-persephone.cloud --listener localhost:13306
```

이 터미널은 닫지 않습니다.

### 6. Flask 서버 실행

```bash
python app.py
```

정상 실행 시 아래 주소에서 서버가 실행됩니다.

```txt
http://localhost:5000
```

## API 확인

팀원 정보 조회:

```txt
GET http://localhost:5000/api/team-members
```

문의 저장:

```txt
POST http://localhost:5000/api/questions
```

