# app.py — 최소 운영 버전 (Chrome 전용, 디버그 비컨 라우트 없음, /report 제출 즉시 관리자 세션으로 방문)

import os
import hashlib
import secrets
import sqlite3
import time
from urllib.parse import urljoin
from flask import Flask, render_template, request, redirect, url_for, session, g, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "devkey")

# ---------------------- 환경설정 ----------------------
DATABASE     = os.environ.get("DB_PATH", "db.sqlite")
BASE_URL     = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
ADMIN_USER   = os.environ.get("BOT_ADMIN_USER", "administrator")
ADMIN_PASS   = os.environ.get("BOT_ADMIN_PASS", "adminpass")

# Chrome 전용
CHROMEDRIVER = os.environ.get("CHROMEDRIVER", "/opt/homebrew/bin/chromedriver")
HEADLESS     = os.environ.get("HEADLESS", "1")
#디버그 전용 
# ---- 추가: LEAK_URL 전역(끝에 / 제거) ----
LEAK_URL = os.environ.get("LEAK_URL", "https://0399039bc5fb.ngrok-free.app").rstrip("/")
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

@app.before_request
def log_session_info():
    if "uid" in session:
        print(f"[DEBUG] current user={session.get('username')} uid={session.get('uid')}")

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
        if is_admin_session():
            ticket = db.execute(
                "SELECT id, uid, seat_code, ticket_color FROM tickets_test WHERE id=?",
                (tid,)
            ).fetchone()
        else:
            ticket = db.execute(
                "SELECT id, uid, seat_code, ticket_color FROM tickets_test WHERE id=? AND uid=?",
                (tid, session["uid"])
            ).fetchone()
    if not ticket:
        ticket = db.execute(
            "SELECT id, uid, seat_code, ticket_color FROM tickets_test WHERE uid=? ORDER BY id DESC LIMIT 1",
            (session["uid"],)
        ).fetchone()

    user = {"username": session.get("username"), "token": session.get("token")}
    return render_template("mypage.html", user=user, ticket=ticket)

@app.route("/list")
def list_page():
    if "uid" not in session or not is_admin_session():
        return "STAFF ONLY!!!!", 403
    db = get_db()
    tickets = db.execute("SELECT * FROM tickets_test ORDER BY id DESC").fetchall()
    return render_template("list.html", tickets=tickets)

# ===== /report : 제출 즉시 관리자 세션으로 방문 =====
@app.route("/report", methods=["GET","POST"])
def report():
    if request.method == "POST":
        path = (request.form.get("path") or "").strip()
        if not path:
            return render_template("report.html", msg="fail: empty path")
        if not path.startswith("/mypage"):
            return render_template("report.html", msg="fail: only /mypage* allowed")
        if path.startswith("/"):
            path = path[1:]
        target_url = urljoin(BASE_URL + "/", path)
        ok = check_url(target_url)
        return render_template("report.html", msg=("success" if ok else "fail"))
    return render_template("report.html")


def check_url(url: str) -> bool:
    import time
    from urllib.parse import urljoin as _join
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service as ChromeService

    
    opts = webdriver.ChromeOptions()
    if HEADLESS != "0":
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")

    # 필요시 정책 완화 플래그
    opts.add_argument("--disable-web-security")
    opts.add_argument("--allow-running-insecure-content")
    opts.add_argument("--allow-insecure-localhost")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure,ImprovedCookieControls,OpaqueResponseBlocking,ORB,ORBv2")
    opts.add_argument("--disable-popup-blocking")

    # prefs (혼합 스크립트 허용 등)
    opts.add_experimental_option("prefs", {
        "profile.default_content_setting_values.images": 1,
        "profile.managed_default_content_settings.mixed_script": 1,
        "profile.content_settings.exceptions.mixed_script.*.setting": 1,
        "download.prompt_for_download": False,
    })
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_argument("--disable-blink-features=AutomationControlled")

    # ✅ Selenium Manager 자동 사용 (경로 지정 안함)
    service = ChromeService()
    d = webdriver.Chrome(service=service, options=opts)
    d.set_page_load_timeout(20)

    try:
        # 1) 관리자 로그인
        d.get(_join(BASE_URL, "/login"))
        d.find_element(By.NAME, "username").send_keys(ADMIN_USER)
        d.find_element(By.NAME, "password").send_keys(ADMIN_PASS)
        d.find_element(By.CSS_SELECTOR, "form button, form input[type=submit]").click()
        time.sleep(0.6)

        # 2) 대상 페이지 방문
        if not (url.startswith("http://") or url.startswith("https://")):
            url = _join(BASE_URL + "/", url.lstrip("/"))
        print(f"[DEBUG] BOT visiting {url}")
        d.get(url)
        d.execute_script("document.body.offsetHeight; window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        leak_url = LEAK_URL                  # 전역 읽기만 (할당 X)
        beacon_base = f"{leak_url}/leak"
        ts = int(time.time())
        d.execute_script(f"""
          (function(){{
            try {{
              fetch("{beacon_base}?src=bot&via=js&ts={ts}", {{
                mode:"no-cors", cache:"no-store", keepalive:true
              }}).catch(()=>{{}});
              var i=new Image();
              i.src="{beacon_base}?src=bot&via=img&ts={ts}&r="+Math.random();
              try {{ window.open("{beacon_base}?via=navigate&ts={ts}", "_blank"); }} catch(e) {{}}
              if (navigator.sendBeacon) navigator.sendBeacon("{beacon_base}?src=bot&via=beacon&ts={ts}");
            }} catch(e) {{}}
          }})();
        """)
        print("[DEBUG] injected JS beacons to:", beacon_base)

        return True

    except Exception as e:
        print("[ERROR]", e)
        return False
    finally:
        try: d.quit()
        except: pass



# ---------------------- Entrypoint ----------------------
if __name__ == "__main__":
    with app.app_context():
        init_db()
        # 관리자 계정 보장
        db = get_db()
        u = db.execute("SELECT 1 FROM users WHERE username=?", (ADMIN_USER,)).fetchone()
        if not u:
            token  = secrets.token_hex(16)
            hashed = hashlib.sha256(ADMIN_PASS.encode()).hexdigest()
            db.execute("INSERT INTO users(username,password,token) VALUES(?,?,?)",
                       (ADMIN_USER, hashed, token))
            db.commit()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
