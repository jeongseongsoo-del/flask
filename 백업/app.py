from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import os

app = Flask(__name__)
CORS(app)


def find_proino(payload):
    if isinstance(payload, dict):
        if 'proino' in payload and payload.get('proino') not in (None, ''):
            return payload['proino']
        for value in payload.values():
            result = find_proino(value)
            if result is not None:
                return result
    elif isinstance(payload, list):
        for item in payload:
            result = find_proino(item)
            if result is not None:
                return result
    return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'ctx-single-collection.html')


@app.route('/ctx-single-collection.html')
def serve_page():
    return send_from_directory(os.path.dirname(__file__), 'ctx-single-collection.html')


@app.route('/collect', methods=['POST'])
def collect():
    data = request.get_json(silent=True) or {}
    target = data.get('target', '').strip()
    collect_type = data.get('type', '단건 조회')

    result = {
        'success': True,
        'message': '수집 요청이 성공적으로 접수되었습니다.',
        'target': target,
        'type': collect_type,
        'output': f"{collect_type} 작업이 {target or '미지정 대상'} 기준으로 실행되었습니다."
    }

    return jsonify(result)


@app.route('/lookup-proino', methods=['POST'])
def lookup_proino():
    data = request.get_json(silent=True) or {}
    target = str(data.get('target', '')).strip()

    if not target:
        return jsonify({'success': False, 'message': '상품코드가 필요합니다.'}), 400

    url = f'https://ctx.cretec.kr/CtxApp/ebook/selectEbookUninumSearch.do?prodCd={quote(target)}&itemCd=&_='
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*'
    })

    try:
        with urlopen(req, timeout=15) as response:
            body = response.read().decode('utf-8', 'ignore')
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
        'target': target,
        'proino': proino,
        'payload': payload
    })


@app.route('/item-detail')
def item_detail():
    item_cd = request.args.get('itemCd', '').strip()
    if not item_cd:
        return jsonify({'success': False, 'message': 'itemCd가 필요합니다.'}), 400

    url = f'https://ctx.cretec.kr/CtxApp/ctx/selectItemDtlIfrm.do?itemCd={quote(item_cd)}&compCd=C&scrollYn=&serveOneYn=&fromAwsCheck=&proCondNm='
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })

    try:
        with urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', 'ignore')
    except Exception as exc:
        return jsonify({'success': False, 'message': '상세 페이지를 불러오지 못했습니다.', 'error': str(exc)}), 502

    if '<head' in html.lower():
        html = html.replace('<head>', '<head><base href="https://ctx.cretec.kr/">', 1)
        html = html.replace('<HEAD>', '<HEAD><base href="https://ctx.cretec.kr/">', 1)
    else:
        html = f'<!doctype html><html><head><base href="https://ctx.cretec.kr/"></head><body>{html}</body></html>'

    return Response(html, mimetype='text/html; charset=utf-8')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
