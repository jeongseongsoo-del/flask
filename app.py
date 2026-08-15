from flask import Flask, jsonify, request, Response, render_template, send_from_directory, session, redirect
from flask_cors import CORS
from urllib.parse import quote
from urllib.request import Request, urlopen
from datetime import datetime
from decimal import Decimal, ROUND_UP
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
    return request.path.startswith('/collect') or request.path.startswith('/lookup-proino') or request.path.startswith('/item-detail') or request.path.startswith('/save-item') or request.path.startswith('/stats-items') or request.path.startswith('/stats-item') or request.path.startswith('/channel-configs')


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


def parse_json_object_text(raw_text, field_name='extra_json'):
    text = '' if raw_text is None else str(raw_text).strip()
    if not text:
        return {}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'{field_name} JSON 형식이 올바르지 않습니다: {exc.msg}') from exc

    if not isinstance(parsed, dict):
        raise ValueError(f'{field_name} 값은 JSON 객체여야 합니다.')

    return parsed


CHANNEL_DEFAULTS = [
    {'channel_code': 'ownmall', 'display_name': '자사몰', 'auth_type': 'db'},
    {'channel_code': 'coupang', 'display_name': '쿠팡', 'auth_type': 'hmac'},
    {'channel_code': 'naver_smartstore', 'display_name': '네이버스마트스토어', 'auth_type': 'oauth2'},
    {'channel_code': 'cafe24', 'display_name': 'cafe24', 'auth_type': 'oauth2'},
    {'channel_code': 'firstmall', 'display_name': '퍼스트몰', 'auth_type': 'api_key'},
    {'channel_code': 'auction', 'display_name': '옥션', 'auth_type': 'oauth2'},
    {'channel_code': 'gmarket', 'display_name': 'g마켓', 'auth_type': 'oauth2'},
    {'channel_code': '11st', 'display_name': '11번가', 'auth_type': 'api_key'}
]


def mask_secret(value):
    text = '' if value is None else str(value)
    if not text:
        return ''
    if len(text) <= 6:
        return '*' * len(text)
    return f'{text[:3]}{"*" * (len(text) - 5)}{text[-2:]}'


def ensure_channel_credentials_table(conn):
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS g5_channel_credentials (
            id BIGINT NOT NULL AUTO_INCREMENT,
            channel_code VARCHAR(50) NOT NULL,
            display_name VARCHAR(120) NOT NULL,
            auth_type VARCHAR(30) NOT NULL DEFAULT 'api_key',
            base_url VARCHAR(255) DEFAULT '',
            shop_id VARCHAR(120) DEFAULT '',
            client_id TEXT,
            client_secret TEXT,
            access_token TEXT,
            refresh_token TEXT,
            api_key TEXT,
            api_secret TEXT,
            extra_json TEXT,
            is_enabled TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uk_channel_code (channel_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """

    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)


def ensure_item_register_status_table(conn):
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS g5_item_register_status (
            id BIGINT NOT NULL AUTO_INCREMENT,
            it_id VARCHAR(20) NOT NULL,
            item_code VARCHAR(20) NOT NULL,
            product_name VARCHAR(255) NOT NULL DEFAULT '',
            shop_name VARCHAR(50) NOT NULL DEFAULT '',
            supply_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
            base_ship_unit VARCHAR(80) NOT NULL DEFAULT '',
            stock_qty INT NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'registered',
            registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uk_it_id (it_id),
            KEY idx_item_code (item_code),
            KEY idx_registered_at (registered_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """

    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'g5_item_register_status'
              AND COLUMN_NAME IN ('product_name', 'shop_name')
            """
        )
        existing_columns = {str(row[0]) for row in (cursor.fetchall() or [])}

        if 'product_name' not in existing_columns:
            cursor.execute("ALTER TABLE g5_item_register_status ADD COLUMN product_name VARCHAR(255) NOT NULL DEFAULT '' AFTER item_code")
        if 'shop_name' not in existing_columns:
            cursor.execute("ALTER TABLE g5_item_register_status ADD COLUMN shop_name VARCHAR(50) NOT NULL DEFAULT '' AFTER product_name")


def normalize_channel_code(value):
    code = str(value or '').strip().lower()
    if not re.fullmatch(r'[a-z0-9_\-]{2,50}', code):
        raise ValueError('채널코드 형식이 올바르지 않습니다.')
    return code


def to_channel_int_flag(value):
    if isinstance(value, bool):
        return 1 if value else 0
    text = str(value or '').strip().lower()
    if text in ('1', 'true', 'y', 'yes', 'on'):
        return 1
    return 0


def normalize_channel_payload(payload, channel_code):
    defaults = {
        'display_name': channel_code,
        'auth_type': 'api_key',
        'base_url': '',
        'shop_id': '',
        'client_id': '',
        'client_secret': '',
        'access_token': '',
        'refresh_token': '',
        'api_key': '',
        'api_secret': '',
        'extra_json': '',
        'is_enabled': 1
    }
    data = {}
    source = payload if isinstance(payload, dict) else {}

    for key, fallback in defaults.items():
        value = source.get(key, fallback)
        if key == 'is_enabled':
            data[key] = to_channel_int_flag(value)
            continue
        if key == 'extra_json' and isinstance(value, dict):
            data[key] = json.dumps(value, ensure_ascii=False)
            continue
        data[key] = '' if value is None else str(value).strip()

    if len(data['display_name']) > 120:
        raise ValueError('display_name 길이는 최대 120자입니다.')
    if len(data['auth_type']) > 30:
        raise ValueError('auth_type 길이는 최대 30자입니다.')
    if len(data['base_url']) > 255:
        raise ValueError('base_url 길이는 최대 255자입니다.')
    if len(data['shop_id']) > 120:
        raise ValueError('shop_id 길이는 최대 120자입니다.')

    data['channel_code'] = channel_code
    return data


def fetch_channel_configs(include_secrets=False):
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
        ensure_channel_credentials_table(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    channel_code,
                    display_name,
                    auth_type,
                    base_url,
                    shop_id,
                    client_id,
                    client_secret,
                    access_token,
                    refresh_token,
                    api_key,
                    api_secret,
                    extra_json,
                    is_enabled,
                    created_at,
                    updated_at
                FROM g5_channel_credentials
                ORDER BY channel_code ASC
                """
            )
            rows = cursor.fetchall() or []
    finally:
        conn.close()

    result = []
    for row in rows:
        item = serialize_db_row(row)
        item['is_enabled'] = bool(item.get('is_enabled'))
        if include_secrets:
            result.append(item)
            continue
        item['client_id_masked'] = mask_secret(item.get('client_id'))
        item['client_secret_masked'] = mask_secret(item.get('client_secret'))
        item['access_token_masked'] = mask_secret(item.get('access_token'))
        item['refresh_token_masked'] = mask_secret(item.get('refresh_token'))
        item['api_key_masked'] = mask_secret(item.get('api_key'))
        item['api_secret_masked'] = mask_secret(item.get('api_secret'))
        item.pop('client_id', None)
        item.pop('client_secret', None)
        item.pop('access_token', None)
        item.pop('refresh_token', None)
        item.pop('api_key', None)
        item.pop('api_secret', None)
        result.append(item)

    return result


def fetch_channel_config(channel_code, include_secrets=False):
    normalized_code = normalize_channel_code(channel_code)
    rows = fetch_channel_configs(include_secrets=include_secrets)
    return next((item for item in rows if item.get('channel_code') == normalized_code), None)


def get_ownmall_target_db_config():
    ownmall_config = fetch_channel_config('ownmall', include_secrets=True)
    if not ownmall_config:
        raise RuntimeError('ownmall 채널 설정이 없습니다. 채널설정 페이지에서 테이블 초기화 후 설정을 저장하세요.')

    if not bool(ownmall_config.get('is_enabled')):
        raise RuntimeError('ownmall 채널이 비활성화 상태입니다. 채널설정에서 사용 체크 후 저장하세요.')

    extra = parse_json_object_text(ownmall_config.get('extra_json', ''), 'ownmall.extra_json')

    db_host = str(extra.get('db_host') or extra.get('host') or '').strip()
    db_port_raw = extra.get('db_port', extra.get('port', 3306))
    db_database = str(extra.get('db_database') or extra.get('database') or '').strip()
    db_user = str(extra.get('db_user') or extra.get('user') or '').strip()
    db_password = '' if extra.get('db_password') is None else str(extra.get('db_password'))

    try:
        db_port = int(str(db_port_raw).strip() or '3306')
    except Exception as exc:
        raise RuntimeError('ownmall.extra_json의 db_port(또는 port) 값이 올바르지 않습니다.') from exc

    target_config = {
        'host': db_host,
        'port': db_port,
        'database': db_database,
        'user': db_user,
        'password': db_password
    }
    missing = validate_db_config(target_config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(
            f'ownmall DB 접속정보가 누락되었습니다: {missing_names}. '
            '채널설정 > ownmall 의 extra_json에 db_host, db_port, db_database, db_user, db_password를 입력하세요.'
        )

    return target_config


def upsert_channel_config(channel_code, payload):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    normalized_code = normalize_channel_code(channel_code)
    normalized_data = normalize_channel_payload(payload, normalized_code)

    if normalized_data.get('extra_json'):
        parse_json_object_text(normalized_data.get('extra_json'), f'{normalized_code}.extra_json')

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
        ensure_channel_credentials_table(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO g5_channel_credentials (
                    channel_code, display_name, auth_type, base_url, shop_id,
                    client_id, client_secret, access_token, refresh_token,
                    api_key, api_secret, extra_json, is_enabled
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    auth_type = VALUES(auth_type),
                    base_url = VALUES(base_url),
                    shop_id = VALUES(shop_id),
                    client_id = COALESCE(NULLIF(VALUES(client_id), ''), client_id),
                    client_secret = COALESCE(NULLIF(VALUES(client_secret), ''), client_secret),
                    access_token = COALESCE(NULLIF(VALUES(access_token), ''), access_token),
                    refresh_token = COALESCE(NULLIF(VALUES(refresh_token), ''), refresh_token),
                    api_key = COALESCE(NULLIF(VALUES(api_key), ''), api_key),
                    api_secret = COALESCE(NULLIF(VALUES(api_secret), ''), api_secret),
                    extra_json = VALUES(extra_json),
                    is_enabled = VALUES(is_enabled)
                """,
                (
                    normalized_data['channel_code'],
                    normalized_data['display_name'],
                    normalized_data['auth_type'],
                    normalized_data['base_url'],
                    normalized_data['shop_id'],
                    normalized_data['client_id'],
                    normalized_data['client_secret'],
                    normalized_data['access_token'],
                    normalized_data['refresh_token'],
                    normalized_data['api_key'],
                    normalized_data['api_secret'],
                    normalized_data['extra_json'],
                    normalized_data['is_enabled']
                )
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_channel_configs():
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
        ensure_channel_credentials_table(conn)
        with conn.cursor() as cursor:
            for channel in CHANNEL_DEFAULTS:
                cursor.execute(
                    """
                    INSERT INTO g5_channel_credentials (channel_code, display_name, auth_type, is_enabled)
                    VALUES (%s, %s, %s, 0)
                    ON DUPLICATE KEY UPDATE
                        display_name = VALUES(display_name),
                        auth_type = COALESCE(NULLIF(auth_type, ''), VALUES(auth_type))
                    """,
                    (channel['channel_code'], channel['display_name'], channel['auth_type'])
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def normalize_selected_item_ids(item_ids):
    normalized_ids = []
    seen_ids = set()
    for item_id in item_ids or []:
        normalized_id = normalize_item_id_for_stats(item_id)
        if not normalized_id or normalized_id in seen_ids:
            continue
        seen_ids.add(normalized_id)
        normalized_ids.append(normalized_id)
    return normalized_ids


def _to_int_or_zero(value):
    text = '' if value is None else str(value).strip()
    if text == '':
        return 0
    try:
        return int(float(text.replace(',', '')))
    except Exception:
        return 0


def _to_decimal_or_zero(value):
    text = '' if value is None else str(value).strip()
    if text == '':
        return Decimal('0.00')
    try:
        return Decimal(text.replace(',', '')).quantize(Decimal('0.01'))
    except Exception:
        return Decimal('0.00')


def _calculate_register_cust_price(it_price):
    # Rule for "내가 상품등록": it_cust_price = ceil((it_price * 1.1) / 100) * 100
    safe_price = max(0, _to_int_or_zero(it_price))
    raw_price = Decimal(safe_price) * Decimal('1.1')
    hundred_units = (raw_price / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_UP)
    return int(hundred_units * Decimal('100'))


def _extract_base_ship_unit(row):
    explain_html = str((row or {}).get('it_explan') or '')
    explain_match = re.search(r'출고수량\(주문단위\)</span>\s*:\s*([^<\n\r]+)', explain_html)
    if explain_match:
        qty_text = explain_match.group(1).strip()
        return qty_text.split('/', 1)[0].strip()

    item_name = str((row or {}).get('it_name') or '').strip()
    match = re.search(r'/\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*([^\s/]+)\s*$', item_name)
    if not match:
        return ''
    qty = match.group(1).strip()
    return qty


def upsert_item_register_status(config, rows, shop_name='nega'):
    if not rows:
        return {'tracked': 0}

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
        ensure_item_register_status_table(conn)
        upsert_sql = """
            INSERT INTO g5_item_register_status (
                it_id,
                item_code,
                product_name,
                shop_name,
                supply_price,
                base_ship_unit,
                stock_qty,
                status,
                registered_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                item_code = VALUES(item_code),
                product_name = VALUES(product_name),
                shop_name = VALUES(shop_name),
                supply_price = VALUES(supply_price),
                base_ship_unit = VALUES(base_ship_unit),
                stock_qty = VALUES(stock_qty),
                status = VALUES(status),
                registered_at = VALUES(registered_at)
        """

        with conn.cursor() as cursor:
            tracked = 0
            for row in rows:
                # Save status rows with canonical 7-digit product code.
                product_code = normalize_target(row.get('it_shop_memo')) or normalize_target(row.get('it_id'))
                if len(product_code) != 7:
                    continue
                it_id = product_code
                item_code = product_code
                product_name = str(row.get('it_name') or '').strip()
                supply_price = _to_decimal_or_zero(row.get('it_cust_price'))
                base_ship_unit = _extract_base_ship_unit(row)
                stock_qty = max(0, _to_int_or_zero(row.get('it_stock_qty')))
                cursor.execute(
                    upsert_sql,
                    (it_id, item_code, product_name, str(shop_name or '').strip(), supply_price, base_ship_unit, stock_qty, 'registered')
                )
                tracked += 1

        conn.commit()
        return {'tracked': tracked}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
                    it_brand,
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


def delete_items_detail(item_ids):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    config = get_db_config()
    missing = validate_db_config(config)
    if missing:
        missing_names = ', '.join(missing)
        raise RuntimeError(f'DB 접속 환경변수가 누락되었습니다: {missing_names}')

    normalized_ids = normalize_selected_item_ids(item_ids)

    if not normalized_ids:
        raise RuntimeError('삭제할 상품코드가 없습니다.')

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
        placeholders = ', '.join(['%s'] * len(normalized_ids))
        with conn.cursor() as cursor:
            affected = cursor.execute(f'DELETE FROM g5_shop_item WHERE it_id IN ({placeholders})', tuple(normalized_ids))
        conn.commit()
        return {'affected': affected, 'requested': len(normalized_ids)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def register_items_to_target_db(item_ids):
    if pymysql is None:
        raise RuntimeError('pymysql 패키지가 설치되지 않았습니다. requirements 설치 후 다시 시도하세요.')

    normalized_ids = normalize_selected_item_ids(item_ids)
    if not normalized_ids:
        raise RuntimeError('전송할 상품코드가 없습니다.')

    source_config = get_db_config()
    source_missing = validate_db_config(source_config)
    if source_missing:
        missing_names = ', '.join(source_missing)
        raise RuntimeError(f'원본 DB 접속 환경변수가 누락되었습니다: {missing_names}')

    target_config = get_ownmall_target_db_config()

    source_conn = pymysql.connect(
        host=source_config['host'],
        port=source_config['port'],
        user=source_config['user'],
        password=source_config['password'],
        database=source_config['database'],
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    target_conn = pymysql.connect(
        host=target_config['host'],
        port=target_config['port'],
        user=target_config['user'],
        password=target_config['password'],
        database=target_config['database'],
        charset='utf8mb4',
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor
    )

    try:
        placeholders = ', '.join(['%s'] * len(normalized_ids))
        with source_conn.cursor() as source_cursor:
            source_cursor.execute(f'SELECT * FROM g5_shop_item WHERE it_id IN ({placeholders})', tuple(normalized_ids))
            source_rows = source_cursor.fetchall() or []

        row_map = {str(row.get('it_id', '')): row for row in source_rows}
        ordered_rows = [row_map[item_id] for item_id in normalized_ids if item_id in row_map]
        missing_item_ids = [item_id for item_id in normalized_ids if item_id not in row_map]

        if not ordered_rows:
            return {
                'requested': len(normalized_ids),
                'transferred': 0,
                'affected': 0,
                'missing': len(missing_item_ids),
                'missingItemIds': missing_item_ids,
                'duplicates': 0,
                'duplicateItemIds': []
            }

        with target_conn.cursor() as target_cursor:
            target_cursor.execute(
                f'SELECT it_id FROM g5_shop_item WHERE it_id IN ({placeholders})',
                tuple(normalized_ids)
            )
            existing_rows = target_cursor.fetchall() or []

        existing_item_ids = {str(row[0]) for row in existing_rows}
        duplicate_item_ids = [item_id for item_id in normalized_ids if item_id in existing_item_ids]
        insert_rows = [row for row in ordered_rows if str(row.get('it_id', '')) not in existing_item_ids]

        if not insert_rows:
            return {
                'requested': len(normalized_ids),
                'transferred': 0,
                'affected': 0,
                'missing': len(missing_item_ids),
                'missingItemIds': missing_item_ids,
                'duplicates': len(duplicate_item_ids),
                'duplicateItemIds': duplicate_item_ids,
                'trackingUpdated': True,
                'tracked': 0,
                'trackingError': ''
            }

        columns = list(insert_rows[0].keys())
        insert_columns = ', '.join([f'`{column}`' for column in columns])
        values_placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f'INSERT INTO g5_shop_item ({insert_columns}) VALUES ({values_placeholders})'

        affected_rows = 0
        with target_conn.cursor() as target_cursor:
            for row in insert_rows:
                row['it_cust_price'] = _calculate_register_cust_price(row.get('it_price'))
                values = [coerce_item_field_value(column, row.get(column)) for column in columns]
                affected_rows += target_cursor.execute(insert_sql, tuple(values))

        target_conn.commit()

        tracking_error = ''
        tracking_result = {'tracked': 0}
        try:
            tracking_result = upsert_item_register_status(source_config, insert_rows, shop_name='nega')
        except Exception as exc:
            tracking_error = str(exc)

        return {
            'requested': len(normalized_ids),
            'transferred': len(insert_rows),
            'affected': affected_rows,
            'missing': len(missing_item_ids),
            'missingItemIds': missing_item_ids,
            'duplicates': len(duplicate_item_ids),
            'duplicateItemIds': duplicate_item_ids,
            'trackingUpdated': bool(not tracking_error),
            'tracked': int(tracking_result.get('tracked', 0) or 0),
            'trackingError': tracking_error
        }
    except Exception:
        target_conn.rollback()
        raise
    finally:
        source_conn.close()
        target_conn.close()


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
    return render_template('pages/dashboard/index.html')


@app.route('/index.html')
def serve_index():
    return render_template('pages/dashboard/index.html')


@app.route('/ctx-single-collection.html')
def serve_page():
    return render_template('pages/ctx/single-collection.html')


@app.route('/channel-configs.html')
def serve_channel_configs_page():
    return render_template('pages/channel-configs/index.html')


def send_html_file(filename):
    response = send_from_directory(os.path.dirname(__file__), filename, max_age=0)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


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

    if len(item_id) != 7:
        return jsonify({'success': False, 'message': '상품코드(itemId)는 숫자 7자리만 허용됩니다.'}), 400

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


@app.route('/stats-items/delete-selected', methods=['POST'])
def stats_items_delete_selected():
    payload = request.get_json(silent=True) or {}
    item_ids = payload.get('itemIds')
    if not isinstance(item_ids, list):
        return jsonify({'success': False, 'message': '삭제할 상품코드 목록 형식이 올바르지 않습니다.'}), 400

    try:
        result = delete_items_detail(item_ids)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '선택 삭제에 실패했습니다.', 'error': str(exc)}), 500

    if result.get('affected', 0) <= 0:
        return jsonify({'success': False, 'message': '삭제할 데이터가 없습니다.'}), 404

    return jsonify({
        'success': True,
        'message': f'선택한 {result.get("requested", 0)}건을 삭제했습니다.',
        'affectedRows': result.get('affected', 0),
        'requested': result.get('requested', 0)
    })


@app.route('/stats-items/register-selected', methods=['POST'])
def stats_items_register_selected():
    payload = request.get_json(silent=True) or {}
    item_ids = payload.get('itemIds')
    if not isinstance(item_ids, list):
        return jsonify({'success': False, 'message': '전송할 상품코드 목록 형식이 올바르지 않습니다.'}), 400

    try:
        result = register_items_to_target_db(item_ids)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '선택 상품 전송에 실패했습니다.', 'error': str(exc)}), 500

    if result.get('transferred', 0) <= 0:
        if result.get('duplicates', 0) > 0:
            return jsonify({
                'success': True,
                'message': f'중복 it_id {result.get("duplicates", 0)}건은 제외되어 신규 등록이 없습니다.',
                **result
            })
        return jsonify({'success': False, 'message': '전송할 데이터가 없습니다.', **result}), 404

    message = f'선택한 {result.get("transferred", 0)}건을 대상 DB로 전송했습니다.'
    if result.get('missing', 0) > 0:
        message += f' (원본 미존재 {result.get("missing", 0)}건)'
    if result.get('duplicates', 0) > 0:
        message += f' (중복 it_id 제외 {result.get("duplicates", 0)}건)'
    if not result.get('trackingUpdated', True):
        message += ' (관리 상태 업데이트 실패)'
    elif result.get('tracked', 0) > 0:
        message += f' (관리 상태 {result.get("tracked", 0)}건 업데이트)'

    return jsonify({'success': True, 'message': message, **result})


@app.route('/channel-configs/init', methods=['POST'])
def channel_configs_init():
    try:
        initialize_channel_configs()
    except Exception as exc:
        return jsonify({'success': False, 'message': '채널 설정 초기화에 실패했습니다.', 'error': str(exc)}), 500

    return jsonify({'success': True, 'message': '채널 설정 테이블 초기화가 완료되었습니다.'})


@app.route('/channel-configs', methods=['GET'])
def channel_configs_list():
    include_secrets = str(request.args.get('includeSecrets', '')).strip().lower() in ('1', 'true', 'y', 'yes')
    try:
        rows = fetch_channel_configs(include_secrets=include_secrets)
    except Exception as exc:
        return jsonify({'success': False, 'message': '채널 설정 목록 조회에 실패했습니다.', 'error': str(exc)}), 500

    return jsonify({'success': True, 'items': rows})


@app.route('/channel-configs/<channel_code>', methods=['PUT'])
def channel_configs_upsert(channel_code):
    payload = request.get_json(silent=True) or {}
    item = payload.get('item') if isinstance(payload.get('item'), dict) else payload

    try:
        upsert_channel_config(channel_code, item)
        rows = fetch_channel_configs(include_secrets=False)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': '채널 설정 저장에 실패했습니다.', 'error': str(exc)}), 500

    matched = next((row for row in rows if row.get('channel_code') == channel_code.lower()), None)
    return jsonify({'success': True, 'message': '채널 설정이 저장되었습니다.', 'item': matched})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
