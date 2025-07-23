# app.py – Flask Fuel‑Consumption‑Prediction System with FuelBot & Live Fuel API + Map Integration

import os
import sqlite3
import pickle
import numpy as np
import subprocess
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, g, jsonify, flash
)
from flask_cors import CORS
from fuel_api import fuel_api
from chatbot import ask_bot  # local chatbot logic

# ──────────────────────────
# Flask App Config
# ──────────────────────────
app = Flask(__name__, instance_relative_config=True)
CORS(app)

app.config.from_mapping(
    SECRET_KEY='your-secret-key',
    DATABASE=os.path.join(app.instance_path, 'fuel.db')
)

os.makedirs(app.instance_path, exist_ok=True)
app.register_blueprint(fuel_api)

# ──────────────────────────
# DB helpers
# ──────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mobile TEXT,
            city TEXT,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            result TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            q TEXT,
            a TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.commit()

# ──────────────────────────
# ML Model & Preprocessing
# ──────────────────────────
MODEL = pickle.load(open('model_assets/trained_model_lr.sav', 'rb'))
SCALER = pickle.load(open('model_assets/scaled_data.sav', 'rb'))

VEH = [
    'Two-seater','Minicompact','Compact','Subcompact','Mid-size','Full-size',
    'SUV: Small','SUV: Standard','Minivan','Station wagon: Small',
    'Station wagon: Mid-size','Pickup truck: Small','Special purpose vehicle',
    'Pickup truck: Standard'
]
TRN = ['AV','AM','M','AS','A']
FUE = ["D","E","X","Z"]

def vector(v_class, engine, cyl, trans, co2, fuel):
    out = []
    if v_class in VEH:
        out.append(VEH.index(v_class))
    if trans in TRN:
        out.append(TRN.index(trans))
    if fuel in FUE:
        out += [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]][FUE.index(fuel)]
    out += [engine, cyl, co2]
    return np.asarray(out).reshape(1, -1)

# ──────────────────────────
# Auth Helpers
# ──────────────────────────
def logged_in():
    return 'user_id' in session

def get_user():
    if logged_in():
        return get_db().execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return None

# ──────────────────────────
# Routes
# ──────────────────────────
@app.route('/')
def index():
    session.clear()
    return redirect('/login')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if logged_in():
        return redirect('/home')

    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        row = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (u,)
        ).fetchone()
        if row and row['password'] == p:
            session.clear()
            session['user_id'] = row['id']
            return redirect('/home')
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        mobile = request.form['mobile']
        city = request.form['city']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords do not match", "warning")
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
            ).fetchone()
            if existing:
                flash("Username or email already exists", "danger")
            else:
                db.execute(
                    "INSERT INTO users (fullname, username, email, mobile, city, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (fullname, username, email, mobile, city, password)
                )
                db.commit()
                flash("Signup successful – please login", "success")
                return redirect('/login')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/home')
def home():
    if not logged_in():
        return redirect('/login')
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if not logged_in():
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/predict', methods=('GET', 'POST'))
def predict():
    if not logged_in():
        return redirect('/login')
    if request.method == 'POST':
        try:
            d = request.form
            X = SCALER.transform(vector(
                d['vehicle'],
                int(d['engine']),
                int(d['cyl']),
                d['trans'],
                int(d['co2']),
                d['fuel']
            ))
            y = MODEL.predict(X)[0]
            res = f"The Fuel Consumption L/100 km is {y:.2f}"
            db = get_db()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute(
                "INSERT INTO predictions(user_id, result, ts) VALUES (?, ?, ?)",
                (session['user_id'], res, timestamp)
            )
            db.commit()
            subprocess.call(["python", "generate_analysis.py"])
            return render_template("predict.html", result=res)
        except Exception as e:
            print("Prediction Error:", e)
            flash("Something went wrong during prediction.", "danger")
            return render_template("predict.html")
    return render_template("predict.html")

@app.route('/history')
def history():
    if not logged_in():
        return redirect('/login')
    mode = request.args.get('mode', 'today')
    if mode == 'today':
        date_str = datetime.now().strftime('%Y-%m-%d')
    else:
        date_str = request.args.get('date')
    user_id = session['user_id']
    rows = get_db().execute(
        "SELECT * FROM predictions WHERE date(ts) = ? AND user_id = ? ORDER BY ts DESC",
        (date_str, user_id)
    ).fetchall()
    return render_template('history.html', rows=rows, mode=mode, date=date_str)

@app.route('/analysis')
def analysis():
    if not logged_in():
        return redirect('/login')
    return render_template('analysis.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/fuel-types')
def fuel_types():
    return render_template('fuel_types.html')

@app.route('/calculator', methods=('GET', 'POST'))
def calculator():
    if not logged_in():
        return redirect('/login')
    cost = None
    if request.method == 'POST':
        dist = float(request.form['dist'])
        eff = float(request.form['eff'])
        price = float(request.form['price'])
        if eff > 0:
            cost = (dist / eff) * price
    return render_template('calculator.html', cost=cost)

@app.route('/chatbot')
def chatbot():
    if not logged_in():
        return redirect('/login')
    return render_template('chatbot.html')

@app.route('/chatbot-response', methods=['POST'])
def chatbot_response():
    if not logged_in():
        return jsonify({"response": "Please login first.", "suggestions": []})
    data = request.get_json()
    user_input = data.get("message", "")
    reply, suggestions = ask_bot(user_input)
    db = get_db()
    db.execute("INSERT INTO chats(user_id, q, a) VALUES (?, ?, ?)", (session['user_id'], user_input, reply))
    db.commit()
    return jsonify({"response": reply, "suggestions": suggestions})

@app.route('/suggest', methods=['POST'])
def suggest():
    data = request.get_json()
    query = data.get("query", "").lower()
    all_questions = [
        "How to improve fuel efficiency?",
        "What is the best car for mileage?",
        "Tips to reduce fuel usage",
        "How often should I service my vehicle?",
        "How are you?",
        "What is fuel injection?",
        "How to save petrol?",
        "How do I check engine health?"
    ]
    suggestions = [q for q in all_questions if query in q.lower()]
    return jsonify({"suggestions": suggestions[:5]})

@app.route('/fuel-live')
def fuel_live():
    return render_template("fuel_live.html")

@app.route('/scan-text', methods=['GET', 'POST'])
def scan_text():
    content = None
    if request.method == 'POST':
        file = request.files.get('textfile')
        if file and file.filename.endswith('.txt'):
            content = file.read().decode('utf-8', errors='ignore')
        else:
            flash("Please upload a valid .txt file", "warning")
    return render_template('scan_text.html', content=content)

@app.route('/map')
def map():
    if not logged_in():
        return redirect('/login')
    return render_template("map.html")

# ──────────────────────────
# Main Entry
# ──────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
