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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    body {
        background-color: #121212;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
        margin: 0;
        padding: 20px;
    }
    
    .container {
        max-width: 900px;
        margin: 0 auto;
    }
    
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        border-bottom: 1px solid #333;
        padding-bottom: 20px;
    }
    
    h1 { margin: 0; font-size: 24px; color: #ffffff; letter-spacing: -0.5px; }
    
    .btn {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        transition: opacity 0.2s;
    }
    .btn:hover { opacity: 0.9; }
    .btn-logout { background-color: #333; color: white; text-decoration: none; }
    .btn-add { background-color: #2196F3; color: white; }
    .btn-del { background-color: #ef5350; color: white; }
    .btn-time { background-color: #424242; color: white; margin-right: 4px; }
    
    /* grid for timers */
    .timer-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
    }
    
    .timer-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .timer-name {
        font-size: 18px;
        font-weight: 600;
        color: #aaaaaa;
        margin-bottom: 10px;
    }
    
    .timer-display {
        font-size: 42px;
        font-weight: 700;
        font-variant-numeric: tabular-nums; /* prevents jitter */
        color: #ffffff;
        margin-bottom: 20px;
    }
    
    .timer-display.urgent { color: #ef5350; }
    
    .controls {
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #333;
        padding-top: 15px;
    }
    
    /* forms */
    .login-box {
        max-width: 400px;
        margin: 100px auto;
        text-align: center;
        background: #1e1e1e;
        padding: 40px;
        border-radius: 12px;
    }
    input {
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #333;
        background: #2c2c2c;
        color: white;
        width: 60%;
    }
    
    .create-form {
        background: #1e1e1e;
        padding: 20px;
        border-radius: 12px;
        margin-top: 40px;
        display: flex;
        gap: 10px;
        align-items: center;
    }
</style>
"""

# we use .replace to inject styles so we don't break python formatting
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>timer login</title>__STYLES__</head>
<body>
    <div class="login-box">
        <h1>timer system</h1>
        <br>
        <form method="post">
            <input type="text" name="code" placeholder="enter code" required autocomplete="off">
            <button type="submit" class="btn btn-add">enter</button>
        </form>
        {% if error %}<p style="color:#ef5350; margin-top:10px;">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
""".replace("__STYLES__", STYLES)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>dashboard</title>
    __STYLES__
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ role }} view</h1>
            <a href="/logout" class="btn btn-logout">logout</a>
        </div>

        <div id="grid-container" class="timer-grid">
            {% for t_id, t_data in timers.items() %}
            <div class="timer-card" id="card-{{ t_id }}">
                <div class="timer-name">{{ t_data.name }}</div>
                <div class="timer-display" id="time-{{ t_id }}">loading...</div>
                
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
                        <button class="btn btn-del">delete</button>
                    </form>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        {% if role == 'admin' %}
        <div class="create-form">
            <span style="font-weight:600">new timer:</span>
            <form action="/add_timer" method="post" style="display:flex; gap:10px; width:100%;">
                <input type="text" name="name" placeholder="activity name" required style="flex-grow:1;">
                <input type="number" name="minutes" placeholder="mins" required style="width:80px;">
                <button type="submit" class="btn btn-add">start</button>
            </form>
        </div>
        {% endif %}
    </div>

    <script>
        // this script runs in the browser
        
        function formatTime(seconds) {
            if (seconds <= 0) return "00:00:00";
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            
            // add leading zeros (e.g., 9 -> 09)
            const fmt = (val) => val.toString().padStart(2, '0');
            return `${fmt(h)}:${fmt(m)}:${fmt(s)}`;
        }

        async function syncTimers() {
            try {
                const response = await fetch('/get_timers');
                const data = await response.json();
                const serverTimers = data.timers;
                const serverTime = data.server_now;
                
                // check if we need to reload page (if timer added/deleted)
                // counting cards currently on screen
                const currentCards = document.querySelectorAll('.timer-card').length;
                if (Object.keys(serverTimers).length !== currentCards) {
                    location.reload(); 
                    return;
                }

                // update each timer
                for (const [id, timer] of Object.entries(serverTimers)) {
                    const displayElement = document.getElementById('time-' + id);
                    if (displayElement) {
                        // calculate remaining time
                        // we use serverTime to ensure sync across all devices
                        const remaining = timer.end_time - serverTime;
                        
                        displayElement.innerText = formatTime(remaining);
                        
                        if (remaining <= 0) {
                            displayElement.innerText = "TIME UP";
                            displayElement.classList.add('urgent');
                        } else if (remaining < 300) { // less than 5 mins
                            displayElement.classList.add('urgent');
                        } else {
                            displayElement.classList.remove('urgent');
                        }
                    }
                }
            } catch (error) {
                console.error("sync error", error);
            }
        }

        // run sync every 1 second (1000 ms)
        setInterval(syncTimers, 1000);
        
        // run immediately on load
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
            return render_template_string(HTML_LOGIN, error="invalid access code")
    return render_template_string(HTML_LOGIN)

@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('index'))
    return render_template_string(HTML_DASHBOARD, role=session['role'], timers=TIMERS)

@app.route('/get_timers')
def get_timers():
    # this endpoint sends raw json data to the javascript
    return jsonify({
        'timers': TIMERS,
        'server_now': time.time()
    })

@app.route('/add_timer', methods=['POST'])
def add_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    name = request.form.get('name')
    try:
        minutes = int(request.form.get('minutes'))
        t_id = str(uuid.uuid4())
        TIMERS[t_id] = {
            'name': name,
            'end_time': time.time() + (minutes * 60)
        }
    except:
        pass
    return redirect(url_for('dashboard'))

@app.route('/delete_timer', methods=['POST'])
def delete_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    t_id = request.form.get('id')
    if t_id in TIMERS:
        del TIMERS[t_id]
    return redirect(url_for('dashboard'))

@app.route('/update_timer', methods=['POST'])
def update_timer():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    t_id = request.form.get('id')
    action = request.form.get('action')
    if t_id in TIMERS:
        if action == 'add_5':
            TIMERS[t_id]['end_time'] += 300
        elif action == 'sub_5':
            TIMERS[t_id]['end_time'] -= 300
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
