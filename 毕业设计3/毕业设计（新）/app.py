from flask import Flask, render_template, request, send_from_directory, jsonify, session, redirect, url_for
import matplotlib
# 切换到非交互模式
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import logging
from functools import lru_cache
import sqlite3
from datetime import datetime
import os
from contextlib import contextmanager

# 配置日志
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 设置会话密钥，用于 session 管理
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_dev_secret_key')  

# 定义 database_connection 上下文管理器
@contextmanager
def database_connection():
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"数据库操作出错: {e}")
        raise
    finally:
        if conn:
            conn.close()

# 定义 init_db 函数
def init_db():
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            # 创建 guanliyuan 表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guanliyuan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            ''')
            # 创建题目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    question TEXT NOT NULL,
                    options TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    explanation TEXT NOT NULL
                )
            ''')
            conn.commit()
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")

# 调用 init_db 函数
init_db()

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用 SimHei 字体，如果没有可以尝试 WenQuanYi Zen Hei
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 使用缓存优化函数数据生成
@lru_cache(maxsize=128)
def generate_function_data(function_type, a, b, c):
    try:
        if function_type == 'linear':
            x = np.linspace(-10, 10, 400)
            y = a * x + b
        elif function_type == 'quadratic':
            x = np.linspace(-10, 10, 400)
            y = a * x**2 + b * x + c
        elif function_type == 'inverse':
            if a == 0:
                raise ValueError("反比例函数的参数 a 不能为 0")
            # 排除 x=0 以避免除零错误
            x = np.concatenate([np.linspace(-10, -0.1, 200), np.linspace(0.1, 10, 200)])
            y = a / x + b
        else:
            raise ValueError("未知的函数类型")
        return x, y
    except Exception as e:
        logger.error(f"生成函数数据时出错: {e}")
        raise

# 定义图像生成逻辑
def generate_plot_image(x, y):
    try:
        plt.figure(figsize=(10, 6))  # 设置图像大小
        plt.plot(x, y, linewidth=2)  # 设置线条宽度
        plt.grid(True, linestyle='--', alpha=0.7)  # 设置网格样式
        plt.axhline(y=0, color='k', linewidth=1.5)  # 添加 x 轴
        plt.axvline(x=0, color='k', linewidth=1.5)  # 添加 y 轴
        plt.title('函数图像', fontsize=16)  # 添加标题
        plt.xlabel('X 轴', fontsize=12)  # 添加 x 轴标签
        plt.ylabel('Y 轴', fontsize=12)  # 添加 y 轴标签

        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=300)  # 设置图像分辨率
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return plot_url
    except Exception as e:
        logger.error(f"生成图像时出错: {e}")
        raise

# 登录验证装饰器
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 首页重定向到登录页
@app.route('/')
def index():
    return render_template('welcome.html')

# 学习材料下载页面
@app.route('/download')
@login_required
def download():
    return render_template('download.html')

# 下载学习材料
@app.route('/download_material/<path:filename>')
@login_required
def download_material(filename):
    return send_from_directory('static/materials', filename, as_attachment=True)

# 函数图像生成页面
@app.route('/graph', methods=['GET', 'POST'])
@login_required
def graph():
    error = None
    plot_url = None
    function_type = request.form.get('function_type', 'linear')
    a = request.form.get('a', 1, type=float)
    b = request.form.get('b', 0, type=float)
    c = request.form.get('c', 0, type=float)

    if request.method == 'POST':
        try:
            x, y = generate_function_data(function_type, a, b, c)
            plot_url = generate_plot_image(x, y)
        except ValueError as e:
            error = str(e)
        except Exception as e:
            error = "生成图像时发生未知错误，请稍后重试。"
            logger.error(f"处理 POST 请求时出错: {e}")

    return render_template('graph.html', plot_url=plot_url, error=error, function_type=function_type, a=a, b=b, c=c)

# 学习者交流页面
from flask import session

from contextlib import contextmanager

@contextmanager
def database_connection():
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"数据库操作出错: {e}")
        raise
    finally:
        if conn:
            conn.close()

# 使用示例，修改 forum 函数
@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    if request.method == 'POST':
        username = session.get('username')
        message = request.form.get('message')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not message:
            return jsonify({'success': False, 'error': '留言内容不能为空'}), 400

        try:
            with database_connection() as conn:
                c = conn.cursor()
                c.execute("INSERT INTO messages (username, message, timestamp) VALUES (?,?,?)", (username, message, timestamp))
            return jsonify({'success': True, 'username': username, 'message': message, 'timestamp': timestamp})
        except Exception as e:
            return jsonify({'success': False, 'error': '保存留言时发生错误，请稍后重试'}), 500

    try:
        with database_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM messages ORDER BY id DESC")
            messages = c.fetchall()
    except Exception as e:
        logger.error(f"获取留言列表时出错: {e}")
        messages = []

    return render_template('forum.html', messages=messages)



# 互动式练习页面
@app.route('/practice', methods=['GET', 'POST'])
@login_required
def practice():
    questions = []
    user_answers = {}
    results = []
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type, question, options, answer, explanation FROM questions ORDER BY id')
            rows = cursor.fetchall()
            for row in rows:
                question = {
                    "id": row[0],
                    "type": row[1],
                    "question": row[2],
                    "options": row[3].split(','),
                    "answer": row[4],
                    "explanation": row[5]
                }
                questions.append(question)
    except Exception as e:
        logger.error(f"获取题目数据时出错: {e}")

    if request.method == 'POST':
        results = []
        for i, question in enumerate(questions):
            user_answer = request.form.get(f'answer_{i}')
            is_correct = user_answer == question['answer']
            user_answers[f'answer_{i}'] = user_answer
            results.append({
                "question": question['question'],
                "user_answer": user_answer,
                "correct_answer": question['answer'],
                "explanation": question['explanation'],
                "is_correct": is_correct
            })

    return render_template('practice.html', questions=questions, results=results, user_answers=user_answers)
    return render_template('practice.html', questions=questions)

def get_request_data():
    if request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
        if not data:
            return None, None, '请求数据格式有误，未正确解析 JSON 数据'
        username = data.get('username')
        password = data.get('password')
    elif request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        username = request.form.get('username')
        password = request.form.get('password')
    else:
        return None, None, '请求头 Content-Type 不正确，请使用 application/json 或 application/x-www-form-urlencoded'
    return username, password, None

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password, error = get_request_data()
        if error:
            return jsonify({'success': False, 'error': error}), 400
        if not username or not password:
            return jsonify({'success': False, 'error': '缺少必要参数，用户名和密码不能为空'}), 400
        conn = None
        try:
            conn = sqlite3.connect('forum.db', check_same_thread=False)
            c = conn.cursor()
            conn.execute('BEGIN')
            # 直接保存密码，不加密
            c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
            conn.commit()
            # 注册成功后自动登录
            session['username'] = username
            # 假设用户注册后不是管理员，这里不设置 is_admin 会话
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            if conn:
                conn.rollback()
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        except Exception as e:
            logger.error(f"注册时出错: {e}")
            if conn:
                conn.rollback()
            return jsonify({'success': False, 'error': '注册时发生错误，请稍后重试'}), 500
        finally:
            if conn:
                conn.close()
    return render_template('register.html')

# 管理员登录页面
@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

# 处理管理员登录请求
@app.route('/admin_login_process', methods=['POST'])
def admin_login_process():
    username, password, error = get_request_data()
    if error:
        logger.error(f"获取请求数据时出错: {error}")
        return redirect(url_for('admin_login', error=error))
    if not username or not password:
        error_msg = "缺少必要参数，用户名和密码不能为空"
        logger.error(error_msg)
        return redirect(url_for('admin_login', error=error_msg))

    # 直接判断用户名和密码
    if username == 'guanliyuan' and password == '123456':
        session['username'] = username
        session['is_admin'] = True
        return redirect(url_for('admin_panel'))
    else:
        error_msg = "管理员用户名或密码错误"
        logger.error(error_msg)
        return redirect(url_for('admin_login', error=error_msg))

   

# 修改原有的登录函数，移除管理员登录逻辑
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password, error = get_request_data()
        if error:
            logger.error(f"获取请求数据时出错: {error}")
            return jsonify({'success': False, 'error': error}), 400
        if not username or not password:
            logger.error("缺少必要参数，用户名和密码不能为空")
            return jsonify({'success': False, 'error': '缺少必要参数，用户名和密码不能为空'}), 400

        try:
            with database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username =? AND password =?", (username, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    session.pop('is_admin', None)
                    return redirect(url_for('graph'))
                else:
                    logger.error("普通用户用户名或密码错误")
                    return jsonify({'success': False, 'error': '普通用户用户名或密码错误'}), 400
        except sqlite3.Error as sql_error:
            logger.error(f"SQLite 登录错误: {sql_error}")
            return jsonify({'success': False, 'error': '数据库操作出错，请稍后重试'}), 500
        except Exception as e:
            logger.error(f"未知登录错误: {e}", exc_info=True)
            return jsonify({'success': False, 'error': '登录时发生未知错误，请稍后重试'}), 500
    return render_template('login.html')

# 注销确认页面
@app.route('/logout_confirm')
@login_required
def logout_confirm():
    return render_template('logout_confirm.html')

# 处理注销请求
@app.route('/logout')
@login_required
def logout():
    # 仅清除会话信息，实现注销功能
    session.pop('username', None)
    session.pop('is_admin', None)  # 同时移除管理员会话标记
    # 明确跳转到登录界面
    return redirect(url_for('login'))

# 若需要删除用户的功能，可以单独定义一个函数
@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    username = session.get('username')
    if not username:
        return jsonify({'success': False, 'error': '未找到用户信息'}), 400
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            # 开始事务
            conn.execute('BEGIN')
            # 删除用户记录
            cursor.execute("DELETE FROM users WHERE username =?", (username,))
            # 删除该用户的所有留言
            cursor.execute("DELETE FROM messages WHERE username =?", (username,))
            conn.commit()
        # 清除会话信息
        session.pop('username', None)
        session.pop('is_admin', None)
        # 重定向到首页
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"删除账号时出错: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': '删除账号时发生错误，请稍后重试'}), 500

# 管理员面板
@app.route('/admin_panel')
@login_required
def admin_panel():
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限访问该页面'}), 403
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        c.execute("SELECT * FROM messages")
        messages = c.fetchall()
        return render_template('admin_panel.html', users=users, messages=messages)
    except Exception as e:
        logger.error(f"访问管理员面板时出错: {e}")
        return jsonify({'success': False, 'error': '访问管理员面板时发生错误，请稍后重试'}), 500
    finally:
        if conn:
            conn.close()

# 删除用户
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限执行该操作'}), 403
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        c = conn.cursor()
        conn.execute('BEGIN')
        c.execute("DELETE FROM users WHERE id =?", (user_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        logger.error(f"删除用户时出错: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': '删除用户时发生错误，请稍后重试'}), 500
    finally:
        if conn:
            conn.close()

# 删除留言
@app.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限执行该操作'}), 403
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        c = conn.cursor()
        conn.execute('BEGIN')
        c.execute("DELETE FROM messages WHERE id =?", (message_id,))
        conn.commit()
        return jsonify({'success': True, 'message': '留言删除成功'})
    except Exception as e:
        logger.error(f"删除留言时出错: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': '删除留言时发生错误，请稍后重试'}), 500
    finally:
        if conn:
            conn.close()

# 管理员查看所有用户信息
@app.route('/admin_view_users', methods=['GET'])
@login_required
def admin_view_users():
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限访问该页面'}), 403
    conn = None
    try:
        conn = sqlite3.connect('forum.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT username, password FROM users")
        users = c.fetchall()
        user_list = [{'username': user[0], 'password': user[1]} for user in users]
        return jsonify({'success': True, 'users': user_list})
    except Exception as e:
        logger.error(f"查看所有用户信息时出错: {e}")
        return jsonify({'success': False, 'error': '查看用户信息时发生错误，请稍后重试'}), 500
    finally:
        if conn:
            conn.close()

# 管理员管理练习题页面
@app.route('/admin_manage_questions', methods=['GET'])
@login_required
def admin_manage_questions():
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限访问该页面'}), 403
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type, question, options, answer, explanation FROM questions ORDER BY id')
            questions = cursor.fetchall()
    except Exception as e:
        logger.error(f"获取题目数据时出错: {e}")
        questions = []
    return render_template('admin_manage_questions.html', questions=questions)

# 添加练习题
@app.route('/add_question', methods=['POST'])
@login_required
def add_question():
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限执行该操作'}), 403
    try:
        question_type = request.form.get('type')
        question_text = request.form.get('question')
        option_A = request.form.get('option_A')
        option_B = request.form.get('option_B')
        option_C = request.form.get('option_C')
        option_D = request.form.get('option_D')
        answer = request.form.get('answer')
        explanation = request.form.get('explanation')

        # 输入验证，确保答案是选项之一
        options = [option_A, option_B, option_C, option_D]
        if answer not in options:
            return jsonify({'success': False, 'error': '正确答案必须是输入的选项之一'}), 400

        options_str = ','.join(options)

        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO questions (type, question, options, answer, explanation)
                VALUES (?,?,?,?,?)
            ''', (question_type, question_text, options_str, answer, explanation))

        return redirect(url_for('admin_manage_questions'))
    except Exception as e:
        logger.error(f"添加题目时出错: {e}")
        return jsonify({'success': False, 'error': '添加题目时发生错误，请稍后重试'}), 500

# 删除练习题
@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限执行该操作'}), 403
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM questions WHERE id =?', (question_id,))
        return redirect(url_for('admin_manage_questions'))
    except Exception as e:
        logger.error(f"删除题目时出错: {e}")
        return jsonify({'success': False, 'error': '删除题目时发生错误，请稍后重试'}), 500

# 编辑练习题页面
@app.route('/edit_question/<int:question_id>', methods=['GET'])
@login_required
def edit_question_page(question_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限访问该页面'}), 403
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, type, question, options, answer, explanation FROM questions WHERE id =?', (question_id,))
            question = cursor.fetchone()
        if question:
            question_dict = {
                "id": question[0],
                "type": question[1],
                "question": question[2],
                "options": question[3],
                "answer": question[4],
                "explanation": question[5]
            }
            return render_template('edit_question.html', question=question_dict)
        else:
            return jsonify({'success': False, 'error': '未找到该题目'}), 404
    except Exception as e:
        logger.error(f"获取题目数据时出错: {e}")
        return jsonify({'success': False, 'error': '获取题目数据时发生错误，请稍后重试'}), 500

# 保存编辑后的练习题
@app.route('/save_question/<int:question_id>', methods=['POST'])
@login_required
def save_question(question_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'success': False, 'error': '您没有权限执行该操作'}), 403
    try:
        question_type = request.form.get('type')
        question_text = request.form.get('question')
        option_A = request.form.get('option_A')
        option_B = request.form.get('option_B')
        option_C = request.form.get('option_C')
        option_D = request.form.get('option_D')
        answer = request.form.get('answer')
        explanation = request.form.get('explanation')

        # 输入验证，确保答案是选项之一
        options = [option_A, option_B, option_C, option_D]
        if answer not in options:
            return jsonify({'success': False, 'error': '正确答案必须是输入的选项之一'}), 400

        options_str = ','.join(options)

        with database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE questions
                SET type =?, question =?, options =?, answer =?, explanation =?
                WHERE id =?
            ''', (question_type, question_text, options_str, answer, explanation, question_id))
        return redirect(url_for('admin_manage_questions'))
    except Exception as e:
        logger.error(f"保存题目时出错: {e}")
        return jsonify({'success': False, 'error': '保存题目时发生错误，请稍后重试'}), 500

# 账户管理页面
@app.route('/account_management', methods=['GET', 'POST'])
@login_required
def account_management():
    if request.method == 'POST' and 'delete_account' in request.form:
        return delete_account()
    elif request.method == 'POST' and 'logout' in request.form:
        return logout()
    return render_template('account_management.html')

if __name__ == '__main__':
    app.run(debug=True)