#inputApitoken 탈취 후 LFI 
import os
import hashlib
import secrets
import sqlite3
import time
from urllib.parse import urljoin
from flask import Flask, render_template, request, redirect, url_for, session, g, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "devkey")

try:
    FLAG = open('./flag.txt', 'r').read()
except:
    FLAG = '[**FLAG**]'

app.secret_key = FLAG
# ---------------------- 환경설정 ----------------------
DATABASE     = os.environ.get("DB_PATH", "db.sqlite")
BASE_URL     = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
ADMIN_USER   = os.environ.get("BOT_ADMIN_USER", "administrator")
ADMIN_PASS   = os.environ.get("BOT_ADMIN_PASS", "adminpass")
WAIT_SEC     = float(os.environ.get("BOT_WAIT_SEC", "5.0"))

# ---------------------- DB ----------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            token   TEXT
        );
        CREATE TABLE IF NOT EXISTS tickets_test(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            seat_code TEXT,
            ticket_color TEXT
        );
    """)
    db.commit()
    
def is_admin_session():
    return session.get("username") == ADMIN_USER

# ---------------------- Routes ----------------------
@app.after_request
def add_header(response):
   csp_policy =[
        "default-src 'none'",
       "script-src 'none'",
       "style-src 'self' 'unsafe-inline'"
   ]
   response.headers['Content-Security-Policy'] = "; ".join(csp_policy)
   return response

@app.route("/setup")
def setup():
    init_db()
    db = get_db()
    row = db.execute("SELECT 1 FROM users WHERE username=?", (ADMIN_USER,)).fetchone()
    if not row:
        token  = secrets.token_hex(16)
        hashed = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
        db.execute("INSERT INTO users(username,password,token) VALUES(?,?,?)",
                   (ADMIN_USER, hashed, token))
        db.commit()
    return f"setup ok (admin={ADMIN_USER})"

@app.route("/")
def index():
    db = get_db()
    reserved = [r["seat_code"] for r in db.execute("SELECT seat_code FROM tickets_test").fetchall()]
    selected = request.args.get("selected")
    msg      = request.args.get("msg")
    return render_template("index.html",
                           reserved=reserved,
                           selected=selected,
                           logged_in=("uid" in session),
                           msg=msg)


@app.route("/buy", methods=["POST"])
def buy():
    if "uid" not in session:
        return redirect(url_for("login"))
    seat_code    = request.form.get("seat_code","").strip()
    ticket_color = request.form.get("ticket_color","").strip()
    if not seat_code:
        flash("좌석을 선택하세요.")
        return redirect(url_for("index"))
    db = get_db()
    db.execute("INSERT INTO tickets_test(uid, seat_code, ticket_color) VALUES(?,?,?)",
               (session["uid"], seat_code, ticket_color))
    db.commit()
    flash("좌석 예약 성공!")
    return redirect(url_for("index", selected=seat_code))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","")
        password = request.form.get("password","")
        hashed   = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                          (username, hashed)).fetchone()
        if user:
            session["uid"]      = user["id"]
            session["username"] = user["username"]
            session["token"]    = user["token"]
            return redirect(url_for("mypage"))
        return render_template("login.html", error="Login failed")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        if not username or not password:
            return render_template("register.html", error="Both fields required")
        db = get_db()
        try:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            token  = secrets.token_hex(16)
            db.execute("INSERT INTO users(username,password,token) VALUES(?,?,?)",
                       (username, hashed, token))
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already taken")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/mypage")
def mypage():
    if "uid" not in session:
        return redirect(url_for("login"))
    db  = get_db()
    tid = request.args.get("ticket_id", type=int)

    ticket = None
    if tid:
        query = "SELECT id, uid, seat_code, ticket_color FROM tickets_test WHERE id=?"
        params = (tid,)
        if not is_admin_session():
            query += " AND uid=?"
            params = (tid, session["uid"])
        ticket = db.execute(query, params).fetchone()
        
    if not ticket:
        ticket = db.execute(
            "SELECT id, uid, seat_code, ticket_color FROM tickets_test WHERE uid=? ORDER BY id DESC LIMIT 1",
            (session["uid"],)
        ).fetchone()

    user = {"username": session.get("username"), "token": session.get("token")}
    return render_template("mypage.html", user=user, ticket=ticket, is_admin_session=is_admin_session)

@app.route("/list")
def list_page():
    if not is_admin_session():
        return "STAFF ONLY!!!!", 403
    db = get_db()
    tickets = db.execute("SELECT * FROM tickets_test ORDER BY id DESC").fetchall()
    return render_template("list.html", tickets=tickets)

@app.route("/report", methods=["GET","POST"])
def report():
    if request.method == "POST":
        path = (request.form.get("path") or "").strip()
        if not path.startswith("/mypage"):
            return render_template("report.html", msg="fail: only /mypage* allowed")

        target_url = urljoin(BASE_URL, path.lstrip("/"))
        verdict = run_admin_visit(target_url)
        return render_template("report.html", msg=verdict)
    return render_template("report.html")

# ---------------------- 관리자 방문 함수 ----------------------
def run_admin_visit(url: str):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException, WebDriverException

    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--disable-web-security")
    opts.add_argument('--incognito')
    opts.add_argument('--disable-cache')
    opts.add_argument('--disk-cache-size=0')

    d = webdriver.Chrome(service=ChromeService(), options=opts)
    d.set_page_load_timeout(5)

    try:
        d.get(urljoin(BASE_URL, "/login"))
        d.find_element(By.NAME, "username").send_keys(ADMIN_USER)
        d.find_element(By.NAME, "password").send_keys(ADMIN_PASS)
        d.find_element(By.CSS_SELECTOR, "form button, form input[type=submit]").click()
        time.sleep(0.5)

        start_time = time.time()
        d.get(url)
        end_time = time.time()
        duration = end_time - start_time
        
        return f"[티켓 검수 시스템] 티켓 검수가 완료되었습니다. (소요 시간: {duration:.2f}초)"

    except TimeoutException:
        return "[티켓 검수 시스템] 경고: 페이지 응답이 지연되어 검수가 중단되었습니다. 네트워크 상태를 확인해주세요."

    except WebDriverException as e:
            return "[티켓 검수 시스템] 경고: 제출된 티켓 디자인이 과도하게 복잡하여 시스템이 멈췄습니다. 검수를 중단합니다."

    except Exception:
        return "[티켓 검수 시스템] 내부 오류가 발생하여 검수를 진행할 수 없습니다. 관리자에게 문의하세요."
        
    finally:
        try: d.quit()
        except: pass
        
if __name__ == "__main__":
    with app.app_context():
        init_db()
        db = get_db()
        u = db.execute("SELECT 1 FROM users WHERE username=?", (ADMIN_USER,)).fetchone()
        if not u:
            token  = secrets.token_hex(16)
            hashed = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
            db.execute("INSERT INTO users(username,password,token) VALUES(?,?,?)",
                       (ADMIN_USER, hashed, token))
            db.commit()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)