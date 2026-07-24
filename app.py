from flask import Flask, jsonify, request, Response, send_from_directory, session, redirect
from flask_cors import CORS
from urllib.parse import quote
from urllib.request import Request, urlopen
from functools import wraps
from datetime import datetime
from decimal import Decimal
import json
import os
import re
import threading
import time

try:
    import pymysql
except Exception:
    pymysql = None

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-secret-key')
app_state = {
    'running': True
}


ITEM_SCHEMA_RULES = {
    'ca_id': {'type': 'str', 'max_len': 10},
    'ca_id2': {'type': 'str', 'max_len': 255},
    'ca_id3': {'type': 'str', 'max_len': 255},
    'it_skin': {'type': 'str', 'max_len': 255},
    'it_mobile_skin': {'type': 'str', 'max_len': 255},
    'it_name': {'type': 'str', 'max_len': 255},
    'it_seo_title': {'type': 'str', 'max_len': 200},
    'it_maker': {'type': 'str', 'max_len': 255},
    'it_origin': {'type': 'str', 'max_len': 255},
    'it_brand': {'type': 'str', 'max_len': 255},
    'it_model': {'type': 'str', 'max_len': 255},
    'it_option_subject': {'type': 'str', 'max_len': 255},
    'it_supply_subject': {'type': 'str', 'max_len': 255},
    'it_type1': {'type': 'int'},
    'it_type2': {'type': 'int'},
    'it_type3': {'type': 'int'},
    'it_type4': {'type': 'int'},
    'it_type5': {'type': 'int'},
    'it_basic': {'type': 'str'},
    'it_explan': {'type': 'str'},
    'it_explan2': {'type': 'str'},
    'it_mobile_explan': {'type': 'str'},
    'it_cust_price': {'type': 'int'},
    'it_price': {'type': 'int'},
    'it_point': {'type': 'int'},
    'it_point_type': {'type': 'int'},
    'it_supply_point': {'type': 'int'},
    'it_notax': {'type': 'int'},
    'it_sell_email': {'type': 'str', 'max_len': 255},
    'it_use': {'type': 'int'},
    'it_nocoupon': {'type': 'int'},
    'it_soldout': {'type': 'int'},
    'it_stock_qty': {'type': 'int'},
    'it_stock_sms': {'type': 'int'},
    'it_noti_qty': {'type': 'int'},
    'it_sc_type': {'type': 'int'},
    'it_sc_method': {'type': 'int'},
    'it_sc_price': {'type': 'int'},
    'it_sc_minimum': {'type': 'int'},
    'it_sc_qty': {'type': 'int'},
    'it_buy_min_qty': {'type': 'int'},
    'it_buy_max_qty': {'type': 'int'},
    'it_head_html': {'type': 'str'},
    'it_tail_html': {'type': 'str'},
    'it_mobile_head_html': {'type': 'str'},
    'it_mobile_tail_html': {'type': 'str'},
    'it_hit': {'type': 'int'},
    'it_time': {'type': 'datetime'},
    'it_update_time': {'type': 'datetime'},
    'it_ip': {'type': 'str', 'max_len': 25},
    'it_order': {'type': 'int'},
    'it_tel_inq': {'type': 'int'},
    'it_info_gubun': {'type': 'str', 'max_len': 50},
    'it_info_value': {'type': 'str'},
    'it_sum_qty': {'type': 'int'},
    'it_use_cnt': {'type': 'int'},
    'it_use_avg': {'type': 'decimal1'},
    'it_shop_memo': {'type': 'str'},
    'ec_mall_pid': {'type': 'str', 'max_len': 255},
    'it_img1': {'type': 'str', 'max_len': 255},
    'it_img2': {'type': 'str', 'max_len': 255},
    'it_img3': {'type': 'str', 'max_len': 255},
    'it_img4': {'type': 'str', 'max_len': 255},
    'it_img5': {'type': 'str', 'max_len': 255},
    'it_img6': {'type': 'str', 'max_len': 255},
    'it_img7': {'type': 'str', 'max_len': 255},
    'it_img8': {'type': 'str', 'max_len': 255},
    'it_img9': {'type': 'str', 'max_len': 255},
    'it_img10': {'type': 'str', 'max_len': 255},
    'it_1_subj': {'type': 'str', 'max_len': 255},
    'it_2_subj': {'type': 'str', 'max_len': 255},
    'it_3_subj': {'type': 'str', 'max_len': 255},
    'it_4_subj': {'type': 'str', 'max_len': 255},
    'it_5_subj': {'type': 'str', 'max_len': 255},
    'it_6_subj': {'type': 'str', 'max_len': 255},
    'it_7_subj': {'type': 'str', 'max_len': 255},
    'it_8_subj': {'type': 'str', 'max_len': 255},
    'it_9_subj': {'type': 'str', 'max_len': 255},
    'it_10_subj': {'type': 'str', 'max_len': 255},
    'it_1': {'type': 'str', 'max_len': 255},
    'it_2': {'type': 'str', 'max_len': 255},
    'it_3': {'type': 'str', 'max_len': 255},
    'it_4': {'type': 'str', 'max_len': 255},
    'it_5': {'type': 'str', 'max_len': 255},
    'it_6': {'type': 'str', 'max_len': 255},
    'it_7': {'type': 'str', 'max_len': 255},
    'it_8': {'type': 'str', 'max_len': 255},
    'it_9': {'type': 'str', 'max_len': 255},
    'it_10': {'type': 'str', 'max_len': 255}
}


def get_access_password():
        return os.environ.get('APP_ACCESS_PASSWORD', '').strip()


def is_authenticated():
        return session.get('authenticated') is True


def is_api_request():
    return request.path.startswith('/collect') or request.path.startswith('/lookup-proino') or request.path.startswith('/item-detail') or request.path.startswith('/save-item') or request.path.startswith('/stats-items') or request.path.startswith('/stats-item')


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


def normalize_item_id_for_stats(value):
    item_id = str(value or '').strip()
    if not item_id:
        return ''
    if len(item_id) > 20:
        return ''
    return item_id


def parse_positive_int(value, default_value, min_value=1, max_value=100000):
    try:
        parsed = int(str(value).strip())
    except Exception:
        return default_value
    return max(min_value, min(parsed, max_value))


def serialize_db_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def serialize_db_row(row):
    if not isinstance(row, dict):
        return row
    return {key: serialize_db_value(val) for key, val in row.items()}


def coerce_item_field_value(column, value):
    rule = ITEM_SCHEMA_RULES.get(column, {'type': 'str'})
    value_type = rule.get('type', 'str')
    max_len = rule.get('max_len')

    if value_type == 'str':
        text_value = '' if value is None else str(value)
        if max_len is not None and len(text_value) > max_len:
            raise ValueError(f'{column} 길이는 최대 {max_len}자입니다.')
        return text_value

    if value_type == 'int':
        text_value = '' if value is None else str(value).strip()
        if text_value == '':
            return 0
        return int(text_value)

    if value_type == 'decimal1':
        text_value = '' if value is None else str(value).strip()
        if text_value == '':
            return Decimal('0.0')
        decimal_value = Decimal(text_value)
        return decimal_value.quantize(Decimal('0.1'))

    if value_type == 'datetime':
        text_value = '' if value is None else str(value).strip()
        if text_value == '':
            return None
        datetime.strptime(text_value, '%Y-%m-%d %H:%M:%S')
        return text_value

    return value


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


def get_db_config():
    host = os.environ.get('MARIADB_HOST', '').strip()
    port = int(os.environ.get('MARIADB_PORT', '3306').strip() or '3306')
    database = os.environ.get('MARIADB_DATABASE', '').strip()
    user = os.environ.get('MARIADB_USER', '').strip()
    password = os.environ.get('MARIADB_PASSWORD', '')
    return {
        'host': host,
        'port': port,
        'database': database,
        'user': user,
        'password': password
    }


def validate_db_config(config):
    required_keys = ('host', 'database', 'user', 'password')
    missing = [key for key in required_keys if not config.get(key)]
    return missing


def execute_item_insert_sql(sql, item_id):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM g5_shop_item WHERE it_id = %s', (item_id,))
            duplicate_count = int(cursor.fetchone()[0] or 0)
            if duplicate_count > 0:
                return {
                    'inserted': False,
                    'affected': 0,
                    'duplicate': True
                }

            affected = cursor.execute(sql)
        conn.commit()
        return {
            'inserted': True,
            'affected': affected,
            'duplicate': False
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_stats_items(limit):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    safe_limit = max(1, min(int(limit), 500))
    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    it_id,
                    it_name,
                    it_seo_title,
                    it_brand,
                    it_model,
                    it_basic,
                    it_explan,
                    it_price,
                    it_stock_qty,
                    it_shop_memo,
                    it_sc_type,
                    it_sc_price,
                    it_1,
                    it_time
                FROM g5_shop_item
                ORDER BY it_time DESC, it_id DESC
                LIMIT %s
                """,
                (safe_limit,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def search_stats_items(item_id, item_name, page, page_size):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    safe_page = parse_positive_int(page, 1, 1, 100000)
    safe_page_size = parse_positive_int(page_size, 30, 1, 100)
    offset = (safe_page - 1) * safe_page_size

    normalized_item_id = normalize_item_id_for_stats(item_id)
    normalized_item_name = str(item_name or '').strip()

    where_clauses = []
    params = []
    if normalized_item_id:
        where_clauses.append('it_shop_memo = %s')
        params.append(normalized_item_id)
    if normalized_item_name:
        where_clauses.append('it_name LIKE %s')
        params.append(f'%{normalized_item_name}%')

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            count_sql = f'SELECT COUNT(*) AS total_count FROM g5_shop_item {where_sql}'
            cursor.execute(count_sql, tuple(params))
            total_count = int((cursor.fetchone() or {}).get('total_count') or 0)

            list_sql = f"""
                SELECT
                    it_id,
                    it_name,
                    it_seo_title,
                    it_brand,
                    it_model,
                    it_basic,
                    it_explan,
                    it_price,
                    it_stock_qty,
                    it_shop_memo,
                    it_sc_type,
                    it_sc_price,
                    it_1,
                    it_time
                FROM g5_shop_item
                {where_sql}
                ORDER BY it_time DESC, it_id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(list_sql, tuple(params + [safe_page_size, offset]))
            items = [serialize_db_row(row) for row in cursor.fetchall()]

        total_pages = max(1, (total_count + safe_page_size - 1) // safe_page_size)
        return {
            'items': items,
            'totalCount': total_count,
            'page': safe_page,
            'pageSize': safe_page_size,
            'totalPages': total_pages,
            'itemId': normalized_item_id,
            'itemName': normalized_item_name
        }
    finally:
        conn.close()


def fetch_item_detail(item_id):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM g5_shop_item WHERE it_id = %s LIMIT 1', (item_id,))
            row = cursor.fetchone()
            return serialize_db_row(row) if row else None
    finally:
        conn.close()


def update_item_detail(item_id, item_data):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    normalized_id = normalize_item_id_for_stats(item_id)
    if not normalized_id:
        raise RuntimeError('유효한 상품코드가 아닙니다.')

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM g5_shop_item WHERE it_id = %s LIMIT 1', (normalized_id,))
            existing = cursor.fetchone()
            if not existing:
                return {'updated': False, 'affected': 0, 'notFound': True}

            editable_columns = [column for column in existing.keys() if column != 'it_id']
            updates = []
            values = []
            for column in editable_columns:
                if column in item_data:
                    updates.append(f'`{column}` = %s')
                    values.append(coerce_item_field_value(column, item_data.get(column)))

            if not updates:
                return {'updated': False, 'affected': 0, 'notFound': False}

            values.append(normalized_id)
            update_sql = f"UPDATE g5_shop_item SET {', '.join(updates)} WHERE it_id = %s"
            affected = cursor.execute(update_sql, tuple(values))

        conn.commit()
        return {'updated': True, 'affected': affected, 'notFound': False}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_item_detail(item_id):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    normalized_id = normalize_item_id_for_stats(item_id)
    if not normalized_id:
        raise RuntimeError('유효한 상품코드가 아닙니다.')

    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset='utf8mb4',
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor
    )
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute('DELETE FROM g5_shop_item WHERE it_id = %s', (normalized_id,))
        conn.commit()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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


@app.route('/save-item', methods=['POST'])
def save_item():
    data = request.get_json(silent=True) or {}
    sql = str(data.get('sql', '')).strip()
    item_id = normalize_target(data.get('itemId', ''))

    if not sql:
        return jsonify({'success': False, 'message': '저장할 SQL이 없습니다.'}), 400

    if not item_id:
        return jsonify({'success': False, 'message': '상품코드(itemId)가 올바르지 않습니다.'}), 400

    normalized = re.sub(r'\s+', ' ', sql).strip().lower()
    if not normalized.startswith('insert into `g5_shop_item`') and not normalized.startswith('insert into g5_shop_item'):
        return jsonify({'success': False, 'message': '허용되지 않은 SQL입니다. g5_shop_item INSERT만 저장할 수 있습니다.'}), 400

    try:
        insert_result = execute_item_insert_sql(sql, item_id)
    except Exception as exc:
        return jsonify({'success': False, 'message': 'DB 저장에 실패했습니다.', 'error': str(exc)}), 500

    if insert_result.get('duplicate'):
        return jsonify({'success': False, 'message': f'이미 등록된 상품코드입니다: {item_id}', 'duplicate': True, 'itemId': item_id}), 409

    return jsonify({'success': True, 'message': 'DB 저장이 완료되었습니다.', 'affectedRows': insert_result.get('affected', 0), 'itemId': item_id})


@app.route('/stats-items', methods=['GET'])
def stats_items():
    item_id = request.args.get('itemId', '')
    item_name = request.args.get('itemName', '')
    page = request.args.get('page', '1')
    page_size = request.args.get('pageSize', '30')
    try:
        result = search_stats_items(item_id, item_name, page, page_size)
    except Exception as exc:
        return jsonify({'success': False, 'message': '통계 목록 조회에 실패했습니다.', 'error': str(exc)}), 500

    return jsonify({'success': True, **result})


@app.route('/stats-item/<item_id>', methods=['GET'])
def stats_item_detail(item_id):
    normalized_id = normalize_item_id_for_stats(item_id)
    if not normalized_id:
        return jsonify({'success': False, 'message': '유효한 상품코드가 아닙니다.'}), 400

    try:
        item = fetch_item_detail(normalized_id)
    except Exception as exc:
        return jsonify({'success': False, 'message': '상세 조회에 실패했습니다.', 'error': str(exc)}), 500

    if not item:
        return jsonify({'success': False, 'message': '대상 데이터가 없습니다.'}), 404

    return jsonify({'success': True, 'item': item})


@app.route('/stats-item/<item_id>', methods=['PUT'])
def stats_item_update(item_id):
    payload = request.get_json(silent=True) or {}
    item_data = payload.get('item')
    if not isinstance(item_data, dict):
        return jsonify({'success': False, 'message': '수정 데이터 형식이 올바르지 않습니다.'}), 400

    try:
        result = update_item_detail(item_id, item_data)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '데이터 수정에 실패했습니다.', 'error': str(exc)}), 500

    if result.get('notFound'):
        return jsonify({'success': False, 'message': '수정 대상이 존재하지 않습니다.'}), 404

    return jsonify({'success': True, 'message': '수정이 완료되었습니다.', 'affectedRows': result.get('affected', 0)})


@app.route('/stats-item/<item_id>', methods=['DELETE'])
def stats_item_delete(item_id):
    try:
        affected = delete_item_detail(item_id)
    except Exception as exc:
        return jsonify({'success': False, 'message': '삭제에 실패했습니다.', 'error': str(exc)}), 500

    if affected == 0:
        return jsonify({'success': False, 'message': '삭제 대상이 존재하지 않습니다.'}), 404

    return jsonify({'success': True, 'message': '삭제가 완료되었습니다.', 'affectedRows': affected})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
