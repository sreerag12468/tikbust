"""
app.py — Flask web interface for Radikikk Downloader.
"""

import io
import zipfile
from flask import Flask, request, send_file, render_template_string, jsonify
from downloader import fetch_hd_video

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Radikikk Downloader — Free TikTok Video Downloader</title>
  <style>
    :root {
      --bg: #0d0d0d; --surface: #161616; --border: #2a2a2a;
      --accent: #fe2c55; --accent2: #25f4ee; --text: #f0f0f0;
      --muted: #888; --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg); color: var(--text);
      font-family: 'Inter', system-ui, sans-serif;
      min-height: 100vh; display: flex; flex-direction: column;
      align-items: center; justify-content: center; padding: 24px;
    }
    .logo { font-size: 2.4rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 6px; }
    .logo span:first-child { color: var(--accent); }
    .logo span:last-child  { color: var(--accent2); }
    .tagline { color: var(--muted); font-size: .9rem; margin-bottom: 28px; }

    /* tabs */
    .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
    .tab {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 8px; color: var(--muted); cursor: pointer;
      font-size: .9rem; font-weight: 600; padding: 10px 22px;
      transition: all .2s;
    }
    .tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }

    /* card */
    .card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 32px; width: 100%; max-width: 540px;
    }
    .panel { display: none; }
    .panel.active { display: block; }

    label {
      display: block; font-size: .8rem; color: var(--muted);
      text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px;
    }
    .input-row { display: flex; gap: 10px; }
    input[type="url"] {
      flex: 1; background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; color: var(--text); font-size: .95rem;
      padding: 12px 14px; outline: none; transition: border-color .2s; width: 100%;
    }
    input[type="url"]:focus { border-color: var(--accent); }
    input[type="url"]::placeholder { color: var(--muted); }

    /* multi inputs */
    .multi-inputs { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
    .link-row { display: flex; align-items: center; gap: 10px; }
    .link-num {
      color: var(--accent); font-weight: 700; font-size: .9rem;
      min-width: 20px; text-align: center;
    }
    .link-status {
      font-size: .75rem; min-width: 60px; text-align: right;
    }

    button {
      background: var(--accent); border: none; border-radius: 8px;
      color: #fff; cursor: pointer; font-size: .95rem; font-weight: 600;
      padding: 12px 20px; transition: opacity .2s, transform .1s; white-space: nowrap;
    }
    button:hover   { opacity: .88; }
    button:active  { transform: scale(.97); }
    button:disabled { opacity: .45; cursor: not-allowed; }
    .btn-full { width: 100%; margin-top: 4px; }

    #status, #multi-status {
      margin-top: 16px; font-size: .9rem; min-height: 22px; text-align: center;
    }
    .ok  { color: var(--accent2); }
    .err { color: var(--accent); }

    .progress-bar {
      height: 4px; background: var(--border); border-radius: 2px;
      margin-top: 14px; overflow: hidden; display: none;
    }
    .progress-fill {
      height: 100%; background: var(--accent2);
      border-radius: 2px; transition: width .3s;
    }

    footer { margin-top: 28px; color: var(--muted); font-size: .78rem; text-align: center; line-height: 1.6; }
  </style>
</head>
<body>

  <div class="logo"><span>Radikikk</span><span> Downloader</span></div>
  <p class="tagline">Watermark-free TikTok downloads — fast & free</p>

  <div class="tabs">
    <button class="tab active" onclick="switchTab('single', this)">Single Video</button>
    <button class="tab" onclick="switchTab('multi', this)">Bulk Download (up to 4)</button>
  </div>

  <div class="card">

    <!-- SINGLE -->
    <div class="panel active" id="panel-single">
      <label for="url-input">TikTok video link</label>
      <div class="input-row">
        <input id="url-input" type="url" placeholder="https://www.tiktok.com/@user/video/..." autocomplete="off" spellcheck="false" />
        <button id="dl-btn" onclick="startSingle()">Download</button>
      </div>
      <div id="status"></div>
    </div>

    <!-- MULTI -->
    <div class="panel" id="panel-multi">
      <label>Paste up to 4 TikTok links</label>
      <div class="multi-inputs">
        <div class="link-row">
          <span class="link-num">1</span>
          <input type="url" class="multi-url" placeholder="https://www.tiktok.com/@user/video/..." autocomplete="off" spellcheck="false" />
          <span class="link-status" id="ls-0"></span>
        </div>
        <div class="link-row">
          <span class="link-num">2</span>
          <input type="url" class="multi-url" placeholder="https://www.tiktok.com/@user/video/..." autocomplete="off" spellcheck="false" />
          <span class="link-status" id="ls-1"></span>
        </div>
        <div class="link-row">
          <span class="link-num">3</span>
          <input type="url" class="multi-url" placeholder="https://www.tiktok.com/@user/video/..." autocomplete="off" spellcheck="false" />
          <span class="link-status" id="ls-2"></span>
        </div>
        <div class="link-row">
          <span class="link-num">4</span>
          <input type="url" class="multi-url" placeholder="https://www.tiktok.com/@user/video/..." autocomplete="off" spellcheck="false" />
          <span class="link-status" id="ls-3"></span>
        </div>
      </div>
      <button class="btn-full" id="multi-btn" onclick="startMulti()">Download All</button>
      <div class="progress-bar" id="prog-bar"><div class="progress-fill" id="prog-fill"></div></div>
      <div id="multi-status"></div>
    </div>

  </div>

  <footer>
    Paste any public TikTok link — videos save directly to your device.<br>
    For personal use only. Respect creators' content.
  </footer>

  <script>
    function switchTab(name, el) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      document.getElementById('panel-' + name).classList.add('active');
    }

    // ── single ──
    async function startSingle() {
      const url = document.getElementById('url-input').value.trim();
      const btn = document.getElementById('dl-btn');
      const st  = document.getElementById('status');
      if (!url) { setStatus(st, 'Paste a TikTok link first.', 'err'); return; }
      btn.disabled = true;
      setStatus(st, '⏳ Fetching video…', '');
      try {
        const blob = await downloadOne(url);
        triggerDownload(blob, 'tiktok_video.mp4');
        setStatus(st, '✓ Download started!', 'ok');
      } catch(e) {
        setStatus(st, 'Error: ' + e.message, 'err');
      } finally { btn.disabled = false; }
    }

    // ── multi ──
    async function startMulti() {
      const inputs = document.querySelectorAll('.multi-url');
      const urls   = [...inputs].map(i => i.value.trim()).filter(Boolean);
      const btn    = document.getElementById('multi-btn');
      const st     = document.getElementById('multi-status');
      const bar    = document.getElementById('prog-bar');
      const fill   = document.getElementById('prog-fill');

      if (urls.length === 0) { setStatus(st, 'Paste at least one link.', 'err'); return; }

      btn.disabled = true;
      bar.style.display = 'block';
      fill.style.width  = '0%';
      clearLinkStatuses();
      setStatus(st, `Downloading ${urls.length} video(s)…`, '');

      const results = [];
      for (let i = 0; i < urls.length; i++) {
        const inputIndex = [...inputs].findIndex((inp, idx) => inp.value.trim() === urls[i] && !results.find(r => r.idx === idx));
        const ls = document.getElementById('ls-' + i);
        if (ls) ls.textContent = '⏳';
        try {
          const blob = await downloadOne(urls[i]);
          results.push({ blob, name: 'video_' + (i+1) + '.mp4' });
          if (ls) { ls.textContent = '✓'; ls.style.color = 'var(--accent2)'; }
        } catch(e) {
          results.push(null);
          if (ls) { ls.textContent = '✗'; ls.style.color = 'var(--accent)'; }
        }
        fill.style.width = ((i+1) / urls.length * 100) + '%';
      }

      const good = results.filter(Boolean);
      if (good.length === 0) {
        setStatus(st, 'All downloads failed. Check your links.', 'err');
        btn.disabled = false; return;
      }

      if (good.length === 1) {
        triggerDownload(good[0].blob, good[0].name);
      } else {
        // zip them
        const zip = await buildZip(good);
        triggerDownload(zip, 'radikikk_videos.zip');
      }

      const failed = results.length - good.length;
      setStatus(st,
        '✓ ' + good.length + ' video(s) downloaded!' + (failed ? ' (' + failed + ' failed)' : ''),
        'ok'
      );
      btn.disabled = false;
    }

    async function downloadOne(url) {
      const resp = await fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(e.error || resp.statusText);
      }
      return await resp.blob();
    }

    async function buildZip(files) {
      // Simple ZIP builder using native APIs
      const { default: JSZip } = await import('https://cdn.skypack.dev/jszip');
      const zip = new JSZip();
      files.forEach(f => zip.file(f.name, f.blob));
      return await zip.generateAsync({ type: 'blob' });
    }

    function triggerDownload(blob, name) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      URL.revokeObjectURL(a.href);
    }

    function setStatus(el, msg, cls) {
      el.textContent = msg;
      el.className = cls || '';
    }

    function clearLinkStatuses() {
      for (let i = 0; i < 4; i++) {
        const ls = document.getElementById('ls-' + i);
        if (ls) { ls.textContent = ''; ls.style.color = ''; }
      }
    }

    document.getElementById('url-input')
      .addEventListener('keydown', e => { if (e.key === 'Enter') startSingle(); });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/download", methods=["POST"])
def download():
    body = request.get_json(silent=True) or {}
    url  = (body.get("url") or "").strip()
    if not url:
        return jsonify(error="No URL provided"), 400
    if "tiktok.com" not in url:
        return jsonify(error="Please provide a valid TikTok URL"), 400
    try:
        filename, content = fetch_hd_video(url)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return send_file(
        io.BytesIO(content),
        mimetype="video/mp4",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
