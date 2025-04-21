from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import uuid

app = Flask(__name__, static_url_path="/static")

idend='.mariana'
filename='/etc/marianamail/users.db'
# DB setup
def init_db():
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS emails (recipient TEXT, sender TEXT, subject TEXT, body TEXT)''')
    conn.commit()
    conn.close()

init_db()

def validate_id(id):
        if not id.endswith(idend):
                return False
        try:
                uuid.UUID(id[:-len(idend)])
                return True
        except:
                return False

@app.route('/')
def home():
    return render_template('auth.html')

@app.route('/check')
def check_user():
    username = request.args.get('username')
    if not validate_id(username):
        return "Invalid request"
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    exists = c.fetchone() is not None
    conn.close()
    return {'exists': exists}

@app.route('/login')
def login():
    username = request.args.get('username')
    if not validate_id(username):
        return "Invalid request"
    password = request.args.get('password')
    hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = c.fetchone()

    if row:
        # User exists, check password
        if row[1] == hashed:
            return redirect(url_for('inbox', username=username))
        else:
            return "Incorrect password", 403
    else:
        # Create new user
        c.execute('INSERT INTO users VALUES (?,?)', (username, hashed))
        conn.commit()
        return redirect(url_for('inbox', username=username))

@app.route('/inbox')
def inbox():
    username = request.args.get('username')
    if not validate_id(username):
        return "Invalid request"

    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT sender, subject, body FROM emails WHERE recipient = ?', (username,))
    emails = c.fetchall()
    conn.close()
    return render_template('inbox.html', emails=emails, username=username)

@app.route('/compose')
def compose():
    username = request.args.get('username')
    if not validate_id(username):
        return "Invalid request"

    to=request.args.get('to', '')

    subject=request.args.get('sub', '')
    bodyx=request.args.get('body', '')

    print(bodyx)


    return render_template('compose.html', username=username, to=to, subject=subject, bodyx=bodyx)

@app.route('/send')
def send():
    sender = request.args.get('username')
    if not validate_id(sender):
        return "Invalid request"

    recipient = request.args.get('to')
    if not validate_id(recipient):
        return "Invalid request"

    subject = request.args.get('subject')
    body = request.args.get('body')

    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('INSERT INTO emails VALUES (?, ?, ?, ?)', (recipient, sender, subject, body))
    conn.commit()
    conn.close()
    return redirect(url_for('inbox', username=sender))

if __name__=='__main__':
        app.run(host='0.0.0.0', port=5000)
