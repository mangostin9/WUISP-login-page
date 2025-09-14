from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"  # 세션 암호화 키

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

@app.route("/")
def home():
    return render_template("home.html")  # 로그인/회원가입 선택 화면


#회원가입 화면
@app.route("/signup", methods=["GET", "POST"])
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return "로그인 실패"
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return f"안녕하세요, {session['username']}님! <br><a href='/logout'>로그아웃</a>"
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()   # 세션 전체 삭제
    flash("로그아웃되었습니다.")
    return redirect(url_for("login"))




if __name__ == "__main__":
    init_db()
    app.run(debug=True)
