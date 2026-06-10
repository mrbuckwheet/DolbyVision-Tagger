import os
from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import subprocess

app = Flask(__name__)

# CONFIGURATION PATHS
CONFIG_PATH = '/app/config/config.env'
LOG_PATH = '/app/config/logs/dv_tagger.log'

def fix_file_permissions(filepath):
    try:
        puid = int(os.environ.get('PUID', 1000))
        pgid = int(os.environ.get('PGID', 1000))
        
        if os.path.exists(filepath):
            os.chown(filepath, puid, pgid)
    except Exception as e:
        print(f"Permission alignment skipped: {str(e)}", flush=True)

def read_config():
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        k, v = line.strip().split('=', 1)
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        config[k] = v
        except Exception:
            pass
    return config

def save_config(new_data):
    current_config = read_config()
    
    for k, v in new_data.items():
        clean_val = str(v).replace('"', '').replace("'", "").replace('`', '').replace('\n', '').replace('\r', '')
        current_config[k] = clean_val
            
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            for k, v in current_config.items():
                f.write(f'{k}="' + v + '"\n')
        fix_file_permissions(CONFIG_PATH) 
    except Exception as e:
        print(f"Error saving config: {str(e)}", flush=True)
            
    cron_sched = current_config.get('CRON_SCHEDULE', '').strip()
    cron_file = '/etc/cron.d/dv-tagger'
    if cron_sched:
        cron_rule = f"{cron_sched} root set -a && . {CONFIG_PATH} && set +a && su -p abc -c '/usr/local/bin/python /app/mrbuckwheets_dv_tagger.py' >> {LOG_PATH} 2>&1\n"
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            fix_file_permissions(os.path.dirname(LOG_PATH))
            with open(cron_file, 'w', encoding='utf-8') as f_cron:
                f_cron.write(cron_rule)
            os.chmod(cron_file, 0o644)
        except Exception as e:
            print(f"Error saving cron rule: {str(e)}", flush=True)
    else:
        if os.path.exists(cron_file):
            try:
                os.remove(cron_file)
            except Exception:
                pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dolby Vision Tagger Control Panel</title>
    <style>
        :root {
            --ui-scale: 1.0;
            --bg-main: #1a1d20;
            --bg-card: #24282c;
            --bg-input: #2f353a;
            --accent: #cc7b19;
            --accent-hover: #b36b14;
            --text-main: #e9ecef;
            --text-muted: #adb5bd;
        }

        html, body { height: 100%; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: var(--bg-main); color: var(--text-main); 
            padding: calc(1.25rem * var(--ui-scale)); font-size: calc(0.875rem * var(--ui-scale));
            display: flex; flex-direction: column; min-height: 100vh; box-sizing: border-box;
        }
        .container { 
            max-width: 1100px; width: 100%; margin: 0 auto; background: var(--bg-card); 
            padding: calc(1.5rem * var(--ui-scale)); border-radius: 8px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: flex; flex-direction: column; box-sizing: border-box;
        }
        .header-wrapper {
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;
            border-bottom: 2px solid #343a40; padding-bottom: calc(0.6rem * var(--ui-scale)); margin-bottom: calc(1.25rem * var(--ui-scale));
        }
        h1 { color: var(--accent); margin: 0; font-weight: 600; font-size: calc(1.5rem * var(--ui-scale)); }
        
        .scale-tool {
            display: flex; align-items: center; gap: 0.5rem; background: var(--bg-input); padding: 0.4rem 0.8rem; border-radius: 20px; border: 1px solid #495057; user-select: none;
        }
        .scale-tool label { font-size: calc(0.75rem * var(--ui-scale)); color: var(--text-muted); font-weight: bold; }
        .scale-tool input[type="range"] { cursor: pointer; accent-color: var(--accent); width: 90px; height: 4px; }
        .scale-val { font-size: calc(0.75rem * var(--ui-scale)); font-family: monospace; min-width: 35px; text-align: right; }

        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: calc(1rem * var(--ui-scale)); margin-bottom: 1.25rem; }
        .form-group { display: flex; flex-direction: column; justify-content: space-between; }
        label { font-weight: bold; color: var(--text-main); font-size: calc(0.85rem * var(--ui-scale)); margin-bottom: 4px; }
        .field-desc { font-size: calc(0.75rem * var(--ui-scale)); color: var(--text-muted); margin-bottom: 6px; font-style: italic; line-height: 1.3; }

        input[type="text"] { 
            padding: calc(0.6rem * var(--ui-scale)); background: var(--bg-input); border: 1px solid #495057; border-radius: 4px; 
            color: #fff; font-size: calc(0.875rem * var(--ui-scale)); width: 100%; box-sizing: border-box;
        }
        input[type="text"]:focus { border-color: var(--accent); outline: none; }
        
        .actions { 
            display: flex; align-items: center; flex-wrap: wrap; gap: 1rem; 
            margin-top: calc(1.5rem * var(--ui-scale)); border-top: 1px solid #343a40; padding-top: calc(1.25rem * var(--ui-scale)); 
        }
        button { 
            padding: calc(0.75rem * var(--ui-scale)) calc(1.25rem * var(--ui-scale)); border: none; border-radius: 4px; 
            font-weight: bold; cursor: pointer; font-size: calc(0.85rem * var(--ui-scale)); transition: background 0.2s, transform 0.1s; 
        }
        button:active { transform: scale(0.98); }
        .btn-save { background-color: var(--accent); color: white; }
        .btn-save:hover { background-color: var(--accent-hover); }
        .btn-run { background-color: #28a745; color: white; }
        .btn-run:hover { background-color: #218838; }
        
        .console-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-top: calc(2rem * var(--ui-scale)); margin-bottom: 8px; }
        .console-title { font-weight: bold; color: var(--accent); font-size: calc(1rem * var(--ui-scale)); }
        .toggle-container { display: flex; align-items: center; gap: 1rem; font-size: calc(0.8rem * var(--ui-scale)); color: var(--text-muted); user-select: none; }
        .toggle-item { display: flex; align-items: center; gap: 0.4rem; }
        .toggle-container input[type="checkbox"] { cursor: pointer; width: 14px; height: 14px; margin: 0; }
        .toggle-container label { color: var(--text-muted); font-weight: normal; font-size: calc(0.8rem * var(--ui-scale)); cursor: pointer; margin: 0; }
        .btn-clear { background-color: #495057; color: var(--text-main); padding: 4px 10px; font-size: calc(0.75rem * var(--ui-scale)); border: 1px solid #6c757d; border-radius: 4px; cursor: pointer; font-weight: normal; }
        .btn-clear:hover { background-color: #343a40; color: #fff; }
        
        pre { 
            background: #0f111a; border: 1px solid #2b2e38; padding: calc(1rem * var(--ui-scale)); border-radius: 4px; 
            height: 45vh; overflow-y: scroll; color: #39adb5; 
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: calc(0.8rem * var(--ui-scale)); line-height: 1.5; margin: 0; box-sizing: border-box;
        }
        pre.wrapped { white-space: pre-wrap; word-wrap: break-word; }
        .status-msg { margin-left: 10px; font-weight: bold; font-size: calc(0.85rem * var(--ui-scale)); color: var(--text-muted); }
        .status-msg.success { color: #28a745; }
        .status-msg.error { color: #dc3545; }

        .log-line-error { color: #e74c3c !important; font-weight: 500; }
        .log-line-success { color: #2ecc71 !important; font-weight: 500; }
        .log-line-warning { color: #f1c40f !important; font-weight: 500; }
        .log-line-trigger { color: #e67e22 !important; font-weight: 500; }
        .log-line-start { 
            color: #00d2ff !important; font-weight: bold; background: rgba(0, 210, 255, 0.08); 
            padding: 4px 8px; margin: 4px 0; border-left: 4px solid #00d2ff; display: block;
        }
        .log-line-summary { color: #9b59b6 !important; font-weight: 600; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-wrapper">
            <div>
                <h1>🎬 MrBuckwheet's Dolby Vision Tagger</h1>
                <div class="sub-header" style="margin-top: 5px;">
                    This script pairs great with MrBuckwheet's custom Kometa script. 
                    <a href="https://github.com/mrbuckwheet/Kometa-Config" target="_blank" style="color: var(--accent);">HERE</a>
                </div>
            </div>
            
            <div class="scale-tool">
                <label for="scaleSlider">ZOOM</label>
                <input type="range" id="scaleSlider" min="0.8" max="1.5" step="0.05" value="1.0" oninput="adjustUiScale(this.value)">
                <span id="scaleVal" class="scale-val">100%</span>
            </div>
        </div>
        
        <form id="configForm">
            <div class="grid">
                <div class="form-group">
                    <label>Plex Server URL</label>
                    <div class="field-desc">Enter the local IP address and port where your Plex server is running (default is http://127.0.0.1:32400).</div>
                    <input type="text" name="PLEX_SERVER_URL" value="{{ config.get('PLEX_SERVER_URL', '') }}" placeholder="e.g., http://192.168.X.X:32400">
                </div>
                <div class="form-group">
                    <label>Plex Authentication Token</label>
                    <div class="field-desc">Your unique Plex token required for API access.  <a href="https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/" target="_blank" style="color: var(--accent);">HOW TO GET TOKEN</a></div>
                    <input type="text" name="PLEX_TOKEN" value="{{ config.get('PLEX_TOKEN', '') }}" placeholder="e.g., aBcDe123FgH_45iJklMN">
                </div>
                <div class="form-group">
                    <label>Plex Target Libraries</label>
                    <div class="field-desc">Enter the names of any Movie libraries in Plex that you want the tagger to scan, separated by commas.</div>
                    <input type="text" name="PLEX_LIBRARIES" value="{{ config.get('PLEX_LIBRARIES', '') }}" placeholder="e.g., Movies, 4K Movies">
                </div>
                <div class="form-group">
                    <label>Cron Schedule</label>
                    <div class="field-desc">Standard 5-field timing for automatic runs (use., 50 6,18 * * * to pair with Mrbuckwheet's Kometa config). Leave blank to disable.</div>
                    <input type="text" name="CRON_SCHEDULE" value="{{ config.get('CRON_SCHEDULE', '') }}" placeholder="e.g., 50 6,18 * * *">
                </div>
                <div class="form-group">
                    <label>Plex Path Prefix</label>
                    <div class="field-desc">The INTERNAL directory that Plex sees for your Movies Library (this may be different than your actual directory where your Media is stored)</div>
                    <input type="text" name="PLEX_PATH_PREFIX" value="{{ config.get('PLEX_PATH_PREFIX', '') }}" placeholder="e.g., /Media/Movies">
                </div>
                <div class="form-group">
                    <label>Apply a 'Dolby Vision' tag</label>
                    <div class="field-desc">This will apply a general 'Dolby Vision' tag to any movie with Dolby Vision regardless of version or profile.</div>
                    <input type="text" name="GENERAL_LABEL" value="{{ config.get('GENERAL_LABEL', '') }}" placeholder="e.g., True">
                </div>
            </div>
            
            <div class="actions">
                <button type="button" class="btn-save" onclick="handleSave()">💾 Save Configuration</button>
                <button type="button" class="btn-run" onclick="handleRun()">🚀 Run Tagger Now</button>
                <span id="statusMessage" class="status-msg"></span>
            </div>
        </form>

        <div class="console-header">
            <div class="console-title">🖥️ Real-Time Log Output</div>
            <div class="toggle-container">
                <button type="button" class="btn-clear" onclick="handleClearLogs()">🗑️ Clear Logs</button>
                <div class="toggle-item">
                    <input type="checkbox" id="wrapToggle" onchange="toggleTextWrap(this.checked)">
                    <label for="wrapToggle">Wrap text</label>
                </div>
                <div class="toggle-item">
                    <input type="checkbox" id="refreshToggle" checked>
                    <label for="refreshToggle">Auto Refresh Logs</label>
                </div>
            </div>
        </div>
        <pre id="logConsole">Waiting for container log framework initialization sequence...</pre>
    </div>

    <script>
        document.getElementById('logConsole').textContent = "⚡ JavaScript Engine Active. Syncing pipeline stream channels...";
        let isFetchingLogs = false;

        function adjustUiScale(val) {
            document.documentElement.style.setProperty('--ui-scale', val);
            document.getElementById('scaleVal').textContent = Math.round(val * 100) + '%';
            try { localStorage.setItem('mrbw_ui_scale', val); } catch(e){}
        }

        function toggleTextWrap(isWrapped) {
            const consoleBox = document.getElementById('logConsole');
            if (isWrapped) consoleBox.classList.add('wrapped');
            else consoleBox.classList.remove('wrapped');
            try { localStorage.setItem('mrbw_log_wrap', isWrapped ? 'true' : 'false'); } catch(e){}
        }

        try {
            const savedScale = localStorage.getItem('mrbw_ui_scale');
            if (savedScale) { document.getElementById('scaleSlider').value = savedScale; adjustUiScale(savedScale); }
            const savedWrap = localStorage.getItem('mrbw_log_wrap') === 'true';
            document.getElementById('wrapToggle').checked = savedWrap;
            toggleTextWrap(savedWrap);
        } catch(e){}

        function handleSave() {
            const saveBtn = document.querySelector('.btn-save');
            
            if (!saveBtn || saveBtn.disabled) return;

            const originalText = saveCTxt = saveBtn.innerHTML;
            const originalOpacity = saveBtn.style.opacity;
            const originalCursor = saveBtn.style.cursor;

            saveBtn.disabled = true;
            saveBtn.innerHTML = "💾 Saving...";
            saveBtn.style.opacity = "0.5";
            saveBtn.style.cursor = "not-allowed";

            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
                saveBtn.style.opacity = originalOpacity;
                saveBtn.style.cursor = originalCursor;
            }, 3000);

            const form = document.getElementById('configForm');
            const data = Object.fromEntries(new FormData(form).entries());
            const statusSpan = document.getElementById('statusMessage');
            statusSpan.className = "status-msg";
            statusSpan.innerText = "Writing to save file...";

            fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(res => {
                if(res.success) {
                    statusSpan.className = "status-msg success";
                    statusSpan.innerText = "✅ Setup values saved!";
                } else {
                    statusSpan.className = "status-msg error";
                    statusSpan.innerText = "❌ Error: " + res.error;
                }
            }).catch(() => {
                statusSpan.className = "status-msg error";
                statusSpan.innerText = "❌ Network connection broken during save operation.";
            });
        }

        function handleRun() {
            const runBtn = document.querySelector('.btn-run');
            
            if (!runBtn || runBtn.disabled) return;

            const originalText = runBtn.innerHTML;
            const originalOpacity = runBtn.style.opacity;
            const originalCursor = runBtn.style.cursor;

            runBtn.disabled = true;
            runBtn.innerHTML = "⏳ Cooling down...";
            runBtn.style.opacity = "0.5";
            runBtn.style.cursor = "not-allowed";

            setTimeout(() => {
                runBtn.disabled = false;
                runBtn.innerHTML = originalText;
                runBtn.style.opacity = originalOpacity;
                runBtn.style.cursor = originalCursor;
            }, 5000);

            const statusSpan = document.getElementById('statusMessage');
            statusint_msg = "Starting manual scan...";
            statusSpan.className = "status-msg";
            statusSpan.innerText = "Starting manual scan...";

            fetch('/api/run', { method: 'POST' })
            .then(res => res.json())
            .then(res => {
                if(res.success) {
                    statusSpan.className = "status-msg success";
                    statusSpan.innerText = "🚀 Media processing triggered!";
                } else {
                    statusSpan.className = "status-msg error";
                    statusSpan.innerText = "❌ Execution failure: " + res.error;
                }
            }).catch(() => {
                statusSpan.className = "status-msg error";
                statusSpan.innerText = "❌ Network error: Unable to reach runner thread.";
            });
        }

        function handleClearLogs() {
            if (!confirm("Wipe log file?")) return;
            fetch('/api/logs/clear', { method: 'POST' })
            .then(res => res.json())
            .then(res => {
                if (res.success) document.getElementById('logConsole').textContent = "Logs cleared successfully.";
            });
        }

        function fetchLogs() {
            if (isFetchingLogs) return;
            if (!document.getElementById('refreshToggle').checked) return; 

            isFetchingLogs = true;
            const consoleBox = document.getElementById('logConsole');
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 1800);

            fetch('/api/logs?t=' + Date.now(), { signal: controller.signal })
            .then(res => {
                clearTimeout(timeoutId);
                if (!res.ok) throw new Error('HTTP ' + res.status);
                return res.text();
            })
            .then(text => {
                if (!text) return;
                const isScrolledToBottom = consoleBox.scrollHeight - consoleBox.clientHeight <= consoleBox.scrollTop + 60;
                let safeHtml = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                let lines = safeHtml.split('\\n');
                
                let processedLines = [];
                lines.forEach(line => {
                    let firstBracket = line.indexOf('[');
                    let secondBracket = -1;
                    if (firstBracket > -1) {
                        secondBracket = line.indexOf('[', firstBracket + 1);
                    }
                    if (secondBracket > -1) {
                        let part1 = line.substring(0, secondBracket).trim();
                        let part2 = line.substring(secondBracket).trim();
                        if (part1) processedLines.push(part1);
                        if (part2) processedLines.push(part2);
                    } else {
                        processedLines.push(line);
                    }
                });
                
                let colorizedLines = processedLines.map(line => {
                    if (line.includes("MrBuckwheet's Dolby Vision Tagger Run Started")) {
                        return `<span class="log-line-start">✨ ${line}</span>`;
                    }
                    if (line.includes('❌') || line.includes('⚠️')) return `<span class="log-line-error">${line}</span>`;
                    if (line.includes('✅')) return `<span class="log-line-success">${line}</span>`;
                    if (line.includes('Warning:')) return `<span class="log-line-warning">${line}</span>`;
                    if (line.includes('🚀')) return `<span class="log-line-trigger">${line}</span>`;
                    if (line.includes('📊') || line.includes('EXECUTION RUN SUMMARY') || line.includes("MrBuckwheet's Dolby Vision Tagger") || /={10,}/.test(line)) {
                        return `<span class="log-line-summary">${line}</span>`;
                    }
                    return line;
                });

                consoleBox.innerHTML = colorizedLines.join('\\n');
                if (isScrolledToBottom) consoleBox.scrollTop = consoleBox.scrollHeight;
            })
            .catch(err => {
                clearTimeout(timeoutId);
                consoleBox.innerHTML = `<span class="log-line-error">⚠️ Connection Pending: (${err.message}). Refreshing...</span>`;
            })
            .finally(() => {
                isFetchingLogs = false;
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            fetchLogs();
            setInterval(fetchLogs, 500);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, config=read_config())

@app.route('/api/save', methods=['POST'])
def api_save():
    import re  # Import regex for validation
    try:
        new_data = request.json
        
        cron_val = new_data.get('CRON_SCHEDULE', '').strip()
        
        if cron_val != "":
            fields = cron_val.split()
            
            if len(fields) != 5:
                return jsonify({
                    "success": False, 
                    "error": "Invalid Cron format. Must be exactly 5 fields (e.g., '50 6,18 * * *')."
                })
            
            cron_regex = r'^[\d\*\,\/\-]+$'
            for field in fields:
                if not re.match(cron_regex, field):
                    return jsonify({
                        "success": False, 
                        "error": f"Invalid character '{field}' detected in Cron expression."
                    })

        save_config(new_data)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"app_error": str(e), "success": False, "error": str(e)})

@app.route('/api/run', methods=['POST'])
def api_run():
    LOCK_FILE = "/tmp/dv_tagger.lock"
    
    if os.path.exists(LOCK_FILE):
        return jsonify({"success": False, "error": "A scan is already in progress. Please wait for the current run to finish."})

    try:
        current_config = read_config()
        isolated_env = os.environ.copy()
        isolated_env.update(current_config)
        
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 5 * 1024 * 1024:
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                f.write("=== Log file exceeded 5MB and was automatically cleared ===\n")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] 🚀 Manual scan execution triggered via Control Panel Web UI...\n"
        
        with open(LOG_PATH, 'a', encoding='utf-8') as f_log:
            f_log.write(log_message)
            f_log.flush()
            
            fix_file_permissions(LOG_PATH)
            
            cmd = [
                'su', '-p', 'abc', '-c', 
                f'touch {LOCK_FILE} && /usr/local/bin/python /app/mrbuckwheets_dv_tagger.py; rm -f {LOCK_FILE}'
            ]
            
            subprocess.Popen(cmd, env=isolated_env, stdout=f_log, stderr=f_log, preexec_fn=os.setsid)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logs')
def api_logs():
    if not os.path.exists(LOG_PATH):
        return "⚙️ Local system log ready... Trigger a run by pressing 'Run Tagger Now' button..."
    try:
        with open(LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            output = "".join(lines[-150:])
        if not output.strip():
            return "⚠️ Local log registry is currently empty. Trigger a run by pressing 'Run Tagger Now' button..."
        return output
    except Exception as e:
        return f"Error reading local runtime log frames: {str(e)}"

@app.route('/api/logs/clear', methods=['POST'])
def api_clear_logs():
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            f.write("=== Logs deleted by user at %s ===\n" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        fix_file_permissions(LOG_PATH)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3636, threaded=True)
