from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import os
import re
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False
app_state = {
    'running': True
}


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
