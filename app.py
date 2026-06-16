"""
app.py — Flask web interface for TikTok downloader.
Deploy on PythonAnywhere as a WSGI app.
"""

import io
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
    /* ── tokens ── */
    :root {
      --bg:       #0d0d0d;
      --surface:  #161616;
      --border:   #2a2a2a;
      --accent:   #fe2c55;   /* TikTok red */
      --accent2:  #25f4ee;   /* TikTok cyan */
      --text:     #f0f0f0;
      --muted:    #888;
      --radius:   12px;
      --font:     'Inter', system-ui, sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }

    /* ── logo ── */
    .logo {
      font-size: 2.4rem;
      font-weight: 800;
      letter-spacing: -1px;
      margin-bottom: 6px;
    }
    .logo span:first-child { color: var(--accent); }
    .logo span:last-child  { color: var(--accent2); }

    .tagline {
      color: var(--muted);
      font-size: 0.9rem;
      margin-bottom: 36px;
    }

    /* ── card ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 32px;
      width: 100%;
      max-width: 520px;
    }

    label {
      display: block;
      font-size: 0.8rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 8px;
    }

    .input-row {
      display: flex;
      gap: 10px;
    }

    input[type="url"] {
      flex: 1;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 0.95rem;
      padding: 12px 14px;
      outline: none;
      transition: border-color .2s;
    }
    input[type="url"]:focus { border-color: var(--accent); }
    input[type="url"]::placeholder { color: var(--muted); }

    button {
      background: var(--accent);
      border: none;
      border-radius: 8px;
      color: #fff;
      cursor: pointer;
      font-size: 0.95rem;
      font-weight: 600;
      padding: 12px 20px;
      transition: opacity .2s, transform .1s;
      white-space: nowrap;
    }
    button:hover   { opacity: .88; }
    button:active  { transform: scale(.97); }
    button:disabled { opacity: .45; cursor: not-allowed; }

    /* ── status ── */
    #status {
      margin-top: 18px;
      font-size: 0.9rem;
      min-height: 22px;
      text-align: center;
    }
    .ok  { color: var(--accent2); }
    .err { color: var(--accent); }
    .spin::before { content: "⏳ "; }

    /* ── footer ── */
    footer {
      margin-top: 28px;
      color: var(--muted);
      font-size: 0.78rem;
      text-align: center;
      line-height: 1.6;
    }
  </style>
</head>
<body>

  <div class="logo"><span>Radikikk</span><span> Downloader</span></div>
  <p class="tagline">Watermark-free TikTok downloads — fast & free</p>

  <div class="card">
    <label for="url-input">TikTok video link</label>
    <div class="input-row">
      <input
        id="url-input"
        type="url"
        placeholder="https://www.tiktok.com/@user/video/..."
        autocomplete="off"
        spellcheck="false"
      />
      <button id="dl-btn" onclick="startDownload()">Download</button>
    </div>
    <div id="status"></div>
  </div>

  <footer>
    Paste any public TikTok link — the video saves directly to your device.<br>
    For personal use only. Respect creators' content.
  </footer>

  <script>
    async function startDownload() {
      const input  = document.getElementById("url-input");
      const btn    = document.getElementById("dl-btn");
      const status = document.getElementById("status");
      const url    = input.value.trim();

      if (!url) { setStatus("Paste a TikTok link first.", "err"); return; }

      btn.disabled = true;
      setStatus("Fetching video…", "spin");

      try {
        const resp = await fetch("/download", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ url }),
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ error: "Unknown error" }));
          throw new Error(err.error || resp.statusText);
        }

        // Trigger browser download from blob
        const blob     = await resp.blob();
        const filename = (resp.headers.get("Content-Disposition") || "")
          .match(/filename="?([^"]+)"?/)?.[1] || "tiktok_video.mp4";

        const a = document.createElement("a");
        a.href     = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);

        setStatus("✓ Download started!", "ok");
      } catch (e) {
        setStatus("Error: " + e.message, "err");
      } finally {
        btn.disabled = false;
      }
    }

    function setStatus(msg, cls) {
      const el = document.getElementById("status");
      el.textContent = msg;
      el.className   = cls || "";
    }

    // Allow Enter key
    document.getElementById("url-input")
      .addEventListener("keydown", e => { if (e.key === "Enter") startDownload(); });
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
    if "tiktok.com" not in url and "vm.tiktok.com" not in url:
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
