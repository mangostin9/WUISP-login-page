from flask import Flask, render_template, request, redirect, url_for, flash, make_response # [추가됨] 쿠키 설정을 위해 make_response 추가
# JWT 확장 라이브러리 임포트
from flask_jwt_extended import *
import sqlite3

application = Flask(import_name = __name__)

# 1. JWT 설정 (매우 중요!)
application.config.update(
    DEBUG = True,
    
    # [추가됨] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # flash() 함수를 사용하려면 Flask 기본 SECRET_KEY가 필요합니다!
    SECRET_KEY = "RANDOM_SECRET_KEY",
    # [추가됨] ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    JWT_SECRET_KEY = "I'M SECRET KEY",
    
    # HTML 웹사이트에서 JWT를 쓰려면 '쿠키'에 담아야 합니다.
    JWT_TOKEN_LOCATION = ["cookies"], 
    # 보안 설정 (개발 환경이라 False로 둡니다. 배포 시엔 True 권장)
    JWT_COOKIE_SECURE = False,
    # CSRF 보호 (실습의 편의를 위해 끕니다)
    JWT_COOKIE_CSRF_PROTECT = False
)

# JWT 매니저 등록
jwt = JWTManager(application)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@application.route("/")
def home():
    return render_template("home.html")

# 회원가입 (기존 코드 유지, DB 연결 부분만 안전하게 수정)
@application.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = c.fetchone()

        if existing_user:
            flash("이미 존재하는 아이디입니다. 다른 아이디를 입력해주세요.")
            conn.close()
            return redirect(url_for("signup"))

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash("회원가입이 완료되었습니다! 로그인 해주세요.")
        return redirect(url_for("login"))

    return render_template("signup.html")

# 2. 로그인: JWT 발급 및 쿠키 저장
@application.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        # [보안 수정] SQL Injection 방지를 위해 파라미터 바인딩(?) 사용
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            # [변경됨] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
            # (기존) session["username"] = username  <-- 삭제됨
            
            # (1) 인증 성공! 토큰을 만듭니다.
            access_token = create_access_token(identity=username)
            
            # (2) 토큰을 쿠키에 담아 보내기 위해 response 객체를 만듭니다.
            resp = make_response(redirect(url_for("dashboard")))
            
            # (3) 쿠키에 JWT를 심습니다. (브라우저야, 이 토큰 잘 가지고 있어!)
            set_access_cookies(resp, access_token)
            
            return resp
            # [변경됨] ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        else:
            flash("로그인 실패: 아이디나 비밀번호를 확인하세요.")
            return redirect(url_for("login"))
            
    return render_template("login.html")

# 3. 대시보드: JWT 검사 (보안 요원 배치)
@application.route("/dashboard")
@jwt_required() # [추가됨] <--- 이 데코레이터가 없으면 아무나 들어옵니다! (보안 요원)
def dashboard():
    # [변경됨] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # (기존) if "username" in session: ... <-- 삭제됨
    
    # 토큰 안에 있는 주인 이름(identity)을 꺼냅니다.
    current_user = get_jwt_identity()
    return f"안녕하세요, {current_user}님! (JWT 인증 성공) <br><a href='/logout'>로그아웃</a>"
    # [변경됨] ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# 4. 로그아웃: 쿠키 삭제
@application.route("/logout")
def logout():
    flash("로그아웃되었습니다.")
    
    # [변경됨] ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # (기존) session.clear() <-- 삭제됨

    # 로그아웃 후 로그인 페이지로 이동할 준비
    resp = make_response(redirect(url_for("login")))
    
    # 쿠키에 있는 JWT를 삭제합니다. (출입증 폐기)
    unset_jwt_cookies(resp)
    return resp
    # [변경됨] ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

if __name__ == "__main__":
    init_db()
    application.run(debug=True)