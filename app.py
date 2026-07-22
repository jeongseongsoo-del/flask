from flask import Flask, jsonify, request, Response, send_from_directory, session, redirect
from flask_cors import CORS
from urllib.parse import quote
from urllib.request import Request, urlopen
from functools import wraps
import json
import os
import re
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-secret-key')
app_state = {
    'running': True
}


def get_access_password():
        return os.environ.get('APP_ACCESS_PASSWORD', '').strip()


def is_authenticated():
        return session.get('authenticated') is True


def is_api_request():
        return request.path.startswith('/collect') or request.path.startswith('/lookup-proino') or request.path.startswith('/item-detail')


@app.before_request
def require_password_login():
        allowed_endpoints = {'login_page', 'login_submit', 'health', 'static'}

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


@app.route('/login', methods=['GET'])
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


@app.route('/login', methods=['POST'])
def login_submit():
        submitted_password = request.form.get('password', '')
        next_path = request.form.get('next', '/').strip() or '/'

        if submitted_password == get_access_password():
                session['authenticated'] = True
                return redirect(next_path)

        return Response('비밀번호가 올바르지 않습니다.', status=401)


@app.route('/logout', methods=['POST'])
def logout():
        session.clear()
        return jsonify({'success': True, 'message': '로그아웃되었습니다.'})


def normalize_target(value):
    cleaned = re.sub(r'\D', '', str(value or ''))
    return cleaned[:7]


def find_proino(payload):
    if isinstance(payload, dict):
        for key in ('proino', 'proNo', 'pro_no', 'proNo', 'itemCd', 'item_cd', 'productNo', 'prodNo'):
            value = payload.get(key)
            if value not in (None, ''):
                return str(value)
        for value in payload.values():
            result = find_proino(value)
            if result is not None:
                return result
    elif isinstance(payload, list):
        for item in payload:
            result = find_proino(item)
            if result is not None:
                return result
    elif isinstance(payload, str):
        match = re.search(r'(?i)(?:pro(?:ino|no)|itemCd)[^0-9A-Za-z]{0,4}([0-9A-Za-z_-]{1,20})', payload)
        if match:
            return match.group(1)
    return None


def _request_text(url, timeout=15, accept='application/json, text/plain, */*'):
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': accept
    })
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', 'ignore')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'appState': 'running' if app_state['running'] else 'stopped'})


@app.route('/run-app', methods=['POST'])
def run_app():
    app_state['running'] = True
    return jsonify({'success': True, 'message': '앱이 실행 중입니다.', 'alreadyRunning': False, 'appState': 'running'})


@app.route('/stop-app', methods=['POST'])
def stop_app():
    app_state['running'] = False

    def shutdown_process():
        time.sleep(0.3)
        os._exit(0)

    threading.Thread(target=shutdown_process, daemon=True).start()
    return jsonify({'success': True, 'message': '앱이 중단되었습니다.', 'appState': 'stopped'})


@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')


@app.route('/index.html')
def serve_index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')


@app.route('/ctx-single-collection.html')
def serve_page():
    return send_from_directory(os.path.dirname(__file__), 'ctx-single-collection.html')


@app.route('/collect', methods=['POST'])
def collect():
    data = request.get_json(silent=True) or {}
    target = normalize_target(data.get('target', ''))
    collect_type = data.get('type', '단건 조회')
    form_data = data.get('formData') or {}

    result = {
        'success': True,
        'message': '수집 요청이 성공적으로 접수되었습니다.',
        'target': target,
        'type': collect_type,
        'formData': form_data,
        'output': f"{collect_type} 작업이 {target or '미지정 대상'} 기준으로 실행되었습니다."
    }

    return jsonify(result)


@app.route('/lookup-proino', methods=['POST'])
def lookup_proino():
    data = request.get_json(silent=True) or {}
    target = str(data.get('target', '')).strip()

    if not target:
        return jsonify({'success': False, 'message': '상품코드가 필요합니다.'}), 400

    normalized_target = normalize_target(target)
    if not normalized_target:
        return jsonify({'success': False, 'message': '상품코드가 올바르지 않습니다.'}), 400

    timestamp = int(time.time() * 1000)
    url = f'https://ctx.cretec.kr/CtxApp/ctx/selectPowerSearchJson.do?prod_cd={quote(normalized_target, safe="")}&keyword=&_={timestamp}'

    try:
        body = _request_text(url, timeout=15)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {'raw': body}
    except Exception as exc:
        return jsonify({'success': False, 'message': '외부 API 조회에 실패했습니다.', 'error': str(exc)}), 502

    proino = find_proino(payload)

    return jsonify({
        'success': True,
        'message': '조회가 완료되었습니다.',
        'target': normalized_target,
        'proino': proino,
        'payload': payload,
        'rawResponse': payload,
        'responseSummary': {
            'proino': proino,
            'target': normalized_target,
            'keys': list(payload.keys()) if isinstance(payload, dict) else []
        }
    })


@app.route('/item-detail')
def item_detail():
    item_cd = request.args.get('itemCd', '').strip()
    if not item_cd:
        return jsonify({'success': False, 'message': 'itemCd가 필요합니다.'}), 400

    url = f'https://ctx.cretec.kr/CtxApp/ctx/selectItemDtlIfrm.do?itemCd={quote(item_cd, safe="")}&compCd=C&scrollYn=&serveOneYn=&fromAwsCheck=&proCondNm='

    try:
        html = _request_text(url, timeout=15, accept='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    except Exception as exc:
        return jsonify({'success': False, 'message': '상세 페이지를 불러오지 못했습니다.', 'error': str(exc)}), 502

    if '<head' in html.lower():
        html = html.replace('<head>', '<head><base href="https://ctx.cretec.kr/">', 1)
        html = html.replace('<HEAD>', '<HEAD><base href="https://ctx.cretec.kr/">', 1)
    else:
        html = f'<!doctype html><html><head><base href="https://ctx.cretec.kr/"></head><body>{html}</body></html>'

    return Response(html, mimetype='text/html; charset=utf-8')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
