from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import time
import uuid

app = Flask(__name__)
app.secret_key = 'secure_key_random'

# database
TIMERS = {}

# passwords
ADMIN_CODE = "admin123"
STUDENT_CODE = "student123"

# ---------------------------------------------------------
# css and html templates
# ---------------------------------------------------------

STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600;800&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --neon-blue: #00f3ff;
        --neon-purple: #bc13fe;
        --neon-red: #ff0055;
        --text-main: #ffffff;
    }

    body {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: var(--text-main);
        font-family: 'Outfit', sans-serif;
        margin: 0;
        min-height: 100vh;
        padding: 40px 20px;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .container {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    /* Header Styles */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 50px;
        padding: 20px;
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid var(--glass-border);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    h1 { 
        margin: 0; 
        font-size: 28px; 
        font-weight: 800; 
        background: linear-gradient(to right, var(--neon-blue), var(--neon-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: lowercase;
        letter-spacing: -1px;
    }

    /* Buttons */
    .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 50px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .btn-logout { background: transparent; border: 1px solid rgba(255,255,255,0.3); color: white; }
    .btn-logout:hover { background: white; color: black; }
    
    .btn-add { 
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple)); 
        color: white; 
        box-shadow: 0 0 15px rgba(188, 19, 254, 0.3);
    }
    .btn-add:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(188, 19, 254, 0.5); }
    
    .btn-del { background: rgba(255, 0, 85, 0.2); color: var(--neon-red); border: 1px solid var(--neon-red); }
    .btn-del:hover { background: var(--neon-red); color: white; }
    
    .btn-time { 
        background: rgba(255,255,255,0.1); 
        color: white; 
        margin-right: 5px; 
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 12px;
    }
    .btn-time:hover { background: rgba(255,255,255,0.3); }

    /* Timer Grid */
    .timer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 30px;
    }
    
    .timer-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .timer-card:hover { transform: translateY(-5px); }
    
    .timer-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
    }

    .timer-name {
        font-size: 16px;
        font-weight: 300;
        color: rgba(255,255,255,0.7);
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .timer-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 56px;
        font-weight: 500;
        color: white;
        text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
        margin-bottom: 25px;
        transition: color 0.3s;
    }
    
    /* Urgent State */
    .timer-display.urgent {
        color: var(--neon-red);
        text-shadow: 0 0 20px rgba(255, 0, 85, 0.6);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; text-shadow: 0 0 30px rgba(255, 0, 85, 0.9); }
        100% { opacity: 1; }
    }
    
    .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 20px;
    }
    
    /* Login & Forms */
    .login-box {
        width: 100%;
        max-width: 400px;
        margin: 15vh auto;
        padding: 50px;
        background: rgba(0,0,0,0.3);
        backdrop-filter: blur(20px);
        border-radius: 30px;
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
    }
    
    input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 15px;
        border-radius: 12px;
        color: white;
        width: 60%;
        font-family: 'Outfit', sans-serif;
        outline: none;
        transition: border 0.3s;
    }
    
    input:focus { border-color: var(--neon-blue); }
    
    .create-form {
        margin-top: 50px;
        padding: 30px;
        background: var(--glass-bg);
        border-radius: 20px;
        border: 1px dashed rgba(255,255,255,0.2);
        display: flex;
        gap: 15px;
        align-items: center;
        justify-content: center;
    }
</style>
"""

# HTML TEMPLATES (Injected with styles)
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>ACCESS // TIMER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    __STYLES__
</head>
<body>
    <div class="login-box">
        <h1>system access</h1>
        <br><br>
        <form method="post">
            <input type="text" name="code" placeholder="Enter Access Code" required autocomplete="off">
            <br><br>
            <button type="submit" class="btn btn-add">INITIALIZE</button>
        </form>
        {% if error %}
            <p style="color:var(--neon-red); margin-top:20px; font-weight:600;">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
""".replace("__STYLES__", STYLES)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>DASHBOARD // TIMER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    __STYLES__
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ role }} console</h1>
            <a href="/logout" class="btn btn-logout">DISCONNECT</a>
        </div>

        <div id="grid-container" class="timer-grid">
            {% for t_id, t_data in timers.items() %}
            <div class="timer-card" id="card-{{ t_id }}">
                <div class="timer-name">{{ t_data.name }}</div>
                <div class="timer-display" id="time-{{ t_id }}">...</div>
                
                {% if role == 'admin' %}
                <div class="controls">
                    <div>
                        <form action="/update_timer" method="post" style="display:inline">
                            <input type="hidden" name="id" value="{{ t_id }}">
                            <button name="action" value="add_5" class="btn btn-time">+5m</button>
                            <button name="action" value="sub_5" class="btn btn-time">-5m</button>
                        </form>
                    </div>
                    <form action="/delete_timer" method="post">
                        <input type="hidden" name="id" value="{{ t_id }}">
                        <button class="btn btn-del">x</button>
                    </form>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        {% if role == 'admin' %}
        <div class="create-form">
            <form action="/add_timer" method="post" style="display:flex; gap:10px; width:100%; justify-content:center;">
                <input type="text" name="name" placeholder="Timer Name" required style="flex-grow:1; max-width:300px;">
                <input type="number" name="minutes" placeholder="Mins" required style="width:80px;">
                <button type="submit" class="btn btn-add">CREATE TIMER</button>
            </form>
        </div>
        {% endif %}
    </div>

    <script>
        function formatTime(seconds) {
            if (seconds <= 0) return "00:00:00";
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            const fmt = (val) => val.toString().padStart(2, '0');
            return `${fmt(h)}:${fmt(m)}:${fmt(s)}`;
        }

        async function syncTimers() {
            try {
                const response = await fetch('/get_timers');
                const data = await response.json();
                const serverTimers = data.timers;
                const serverTime = data.server_now;
                
                // Reload if count changes
                const currentCards = document.querySelectorAll('.timer-card').length;
                if (Object.keys(serverTimers).length !== currentCards) {
                    location.reload(); 
                    return;
                }

                for (const [id, timer] of Object.entries(serverTimers)) {
                    const displayElement = document.getElementById('time-' + id);
                    if (displayElement) {
                        const remaining = timer.end_time - serverTime;
                        displayElement.innerText = formatTime(remaining);
                        
                        if (remaining <= 0) {
                            displayElement.innerText = "00:00:00";
                            displayElement.classList.add('urgent');
                        } else if (remaining < 300) { 
                            displayElement.classList.add('urgent');
                        } else {
                            displayElement.classList.remove('urgent');
                        }
                    }
                }
            } catch (error) { console.error(error); }
        }

        setInterval(syncTimers, 1000);
        syncTimers();
    </script>
</body>
</html>
""".replace("__STYLES__", STYLES)

# ---------------------------------------------------------
# routes
# ---------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form.get('code')
        if code == ADMIN_CODE:
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
        elif code == STUDENT_CODE:
            session['role'] = 'student'
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(HTML_LOGIN, error="INVALID ACCESS CODE")
    return render_template_string(HTML_LOGIN)

@app.route('/dashboard')
def dashboard():
    if 'role' not in session: return redirect(url_for('index'))
    return render_template_string(HTML_DASHBOARD, role=session['role'], timers=TIMERS)

@app.route('/get_timers')
def get_timers():
    return jsonify({'timers': TIMERS, 'server_now': time.time()})

@app.route('/add_timer', methods=['POST'])
def add_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    name = request.form.get('name')
    try:
        minutes = int(request.form.get('minutes'))
        t_id = str(uuid.uuid4())
        TIMERS[t_id] = {'name': name, 'end_time': time.time() + (minutes * 60)}
    except: pass
    return redirect(url_for('dashboard'))

@app.route('/delete_timer', methods=['POST'])
def delete_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    t_id = request.form.get('id')
    if t_id in TIMERS: del TIMERS[t_id]
    return redirect(url_for('dashboard'))

@app.route('/update_timer', methods=['POST'])
def update_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    t_id = request.form.get('id')
    action = request.form.get('action')
    if t_id in TIMERS:
        if action == 'add_5': TIMERS[t_id]['end_time'] += 300
        elif action == 'sub_5': TIMERS[t_id]['end_time'] -= 300
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
