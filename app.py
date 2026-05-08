#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NOX IPTV CLOUD PANEL V4.1
-----------------------
Admin panel + Client Portal + Web Player.

Përdorim vetëm me lista/stream-e që ke të drejtë t'i përdorësh.

Funksionet V4:
- Admin login
- Master Template
- Klientë me host/user/pass ose source M3U individual
- Permanent M3U link për Smart IPTV
- Client portal login: /watch
- Çdo klient ka portal user/password
- Kërkim kanalesh
- Kategori/grupe
- Web player për m3u8/HLS
- Për TS/MPEGTS: buton Open Stream / Copy URL / Download M3U
- Download M3U për klientin
- Bulk refresh, clear cache, export JSON
- Nuk proxy-on video stream-in; video hapet direkt nga provider-i te klienti
"""

import json
import os
import re
import socket
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from flask import Flask, Response, abort, redirect, render_template_string, request, session, url_for

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", APP_DIR / "data"))
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

CLIENTS_FILE = DATA_DIR / "clients.json"
TEMPLATE_FILE = DATA_DIR / "master_template.m3u"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "120"))

HEADERS = {
    "User-Agent": "VLC/3.0.20 LibVLC/3.0.20",
    "Accept": "*/*",
    "Connection": "close",
}

DEFAULT_GROUP_ORDER = [
    "ALBANIA", "SHQIP", "KOSOVA", "KOSOVO",
    "SPORT", "SPORTS",
    "GERMANY", "DEUTSCHLAND", "DE",
    "KIDS", "FEMIJE", "FËMIJË",
    "MOVIES", "FILM", "SERIES", "SERIALE",
]

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ---------------- Helpers ----------------

def load_clients():
    if CLIENTS_FILE.exists():
        try:
            return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_clients(clients):
    CLIENTS_FILE.write_text(json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "client"


def unix_to_date(value):
    if value in (None, "", "0", "null", "None"):
        return "Pa expiry / e panjohur"
    try:
        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def days_left(value):
    try:
        return (datetime.fromtimestamp(int(value)) - datetime.now()).days
    except Exception:
        return None


def resolve_ip(host):
    try:
        return ", ".join(sorted(set(x[4][0] for x in socket.getaddrinfo(host, None))))
    except Exception as e:
        return f"DNS problem: {e}"


def normalize_base(server):
    server = (server or "").strip().rstrip("/")
    if not server:
        return ""
    if not server.startswith(("http://", "https://")):
        server = "http://" + server
    return server


def parse_m3u_link(link):
    p = urlparse(link.strip())
    q = parse_qs(p.query)
    if not p.scheme or not p.netloc:
        raise ValueError("Linku duhet të fillojë me http:// ose https://")
    username = (q.get("username") or [""])[0]
    password = (q.get("password") or [""])[0]
    if not username or not password:
        raise ValueError("Nuk gjeta username/password në link.")
    return {
        "scheme": p.scheme,
        "base": f"{p.scheme}://{p.netloc}",
        "netloc": p.netloc,
        "host": p.hostname or "",
        "username": username,
        "password": password,
        "query": q,
    }


def get_template_text():
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8", errors="ignore")
    return ""


def save_template_text(text):
    TEMPLATE_FILE.write_text(text, encoding="utf-8")


def proxy_fetch_url(client, target_url):
    proxy = (client.get("proxy_url") or "").strip()
    if not proxy:
        return target_url
    sep = "" if proxy.endswith(("=", "/", "?url=")) else "?url="
    return proxy + sep + requests.utils.quote(target_url, safe="")


def request_get(url, client=None):
    final_url = proxy_fetch_url(client or {}, url)
    return requests.get(final_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)


# ---------------- API / M3U ----------------

def check_api_from_link(m3u_link, client=None):
    p = parse_m3u_link(m3u_link)
    return check_api_from_parts(p["base"], p["username"], p["password"], client=client)


def check_api_from_parts(base, username, password, client=None):
    base = normalize_base(base)
    parsed = urlparse(base)
    url = base.rstrip("/") + "/player_api.php?" + urlencode({"username": username, "password": password})
    try:
        r = request_get(url, client)
        data = r.json()
        user = data.get("user_info", {}) or {}
        server = data.get("server_info", {}) or {}
        return {
            "ok": True,
            "status": user.get("status", "Unknown"),
            "auth": user.get("auth", "Unknown"),
            "expiry": unix_to_date(user.get("exp_date")),
            "days_left": days_left(user.get("exp_date")),
            "active": user.get("active_cons", "Unknown"),
            "max": user.get("max_connections", "Unknown"),
            "trial": user.get("is_trial", "Unknown"),
            "timezone": server.get("timezone", "Unknown"),
            "server_url": server.get("url", "Unknown"),
            "server_port": server.get("port", "Unknown"),
            "host": parsed.hostname or "",
            "ip": resolve_ip(parsed.hostname or ""),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "host": parsed.hostname or ""}


def build_m3u_url(m3u_link, output="ts"):
    p = urlparse(m3u_link.strip())
    q = parse_qs(p.query)
    q["type"] = ["m3u_plus"]
    q["output"] = [output]
    query = urlencode({k: v[0] if isinstance(v, list) else v for k, v in q.items()})
    return urlunparse((p.scheme, p.netloc, "/get.php", "", query, ""))


def fetch_m3u(m3u_link, output="ts", client=None):
    url = build_m3u_url(m3u_link, output)
    r = request_get(url, client)
    r.raise_for_status()
    text = r.text
    if "#EXTM3U" not in text[:1000]:
        raise ValueError("Përgjigjja nuk duket M3U valid.")
    return text


# ---------------- M3U processing ----------------

def extract_group(extinf_line):
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    return m.group(1) if m else "Pa grup"


def extract_name(extinf_line):
    return extinf_line.split(",", 1)[-1].strip() if "," in extinf_line else extinf_line.strip()


def extract_logo(extinf_line):
    m = re.search(r'tvg-logo="([^"]*)"', extinf_line)
    return m.group(1) if m else ""


def group_priority(group, order):
    g = group.upper()
    for i, key in enumerate(order):
        if key.upper() in g:
            return i
    return len(order) + 1


def parse_m3u_items(text):
    lines = text.splitlines()
    items = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            url = ""
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
            if url.startswith("http://") or url.startswith("https://"):
                items.append({
                    "extinf": line,
                    "url": url,
                    "group": extract_group(line),
                    "name": extract_name(line),
                    "logo": extract_logo(line),
                })
                i += 2
                continue
        i += 1
    return items


def rebuild_m3u(items):
    output = ["#EXTM3U"]
    for item in items:
        output.append(item["extinf"])
        output.append(item["url"])
    return "\n".join(output) + "\n"


def template_stats(text):
    items = parse_m3u_items(text)
    groups = {}
    for it in items:
        groups[it["group"]] = groups.get(it["group"], 0) + 1
    return {
        "channels": len(items),
        "groups": len(groups),
        "top_groups": sorted(groups.items(), key=lambda x: x[1], reverse=True)[:15],
    }


def replace_stream_credentials_in_url(url, new_base, username, password):
    new_base = normalize_base(new_base)
    old = urlparse(url)
    nb = urlparse(new_base)
    parts = [x for x in old.path.split("/") if x]
    if len(parts) >= 3:
        rest = parts[2:]
        new_path = "/" + "/".join([username, password] + rest)
    elif len(parts) >= 1:
        new_path = "/" + "/".join([username, password] + parts[-1:])
    else:
        new_path = f"/{username}/{password}"
    return urlunparse((nb.scheme or old.scheme or "http", nb.netloc, new_path, "", "", ""))


def apply_template_for_client(template_text, client):
    server = normalize_base(client.get("server") or "")
    username = (client.get("username") or "").strip()
    password = (client.get("password") or "").strip()
    if not server or not username or not password:
        raise ValueError("Për template mode duhen server, username dhe password te klienti.")
    items = parse_m3u_items(template_text)
    for item in items:
        item["url"] = replace_stream_credentials_in_url(item["url"], server, username, password)
    processed = rebuild_m3u(items)
    return process_m3u(processed, client)


def process_m3u(text, client):
    replace_from = (client.get("replace_from") or "").strip()
    replace_to = (client.get("replace_to") or "").strip()
    remove_duplicates = bool(client.get("remove_duplicates", True))
    sort_groups = bool(client.get("sort_groups", False))

    if replace_from and replace_to:
        old_netloc = urlparse(replace_from if "://" in replace_from else "http://" + replace_from).netloc
        new_netloc = urlparse(replace_to if "://" in replace_to else "http://" + replace_to).netloc
        if old_netloc and new_netloc:
            text = text.replace(old_netloc, new_netloc)

    items = parse_m3u_items(text)

    if remove_duplicates:
        seen = set()
        deduped = []
        for item in items:
            key = item["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        items = deduped

    order_text = client.get("group_order", "")
    order = [x.strip() for x in order_text.split(",") if x.strip()] or DEFAULT_GROUP_ORDER
    if sort_groups:
        items.sort(key=lambda x: (group_priority(x["group"], order), x["group"].lower(), x["name"].lower()))

    return rebuild_m3u(items)


def cache_path(slug):
    return CACHE_DIR / f"{slug}.m3u"


def get_playlist_for_client(slug, force_refresh=False):
    clients = load_clients()
    client = clients.get(slug)
    if not client:
        abort(404)

    cp = cache_path(slug)
    if not force_refresh and cp.exists() and time.time() - cp.stat().st_mtime < CACHE_SECONDS:
        return cp.read_text(encoding="utf-8", errors="ignore")

    mode = client.get("mode", "source_link")
    if mode == "template":
        template_text = get_template_text()
        if not template_text:
            raise ValueError("Master template nuk është vendosur ende.")
        processed = apply_template_for_client(template_text, client)
    else:
        raw = fetch_m3u(client["m3u_link"], client.get("output", "ts"), client=client)
        processed = process_m3u(raw, client)

    cp.write_text(processed, encoding="utf-8")
    client["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client["last_channels"] = processed.count("#EXTINF")
    clients[slug] = client
    save_clients(clients)
    return processed


def clear_all_cache():
    count = 0
    for f in CACHE_DIR.glob("*.m3u"):
        try:
            f.unlink()
            count += 1
        except Exception:
            pass
    return count


def login_required():
    return session.get("logged_in") is True


def client_login_required():
    return bool(session.get("client_slug"))


# ---------------- HTML layouts ----------------

ADMIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Nox IPTV Panel V4.1</title>
  <style>
    :root { --bg:#0f172a; --text:#0f172a; --muted:#64748b; --brand:#2563eb; --green:#16a34a; --red:#dc2626; }
    body { font-family: Inter, Arial, sans-serif; margin:0; background:#f1f5f9; color:var(--text); }
    .top { background:linear-gradient(135deg,#0f172a,#1e3a8a); color:white; padding:28px; }
    .top h1 { margin:0 0 8px; font-size:28px; }
    .top p { margin:0; opacity:.85; }
    .wrap { max-width:1250px; margin:0 auto; padding:22px; }
    .nav { margin-top:18px; display:flex; gap:8px; flex-wrap:wrap; }
    .btn, button { background:var(--brand); color:white; border:0; padding:9px 13px; border-radius:10px; text-decoration:none; display:inline-block; margin:3px; cursor:pointer; font-weight:600; }
    .btn.dark { background:#111827; }
    .btn.gray { background:#64748b; }
    .btn.red { background:var(--red); }
    .btn.green { background:var(--green); }
    .card { background:white; padding:18px; border-radius:16px; margin-bottom:16px; box-shadow:0 8px 26px #00000012; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; }
    .stat { background:white; padding:18px; border-radius:16px; box-shadow:0 8px 26px #00000012; }
    .stat .num { font-size:28px; font-weight:800; }
    .stat .label { color:var(--muted); font-size:13px; }
    input, select, textarea { width:100%; padding:11px; margin:6px 0 13px; box-sizing:border-box; border:1px solid #cbd5e1; border-radius:10px; background:#fff; }
    label { font-weight:700; font-size:13px; }
    table { width:100%; border-collapse:collapse; background:white; overflow:hidden; border-radius:14px; }
    th, td { padding:12px; border-bottom:1px solid #e2e8f0; text-align:left; vertical-align:top; }
    th { background:#f8fafc; font-size:13px; color:#475569; }
    code { background:#e2e8f0; padding:3px 6px; border-radius:6px; word-break:break-all; }
    .small { color:#64748b; font-size:12px; }
    .ok { color:var(--green); font-weight:800; }
    .bad { color:var(--red); font-weight:800; }
    pre { background:#0f172a; color:#e5e7eb; padding:15px; border-radius:12px; overflow:auto; }
  </style>
</head>
<body>
  <div class="top">
    <div class="wrap">
      <h1>Nox IPTV Panel V4.1</h1>
      <p>Admin panel + Client portal + Web player.</p>
      {% if logged %}
      <div class="nav">
        <a class="btn" href="/">Dashboard</a>
        <a class="btn" href="/template">Master Template</a>
        <a class="btn green" href="/add">Add Client</a>
        <a class="btn gray" href="/bulk-refresh">Bulk Refresh</a>
        <a class="btn gray" href="/clear-cache">Clear Cache</a>
        <a class="btn dark" href="/export">Export JSON</a>
        <a class="btn red" href="/logout">Logout</a>
      </div>
      {% endif %}
    </div>
  </div>
  <div class="wrap">
    {{ body|safe }}
  </div>
</body>
</html>
"""

CLIENT_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Nox IPTV Watch</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <style>
    body { margin:0; font-family:Arial,sans-serif; background:#0b1220; color:#e5e7eb; }
    .top { background:#111827; padding:14px; position:sticky; top:0; z-index:10; }
    .top h2 { margin:0 0 8px; font-size:20px; }
    .bar { display:flex; gap:8px; flex-wrap:wrap; }
    input, select { padding:10px; border-radius:10px; border:1px solid #334155; background:#0f172a; color:white; flex:1; min-width:160px; }
    .btn { background:#2563eb; color:white; padding:10px 12px; border-radius:10px; text-decoration:none; border:0; display:inline-block; cursor:pointer; }
    .btn.gray { background:#475569; }
    .btn.red { background:#dc2626; }
    .wrap { padding:12px; max-width:1100px; margin:auto; }
    video { width:100%; background:#000; border-radius:14px; max-height:55vh; }
    .player { background:#111827; padding:12px; border-radius:16px; margin-bottom:14px; }
    .now { font-weight:700; margin:8px 0; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:10px; }
    .ch { background:#111827; border:1px solid #1f2937; border-radius:14px; padding:10px; cursor:pointer; }
    .ch:hover { border-color:#2563eb; }
    .logo { width:42px; height:42px; object-fit:contain; float:left; margin-right:10px; background:#fff1; border-radius:8px; }
    .name { font-size:14px; font-weight:700; min-height:38px; }
    .group { font-size:12px; color:#94a3b8; margin-top:6px; clear:both; }
    .hint { color:#94a3b8; font-size:13px; }
    code { word-break:break-all; background:#020617; padding:4px 6px; border-radius:6px; }
  </style>
</head>
<body>
  {{ body|safe }}
</body>
</html>
"""


def admin_page(body):
    return render_template_string(ADMIN_HTML, body=body, logged=login_required())


def client_page(body):
    return render_template_string(CLIENT_HTML, body=body)


# ---------------- Admin routes ----------------

@app.route("/admin-login", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        error = "Password gabim."
    body = f"""
    <div class="card" style="max-width:480px;margin:50px auto;">
      <h2>Admin Login</h2>
      <form method="post">
        <input type="password" name="password" placeholder="Admin password">
        <button>Login</button>
      </form>
      <p class="bad">{error}</p>
      <p class="small">Client portal është te <code>/watch</code></p>
    </div>
    """
    return admin_page(body)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/login")


@app.route("/")
def dashboard():
    if not login_required():
        return redirect("/login")

    clients = load_clients()
    template_text = get_template_text()
    stats = template_stats(template_text) if template_text else {"channels":0, "groups":0}
    cache_files = list(CACHE_DIR.glob("*.m3u"))

    stat_html = f"""
    <div class="grid">
      <div class="stat"><div class="num">{len(clients)}</div><div class="label">Clients</div></div>
      <div class="stat"><div class="num">{stats['channels']}</div><div class="label">Template channels</div></div>
      <div class="stat"><div class="num">{stats['groups']}</div><div class="label">Template groups</div></div>
      <div class="stat"><div class="num">{len(cache_files)}</div><div class="label">Cached playlists</div></div>
    </div>
    """

    rows = ""
    for slug, c in sorted(clients.items()):
        public_url = request.url_root.rstrip("/") + url_for("playlist", slug=slug)
        watch_url = request.url_root.rstrip("/") + "/watch"
        mode = c.get("mode", "source_link")
        rows += f"""
        <tr>
          <td><b>{c.get('name')}</b><br><span class="small">{slug}</span></td>
          <td><code>{public_url}</code><br><span class="small">Watch portal: <code>{watch_url}</code></span></td>
          <td>{mode}</td>
          <td>{c.get('output','ts')}</td>
          <td>{c.get('last_channels','-')}</td>
          <td>{c.get('last_update','-')}</td>
          <td>
            <a class="btn gray" href="/check/{slug}">Check</a>
            <a class="btn green" href="/refresh/{slug}">Refresh</a>
            <a class="btn" href="/edit/{slug}">Edit</a>
            <a class="btn dark" href="/download/{slug}">Download</a>
            <a class="btn gray" href="/p/{slug}.m3u">Open</a>
            <a class="btn red" href="/delete/{slug}" onclick="return confirm('Delete?')">Delete</a>
          </td>
        </tr>
        """
    body = f"""
    {stat_html}
    <div class="card">
      <h2>Clients</h2>
      <p class="small">Client portal për telefon/laptop: <code>{request.url_root.rstrip()}/watch</code></p>
      <table>
        <tr><th>Client</th><th>Links</th><th>Mode</th><th>Output</th><th>Channels</th><th>Last update</th><th>Actions</th></tr>
        {rows or '<tr><td colspan="7">Nuk ka klientë ende.</td></tr>'}
      </table>
    </div>
    """
    return admin_page(body)


@app.route("/template", methods=["GET", "POST"])
def template():
    if not login_required():
        return redirect("/login")

    msg = ""
    if request.method == "POST":
        text = request.form.get("template_text", "")
        if "#EXTM3U" not in text[:1000]:
            msg = "<p class='bad'>Kjo nuk duket si M3U template valid.</p>"
        else:
            save_template_text(text)
            clear_all_cache()
            msg = "<p class='ok'>Master template u ruajt. Cache u pastrua.</p>"

    text = get_template_text()
    stats = template_stats(text) if text else {"channels":0, "groups":0, "top_groups":[]}
    groups = "".join(f"<li>{g}: <b>{c}</b></li>" for g,c in stats.get("top_groups", []))
    body = f"""
    <div class="grid">
      <div class="stat"><div class="num">{stats['channels']}</div><div class="label">Channels</div></div>
      <div class="stat"><div class="num">{stats['groups']}</div><div class="label">Groups</div></div>
    </div>
    <div class="card">
      <h2>Master Template</h2>
      <form method="post">
        <textarea name="template_text" rows="24" placeholder="#EXTM3U...">{text}</textarea>
        <button>Save Master Template</button>
      </form>
      {msg}
    </div>
    <div class="card"><h3>Top Groups</h3><ul>{groups or '<li>Pa grupe ende</li>'}</ul></div>
    """
    return admin_page(body)


@app.route("/add", methods=["GET", "POST"])
@app.route("/edit/<slug>", methods=["GET", "POST"])
def add_edit(slug=None):
    if not login_required():
        return redirect("/login")

    clients = load_clients()
    client = clients.get(slug, {}) if slug else {}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mode = request.form.get("mode", "source_link")
        if not name:
            return admin_page("<p class='bad'>Client name është i detyrueshëm.</p>")

        new_slug = slug or slugify(name)
        portal_user = request.form.get("portal_user", "").strip() or new_slug
        portal_password = request.form.get("portal_password", "").strip() or client.get("portal_password", "1234")

        data = {
            "name": name,
            "mode": mode,
            "output": request.form.get("output", "ts"),
            "replace_from": request.form.get("replace_from", "").strip(),
            "replace_to": request.form.get("replace_to", "").strip(),
            "sort_groups": request.form.get("sort_groups") == "on",
            "remove_duplicates": request.form.get("remove_duplicates") == "on",
            "group_order": request.form.get("group_order", ""),
            "proxy_url": request.form.get("proxy_url", "").strip(),
            "portal_user": portal_user,
            "portal_password": portal_password,
            "allow_watch": request.form.get("allow_watch") == "on",
            "created": client.get("created") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": client.get("last_update"),
            "last_channels": client.get("last_channels"),
        }

        if mode == "template":
            server = normalize_base(request.form.get("server", ""))
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            if not server or not username or not password:
                return admin_page("<p class='bad'>Në Template mode duhen server, username dhe password.</p>")
            data.update({"server": server, "username": username, "password": password})
            data["m3u_link"] = f"{server.rstrip('/')}/get.php?username={username}&password={password}&type=m3u_plus&output={data['output']}"
        else:
            m3u_link = request.form.get("m3u_link", "").strip()
            if not m3u_link:
                return admin_page("<p class='bad'>M3U source link është i detyrueshëm.</p>")
            parse_m3u_link(m3u_link)
            data["m3u_link"] = m3u_link

        clients[new_slug] = data
        save_clients(clients)

        cp = cache_path(new_slug)
        if cp.exists():
            cp.unlink()

        return redirect("/")

    mode = client.get("mode", "source_link")
    body = f"""
    <div class="card">
      <h2>{'Edit Client' if slug else 'Add Client'}</h2>
      <form method="post">
        <label>Client name</label>
        <input name="name" value="{client.get('name','')}" placeholder="p.sh. Nox">

        <label>Client Portal Username</label>
        <input name="portal_user" value="{client.get('portal_user', slug or '')}" placeholder="p.sh. nox">

        <label>Client Portal Password</label>
        <input name="portal_password" value="{client.get('portal_password','1234')}" placeholder="p.sh. 1234">

        <label><input style="width:auto" type="checkbox" name="allow_watch" {"checked" if client.get("allow_watch", True) else ""}> Allow client portal / web player</label><br><br>

        <label>Mode</label>
        <select name="mode">
          <option value="source_link" {"selected" if mode=="source_link" else ""}>Source M3U link individual</option>
          <option value="template" {"selected" if mode=="template" else ""}>Use Master Template - only host/user/pass changes</option>
        </select>

        <div class="grid">
          <div class="card">
            <h3>Template mode</h3>
            <label>Server/host</label>
            <input name="server" value="{client.get('server','')}" placeholder="http://host.com:80">
            <label>Username</label>
            <input name="username" value="{client.get('username','')}" placeholder="username">
            <label>Password</label>
            <input name="password" value="{client.get('password','')}" placeholder="password">
          </div>

          <div class="card">
            <h3>Individual source mode</h3>
            <label>M3U source link</label>
            <textarea name="m3u_link" rows="7" placeholder="http://server/get.php?username=...&password=...&type=m3u_plus">{client.get('m3u_link','')}</textarea>
          </div>
        </div>

        <label>Output format</label>
        <select name="output">
          {''.join(f'<option value="{x}" {"selected" if client.get("output","ts")==x else ""}>{x}</option>' for x in ["ts","mpegts","m3u8"])}
        </select>

        <label>Optional Proxy URL / VPN gateway</label>
        <input name="proxy_url" value="{client.get('proxy_url','')}" placeholder="p.sh. https://proxy-domain/fetch?url=">

        <label>Replace from host/server optional</label>
        <input name="replace_from" value="{client.get('replace_from','')}" placeholder="http://oldhost.com ose oldhost.com">

        <label>Replace to host/server optional</label>
        <input name="replace_to" value="{client.get('replace_to','')}" placeholder="http://newhost.com">

        <label>Group order, nda me presje</label>
        <input name="group_order" value="{client.get('group_order', ', '.join(DEFAULT_GROUP_ORDER))}">

        <label><input style="width:auto" type="checkbox" name="sort_groups" {"checked" if client.get("sort_groups", False) else ""}> Sort groups automatically</label><br>
        <label><input style="width:auto" type="checkbox" name="remove_duplicates" {"checked" if client.get("remove_duplicates", True) else ""}> Remove duplicate channel names</label><br><br>

        <button>Save</button>
      </form>
    </div>
    """
    return admin_page(body)


@app.route("/check/<slug>")
def check(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        abort(404)

    if c.get("mode") == "template":
        info = check_api_from_parts(c.get("server"), c.get("username"), c.get("password"), client=c)
    else:
        info = check_api_from_link(c["m3u_link"], client=c)

    status_class = "ok" if info.get("ok") else "bad"
    body = f"""
    <div class="card">
      <h2>Check: {c.get('name')}</h2>
      <p class="{status_class}">API: {'OK' if info.get('ok') else 'PROBLEM'}</p>
      <pre>{json.dumps(info, ensure_ascii=False, indent=2)}</pre>
    </div>
    """
    return admin_page(body)


@app.route("/refresh/<slug>")
def refresh(slug):
    if not login_required():
        return redirect("/login")
    try:
        get_playlist_for_client(slug, force_refresh=True)
        return redirect("/")
    except Exception as e:
        return admin_page(f"<div class='card'><p class='bad'>Refresh problem: {e}</p></div>")


@app.route("/bulk-refresh")
def bulk_refresh():
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    results = []
    for slug in clients:
        try:
            get_playlist_for_client(slug, force_refresh=True)
            results.append((slug, "OK"))
        except Exception as e:
            results.append((slug, str(e)))
    lis = "".join(f"<li><b>{s}</b>: {r}</li>" for s, r in results)
    return admin_page(f"<div class='card'><h2>Bulk Refresh Results</h2><ul>{lis}</ul></div>")


@app.route("/clear-cache")
def clear_cache():
    if not login_required():
        return redirect("/login")
    count = clear_all_cache()
    return admin_page(f"<div class='card'><h2>Cache cleared</h2><p>{count} playlist cache files deleted.</p></div>")


@app.route("/download/<slug>")
def download(slug):
    if not login_required():
        return redirect("/login")
    text = get_playlist_for_client(slug, force_refresh=True)
    return Response(
        text,
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": f"attachment; filename={slug}.m3u"}
    )


@app.route("/delete/<slug>")
def delete(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    clients.pop(slug, None)
    save_clients(clients)
    cp = cache_path(slug)
    if cp.exists():
        cp.unlink()
    return redirect("/")


@app.route("/export")
def export_json():
    if not login_required():
        return redirect("/login")
    data = json.dumps(load_clients(), ensure_ascii=False, indent=2)
    return Response(data, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=clients_export.json"})


@app.route("/p/<slug>.m3u")
def playlist(slug):
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        return Response(text, mimetype="audio/x-mpegurl")
    except Exception as e:
        return Response(f"#EXTM3U\n# ERROR: {e}\n", mimetype="text/plain", status=500)


# ---------------- Client Portal ----------------

@app.route("/watch", methods=["GET", "POST"])
def watch_login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        clients = load_clients()
        for slug, c in clients.items():
            if not c.get("allow_watch", True):
                continue
            if c.get("portal_user") == u and c.get("portal_password") == p:
                session["client_slug"] = slug
                return redirect("/watch/home")
        return client_page("""
        <div class="top"><h2>Nox IPTV Watch</h2></div>
        <div class="wrap"><div class="player"><p style="color:#fca5a5">Login gabim.</p><a class="btn" href="/watch">Provo prapë</a></div></div>
        """)

    body = """
    <div class="top"><h2>Nox IPTV Watch</h2></div>
    <div class="wrap">
      <div class="player">
        <h3>Client Login</h3>
        <form method="post">
          <input name="username" placeholder="Username">
          <input name="password" type="password" placeholder="Password">
          <button class="btn">Login</button>
        </form>
      </div>
    </div>
    """
    return client_page(body)


@app.route("/watch/logout")
def watch_logout():
    session.pop("client_slug", None)
    return redirect("/watch")


@app.route("/watch/home")
def watch_home():
    if not client_login_required():
        return redirect("/watch")

    slug = session["client_slug"]
    clients = load_clients()
    c = clients.get(slug)
    if not c or not c.get("allow_watch", True):
        return redirect("/watch/logout")

    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
    except Exception as e:
        return client_page(f"""
        <div class="top"><h2>Nox IPTV Watch</h2></div>
        <div class="wrap"><div class="player"><p>Problem: {e}</p></div></div>
        """)

    groups = sorted(set(i["group"] for i in items))
    safe_items = []
    for idx, it in enumerate(items):
        safe_items.append({
            "i": idx,
            "name": it["name"],
            "group": it["group"],
            "logo": it["logo"],
            "url": it["url"],
        })

    data_json = json.dumps(safe_items, ensure_ascii=False)
    body = f"""
    <div class="top">
      <h2>{c.get('name')} - Nox IPTV Watch</h2>
      <div class="bar">
        <input id="search" placeholder="Kërko kanal...">
        <select id="group">
          <option value="">Të gjitha kategoritë</option>
          {''.join(f'<option value="{g}">{g}</option>' for g in groups)}
        </select>
        <a class="btn red" href="/watch/logout">Logout</a>
      </div>
    </div>
    <div class="wrap">
      <div class="player">
        <video id="video" controls playsinline></video>
        <div class="now" id="now">Zgjedh një kanal.</div>
        <div class="hint" id="hint">Zgjedh një kanal. Player-i do të provojë ta hapë direkt në browser.</div>
        <p class="hint">Shikimi është vetëm brenda këtij player-i.</p>
        <p class="hint">Nëse një kanal nuk hapet, ai format mund të mos suportohet nga browseri. Për shikim 100% në browser kërko output m3u8/HLS.</p>
      </div>
      <div class="grid" id="channels"></div>
    </div>
    <script>
      const channels = {data_json};
      let currentUrl = "";

      function playChannel(ch) {{
        currentUrl = ch.url;
        document.getElementById("now").innerText = ch.name + " — " + ch.group;
        const video = document.getElementById("video");

        if (window.hls) {{
          window.hls.destroy();
          window.hls = null;
        }}

        video.pause();
        video.removeAttribute("src");
        video.load();

        video.onerror = function() {{
          document.getElementById("hint").innerText =
            "Ky kanal nuk u hap në browser. Zakonisht ndodh kur stream është TS/MPEGTS dhe jo HLS/M3U8.";
        }};

        if (ch.url.toLowerCase().includes(".m3u8")) {{
          if (Hls.isSupported()) {{
            window.hls = new Hls({{
              maxBufferLength: 30,
              liveSyncDurationCount: 3,
              enableWorker: true
            }});
            window.hls.loadSource(ch.url);
            window.hls.attachMedia(video);
            window.hls.on(Hls.Events.MANIFEST_PARSED, function() {{
              video.play().catch(() => {{}});
            }});
            window.hls.on(Hls.Events.ERROR, function(event, data) {{
              if (data.fatal) {{
                document.getElementById("hint").innerText =
                  "HLS error: kanali nuk u hap në browser.";
              }}
            }});
          }} else if (video.canPlayType("application/vnd.apple.mpegurl")) {{
            video.src = ch.url;
            video.play().catch(() => {{}});
          }}
          document.getElementById("hint").innerText = "Duke provuar HLS/M3U8 në browser...";
        }} else {{
          video.src = ch.url;
          video.play().catch(() => {{
            document.getElementById("hint").innerText =
              "Browseri nuk e hapi këtë format. Për shikim 100% në browser duhet stream/output m3u8 nga provider-i.";
          }});
          document.getElementById("hint").innerText = "Duke provuar direct playback në browser...";
        }}
      }}

      function render() {{
        const q = document.getElementById("search").value.toLowerCase();
        const g = document.getElementById("group").value;
        const box = document.getElementById("channels");
        box.innerHTML = "";
        channels.filter(ch => {{
          return (!q || ch.name.toLowerCase().includes(q)) && (!g || ch.group === g);
        }}).slice(0, 500).forEach(ch => {{
          const div = document.createElement("div");
          div.className = "ch";
          div.onclick = () => playChannel(ch);
          div.innerHTML = `
            ${{ch.logo ? `<img class="logo" src="${{ch.logo}}" onerror="this.style.display='none'">` : ""}}
            <div class="name">${{ch.name}}</div>
            <div class="group">${{ch.group}}</div>
          `;
          box.appendChild(div);
        }});
      }}


      document.getElementById("search").addEventListener("input", render);
      document.getElementById("group").addEventListener("change", render);
      render();
    </script>
    """
    return client_page(body)




@app.route("/health")
def health():
    return {"ok": True, "time": datetime.now().isoformat()}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
