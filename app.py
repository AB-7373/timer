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
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    :root {
        --hud-primary: #0aff0a;
        --hud-dim: #004400;
        --hud-alert: #ff3333;
        --bg-color: #050505;
        --glass: rgba(10, 255, 10, 0.05);
    }

    * { box-sizing: border-box; }

    body {
        background-color: var(--bg-color);
        color: var(--hud-primary);
        font-family: 'Share Tech Mono', monospace;
        margin: 0;
        padding: 20px;
        overflow-x: hidden;
        min-height: 100vh;
        text-transform: uppercase;
    }

    /* CRT SCANLINE EFFECT OVERLAY */
    body::after {
        content: " ";
        display: block;
        position: fixed;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 2;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        border: 1px solid var(--hud-dim);
        padding: 20px;
        position: relative;
    }

    /* CORNER MARKERS */
    .container::before {
        content: "";
        position: absolute;
        top: -1px; left: -1px;
        width: 20px; height: 20px;
        border-top: 2px solid var(--hud-primary);
        border-left: 2px solid var(--hud-primary);
    }
    .container::after {
        content: "";
        position: absolute;
        bottom: -1px; right: -1px;
        width: 20px; height: 20px;
        border-bottom: 2px solid var(--hud-primary);
        border-right: 2px solid var(--hud-primary);
    }

    /* HEADER */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid var(--hud-dim);
        padding-bottom: 15px;
        margin-bottom: 30px;
    }

    h1 {
        margin: 0;
        font-size: 24px;
        letter-spacing: 4px;
        text-shadow: 0 0 10px var(--hud-primary);
    }

    .status-badge {
        font-size: 12px;
        background: var(--hud-dim);
        padding: 5px 10px;
        letter-spacing: 2px;
    }

    /* INPUTS & FORMS */
    input {
        background: transparent;
        border: 1px solid var(--hud-dim);
        color: var(--hud-primary);
        padding: 15px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 18px;
        outline: none;
        width: 100%;
        transition: 0.3s;
    }
    input:focus {
        border-color: var(--hud-primary);
        box-shadow: 0 0 15px var(--hud-dim);
        background: var(--glass);
    }

    /* TACTICAL BUTTONS */
    .btn {
        background: transparent;
        border: 1px solid var(--hud-primary);
        color: var(--hud-primary);
        padding: 10px 20px;
        cursor: pointer;
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: 0.2s;
        /* Angled corners */
        clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    }
    .btn:hover {
        background: var(--hud-primary);
        color: #000;
        box-shadow: 0 0 20px var(--hud-primary);
    }
    
    .btn-del {
        border-color: var(--hud-alert);
        color: var(--hud-alert);
    }
    .btn-del:hover {
        background: var(--hud-alert);
        color: #000;
        box-shadow: 0 0 20px var(--hud-alert);
    }

    .btn-time {
        font-size: 12px;
        padding: 5px 10px;
        margin-right: 5px;
    }

    /* TIMER GRID */
    .timer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 30px;
    }

    .timer-card {
        border: 1px solid var(--hud-dim);
        background: rgba(0,20,0,0.3);
        padding: 20px;
        position: relative;
    }
    
    /* Technical markings on card */
    .timer-card::before {
        content: "SYS.MDL";
        position: absolute;
        top: 5px; right: 5px;
        font-size: 8px;
        color: var(--hud-dim);
    }

    .timer-name {
        font-size: 14px;
        color: var(--hud-primary);
        border-bottom: 1px solid var(--hud-dim);
        padding-bottom: 5px;
        margin-bottom: 15px;
    }

    .timer-display {
        font-size: 48px;
        letter-spacing: 2px;
        margin-bottom: 20px;
        text-align: center;
        background: rgba(0,0,0,0.5);
        border: 1px solid var(--hud-dim);
        padding: 10px 0;
    }

    /* URGENT STATE */
    .urgent {
        color: var(--hud-alert);
        border-color: var(--hud-alert);
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0% { opacity: 1; text-shadow: 0 0 10px red; }
        50% { opacity: 0.5; text-shadow: none; }
        100% { opacity: 1; text-shadow: 0 0 10px red; }
    }

    /* LOGIN SCREEN SPECIFIC */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    .login-box {
        border: 2px solid var(--hud-primary);
        padding: 40px;
        width: 400px;
        text-align: center;
        background: rgba(0,0,0,0.8);
        box-shadow: 0 0 30px var(--hud-dim);
        clip-path: polygon(20px 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%, 0 20px);
    }
    
    .create-form {
        margin-top: 40px;
        border-top: 1px dashed var(--hud-dim);
        padding-top: 20px;
        display: flex;
        gap: 10px;
    }

</style>
"""

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>SECURE ACCESS</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    __STYLES__
</head>
<body>
    <div class="login-wrapper">
        <div class="login-box">
            <h1 style="margin-bottom:30px;">// SYSTEM LOCKED</h1>
            <form method="post">
                <p style="text-align:left; font-size:12px; margin-bottom:5px;">ENTER AUTH CODE:</p>
                <input type="text" name="code" required autocomplete="off" autofocus>
                <br><br><br>
                <button type="submit" class="btn" style="width:100%">INITIATE HANDSHAKE</button>
            </form>
            {% if error %}
                <p style="color:var(--hud-alert); margin-top:20px;">>> ACCESS DENIED <<</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
""".replace("__STYLES__", STYLES)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>TACTICAL DASHBOARD</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    __STYLES__
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>// COMMAND UNIT: {{ role }}</h1>
                <span style="font-size:10px; color:#666;">SYS.VER.2.0.4 // NET.SECURE</span>
            </div>
            <div>
                <span class="status-badge">ONLINE</span>
                <a href="/logout" class="btn" style="border:none; font-size:12px;">[ ABORT ]</a>
            </div>
        </div>

        <div id="grid-container" class="timer-grid">
            {% for t_id, t_data in timers.items() %}
            <div class="timer-card" id="card-{{ t_id }}">
                <div class="timer-name">Op: {{ t_data.name }}</div>
                <div class="timer-display" id="time-{{ t_id }}">--:--:--</div>
                
                {% if role == 'admin' %}
                <div class="controls" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <form action="/update_timer" method="post" style="display:inline">
                            <input type="hidden" name="id" value="{{ t_id }}">
                            <button name="action" value="add_5" class="btn btn-time">[ +5 ]</button>
                            <button name="action" value="sub_5" class="btn btn-time">[ -5 ]</button>
                        </form>
                    </div>
                    <form action="/delete_timer" method="post">
                        <input type="hidden" name="id" value="{{ t_id }}">
                        <button class="btn btn-del" style="font-size:12px; padding: 5px 10px;">PURGE</button>
                    </form>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        {% if role == 'admin' %}
        <div class="create-form">
            <form action="/add_timer" method="post" style="display:flex; gap:10px; width:100%;">
                <input type="text" name="name" placeholder="OPERATION NAME" required style="flex-grow:1;">
                <input type="number" name="minutes" placeholder="MIN" required style="width:80px;">
                <button type="submit" class="btn">[ EXECUTE ]</button>
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
                            displayElement.innerText = "TERMINATED";
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
            return render_template_string(HTML_LOGIN, error="INVALID")
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
