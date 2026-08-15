import os
from urllib.parse import quote

from flask import Blueprint, Response, jsonify, redirect, request, session


auth_bp = Blueprint('auth', __name__)


def get_access_password():
    return os.environ.get('APP_ACCESS_PASSWORD', '').strip()


def is_authenticated():
    return session.get('authenticated') is True


def is_api_request():
    return (
        request.path.startswith('/collect')
        or request.path.startswith('/lookup-proino')
        or request.path.startswith('/item-detail')
        or request.path.startswith('/save-item')
        or request.path.startswith('/stats-items')
        or request.path.startswith('/stats-item')
        or request.path.startswith('/channel-configs')
    )


@auth_bp.before_app_request
def require_password_login():
    allowed_endpoints = {'auth.login_page', 'auth.login_submit', 'health', 'static'}

    if request.method == 'OPTIONS':
        return None

    if request.endpoint in allowed_endpoints:
        return None

    configured_password = get_access_password()
    if not configured_password:
        if is_api_request():
            return jsonify({'success': False, 'message': 'APP_ACCESS_PASSWORD 환경변수가 설정되지 않았습니다.'}), 503
        return Response('APP_ACCESS_PASSWORD environment variable is required.', status=503)

    if is_authenticated():
        return None

    if is_api_request() or request.path.startswith('/run-app') or request.path.startswith('/stop-app'):
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    return redirect(f"/login?next={quote(request.full_path if request.query_string else request.path, safe='/?=&')}")


@auth_bp.get('/login')
def login_page():
    next_path = request.args.get('next', '/').strip() or '/'
    html = f"""<!doctype html>
<html lang=\"ko\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Access Login</title>
    <style>
        body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: #f4f6f8;
            font-family: Segoe UI, sans-serif;
        }}
        form {{
            width: min(360px, 92vw);
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
        }}
        h1 {{
            margin: 0 0 16px;
            font-size: 20px;
        }}
        label {{
            display: block;
            font-size: 14px;
            margin: 0 0 8px;
            color: #333;
        }}
        input {{
            width: 100%;
            box-sizing: border-box;
            height: 42px;
            border: 1px solid #cfd8dc;
            border-radius: 10px;
            padding: 0 12px;
            margin-bottom: 14px;
            font-size: 15px;
        }}
        button {{
            width: 100%;
            height: 42px;
            border: 0;
            border-radius: 10px;
            background: #1e293b;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
        }}
        .help {{
            margin-top: 10px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <form method=\"post\" action=\"/login\">
        <h1>비밀번호 확인</h1>
        <input type=\"hidden\" name=\"next\" value=\"{next_path}\" />
        <label for=\"password\">접속 비밀번호</label>
        <input id=\"password\" name=\"password\" type=\"password\" autocomplete=\"current-password\" required />
        <button type=\"submit\">로그인</button>
        <div class=\"help\">비밀번호는 서버 환경변수 APP_ACCESS_PASSWORD 값과 일치해야 합니다.</div>
    </form>
</body>
</html>"""
    return Response(html, mimetype='text/html; charset=utf-8')


@auth_bp.post('/login')
def login_submit():
    submitted_password = request.form.get('password', '')
    next_path = request.form.get('next', '/').strip() or '/'

    if submitted_password == get_access_password():
        session['authenticated'] = True
        return redirect(next_path)

    return Response('비밀번호가 올바르지 않습니다.', status=401)


@auth_bp.post('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': '로그아웃되었습니다.'})
