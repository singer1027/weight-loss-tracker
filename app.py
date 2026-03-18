import os
from functools import wraps

import pymysql
import pymysql.cursors
from flask import Flask, jsonify, redirect, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────────
# 数据库辅助
# ──────────────────────────────────────────────
def get_db():
    kwargs = dict(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    # TiDB Cloud Serverless 需要 SSL
    if config.DB_SSL:
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        kwargs['ssl'] = ctx
    return pymysql.connect(**kwargs)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
# 页面路由
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'auth.html'))


@app.route('/record')
def record():
    if 'user_id' not in session:
        return redirect('/')
    return send_file(os.path.join(BASE_DIR, 'record.html'))


# ──────────────────────────────────────────────
# 认证接口
# ──────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if len(username) < 2 or len(username) > 20:
        return jsonify({'error': '用户名长度应为 2-20 个字符'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于 6 位'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                return jsonify({'error': '用户名已存在'}), 400
            pwd_hash = generate_password_hash(password)
            cur.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                (username, pwd_hash),
            )
            conn.commit()
            user_id = cur.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, username, password_hash FROM users WHERE username = %s',
                (username,),
            )
            user = cur.fetchone()
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': '用户名或密码错误'}), 401
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'username': user['username']})
    finally:
        conn.close()


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({'user_id': session['user_id'], 'username': session['username']})


# ──────────────────────────────────────────────
# 打卡记录接口
# ──────────────────────────────────────────────
def _empty_day(i):
    return {
        'date': i, 'weight': '', 'waist': '', 'thigh': '',
        'sport': '', 'done': False, 'lunch': '', 'snack': '', 'dinner': '',
    }


@app.route('/api/records', methods=['GET'])
@login_required
def get_records():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM records WHERE user_id = %s ORDER BY day',
                (session['user_id'],),
            )
            rows = {r['day']: r for r in cur.fetchall()}

        result = []
        for i in range(1, 31):
            if i in rows:
                r = rows[i]
                result.append({
                    'date': i,
                    'weight': str(r['weight']) if r['weight'] is not None else '',
                    'waist':  str(r['waist'])  if r['waist']  is not None else '',
                    'thigh':  str(r['thigh'])  if r['thigh']  is not None else '',
                    'sport':  r['sport']  or '',
                    'done':   bool(r['done']),
                    'lunch':  r['lunch']  or '',
                    'snack':  r['snack']  or '',
                    'dinner': r['dinner'] or '',
                })
            else:
                result.append(_empty_day(i))
        return jsonify({'records': result})
    finally:
        conn.close()


@app.route('/api/records/<int:day>', methods=['PUT'])
@login_required
def update_record(day):
    if day < 1 or day > 30:
        return jsonify({'error': '无效的天数'}), 400

    data = request.get_json(silent=True) or {}

    def to_decimal(val):
        try:
            return float(val) if val not in (None, '') else None
        except (ValueError, TypeError):
            return None

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO records
                    (user_id, day, weight, waist, thigh, sport, done, lunch, snack, dinner)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    weight = VALUES(weight),
                    waist  = VALUES(waist),
                    thigh  = VALUES(thigh),
                    sport  = VALUES(sport),
                    done   = VALUES(done),
                    lunch  = VALUES(lunch),
                    snack  = VALUES(snack),
                    dinner = VALUES(dinner)
                ''',
                (
                    session['user_id'], day,
                    to_decimal(data.get('weight')),
                    to_decimal(data.get('waist')),
                    to_decimal(data.get('thigh')),
                    data.get('sport') or None,
                    bool(data.get('done', False)),
                    data.get('lunch')  or None,
                    data.get('snack')  or None,
                    data.get('dinner') or None,
                ),
            )
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/records', methods=['DELETE'])
@login_required
def reset_records():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM records WHERE user_id = %s', (session['user_id'],))
            conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ──────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
