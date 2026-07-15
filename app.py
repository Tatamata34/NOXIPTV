#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NOX IPTV CLOUD PANEL V11.0
Admin panel + Master Template + Backup/Restore + Client Portal direct VLC + Native Android API.

Use only with playlists/streams you are authorized to manage.
"""

import json
import base64
import os
import re
import socket
import secrets
import subprocess
import threading
import shutil
import shutil
import subprocess
import threading
import time
import uuid
import base64
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse, urljoin

import requests
from flask import send_from_directory, stream_with_context, Flask, Response, abort, redirect, render_template_string, request, session, url_for

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", APP_DIR / "data"))
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
HLS_DIR = DATA_DIR / "hls"
HLS_DIR.mkdir(exist_ok=True)

CLIENTS_FILE = DATA_DIR / "clients.json"
TEMPLATE_FILE = DATA_DIR / "master_template.m3u"
DEFAULT_BACKUP_FILE = APP_DIR / "noxiptv_backup.json"
AUTO_BACKUP_FILE = DATA_DIR / "auto_backup.json"
LOGS_FILE = DATA_DIR / "logs.jsonl"
SETTINGS_FILE = DATA_DIR / "settings.json"
DEVICE_FILE = DATA_DIR / "devices.json"
CHANNEL_STATS_FILE = DATA_DIR / "channel_stats.json"
SERVER_TEMPLATES_FILE = DATA_DIR / "server_templates.json"

DEFAULT_SERVER_TEMPLATES = [
    {"id": "default-0", "name": "Server 1", "server": "http://ktzcvyrm.sqhsm.com", "note": "default template", "created": "default"},
    {"id": "default-1", "name": "Server 2", "server": "http://cytwuvie.msostvip.com", "note": "default template", "created": "default"},
    {"id": "default-2", "name": "Server 3", "server": "http://zqvsqzyg.msostvip.com", "note": "default template", "created": "default"},
    {"id": "default-3", "name": "Server 4", "server": "http://cytwuvie.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-4", "name": "Server 5", "server": "http://augacsej.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-5", "name": "Server 6", "server": "http://augacsej.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-6", "name": "Server 7", "server": "http://bfvbdsnd.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-7", "name": "Server 8", "server": "http://bfvbdsnd.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-8", "name": "Server 9", "server": "http://kypzbyrd.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-9", "name": "Server 10", "server": "http://kypzbyrd.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-10", "name": "Server 11", "server": "http://pbmnnegi.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-11", "name": "Server 12", "server": "http://pbmnnegi.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-12", "name": "Server 13", "server": "http://mhpnrzxt.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-13", "name": "Server 14", "server": "http://mhpnrzxt.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-14", "name": "Server 15", "server": "http://zkyzefwp.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-15", "name": "Server 16", "server": "http://zkyzefwp.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-16", "name": "Server 17", "server": "http://zsbgkxja.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-17", "name": "Server 18", "server": "http://zsbgkxja.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-18", "name": "Server 19", "server": "http://nfpfcrji.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-19", "name": "Server 20", "server": "http://nfpfcrji.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-20", "name": "Server 21", "server": "http://myrcztdp.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-21", "name": "Server 22", "server": "http://myrcztdp.yangsmart.com", "note": "default template", "created": "default"},
    {"id": "default-22", "name": "Server 23", "server": "http://ktzcvyrm.nelidns.com", "note": "default template", "created": "default"},
    {"id": "default-23", "name": "Server 24", "server": "http://zqvsqzyg.meza.in", "note": "default template", "created": "default"},
    {"id": "default-24", "name": "Server 25", "server": "http://egxbnjjg.qastertv.xyz", "note": "default template", "created": "default"},
    {"id": "default-25", "name": "Server 26", "server": "http://egxbnjjg.smyia.com", "note": "default template", "created": "default"}
]

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "NjoNoxi69")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "120"))
APP_VERSION = "V11.0"
API_VERSION = "v11.0"


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


@app.route("/abedin-bujupi")
def abedin_bujupi_redirect():
    return redirect("/abedin-bujupi/")


@app.route("/abedin-bujupi/")
def abedin_bujupi_index():
    return send_from_directory(APP_DIR / "static" / "abedin-bujupi", "index.html")


@app.route("/abedin-bujupi/<path:filename>")
def abedin_bujupi_files(filename):
    return send_from_directory(APP_DIR / "static" / "abedin-bujupi", filename)

# ---------------- Persistent Backup / GitHub Sync ----------------

def build_full_backup():
    return {
        "version": API_VERSION if "API_VERSION" in globals() else "v7.1",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clients": load_clients_raw(),
        "master_template": get_template_text_raw(),
        "server_templates": load_server_templates() if "load_server_templates" in globals() else [],
        "note": "Auto backup from NOX IPTV panel."
    }


def save_auto_backup():
    try:
        data = build_full_backup()
        AUTO_BACKUP_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        github_auto_sync(data)
    except Exception as e:
        print("auto backup problem:", e)


def github_auto_sync(data):
    """
    Optional true GitHub overwrite.
    Set these Render Environment variables:
    GITHUB_TOKEN = github personal access token
    GITHUB_REPO = username/repository
    GITHUB_BRANCH = main
    GITHUB_BACKUP_PATH = noxiptv_backup.json
    """
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", "").strip()
    branch = os.environ.get("GITHUB_BRANCH", "main").strip()
    path = os.environ.get("GITHUB_BACKUP_PATH", "noxiptv_backup.json").strip()
    if not token or not repo:
        return

    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "NOX-IPTV-Panel"
    }

    sha = None
    try:
        r = requests.get(api, headers=headers, params={"ref": branch}, timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass

    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
    payload = {
        "message": f"Auto backup clients {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    try:
        requests.put(api, headers=headers, json=payload, timeout=20)
    except Exception as e:
        print("github sync problem:", e)


def load_clients_raw():
    if CLIENTS_FILE.exists():
        try:
            return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def get_template_text_raw():
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8", errors="ignore")
    return ""


# ---------------- Helpers ----------------

def load_clients():
    if CLIENTS_FILE.exists():
        try:
            return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    # First deploy: seed clients from repo backup file
    if DEFAULT_BACKUP_FILE.exists():
        try:
            data = json.loads(DEFAULT_BACKUP_FILE.read_text(encoding="utf-8"))
            clients = data.get("clients", {})
            master = data.get("master_template", "")
            if clients:
                CLIENTS_FILE.write_text(json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8")
            if master and not TEMPLATE_FILE.exists():
                TEMPLATE_FILE.write_text(master, encoding="utf-8")
            servers = data.get("server_templates", [])
            if servers and not SERVER_TEMPLATES_FILE.exists():
                SERVER_TEMPLATES_FILE.write_text(json.dumps(servers, ensure_ascii=False, indent=2), encoding="utf-8")
            return clients
        except Exception as e:
            print("seed backup problem:", e)
    return {}


def save_clients(clients):
    CLIENTS_FILE.write_text(json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8")
    save_auto_backup()

# ---------------- V11 Client Direct Access Helpers ----------------

def ensure_client_public_token(slug, client=None):
    """
    Each client can have a private direct-login link:
    /c/<slug>/<token>
    Admin can enable/disable this without changing normal user/pass login.
    """
    clients = load_clients()
    changed = False
    if client is None:
        client = clients.get(slug, {})
    if not client.get("public_token"):
        client["public_token"] = secrets.token_urlsafe(18)
        changed = True
    if "public_enabled" not in client:
        client["public_enabled"] = False
        changed = True
    clients[slug] = client
    if changed:
        save_clients(clients)
    return client.get("public_token")


def client_direct_url(slug):
    token = ensure_client_public_token(slug)
    return request.url_root.rstrip("/") + url_for("client_direct_login", slug=slug, token=token)




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
    save_auto_backup()


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


def replace_stream_credentials_in_url(url, new_base, username, password, output="ts"):
    # V7 stable: direct Xtream URL, no forced /live/*.m3u8
    new_base = normalize_base(new_base)
    old = urlparse(url)
    nb = urlparse(new_base)
    parts = [x for x in old.path.split("/") if x]
    stream_id = parts[-1] if parts else ""
    stream_id = stream_id.replace(".ts", "").replace(".m3u8", "")
    new_path = "/" + "/".join([username, password, stream_id])
    return urlunparse((nb.scheme or old.scheme or "http", nb.netloc, new_path, "", "", ""))


def apply_template_for_client(template_text, client):
    server = normalize_base(client.get("server") or "")
    username = (client.get("username") or "").strip()
    password = (client.get("password") or "").strip()
    if not server or not username or not password:
        raise ValueError("Për template mode duhen server, username dhe password te klienti.")
    items = parse_m3u_items(template_text)
    for item in items:
        item["url"] = replace_stream_credentials_in_url(item["url"], server, username, password, client.get("output", "ts"))
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

# ---------------- V10.1 Admin Route Protection ----------------

@app.before_request
def protect_admin_routes_v101():
    """
    Public routes stay public. Admin routes are blocked unless logged in.
    This fixes direct browsing of admin pages without password.
    """
    path = request.path or "/"

    public_prefixes = (
        "/static",
        "/watch",
        "/manifest",
        "/service-worker",
        "/p/",
        "/playlist",
        "/vlc-list",
        "/browser",
        "/proxy",
        "/api/native",
        "/c/",
        "/turniri",
    )
    public_exact = {"/", "/login", "/logout", "/favicon.ico"}

    if path in public_exact or path.startswith(public_prefixes):
        return None

    admin_prefixes = (
        "/dashboard",
        "/template",
        "/add",
        "/edit",
        "/delete",
        "/refresh",
        "/status",
        "/servers",
        "/logs",
        "/analytics",
        "/settings",
        "/bulk-refresh",
        "/clear-cache",
        "/backup",
        "/auto-backup",
        "/github-sync",
        "/restore",
        "/import",
        "/export",
        "/duplicate",
        "/toggle",
        "/client",
        "/client-direct-toggle",
        "/client-direct-reset",
        "/devices",
    )

    if path.startswith(admin_prefixes) and not login_required():
        return redirect("/login")

    return None

# ---------------- Public Turniri Editor Route ----------------
# Hap editorin në: https://noxiptv.pro/turniri
# Vendose file-in HTML këtu: NOXIPTV/turniri/index.html
@app.route("/turniri")
@app.route("/turniri/")
def turniri_editor_page():
    return send_from_directory(str(APP_DIR / "turniri"), "index.html")


# Opsionale: nëse më vonë vendos foto/CSS/JS brenda folderit turniri
# p.sh. NOXIPTV/turniri/assets/logo.png
@app.route("/turniri/<path:filename>")
def turniri_editor_files(filename):
    return send_from_directory(str(APP_DIR / "turniri"), filename)








# ---------------- V6.3----------------

def load_json_file(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json_file(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_settings():
    default = {
        "brand_name": "NOX IPTV",
        "logo_text": "NOX",
        "logo_url": "/static/nox_logo.svg",
        "theme_preset": "modern_blue",
        "brand_color": "#2563eb",
        "accent_color": "#16a34a",
        "background_color": "#0b1220",
        "card_color": "#111827",
        "text_color": "#e5e7eb",
        "layout_mode": "sidebar",
        "player_position": "top",
        "card_style": "rounded",
        "channel_columns": "auto",
        "dark_mode": True,
        "smart_engine": True,
        "auto_fallback": True,
        "proxy_first": False,
        "vlc_auto_fallback": True,
        "fast_zapping": True,
        "pwa": True,
        "custom_categories": {
            "Sport": [
                "ART SPORT", "SUPER SPORT", "TRING SPORT", "KUJTESA SPORT",
                "EUROSPORT", "FIGHT BOX", "FIGHTBOX"
            ]
        }
    }
    s = load_json_file(SETTINGS_FILE, default)
    for k, v in default.items():
        s.setdefault(k, v)
    return s


def save_settings(data):
    save_json_file(SETTINGS_FILE, data)


def log_event(event_type, client_slug="", channel="", status="", extra=None):
    try:
        row = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "client": client_slug,
            "channel": channel,
            "status": status,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "ua": request.headers.get("User-Agent", ""),
            "extra": extra or {}
        }
        with LOGS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_logs(limit=500):
    if not LOGS_FILE.exists():
        return []
    rows = []
    for line in LOGS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return list(reversed(rows))


def increment_channel_stat(slug, channel_name):
    stats = load_json_file(CHANNEL_STATS_FILE, {})
    key = f"{slug}::{channel_name}"
    stats[key] = stats.get(key, 0) + 1
    save_json_file(CHANNEL_STATS_FILE, stats)


def get_device_id():
    return request.cookies.get("nox_device_id") or str(uuid.uuid4())


def device_allowed(slug, client):
    max_devices = int(client.get("max_devices", 2) or 2)
    devices = load_json_file(DEVICE_FILE, {})
    used = devices.get(slug, {})
    did = get_device_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if did not in used and len(used) >= max_devices:
        return False, did, len(used), max_devices
    used[did] = {"last_seen": now, "ua": request.headers.get("User-Agent", "")[:180]}
    devices[slug] = used
    save_json_file(DEVICE_FILE, devices)
    return True, did, len(used), max_devices


def detect_device_type():
    ua = (request.headers.get("User-Agent", "") or "").lower()
    if "android" in ua:
        return "android"
    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "windows" in ua or "macintosh" in ua:
        return "pc"
    return "unknown"


# ---------------- Layouts ----------------

ADMIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>NOX IPTV V11.0</title>
  <style>

/* V11 responsive overflow fix */
html, body { max-width:100%; overflow-x:hidden !important; }
* { box-sizing:border-box; }
img, video, iframe, table { max-width:100%; }

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
  
/* V11 admin organized menu */
.admin-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}
.admin-group{background:#0f172a66;border:1px solid #334155;border-radius:18px;padding:12px}
.admin-group summary{cursor:pointer;font-weight:900;color:#e5e7eb;list-style:none}
.admin-group summary::-webkit-details-marker{display:none}
.admin-group .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.admin-searchbar{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.admin-searchbar input,.admin-searchbar select{background:#0b1220;border:1px solid #334155;border-radius:13px;color:white;padding:11px;min-width:210px}
.client-direct{font-size:12px;background:#0b1220;border:1px solid #334155;border-radius:12px;padding:9px;margin-top:8px;word-break:break-all;color:#cbd5e1}
.iconbtn{display:inline-flex;align-items:center;gap:6px}
@media(max-width:800px){.admin-groups{grid-template-columns:1fr}.admin-searchbar input,.admin-searchbar select{width:100%;min-width:0}}

</style>
</head>
<body>
  <div class="top">
    <div class="wrap">
      <h1>NOX IPTV Panel <span style="font-size:13px;background:#14b8a6;color:white;padding:4px 8px;border-radius:999px;">V11.0</span></h1>
      <p>Admin panel, Master Template, Backup/Restore, Client VLC portal, Native App API.</p>
      {% if logged %}
      <div class="nav">
        <a class="btn" href="/dashboard">Dashboard</a>
        <a class="btn" href="/template">Master Template</a>
        <a class="btn green" href="/add">Add Client</a>
        <a class="btn gray" href="/status">Status</a>
        <a class="btn gray" href="/servers">Server Templates</a>
        <a class="btn gray" href="/logs">Logs</a>
        <a class="btn gray" href="/analytics">Analytics</a>
        <a class="btn gray" href="/settings">Branding/Settings</a>
        <a class="btn gray" href="/bulk-refresh">Bulk Refresh</a>
        <a class="btn gray" href="/clear-cache">Clear Cache</a>
        <a class="btn dark" href="/backup">Backup All</a>
        <a class="btn dark" href="/auto-backup">Auto Backup</a>
        <a class="btn gray" href="/github-sync">GitHub Sync</a>
        <a class="btn dark" href="/restore">Restore</a>
        <a class="btn dark" href="/import-clients">Import Clients</a>
        <a class="btn gray" href="/export-template">Export Template</a>
        <a class="btn gray" href="/import-template">Import Template</a>
        <a class="btn dark" href="/export">Export Clients</a>
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
  <title>NOX IPTV V11.0</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/mpegts.js@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/mux.js@latest/dist/mux.min.js"></script>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="manifest" href="/manifest.json">
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
    .player { background:#111827; padding:12px; border-radius:16px; margin-bottom:14px; }
    video { width:100%; max-height:55vh; background:#000; border-radius:14px; margin-bottom:10px; }
    .now { font-weight:700; margin:8px 0; }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:10px; }
    .ch { background:#111827; border:1px solid #1f2937; border-radius:14px; padding:10px; cursor:pointer; }
    .ch:hover { border-color:#2563eb; }
    .logo { width:42px; height:42px; object-fit:contain; float:left; margin-right:10px; background:#fff1; border-radius:8px; }
    .name { font-size:14px; font-weight:700; min-height:38px; }
    .group { font-size:12px; color:#94a3b8; margin-top:6px; clear:both; }
    .hint { color:#94a3b8; font-size:13px; }
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



# ---------------- Server Templates ----------------

def load_server_templates():
    if SERVER_TEMPLATES_FILE.exists():
        try:
            data = json.loads(SERVER_TEMPLATES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass

    defaults = DEFAULT_SERVER_TEMPLATES if "DEFAULT_SERVER_TEMPLATES" in globals() else []
    if defaults:
        try:
            SERVER_TEMPLATES_FILE.write_text(json.dumps(defaults, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return defaults
    return []


def save_server_templates(servers):
    SERVER_TEMPLATES_FILE.write_text(json.dumps(servers, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        save_auto_backup()
    except Exception:
        pass


def server_slug(name, server):
    return slugify((name or server or "server")[:80])


def test_server_template(server, username="", password=""):
    server = normalize_base(server)
    parsed = urlparse(server)
    out = {
        "server": server,
        "host": parsed.hostname or "",
        "ip": resolve_ip(parsed.hostname or "") if parsed.hostname else "",
        "root_ok": False,
        "api_ok": False,
        "status": "",
        "expiry": "",
        "connections": "",
        "error": ""
    }
    try:
        r = requests.get(server, headers=HEADERS, timeout=12, allow_redirects=True)
        out["root_ok"] = r.status_code < 500
        out["root_status"] = r.status_code
    except Exception as e:
        out["root_error"] = str(e)

    if username and password:
        try:
            info = check_api_from_parts(server, username, password)
            out["api_ok"] = bool(info.get("ok"))
            out["status"] = info.get("status", "")
            out["expiry"] = info.get("expiry", "")
            out["connections"] = f"{info.get('active','?')}/{info.get('max','?')}"
            if not info.get("ok"):
                out["error"] = info.get("error", "")
        except Exception as e:
            out["api_ok"] = False
            out["error"] = str(e)
    return out




def client_direct_badge_html(slug, c):
    token = ensure_client_public_token(slug, c)
    direct_url = request.url_root.rstrip("/") + url_for("client_direct_login", slug=slug, token=token)
    enabled = c.get("public_enabled", False)
    status = "Direct ON" if enabled else "Direct OFF"
    color = "#16a34a" if enabled else "#64748b"
    return f"""
    <div class="client-direct">
      <b style="color:{color}">{status}</b><br>
      <span>{direct_url}</span><br>
      <a class="btn gray" href="/client-direct-toggle/{slug}">{"Disable Direct" if enabled else "Enable Direct"}</a>
      <a class="btn gray" href="/client-direct-reset/{slug}">Reset Link</a>
    </div>
    """


def admin_quick_groups_html():
    return """
    <div class="admin-searchbar">
      <input id="adminSearch" placeholder="🔎 Kërko klient, username, server..." oninput="adminFilterRows()">
      <select id="adminStatus" onchange="adminFilterRows()">
        <option value="">Të gjithë statuset</option>
        <option value="enabled">Aktiv</option>
        <option value="disabled">Disabled</option>
        <option value="direct">Direct link aktiv</option>
      </select>
    </div>
    <div class="admin-groups">
      <details class="admin-group" open>
        <summary>👥 Menaxhimi i klientëve</summary>
        <div class="row">
          <a class="btn green iconbtn" href="/add">➕ Add Client</a>
          <a class="btn gray iconbtn" href="/import-clients">⬆ Import Clients</a>
          <a class="btn gray iconbtn" href="/export-clients">⬇ Export Clients</a>
          <a class="btn gray iconbtn" href="/bulk-refresh">🔄 Bulk Refresh</a>
        </div>
      </details>
      <details class="admin-group">
        <summary>📺 Playlist & Server</summary>
        <div class="row">
          <a class="btn iconbtn" href="/template">📋 Master Template</a>
          <a class="btn gray iconbtn" href="/servers">🌐 Server Templates</a>
          <a class="btn gray iconbtn" href="/status">📡 Status</a>
          <a class="btn gray iconbtn" href="/clear-cache">🧹 Clear Cache</a>
        </div>
      </details>
      <details class="admin-group">
        <summary>📊 Analitika & Logs</summary>
        <div class="row">
          <a class="btn gray iconbtn" href="/analytics">📈 Analytics</a>
          <a class="btn gray iconbtn" href="/logs">🧾 Logs</a>
        </div>
      </details>
      <details class="admin-group">
        <summary>💾 Backup & Settings</summary>
        <div class="row">
          <a class="btn gray iconbtn" href="/backup">💾 Backup All</a>
          <a class="btn gray iconbtn" href="/auto-backup">⏰ Auto Backup</a>
          <a class="btn gray iconbtn" href="/restore">♻ Restore</a>
          <a class="btn gray iconbtn" href="/settings">🎨 Branding/Settings</a>
        </div>
      </details>
    </div>
    <script>
      function adminFilterRows(){
        const q=(document.getElementById('adminSearch')?.value||'').toLowerCase();
        const st=(document.getElementById('adminStatus')?.value||'').toLowerCase();
        document.querySelectorAll('[data-client-row]').forEach(row=>{
          const txt=(row.innerText||'').toLowerCase();
          let ok=!q || txt.includes(q);
          if(st==='enabled') ok=ok && txt.includes('enabled');
          if(st==='disabled') ok=ok && txt.includes('disabled');
          if(st==='direct') ok=ok && txt.includes('direct on');
          row.style.display=ok?'':'none';
        });
      }
      document.querySelectorAll('a[href*="/delete"]').forEach(a=>{
        a.addEventListener('click', e=>{
          if(!confirm('A je i sigurt që dëshiron ta fshish?')) e.preventDefault();
        });
      });
    </script>
    """


# ---------------- Admin routes ----------------

@app.route("/admin-login", methods=["GET", "POST"])

@app.route("/")
def public_home():
    return """
    <!doctype html>
    <html lang="sq">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>NOX IPTV V11.0</title>
      <meta name="theme-color" content="#050816">
      <style>
        *{box-sizing:border-box}
        body{margin:0;min-height:100vh;font-family:Inter,Arial,sans-serif;background:#050816;color:#f8fafc;overflow-x:hidden}
        body:before{content:"";position:fixed;inset:-20%;background:
          radial-gradient(circle at 16% 18%,#0ea5e966,transparent 28%),
          radial-gradient(circle at 78% 12%,#8b5cf666,transparent 30%),
          radial-gradient(circle at 48% 92%,#22c55e44,transparent 32%);filter:blur(35px);z-index:-2;animation:bg 10s ease-in-out infinite alternate}
        body:after{content:"";position:fixed;inset:0;background:linear-gradient(180deg,#050816aa,#050816 75%);z-index:-1}
        @keyframes bg{from{transform:scale(1)}to{transform:scale(1.06) translateY(-18px)}}
        .nav{max-width:1180px;margin:auto;padding:22px;display:flex;justify-content:space-between;align-items:center}
        .logo{display:flex;align-items:center;gap:12px;font-weight:1000;font-size:25px;letter-spacing:-.4px}.logo img{width:52px;height:52px;border-radius:18px;box-shadow:0 14px 42px #0009}
        .pill{border:1px solid #334155;background:#0f172acc;border-radius:999px;padding:10px 14px;color:#cbd5e1;text-decoration:none;font-size:13px}
        .hero{max-width:1180px;margin:36px auto 0;padding:22px;display:grid;grid-template-columns:1.08fr .92fr;gap:34px;align-items:center}
        h1{font-size:clamp(44px,7vw,88px);line-height:.9;margin:0;font-weight:1000;letter-spacing:-3px}
        h1 span{background:linear-gradient(90deg,#38bdf8,#a78bfa,#22c55e);-webkit-background-clip:text;color:transparent}
        .lead{font-size:19px;color:#b8c5d7;line-height:1.7;max-width:690px;margin:24px 0}
        .actions{display:flex;gap:16px;flex-wrap:wrap;margin-top:30px}
        .bigbtn{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-width:245px;padding:20px 28px;border-radius:25px;text-decoration:none;font-weight:1000;font-size:18px;box-shadow:0 18px 48px #0009;transition:.16s}
        .bigbtn:hover{transform:translateY(-3px);filter:brightness(1.08)}
        .client{background:linear-gradient(135deg,#0ea5e9,#2563eb,#7c3aed);color:white}.admin{background:#0f172acc;border:1px solid #334155;color:#f8fafc}
        .showcase{background:linear-gradient(180deg,#0f172a,#020617);border:1px solid #26324a;border-radius:38px;padding:18px;box-shadow:0 35px 90px #000c;position:relative;overflow:hidden}
        .screen{height:330px;border-radius:28px;background:linear-gradient(135deg,#111827,#020617);border:1px solid #334155;display:flex;align-items:center;justify-content:center;position:relative}
        .screen:after{content:"LIVE";position:absolute;right:18px;top:18px;background:#22c55e;color:white;border-radius:999px;padding:7px 11px;font-size:12px;font-weight:900}
        .play{width:94px;height:94px;border-radius:32px;background:#ffffff18;display:flex;align-items:center;justify-content:center}.play:after{content:"";border-left:31px solid white;border-top:20px solid transparent;border-bottom:20px solid transparent;margin-left:8px}
        .tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}.tile{background:#111827;border:1px solid #26324a;border-radius:22px;padding:15px}.tile span{font-size:12px;color:#94a3b8}
        .features{max-width:1180px;margin:44px auto;padding:22px;display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.feature{background:#0f172acc;border:1px solid #26324a;border-radius:26px;padding:20px;transition:.16s}.feature:hover{transform:translateY(-3px);border-color:#38bdf8}.feature h3{margin:0 0 9px}.feature p{margin:0;color:#94a3b8;line-height:1.55}
        footer{max-width:1180px;margin:auto;padding:26px 22px 45px;color:#64748b;font-size:13px}
        @media(max-width:900px){.hero{grid-template-columns:1fr;margin-top:12px}.features{grid-template-columns:1fr}.tiles{grid-template-columns:1fr}.actions .bigbtn{width:100%}.screen{height:220px}.pill{display:none}h1{letter-spacing:-1.5px}}
      </style>
    </head>
    <body>
      <nav class="nav"><div class="logo"><img src="/static/nox_logo.svg" onerror="this.style.display='none'"><span>NOX IPTV</span></div><a class="pill" href="/watch">Client Portal</a></nav>
      <section class="hero">
        <div>
          <h1>Premium IPTV <span>experience</span> për çdo pajisje.</h1>
          <p class="lead">Platformë moderne për klientët e tu: hyrje e mbrojtur, kategori të pastra, favorite, PC browser mode dhe hapje direkte në VLC për iPhone/Android.</p>
          <div class="actions">
            <a class="bigbtn client" href="/watch">▶ KYQU SI KLIENT</a>
            <a class="bigbtn admin" href="/login">⚙ ADMIN</a>
          </div>
        </div>
        <div class="showcase">
          <div class="screen"><div class="play"></div></div>
          <div class="tiles">
            <div class="tile"><b>Sport</b><br><span>ART, Super Sport, Tring</span></div>
            <div class="tile"><b>Favorites</b><br><span>Kanalet e preferuara</span></div>
            <div class="tile"><b>PC Mode</b><br><span>Shikim nga browseri</span></div>
          </div>
        </div>
      </section>
      <section class="features">
        <div class="feature"><h3>⚡ Fast access</h3><p>Navigim i shpejtë dhe hapje direkte në app.</p></div>
        <div class="feature"><h3>📱 Mobile first</h3><p>Dizajn i veçantë për telefon, jo desktop i zvogëluar.</p></div>
        <div class="feature"><h3>💻 PC mode</h3><p>Desktop shikon direkt në browser.</p></div>
        <div class="feature"><h3>🔐 Private</h3><p>Admin panel i mbrojtur me password.</p></div>
      </section>
      <footer>© NOX IPTV — premium private IPTV portal.</footer>
    </body>
    </html>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        error = "Password gabim."
    body = f"""
    <div class="card" style="max-width:480px;margin:50px auto;">
      <h2>Admin Login</h2>
      <form method="post">
        <input type="password" name="password" placeholder="Admin password">
        <button>Login</button>
      </form>
      <p class="bad">{error}</p>
      <p class="small">Client portal: <code>/watch</code></p>
    </div>
    """
    return admin_page(body)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/login")




@app.route("/dashboard")
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
        public_url = request.url_root.rstrip("/") + url_for("playlist_alias_for_vlc", slug=slug)
        watch_url = request.url_root.rstrip("/") + "/watch"
        mode = c.get("mode", "source_link")
        fav = "★ " if c.get("favorite") else ""
        rows += f"""
        <tr data-client-row>
          <td><b>{fav}{c.get('name')}</b><br><span class="small">{slug}</span><br><span class="small">{c.get('client_note','')}</span></td>
          <td><code>{public_url}</code><br><span class="small">VLC portal: <code>{watch_url}</code></span></td>
          <td>{mode}</td>
          <td>{c.get('output','ts')}</td>
          <td>{c.get('last_channels','-')}</td>
          <td>{c.get('last_update','-')}</td>
          <td>
            <a class="btn gray" href="/check/{slug}">Check</a>
            <a class="btn green" href="/refresh/{slug}">Refresh</a>
            <a class="btn" href="/edit/{slug}">Edit</a>
            <a class="btn gray" href="/duplicate/{slug}">Duplicate</a>
            <a class="btn gray" href="/toggle/{slug}">Enable/Disable</a>
            <a class="btn dark" href="/download/{slug}">Download</a>
            <a class="btn gray" href="/p/{slug}.m3u">Open</a>
            <a class="btn red" href="/delete/{slug}" onclick="return confirm('Delete?')">Delete</a>
          </td>
        </tr>
        """
    body = f"""
    {stat_html}
    <div class="card" data-client-row>
      <h2>Clients</h2>
      <p class="small">Use Backup All often on Render Free. Health URL for uptime monitor: <code>{request.url_root.rstrip()}/health</code></p>
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
            msg = "<p class='ok'>Master template u ruajt si favourite. Cache u pastrua.</p>"

    text = get_template_text()
    stats = template_stats(text) if text else {"channels":0, "groups":0, "top_groups":[]}
    groups = "".join(f"<li>{g}: <b>{c}</b></li>" for g,c in stats.get("top_groups", []))
    body = f"""
    <div class="grid">
      <div class="stat"><div class="num">{stats['channels']}</div><div class="label">Channels</div></div>
      <div class="stat"><div class="num">{stats['groups']}</div><div class="label">Groups</div></div>
    </div>
    <div class="card">
      <h2>★ Favourite Master Template</h2>
      <form method="post">
        <textarea name="template_text" rows="24" placeholder="#EXTM3U...">{text}</textarea>
        <button>Save Favourite Master Template</button>
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
            "client_note": request.form.get("client_note", "").strip(),
            "favorite": request.form.get("favorite") == "on",
            "enabled": request.form.get("enabled") == "on",
            "max_devices": int(request.form.get("max_devices", "2") or 2),
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

        <label><input style="width:auto" type="checkbox" name="allow_watch" {"checked" if client.get("allow_watch", True) else ""}> Allow client portal / direct VLC</label><br>
        <label><input style="width:auto" type="checkbox" name="favorite" {"checked" if client.get("favorite", False) else ""}> Mark as favourite</label><br>
        <label><input style="width:auto" type="checkbox" name="enabled" {"checked" if client.get("enabled", True) else ""}> Client enabled</label><br>
        <label>Device limit</label>
        <input name="max_devices" type="number" min="1" max="10" value="{client.get('max_devices',2)}"><br>

        <label>Private note for this client</label>
        <input name="client_note" value="{client.get('client_note','')}" placeholder="p.sh. Gjermani, Samsung TV, skadon...">

        <label>Mode</label>
        <select name="mode">
          <option value="source_link" {"selected" if mode=="source_link" else ""}>Source M3U link individual</option>
          <option value="template" {"selected" if mode=="template" else ""}>Use Master Template - only host/user/pass changes</option>
        </select>

        <div class="grid">
          <div class="card">
            <h3>Template mode</h3>
            <label>Server Template</label>
            <select name="server_template_select" onchange="document.querySelector('[name=server]').value=this.value">
              <option value="">Mos ndrysho / manual</option>
              {''.join(f'<option value="{s.get("server","")}">{s.get("name","Server")} - {s.get("server","")}</option>' for s in load_server_templates())}
            </select>

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


@app.route("/duplicate/<slug>")
def duplicate_client(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        abort(404)
    new_slug = slugify(slug + "-copy")
    i = 2
    while new_slug in clients:
        new_slug = slugify(slug + f"-copy-{i}")
        i += 1
    new_client = dict(c)
    new_client["name"] = c.get("name", slug) + " Copy"
    new_client["portal_user"] = new_slug
    new_client["portal_password"] = "1234"
    new_client["created"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_client["last_update"] = None
    new_client["last_channels"] = None
    clients[new_slug] = new_client
    save_clients(clients)
    return redirect(f"/edit/{new_slug}")



@app.route("/toggle/<slug>")
def toggle_client(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        abort(404)
    c["enabled"] = not c.get("enabled", True)
    clients[slug] = c
    save_clients(clients)
    return redirect("/")


@app.route("/servers", methods=["GET", "POST"])
def servers_page():
    if not login_required():
        return redirect("/login")

    servers = load_server_templates()
    msg = ""

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add":
            name = request.form.get("name", "").strip()
            server = normalize_base(request.form.get("server", "").strip())
            note = request.form.get("note", "").strip()
            if server:
                sid = server_slug(name, server)
                servers.append({
                    "id": sid + "-" + str(int(time.time())),
                    "name": name or server,
                    "server": server,
                    "note": note,
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_server_templates(servers)
                msg = "<p class='ok'>Server template u shtua.</p>"
        elif action == "bulk":
            raw = request.form.get("bulk_servers", "")
            added = 0
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    name, server = [x.strip() for x in line.split("|", 1)]
                else:
                    server = line
                    name = server
                server = normalize_base(server)
                if server:
                    servers.append({
                        "id": server_slug(name, server) + "-" + str(int(time.time())) + "-" + str(added),
                        "name": name,
                        "server": server,
                        "note": "",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    added += 1
            save_server_templates(servers)
            msg = f"<p class='ok'>{added} serverë u shtuan.</p>"

    rows = ""
    clients = load_clients()
    client_options = "".join(f'<option value="{slug}">{c.get("name", slug)} ({slug})</option>' for slug, c in sorted(clients.items()))

    for s in servers:
        sid = s.get("id", "")
        rows += f"""
        <tr>
          <td><b>{s.get('name')}</b><br><span class="small">{s.get('note','')}</span></td>
          <td><code>{s.get('server')}</code></td>
          <td>{s.get('created','')}</td>
          <td>
            <a class="btn gray" href="/servers/test/{sid}">Test</a>
            <form method="post" action="/servers/apply/{sid}" style="display:inline-block;min-width:260px;">
              <select name="client_slug" style="width:180px;display:inline-block;">{client_options}</select>
              <button class="btn green">Apply to client</button>
            </form>
            <a class="btn red" href="/servers/delete/{sid}" onclick="return confirm('Delete server?')">Delete</a>
          </td>
        </tr>
        """

    body = f"""
    <div class="card">
      <h2>Server Templates</h2>
      <p><a class="btn green" href="/servers/test-all">TEST ALL</a></p>
      <p class="small">Këtu i ruan serverët si template, i teston, dhe pastaj zgjedh cilit klient t'ia vendosësh.</p>
      {msg}
      <form method="post">
        <input type="hidden" name="action" value="add">
        <label>Emri</label>
        <input name="name" placeholder="p.sh. Server 1 Germany">
        <label>Server/Host</label>
        <input name="server" placeholder="http://host.com:80">
        <label>Shënim</label>
        <input name="note" placeholder="opsionale">
        <button>Add Server Template</button>
      </form>
    </div>

    <div class="card">
      <h3>Bulk Add</h3>
      <p class="small">Një server për rresht. Format: <code>Emri | http://host:port</code> ose vetëm <code>http://host:port</code></p>
      <form method="post">
        <input type="hidden" name="action" value="bulk">
        <textarea name="bulk_servers" rows="7" placeholder="Server 1 | http://host1.com:80&#10;Server 2 | http://host2.com:8080"></textarea>
        <button>Add Bulk Servers</button>
      </form>
    </div>

    <div class="card">
      <h3>Saved Servers</h3>
      <table>
        <tr><th>Name</th><th>Server</th><th>Created</th><th>Actions</th></tr>
        {rows or '<tr><td colspan="4">Ende nuk ka serverë.</td></tr>'}
      </table>
    </div>
    """
    return admin_page(body)


@app.route("/servers/delete/<sid>")
def server_delete(sid):
    if not login_required():
        return redirect("/login")
    servers = [s for s in load_server_templates() if s.get("id") != sid]
    save_server_templates(servers)
    return redirect("/servers")



@app.route("/servers/test-all")
def servers_test_all():
    if not login_required():
        return redirect("/login")

    servers = load_server_templates()
    clients = load_clients()

    # Choose credentials from selected client if provided, otherwise first client with username/password.
    selected_slug = request.args.get("client_slug", "")
    selected_client = clients.get(selected_slug) if selected_slug else None
    if not selected_client:
        selected_client = None
        for _slug, _c in sorted(clients.items()):
            if _c.get("username") and _c.get("password"):
                selected_slug = _slug
                selected_client = _c
                break
            try:
                p = parse_m3u_link(_c.get("m3u_link", ""))
                selected_slug = _slug
                selected_client = dict(_c)
                selected_client["username"] = p["username"]
                selected_client["password"] = p["password"]
                break
            except Exception:
                pass

    username = ""
    password = ""
    client_name = "-"
    if selected_client:
        client_name = selected_client.get("name", selected_slug)
        username = selected_client.get("username", "")
        password = selected_client.get("password", "")
        if not username or not password:
            try:
                p = parse_m3u_link(selected_client.get("m3u_link", ""))
                username = p["username"]
                password = p["password"]
            except Exception:
                pass

    results = []
    for s in servers:
        r = test_server_template(s.get("server"), username, password)
        r["id"] = s.get("id")
        r["name"] = s.get("name")
        r["note"] = s.get("note", "")
        results.append(r)

    ok_count = sum(1 for r in results if r.get("api_ok") or r.get("root_ok"))
    rows = ""
    for r in results:
        ok = bool(r.get("api_ok") or r.get("root_ok"))
        cls = "ok" if ok else "bad"
        badge = "KALON" if ok else "NUK KALON"
        rows += f"""
        <tr style="background:{'#dcfce7' if ok else '#fee2e2'}">
          <td><b>{r.get('name')}</b><br><span class="small">{r.get('note','')}</span></td>
          <td><code>{r.get('server')}</code></td>
          <td class="{cls}"><b>{badge}</b></td>
          <td>{r.get('status','')}</td>
          <td>{r.get('expiry','')}</td>
          <td>{r.get('connections','')}</td>
          <td>{r.get('ip','')}</td>
          <td><a class="btn gray" href="/servers/test/{r.get('id')}">Details</a></td>
        </tr>
        """

    client_options = "".join(
        f'<option value="{slug}" {"selected" if slug == selected_slug else ""}>{c.get("name", slug)} ({slug})</option>'
        for slug, c in sorted(clients.items())
    )

    body = f"""
    <div class="card">
      <h2>TEST ALL Server Templates</h2>
      <p class="small">Testuar me klientin: <b>{client_name}</b>. Kaluan: <b>{ok_count}/{len(results)}</b></p>
      <form method="get" action="/servers/test-all">
        <label>Zgjedh klientin për username/password test</label>
        <select name="client_slug">{client_options}</select>
        <button>Test All Again</button>
        <a class="btn gray" href="/servers">Back</a>
      </form>
    </div>
    <div class="card">
      <table>
        <tr><th>Name</th><th>Server</th><th>Result</th><th>Status</th><th>Expiry</th><th>Conn</th><th>IP</th><th>Details</th></tr>
        {rows or '<tr><td colspan="8">Nuk ka serverë.</td></tr>'}
      </table>
    </div>
    """
    return admin_page(body)


@app.route("/servers/test/<sid>")
def server_test(sid):
    if not login_required():
        return redirect("/login")
    servers = load_server_templates()
    server = next((s for s in servers if s.get("id") == sid), None)
    if not server:
        abort(404)

    clients = load_clients()
    results = []
    for slug, c in sorted(clients.items()):
        username = c.get("username") or ""
        password = c.get("password") or ""
        if not username or not password:
            try:
                p = parse_m3u_link(c.get("m3u_link", ""))
                username = p["username"]
                password = p["password"]
            except Exception:
                pass
        if username and password:
            res = test_server_template(server.get("server"), username, password)
            res["client"] = c.get("name", slug)
            res["slug"] = slug
            results.append(res)

    if not results:
        res = test_server_template(server.get("server"))
        results.append(res)

    rows = ""
    for r in results:
        cls = "ok" if r.get("api_ok") or r.get("root_ok") else "bad"
        rows += f"""
        <tr>
          <td>{r.get('client','-')}<br><span class="small">{r.get('slug','')}</span></td>
          <td class="{cls}">{'OK' if cls == 'ok' else 'Problem'}</td>
          <td>{r.get('status','')}</td>
          <td>{r.get('expiry','')}</td>
          <td>{r.get('connections','')}</td>
          <td>{r.get('ip','')}</td>
          <td><pre>{json.dumps(r, ensure_ascii=False, indent=2)}</pre></td>
        </tr>
        """

    body = f"""
    <div class="card">
      <h2>Test Server: {server.get('name')}</h2>
      <p>Server: <code>{server.get('server')}</code></p>
      <a class="btn gray" href="/servers">Back</a>
      <table>
        <tr><th>Client</th><th>Root/API</th><th>Status</th><th>Expiry</th><th>Conn</th><th>IP</th><th>Raw</th></tr>
        {rows}
      </table>
    </div>
    """
    return admin_page(body)


@app.route("/servers/apply/<sid>", methods=["POST"])
def server_apply(sid):
    if not login_required():
        return redirect("/login")
    client_slug = request.form.get("client_slug")
    servers = load_server_templates()
    server = next((s for s in servers if s.get("id") == sid), None)
    if not server or not client_slug:
        abort(404)

    clients = load_clients()
    c = clients.get(client_slug)
    if not c:
        abort(404)

    new_server = normalize_base(server.get("server"))
    c["server"] = new_server

    if c.get("mode") != "template":
        try:
            p = parse_m3u_link(c.get("m3u_link", ""))
            c["username"] = p["username"]
            c["password"] = p["password"]
        except Exception:
            pass
        c["mode"] = "template"

    if c.get("username") and c.get("password"):
        c["m3u_link"] = f"{new_server.rstrip('/')}/get.php?username={c.get('username')}&password={c.get('password')}&type=m3u_plus&output={c.get('output','ts')}"

    clients[client_slug] = c
    save_clients(clients)
    cp = cache_path(client_slug)
    if cp.exists():
        cp.unlink()
    return redirect(f"/edit/{client_slug}")


@app.route("/status")
def status_page():
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    rows = ""
    for slug, c in sorted(clients.items()):
        try:
            if c.get("mode") == "template":
                info = check_api_from_parts(c.get("server"), c.get("username"), c.get("password"), client=c)
            else:
                info = check_api_from_link(c["m3u_link"], client=c)
            cls = "ok" if info.get("ok") and str(info.get("status")).lower() == "active" else "bad"
            rows += f"<tr><td>{c.get('name')}</td><td>{slug}</td><td class='{cls}'>{info.get('status','?')}</td><td>{info.get('expiry','?')}</td><td>{info.get('active','?')}/{info.get('max','?')}</td><td>{info.get('host','')}</td></tr>"
        except Exception as e:
            rows += f"<tr><td>{c.get('name')}</td><td>{slug}</td><td class='bad'>ERROR</td><td colspan='3'>{e}</td></tr>"
    body = f"""
    <div class="card">
      <h2>All Client Status</h2>
      <table>
        <tr><th>Client</th><th>Slug</th><th>Status</th><th>Expiry</th><th>Connections</th><th>Host</th></tr>
        {rows}
      </table>
    </div>
    """
    return admin_page(body)


@app.route("/export")
def export_json():
    if not login_required():
        return redirect("/login")
    data = json.dumps(load_clients(), ensure_ascii=False, indent=2)
    return Response(data, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=clients_export.json"})



@app.route("/import-clients", methods=["GET", "POST"])
def import_clients():
    if not login_required():
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        try:
            raw = request.form.get("clients_json", "").strip()
            uploaded = request.files.get("clients_file")
            if uploaded and uploaded.filename:
                raw = uploaded.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            clients = data.get("clients", data)
            if not isinstance(clients, dict):
                raise ValueError("Clients JSON nuk është valid.")
            save_clients(clients)
            clear_all_cache()
            msg = "<p class='ok'>Clients u importuan me sukses.</p>"
        except Exception as e:
            msg = f"<p class='bad'>Import problem: {e}</p>"
    body = f"""
    <div class="card">
      <h2>Import Clients</h2>
      {msg}
      <form method="post" enctype="multipart/form-data">
        <label>Upload clients/backup JSON</label>
        <input type="file" name="clients_file" accept=".json">
        <label>OSE paste JSON</label>
        <textarea name="clients_json" rows="16" placeholder="{{...}}"></textarea>
        <button>Import Clients</button>
      </form>
    </div>
    """
    return admin_page(body)



@app.route("/auto-backup")
def auto_backup_download():
    if not login_required():
        return redirect("/login")
    save_auto_backup()
    if AUTO_BACKUP_FILE.exists():
        return Response(
            AUTO_BACKUP_FILE.read_text(encoding="utf-8"),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=noxiptv_backup.json"}
        )
    return Response("{}", mimetype="application/json")

@app.route("/github-sync")
def github_sync_now():
    if not login_required():
        return redirect("/login")
    data = build_full_backup()
    github_auto_sync(data)
    return admin_page("<div class='card'><h2>GitHub Sync</h2><p class='ok'>Sync u provua. Kontrollo GitHub file-in noxiptv_backup.json.</p></div>")


@app.route("/backup")
def backup_all():
    if not login_required():
        return redirect("/login")
    data = {
        "version": API_VERSION,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clients": load_clients(),
        "master_template": get_template_text(),
        "server_templates": load_server_templates(),
        "note": "Backup contains clients, master template and server templates. Keep private."
    }
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=noxiptv_backup.json"}
    )


@app.route("/restore", methods=["GET", "POST"])
def restore_backup():
    if not login_required():
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        try:
            raw = request.form.get("backup_json", "").strip()
            uploaded = request.files.get("backup_file")
            if uploaded and uploaded.filename:
                raw = uploaded.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            clients = data.get("clients", {})
            master_template = data.get("master_template", "")
            server_templates = data.get("server_templates", [])
            if not isinstance(clients, dict):
                raise ValueError("Backup clients nuk është valid.")
            if master_template and "#EXTM3U" not in master_template[:1000]:
                raise ValueError("Master template nuk duket valid.")
            save_clients(clients)
            if master_template:
                save_template_text(master_template)
            if isinstance(server_templates, list):
                save_server_templates(server_templates)
            clear_all_cache()
            msg = "<p class='ok'>Restore u krye me sukses. Cache u pastrua.</p>"
        except Exception as e:
            msg = f"<p class='bad'>Restore problem: {e}</p>"
    body = f"""
    <div class="card">
      <h2>Restore Backup</h2>
      {msg}
      <form method="post" enctype="multipart/form-data">
        <label>Upload backup JSON</label>
        <input type="file" name="backup_file" accept=".json">
        <label>OSE paste backup JSON</label>
        <textarea name="backup_json" rows="16" placeholder="{{...}}"></textarea>
        <button>Restore</button>
      </form>
    </div>
    """
    return admin_page(body)


@app.route("/export-template")
def export_template():
    if not login_required():
        return redirect("/login")
    text = get_template_text()
    return Response(
        text,
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": "attachment; filename=master_template.m3u"}
    )


@app.route("/import-template", methods=["GET", "POST"])
def import_template():
    if not login_required():
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        try:
            raw = request.form.get("template_text", "")
            uploaded = request.files.get("template_file")
            if uploaded and uploaded.filename:
                raw = uploaded.read().decode("utf-8", errors="ignore")
            if "#EXTM3U" not in raw[:1000]:
                raise ValueError("Template nuk duket M3U valid.")
            save_template_text(raw)
            clear_all_cache()
            msg = "<p class='ok'>Template u importua dhe u ruajt si favourite/master.</p>"
        except Exception as e:
            msg = f"<p class='bad'>Import problem: {e}</p>"
    body = f"""
    <div class="card">
      <h2>Import Master Template</h2>
      {msg}
      <form method="post" enctype="multipart/form-data">
        <label>Upload M3U/TXT template</label>
        <input type="file" name="template_file" accept=".m3u,.txt">
        <label>OSE paste template</label>
        <textarea name="template_text" rows="18" placeholder="#EXTM3U..."></textarea>
        <button>Import Template</button>
      </form>
    </div>
    """
    return admin_page(body)


@app.route("/p/<slug>.m3u")
def playlist(slug):
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        return Response(text, mimetype="audio/x-mpegurl")
    except Exception as e:
        return Response(f"#EXTM3U\n# ERROR: {e}\n", mimetype="text/plain", status=500)


# ---------------- Client Portal Direct VLC ----------------

@app.route("/watch", methods=["GET", "POST"])
def watch_login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        clients = load_clients()
        for slug, c in clients.items():
            if not c.get("allow_watch", True) or not c.get("enabled", True):
                continue
            if c.get("portal_user") == u and c.get("portal_password") == p:
                ok, did, used, maxd = device_allowed(slug, c)
                if not ok:
                    log_event("login_blocked_device_limit", slug, status="blocked", extra={"used": used, "max": maxd})
                    return client_page(f"""
                    <div class="top"><h2>NOX IPTV</h2></div>
                    <div class="wrap"><div class="player"><p style="color:#fca5a5">Device limit arritur: {used}/{maxd}</p><a class="btn" href="/watch">Kthehu</a></div></div>
                    """)
                session["client_slug"] = slug
                log_event("login", slug, status="ok", extra={"device": did, "device_type": detect_device_type()})
                resp = redirect("/watch/home")
                resp.set_cookie("nox_device_id", did, max_age=60*60*24*365)
                return resp
        return client_page("""
        <div class="top"><h2>NOX IPTV VLC Portal</h2></div>
        <div class="wrap"><div class="player"><p style="color:#fca5a5">Login gabim.</p><a class="btn" href="/watch">Provo prapë</a></div></div>
        """)
    body = """
    <div class="top"><h2>NOX IPTV VLC Portal</h2></div>
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








@app.route("/c/<slug>/<int:channel_id>.m3u")
def single_channel_playlist(slug, channel_id):
    """Clean single-channel M3U for VLC."""
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
        if channel_id < 0 or channel_id >= len(items):
            return Response("#EXTM3U\n# ERROR: channel not found\n", mimetype="audio/x-mpegurl", status=404)
        it = items[channel_id]
        name = it.get("name", "Channel")
        group = it.get("group", "")
        url = it.get("url", "")
        body = "#EXTM3U\n"
        body += f'#EXTINF:-1 tvg-name="{name}" group-title="{group}",{name}\n'
        body += f"{url}\n"
        return Response(
            body,
            mimetype="audio/x-mpegurl",
            headers={
                "Content-Type": "audio/x-mpegurl; charset=utf-8",
                "Content-Disposition": f"inline; filename={slug}-{channel_id}.m3u",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        return Response(f"#EXTM3U\n# ERROR: {e}\n", mimetype="audio/x-mpegurl", status=500)







def build_proxy_playlist_for_client(slug):
    """
    Build M3U where every stream URL points to NOX proxy.
    VLC/browser then use the same relay engine instead of direct provider URLs.
    """
    text = get_playlist_for_client(slug, force_refresh=False)
    items = parse_m3u_items(text)
    base = request.url_root.rstrip("/")
    lines = ["#EXTM3U"]
    for idx, it in enumerate(items):
        extinf = it.get("extinf") or f'#EXTINF:-1,{it.get("name","Channel")}'
        lines.append(extinf)
        lines.append(f"{base}/proxy/{slug}/{idx}")
    return "\n".join(lines) + "\n"



def b64url_encode_text(s):
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


def b64url_decode_text(s):
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii")).decode("utf-8")


def make_hls_candidate_url(stream_url):
    """
    Try common Xtream HLS form:
    http://host/user/pass/id  -> http://host/live/user/pass/id.m3u8
    http://host/live/user/pass/id.ts -> http://host/live/user/pass/id.m3u8
    """
    try:
        p = urlparse(stream_url)
        parts = [x for x in p.path.split("/") if x]
        if len(parts) >= 4 and parts[0] == "live":
            user, pwd, sid = parts[1], parts[2], parts[3]
            sid = sid.replace(".ts", "").replace(".m3u8", "")
            return urlunparse((p.scheme, p.netloc, f"/live/{user}/{pwd}/{sid}.m3u8", "", "", ""))
        if len(parts) >= 3:
            user, pwd, sid = parts[0], parts[1], parts[2]
            sid = sid.replace(".ts", "").replace(".m3u8", "")
            return urlunparse((p.scheme, p.netloc, f"/live/{user}/{pwd}/{sid}.m3u8", "", "", ""))
    except Exception:
        pass
    return stream_url


@app.route("/browser/hls/<slug>/<int:channel_id>")
def browser_hls_manifest(slug, channel_id):
    """
    Browser-only HLS manifest proxy/rewrite.
    This helps iPhone Safari when provider supports HLS but original list gives TS.
    """
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
        if channel_id < 0 or channel_id >= len(items):
            return Response("#EXTM3U\n# ERROR: channel not found\n", mimetype="application/vnd.apple.mpegurl", status=404)

        original = items[channel_id]["url"]
        candidates = []
        if ".m3u8" in original.lower():
            candidates.append(original)
        candidates.append(make_hls_candidate_url(original))
        candidates.append(original)

        headers = {
            "User-Agent": "VLC/3.0.20 LibVLC/3.0.20 NOXIPTV",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
        }

        last_error = ""
        resp = None
        for cand in candidates:
            try:
                r = requests.get(cand, headers=headers, timeout=(8, 16), allow_redirects=True)
                sample = r.text[:500] if r.text else ""
                if r.status_code < 400 and "#EXTM3U" in sample:
                    resp = r
                    break
                last_error = f"{cand} -> {r.status_code}"
            except Exception as e:
                last_error = f"{cand} -> {e}"

        if resp is None:
            return Response(f"#EXTM3U\n# ERROR: HLS not available. {last_error}\n", mimetype="application/vnd.apple.mpegurl", status=502)

        base_url = resp.url
        out = []
        for line in resp.text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                # Also rewrite URI="key" attributes if present
                if 'URI="' in line:
                    def repl_key(m):
                        key_url = urljoin(base_url, m.group(1))
                        return 'URI="' + url_for("browser_hls_asset", encoded=b64url_encode_text(key_url)) + '"'
                    line = re.sub(r'URI="([^"]+)"', repl_key, line)
                out.append(line)
            else:
                abs_url = urljoin(base_url, s)
                out.append(url_for("browser_hls_asset", encoded=b64url_encode_text(abs_url)))
        return Response(
            "\n".join(out) + "\n",
            mimetype="application/vnd.apple.mpegurl",
            headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        return Response(f"#EXTM3U\n# ERROR: {e}\n", mimetype="application/vnd.apple.mpegurl", status=500)


@app.route("/browser/hls-asset/<encoded>")
def browser_hls_asset(encoded):
    """
    HLS segment/key proxy.
    """
    try:
        asset_url = b64url_decode_text(encoded)
        headers = {
            "User-Agent": "VLC/3.0.20 LibVLC/3.0.20 NOXIPTV",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
        }
        upstream = requests.get(asset_url, headers=headers, stream=True, timeout=(8, None), allow_redirects=True)
        content_type = upstream.headers.get("Content-Type", "video/mp2t")
        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                try:
                    upstream.close()
                except Exception:
                    pass
        return Response(
            stream_with_context(generate()),
            mimetype=content_type,
            headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*", "X-Accel-Buffering": "no"},
            direct_passthrough=True,
        )
    except Exception as e:
        return Response(f"HLS asset error: {e}", status=500)


@app.route("/proxy/<slug>/<int:channel_id>")
def proxy_channel(slug, channel_id):
    """
    Public proxy stream for VLC playlist.
    It relays the real provider stream with VLC-friendly headers.
    """
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
        if channel_id < 0 or channel_id >= len(items):
            return Response("Channel not found", status=404)

        stream_url = items[channel_id]["url"]
        upstream_headers = {
            "User-Agent": "VLC/3.0.20 LibVLC/3.0.20 NOXIPTV",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
            "Icy-MetaData": "0",
        }

        last_error = None
        upstream = None
        for _attempt in range(3):
            try:
                upstream = requests.get(
                    stream_url,
                    headers=upstream_headers,
                    stream=True,
                    timeout=(10, None),
                    allow_redirects=True,
                )
                if upstream.status_code < 500:
                    break
            except Exception as e:
                last_error = e
                upstream = None
                time.sleep(0.7)

        if upstream is None:
            return Response(f"Proxy upstream error: {last_error}", status=502)

        content_type = upstream.headers.get("Content-Type", "video/mp2t")
        low = content_type.lower()
        if "text" in low or "html" in low:
            content_type = "video/mp2t"

        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                try:
                    upstream.close()
                except Exception:
                    pass

        return Response(
            stream_with_context(generate()),
            mimetype=content_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
            direct_passthrough=True,
        )
    except Exception as e:
        return Response(f"Proxy error: {e}", status=500)


@app.route("/vlc-list/<slug>.m3u")
@app.route("/playlist/<slug>.m3u")
def playlist_alias_for_vlc(slug):
    """
    VLC-friendly full playlist with PROXY stream URLs.
    This is the key V7.8 change.
    """
    try:
        text = build_proxy_playlist_for_client(slug)
        return Response(
            text,
            mimetype="audio/x-mpegurl",
            headers={
                "Content-Type": "audio/x-mpegurl; charset=utf-8",
                "Content-Disposition": f"inline; filename={slug}-proxy.m3u",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        return Response(f"#EXTM3U\n# ERROR: {e}\n", mimetype="audio/x-mpegurl", status=500)


@app.route("/vlc/iphone/<slug>/<int:channel_id>")
@app.route("/vlc/iphone/<slug>")
def open_vlc_iphone(slug, channel_id=None):
    playlist_url = request.url_root.rstrip("/") + url_for("playlist_alias_for_vlc", slug=slug)
    enc = requests.utils.quote(playlist_url, safe="")

    # CONFIRMED WORKING ON iPHONE: Method 2
    method_2 = "vlc-x-callback://x-callback-url/stream?url=" + enc

    # Backup methods
    method_1 = "vlc://x-callback-url/stream?url=" + enc
    method_3 = "vlc://" + enc

    return client_page(f"""
    <div class="top"><h2>NOX IPTV VLC iPhone</h2></div>
    <div class="wrap">
      <div class="player">
        <h3>iPhone VLC</h3>
        <p class="ok"><b>Default:</b> Method 2, sepse kjo u konfirmua që punon.</p>
        <p>
          <a class="btn" id="primary" href="{method_2}">🎥  Hap në VLC iPhone</a>
          <a class="btn gray" href="{method_1}">Backup Method 1</a>
          <a class="btn gray" href="{method_3}">Backup Method 3</a>
        </p>
        <p>
          <a class="btn gray" href="{playlist_url}">Open playlist file</a>
          <button class="btn gray" onclick="navigator.clipboard.writeText('{playlist_url}').then(()=>alert('Playlist URL u kopjua'))">Copy playlist URL</button>
          <a class="btn gray" href="/watch/home">Back</a>
        </p>
        <p class="hint">Playlist URL:<br><code>{playlist_url}</code></p>
      </div>
    </div>
    <script>
      setTimeout(function() {{
        window.location.href = "{method_2}";
      }}, 500);
    </script>
    """)


@app.route("/vlc/android/<slug>/<int:channel_id>")
@app.route("/vlc/android/<slug>")
def open_vlc_android(slug, channel_id=None):
    playlist_url = request.url_root.rstrip("/") + url_for("playlist_alias_for_vlc", slug=slug)
    p = urlparse(playlist_url)
    clean = playlist_url.replace("https://", "").replace("http://", "")
    scheme = p.scheme or "https"

    # CONFIRMED WORKING ON ANDROID: Intent Video
    intent_video = (
        "intent://" + clean +
        "#Intent;scheme=" + scheme +
        ";action=android.intent.action.VIEW;category=android.intent.category.BROWSABLE" +
        ";package=org.videolan.vlc;type=video/*;S.title=NOXIPTV;end"
    )

    # Backup methods
    intent_m3u = (
        "intent://" + clean +
        "#Intent;scheme=" + scheme +
        ";action=android.intent.action.VIEW;category=android.intent.category.BROWSABLE" +
        ";package=org.videolan.vlc;type=audio/x-mpegurl;S.title=NOXIPTV;end"
    )
    vlc_scheme = "vlc://" + requests.utils.quote(playlist_url, safe="")

    return client_page(f"""
    <div class="top"><h2>NOX IPTV VLC Android</h2></div>
    <div class="wrap">
      <div class="player">
        <h3>Android VLC</h3>
        <p class="ok"><b>Default:</b> Intent Video, sepse kjo u konfirmua që punon.</p>
        <p>
          <a class="btn" id="primary" href="{intent_video}">🎥 🤖 Hap në VLC Android</a>
          <a class="btn gray" href="{intent_m3u}">Backup Intent M3U</a>
          <a class="btn gray" href="{vlc_scheme}">Backup VLC Scheme</a>
        </p>
        <p>
          <a class="btn gray" href="{playlist_url}">Open playlist file</a>
          <button class="btn gray" onclick="navigator.clipboard.writeText('{playlist_url}').then(()=>alert('Playlist URL u kopjua'))">Copy playlist URL</button>
          <a class="btn gray" href="/watch/home">Back</a>
        </p>
        <p class="hint">Playlist URL:<br><code>{playlist_url}</code></p>
      </div>
    </div>
    <script>
      setTimeout(function() {{
        window.location.href = "{intent_video}";
      }}, 500);
    </script>
    """)


@app.route("/watch/debug")
def watch_debug():
    if not client_login_required():
        return redirect("/watch")
    slug = session["client_slug"]
    try:
        text = get_playlist_for_client(slug, force_refresh=True)
        items = parse_m3u_items(text)[:30]
        full_playlist = request.url_root.rstrip("/") + url_for("playlist_alias_for_vlc", slug=slug)
        iphone = request.url_root.rstrip("/") + url_for("open_vlc_iphone", slug=slug)
        android = request.url_root.rstrip("/") + url_for("open_vlc_android", slug=slug)

        rows = ""
        for idx, it in enumerate(items):
            rows += f"<tr><td>{idx}</td><td>{it.get('name')}</td><td><code>{it.get('url')}</code></td></tr>"

        return client_page(f"""
        <div class="top"><h2>NOX IPTV Debug</h2></div>
        <div class="wrap"><div class="player">
          <h3>VLC Proxy Playlist Debug</h3>
          <p>Proxy playlist: <code>{full_playlist}</code></p>
          <p>iPhone launcher: <code>{iphone}</code></p>
          <p>Android launcher: <code>{android}</code></p>
          <p><a class="btn" href="{full_playlist}">Open playlist file</a>
             <a class="btn gray" href="{iphone}">Test iPhone VLC</a>
             <a class="btn gray" href="{android}">Test Android VLC</a>
             <a class="btn gray" href="/watch/home">Back</a></p>
          <h3>First 30 generated channel URLs</h3>
          <table>{rows}</table>
        </div></div>
        """)
    except Exception as e:
        return client_page(f"<div class='top'><h2>Debug</h2></div><div class='wrap'><div class='player'>Error: {e}</div></div>")



# ---------------- V8.1 Optional FFmpeg HLS Browser Mode ----------------

FFMPEG_PROCESSES = {}

def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def hls_session_dir(slug, channel_id):
    d = HLS_DIR / slug / str(channel_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_stream_url_by_id(slug, channel_id):
    text = get_playlist_for_client(slug, force_refresh=False)
    items = parse_m3u_items(text)
    if channel_id < 0 or channel_id >= len(items):
        raise ValueError("Channel not found")
    return items[channel_id]["url"]


def stop_old_ffmpeg(slug, channel_id):
    key = f"{slug}:{channel_id}"
    proc = FFMPEG_PROCESSES.get(key)
    if proc and proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass


def start_ffmpeg_hls(slug, channel_id, mode="copy"):
    """
    Starts ffmpeg HLS output for browser playback.
    mode=copy: fast transmux, low CPU. Works if stream codec is browser-compatible.
    mode=transcode: heavier, more compatible, needs more Railway CPU.
    """
    if not ffmpeg_available():
        return False, "ffmpeg not installed"

    key = f"{slug}:{channel_id}:{mode}"
    existing = FFMPEG_PROCESSES.get(key)
    out_dir = hls_session_dir(slug, channel_id)
    index_file = out_dir / "index.m3u8"

    if existing and existing.poll() is None and index_file.exists():
        return True, "already running"

    # cleanup old hls files for this channel
    for f in out_dir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    stream_url = get_stream_url_by_id(slug, channel_id)

    common = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "2",
        "-user_agent", "VLC/3.0.20 LibVLC/3.0.20 NOXIPTV",
        "-i", stream_url,
    ]

    if mode == "transcode":
        codec = [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-profile:v", "baseline",
            "-level", "3.1",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
        ]
    else:
        codec = ["-c", "copy"]

    hls = [
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments+append_list+omit_endlist+program_date_time",
        "-hls_segment_filename", str(out_dir / "seg_%03d.ts"),
        str(index_file),
    ]

    proc = subprocess.Popen(common + codec + hls, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    FFMPEG_PROCESSES[key] = proc
    return True, "started"


@app.route("/browser/ffmpeg/<slug>/<int:channel_id>/index.m3u8")
def browser_ffmpeg_index(slug, channel_id):
    """
    Optional browser fallback that converts/transmuxes streams into HLS.
    Query:
      ?mode=copy       fast
      ?mode=transcode  heavier but more compatible
    """
    mode = request.args.get("mode", "copy")
    if mode not in ("copy", "transcode"):
        mode = "copy"
    ok, msg = start_ffmpeg_hls(slug, channel_id, mode=mode)
    if not ok:
        return Response(f"#EXTM3U\n# ERROR: {msg}\n", mimetype="application/vnd.apple.mpegurl", status=500)

    out_dir = hls_session_dir(slug, channel_id)
    index_file = out_dir / "index.m3u8"

    # wait briefly for manifest creation
    for _ in range(20):
        if index_file.exists() and index_file.stat().st_size > 0:
            break
        time.sleep(0.15)

    if not index_file.exists():
        return Response("#EXTM3U\n# ERROR: ffmpeg manifest not ready\n", mimetype="application/vnd.apple.mpegurl", status=503)

    text = index_file.read_text(encoding="utf-8", errors="ignore")
    # rewrite segment URLs to served endpoint
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and s.endswith(".ts"):
            lines.append(url_for("browser_ffmpeg_segment", slug=slug, channel_id=channel_id, filename=s))
        else:
            lines.append(line)

    return Response(
        "\n".join(lines) + "\n",
        mimetype="application/vnd.apple.mpegurl",
        headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"}
    )


@app.route("/browser/ffmpeg/<slug>/<int:channel_id>/<path:filename>")
def browser_ffmpeg_segment(slug, channel_id, filename):
    out_dir = hls_session_dir(slug, channel_id)
    return send_from_directory(out_dir, filename, mimetype="video/mp2t")


@app.route("/browser/ffmpeg-status")
def browser_ffmpeg_status():
    return {
        "ffmpeg": ffmpeg_available(),
        "processes": sum(1 for p in FFMPEG_PROCESSES.values() if p and p.poll() is None),
    }


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
    if not c or not c.get("allow_watch", True) or not c.get("enabled", True):
        return redirect("/watch/logout")

    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
    except Exception as e:
        return client_page(f"<div class='top'><h2>NOX IPTV</h2></div><div class='wrap'><div class='player'><p>Problem: {e}</p></div></div>")

    sport_order = [
        "AL| ART SPORT 1 FHD","AL| ART SPORT 2 FHD","AL| ART SPORT 3 FHD","AL| ART SPORT 4 FHD","AL| ART SPORT 5 FHD","AL| ART SPORT 6 FHD",
        "AL| SUPER SPORT 1 FHD","AL| SUPER SPORT 2 FHD","AL| SUPER SPORT 3 FHD","AL| SUPER SPORT 4 FHD","AL| SUPER SPORT 5 FHD","AL| SUPER SPORT 6 FHD",
        "AL| TRING SPORT 1 FHD","AL| TRING SPORT 2 FHD","AL| TRING SPORT 3 FHD","AL| TRING SPORT 4 FHD",
        "AL| KUJTESA SPORT 1 HD","AL| KUJTESA SPORT 2 HD","AL| KUJTESA SPORT 3 HD","AL| KUJTESA SPORT 4 HD","AL| KUJTESA SPORT 5 HD",
        "AL| EUROSPORT 1 HD","AL| EUROSPORT 2 HD","AL| Fight Box HD"
    ]
    sport_rank = {name.upper(): i for i, name in enumerate(sport_order)}
    sport_keys = ["SPORT", "SUPER SPORT", "TRING", "KUJTESA", "EUROSPORT", "ART SPORT", "FIGHT"]

    safe_items = []
    for idx, it in enumerate(items):
        name_up = it["name"].upper().strip()
        textkey = (it["name"] + " " + it["group"]).upper()
        sport = any(k in textkey for k in sport_keys)
        safe_items.append({
            "i": idx,
            "name": it["name"],
            "group": "Sport" if sport else it["group"],
            "raw_group": it["group"],
            "logo": it["logo"],
            "url": it["url"],
            "sport_rank": sport_rank.get(name_up, 9999),
        })

    data_json = json.dumps(safe_items, ensure_ascii=False)
    brand = get_settings().get("brand_name", "NOX IPTV") if "get_settings" in globals() else "NOX IPTV"

    body = f"""
    <style>
      :root{{--bg:#050816;--panel:#0b1220e6;--soft:#111827;--line:#26324a;--text:#f8fafc;--muted:#94a3b8;--blue:#0ea5e9;--violet:#8b5cf6;--green:#22c55e}}
      body.light{{--bg:#f8fafc;--panel:#ffffffee;--soft:#f1f5f9;--line:#dbe3ef;--text:#0f172a;--muted:#64748b}}
      body{{background:var(--bg)!important;color:var(--text)!important;font-family:Inter,Arial,sans-serif}}
      .desktopOnly{{display:block}}.mobileOnly{{display:none}}
      .top{{background:linear-gradient(135deg,#020617,#0f172a,#111827)!important;padding:16px!important;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20;backdrop-filter:blur(14px);width:100%;overflow:hidden}}
      .brandrow{{display:flex;justify-content:space-between;align-items:center;gap:12px;max-width:1360px;margin:auto}}
      .brand{{display:flex;align-items:center;gap:12px}}.brand img{{width:48px;height:48px;border-radius:17px;box-shadow:0 12px 35px #0008}}.brand h2{{margin:0;font-size:24px;font-weight:950}}.vtag{{font-size:11px;background:#8b5cf6;color:white;border-radius:999px;padding:4px 8px;margin-left:7px}}
      .userpill{{font-size:12px;color:#cbd5e1;background:#0f172acc;border:1px solid #334155;border-radius:999px;padding:8px 11px}}.switch{{background:#0f172a;border:1px solid #334155;color:white;border-radius:999px;padding:8px 10px;cursor:pointer}}
      .toolbar{{max-width:1360px;width:100%;margin:13px auto 0;display:flex;gap:10px;flex-wrap:wrap;overflow:hidden}}.toolbar input,.toolbar select{{flex:1;min-width:190px;background:#0b1220;border:1px solid #31405e;border-radius:16px;padding:13px;color:white;outline:none}}
      .layout{{display:grid;grid-template-columns:minmax(220px,255px) minmax(0,1fr);gap:14px;max-width:1360px;width:100%;margin:auto;padding:14px;overflow:hidden}}
      .side,.hero,.pcbox,.rail{{background:var(--panel);border:1px solid var(--line);border-radius:26px;box-shadow:0 18px 55px #0008}}
      .side{{padding:14px;height:fit-content;position:sticky;top:118px}}.navbtn{{width:100%;display:flex;align-items:center;gap:10px;text-align:left;margin:7px 0;background:#1e293b;border-radius:16px}}.navbtn.active{{background:linear-gradient(135deg,#0ea5e9,#2563eb)}}
      .hero{{padding:17px;margin-bottom:14px;overflow:hidden;position:relative}}.hero h3{{margin:0 0 7px;font-size:24px;font-weight:950}}.hint{{color:var(--muted);font-size:13px;line-height:1.5}}
      .controls{{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px}}.btn{{border-radius:14px!important;padding:11px 14px!important;font-weight:850!important}}.onlyfav{{background:linear-gradient(135deg,#f59e0b,#f97316)!important;color:white!important}}
      .pcbox{{display:none;padding:12px;margin-bottom:14px}}video{{width:100%;max-width:100%;height:390px;background:#000;border-radius:22px;display:block}}
      .rail{{padding:13px;margin-bottom:14px}}.railtitle{{display:flex;align-items:center;justify-content:space-between;margin:4px 0 10px}}.railtitle h3{{margin:0;font-size:18px}}.railrow{{display:flex;gap:10px;overflow:auto;padding-bottom:4px}}
      .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(248px,100%),1fr));gap:11px;min-width:0;overflow:hidden}}.ch,.railcard{{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:13px;cursor:pointer;min-height:92px;transition:.14s;position:relative;overflow:hidden}}.railcard{{min-width:220px}}.ch:hover,.railcard:hover{{border-color:#38bdf8;transform:translateY(-2px)}}.selected{{border-color:#0ea5e9!important;box-shadow:0 0 0 1px #0ea5e9aa}}
      .logo{{width:48px;height:48px;object-fit:contain;float:left;margin-right:12px;background:#ffffff12;border-radius:15px}}.name{{font-size:15px;font-weight:950;line-height:1.25}}.group{{clear:both;color:var(--muted);font-size:12px;margin-top:9px}}.live{{position:absolute;right:10px;bottom:10px;background:#16a34a;color:white;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:900}}
      .bottomnav{{display:none}}
      @media(max-width:900px){{
        .desktopOnly{{display:none!important}}.mobileOnly{{display:block!important}}
        .top{{padding:12px!important}}.brand img{{width:42px;height:42px}}.brand h2{{font-size:20px}}.userpill{{display:none}}
        .toolbar{{display:block}}.toolbar input{{width:100%;min-width:0;margin-bottom:8px}}.toolbar select{{width:100%;min-width:0}}
        .layout{{display:block;padding:10px;padding-bottom:86px}}.side{{display:none}}
        .hero{{border-radius:22px;padding:14px}}.hero h3{{font-size:19px}}
        .rail{{border-radius:22px;padding:12px}}.railrow{{gap:8px}}.railcard{{min-width:178px;min-height:84px}}
        .grid{{grid-template-columns:1fr;gap:9px}}.ch{{min-height:82px;border-radius:19px}}.logo{{width:42px;height:42px}}.name{{font-size:15px}}
        .pcbox{{border-radius:22px}}video{{height:225px;border-radius:18px}}
        .bottomnav{{display:flex;position:fixed;bottom:0;left:0;right:0;background:#020617ee;border-top:1px solid #26324a;z-index:50;padding:8px;gap:8px;backdrop-filter:blur(12px)}}.bottomnav button{{flex:1;padding:11px 8px!important;font-size:12px}}
      }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/mpegts.js@latest"></script>

    <div class="top">
      <div class="brandrow">
        <div class="brand"><img src="/static/nox_logo.svg" onerror="this.style.display='none'"><div><h2>{brand}<span class="vtag">V10.1</span></h2><div class="hint">{c.get('name', slug)}</div></div></div>
        <div style="display:flex;gap:8px;align-items:center"><button class="switch desktopOnly" onclick="toggleTheme()">🌙/☀️</button><span class="userpill">Online</span><a class="btn red" href="/watch/logout">Logout</a></div>
      </div>
      <div class="toolbar">
        <input id="search" placeholder="Kërko kanal...">
        <select id="group"><option value="">Të gjitha</option><option value="__fav">⭐ Favorites</option><option value="__recent">🕘 Recent</option><option value="Sport">Sport</option></select>
      </div>
    </div>

    <div class="layout">
      <aside class="side">
        <button class="btn navbtn active" onclick="setGroup('',this)">🏠 <span>Home</span></button>
        <button class="btn navbtn" onclick="setGroup('__fav',this)">⭐ <span>Favorites</span></button>
        <button class="btn navbtn" onclick="setGroup('__recent',this)">🕘 <span>Recent</span></button>
        <button class="btn navbtn" onclick="setGroup('Sport',this)">🏆 <span>Sport</span></button>
        <button class="btn navbtn" onclick="setMode('pc')">💻 <span>PC Mode</span></button>
        <button class="btn navbtn" onclick="setMode('auto')">📱 <span>Mobile App</span></button>
      </aside>

      <main>
        <section class="hero">
          <h3 id="now">Zgjedh një kanal</h3>
          <div class="hint" id="hint">Në telefon hapet direkt në app. Android përdor proxy stream për stabilitet. Për kompjuter zgjidh PC Mode.</div>
          <div class="controls"><button class="btn onlyfav" onclick="toggleFavorite()">⭐ Favorite</button></div>
        </section>

        <section class="pcbox" id="pcbox">
          <video id="pcvideo" controls playsinline></video>
          <div class="hint" id="pchint">PC Browser player aktiv.</div>
        </section>

        <section class="rail" id="continueBox">
          <div class="railtitle"><h3>Continue Watching</h3><span class="hint">Kanalet e fundit</span></div>
          <div class="railrow" id="continueRail"></div>
        </section>

        <section class="rail">
          <div class="railtitle"><h3>Recommended for you</h3><span class="hint">Sport & të shikuara</span></div>
          <div class="railrow" id="recommendRail"></div>
        </section>

        <div class="grid" id="channels"></div>
      </main>
    </div>

    <div class="bottomnav">
      <button class="btn" onclick="setGroup('',null)">Home</button>
      <button class="btn gray" onclick="setGroup('__fav',null)">⭐</button>
      <button class="btn gray" onclick="setGroup('Sport',null)">Sport</button>
      <button class="btn gray" onclick="setMode('pc')">PC</button>
    </div>

    <script>
      const channels = {data_json};
      let currentChannel=null, mode=localStorage.getItem("nox_mode_{slug}")||"auto", hls=null, ts=null;
      const favKey="nox_fav_{slug}", recKey="nox_rec_{slug}", themeKey="nox_theme";
      function favs(){{return JSON.parse(localStorage.getItem(favKey)||"[]")}} function setFavs(v){{localStorage.setItem(favKey,JSON.stringify(v))}}
      function recents(){{return JSON.parse(localStorage.getItem(recKey)||"[]")}} function setRec(v){{localStorage.setItem(recKey,JSON.stringify(v.slice(0,50)))}}
      function isIOS(){{return /iphone|ipad|ipod/i.test(navigator.userAgent)}} function isAndroid(){{return /android/i.test(navigator.userAgent)}}
      if(localStorage.getItem(themeKey)==="light") document.body.classList.add("light");
      function toggleTheme(){{document.body.classList.toggle("light");localStorage.setItem(themeKey,document.body.classList.contains("light")?"light":"dark")}}
      function setMode(m){{mode=m;localStorage.setItem("nox_mode_{slug}",m);document.getElementById("pcbox").style.display=m==="pc"?"block":"none";document.getElementById("hint").innerText=m==="pc"?"PC Mode aktiv: kanalet hapen në browser.":"Mobile App aktiv: kanalet hapen direkt në app."; if(currentChannel&&m==="pc")playPc(currentChannel)}}
      function appLinks(ch){{
        const iosUrl=ch.url;
        const androidUrl=location.origin+"/proxy/{slug}/"+ch.i;
        const clean=androidUrl.replace(/^https?:\\/\\//,"");
        const scheme=androidUrl.startsWith("https://")?"https":"http";
        return {{
          iphone:"vlc-x-callback://x-callback-url/stream?url="+encodeURIComponent(iosUrl),
          android:"intent://"+clean+"#Intent;scheme="+scheme+";package=org.videolan.vlc;type=video/*;S.title=NoxIPTV;end",
          direct:ch.url
        }}
      }}
      function selectChannel(ch){{currentChannel=ch;let r=recents().filter(x=>x!==ch.i);r.unshift(ch.i);setRec(r);document.getElementById("now").innerText=ch.name+" — "+(ch.raw_group||ch.group);document.querySelectorAll(".ch,.railcard").forEach(x=>x.classList.remove("selected"));document.querySelectorAll(`[data-i="${{ch.i}}"]`).forEach(x=>x.classList.add("selected"));renderRails();try{{navigator.sendBeacon("/watch/log",JSON.stringify({{channel:ch.name,id:ch.i,event:"channel_click"}}));}}catch(e){{}} if(mode==="pc")return playPc(ch);const l=appLinks(ch);if(isIOS())window.location.href=l.iphone;else if(isAndroid())window.location.href=l.android;else window.location.href=l.direct}}
      function stopPc(){{const v=document.getElementById("pcvideo");if(hls){{try{{hls.destroy()}}catch(e){{}}hls=null}}if(ts){{try{{ts.pause();ts.unload();ts.detachMediaElement();ts.destroy()}}catch(e){{}}ts=null}}try{{v.pause()}}catch(e){{}}v.removeAttribute("src");v.load()}}
      function playPc(ch){{document.getElementById("pcbox").style.display="block";stopPc();const v=document.getElementById("pcvideo");document.getElementById("pchint").innerText="Duke hapur në PC Browser...";if(ch.url.toLowerCase().includes(".m3u8"))return playHls(ch.url);if(window.mpegts&&mpegts.getFeatureList().mseLivePlayback){{try{{ts=mpegts.createPlayer({{type:"mpegts",isLive:true,url:"/proxy/{slug}/"+ch.i,cors:false,enableStashBuffer:false,stashInitialSize:128,lazyLoad:false}});ts.on(mpegts.Events.ERROR,()=>playHls("/browser/ffmpeg/{slug}/"+ch.i+"/index.m3u8?mode=copy&t="+Date.now()));ts.attachMediaElement(v);ts.load();ts.play();v.onplaying=()=>document.getElementById("pchint").innerText="Live në PC Browser.";}}catch(e){{playHls("/browser/ffmpeg/{slug}/"+ch.i+"/index.m3u8?mode=copy&t="+Date.now())}}}}else playHls("/browser/ffmpeg/{slug}/"+ch.i+"/index.m3u8?mode=copy&t="+Date.now())}}
      function playHls(src){{
        const v=document.getElementById("pcvideo");
        if(Hls.isSupported()){{
          hls=new Hls({{lowLatencyMode:true,liveSyncDurationCount:2,maxBufferLength:10,backBufferLength:4}});
          hls.loadSource(src);
          hls.attachMedia(v);
          hls.on(Hls.Events.MANIFEST_PARSED,()=>v.play().catch(()=>document.getElementById("pchint").innerText="Nuk u hap në browser."));
          hls.on(Hls.Events.ERROR,(ev,data)=>{{if(data.fatal)document.getElementById("pchint").innerText="Nuk u hap në browser."; }});
        }} else {{
          v.src=src;
          v.play().catch(()=>document.getElementById("pchint").innerText="Nuk u hap në browser.");
        }}
        v.onplaying=()=>document.getElementById("pchint").innerText="Live në PC Browser.";
      }}
      function setGroup(g,el){{document.getElementById("group").value=g;document.querySelectorAll(".navbtn").forEach(x=>x.classList.remove("active"));if(el)el.classList.add("active");render()}}
      function toggleFavorite(){{if(!currentChannel)return;let f=favs();if(f.includes(currentChannel.i))f=f.filter(x=>x!==currentChannel.i);else f.push(currentChannel.i);setFavs(f);render();renderRails()}}
      function cardHtml(ch){{const f=favs();return `${{ch.logo?`<img class="logo" src="${{ch.logo}}" onerror="this.style.display='none'">`:""}}<div class="name">${{f.includes(ch.i)?"⭐ ":""}}${{ch.name}}</div><div class="group">${{ch.group}} · ${{ch.raw_group||""}}</div><span class="live">LIVE</span>`}}
      function filtered(){{const q=document.getElementById("search").value.toLowerCase(),g=document.getElementById("group").value,f=favs(),r=recents();let list=channels.filter(ch=>{{let ok=!g||ch.group===g||ch.raw_group===g;if(g==="__fav")ok=f.includes(ch.i);if(g==="__recent")ok=r.includes(ch.i);return ok&&(!q||ch.name.toLowerCase().includes(q));}});if(g==="Sport")list=list.slice().sort((a,b)=>(a.sport_rank-b.sport_rank)||a.name.localeCompare(b.name));return list}}
      function renderRails(){{const r=recents();const cont=document.getElementById("continueRail");cont.innerHTML="";r.slice(0,10).map(i=>channels.find(c=>c.i===i)).filter(Boolean).forEach(ch=>{{const d=document.createElement("div");d.className="railcard";d.dataset.i=ch.i;d.onclick=()=>selectChannel(ch);d.innerHTML=cardHtml(ch);cont.appendChild(d)}});const rec=document.getElementById("recommendRail");rec.innerHTML="";let base=channels.filter(ch=>ch.group==="Sport").sort((a,b)=>(a.sport_rank-b.sport_rank)||a.name.localeCompare(b.name)).slice(0,10);if(!base.length)base=channels.slice(0,10);base.forEach(ch=>{{const d=document.createElement("div");d.className="railcard";d.dataset.i=ch.i;d.onclick=()=>selectChannel(ch);d.innerHTML=cardHtml(ch);rec.appendChild(d)}})}}
      function render(){{const box=document.getElementById("channels");box.innerHTML="";filtered().slice(0,1200).forEach(ch=>{{const d=document.createElement("div");d.className="ch";d.dataset.i=ch.i;d.onclick=()=>selectChannel(ch);d.innerHTML=cardHtml(ch);box.appendChild(d)}});renderRails()}}
      document.getElementById("search").addEventListener("input",render);document.getElementById("group").addEventListener("change",render);setMode(mode);render();
    </script>
    """
    return client_page(body)


@app.route("/watch/log", methods=["POST"])
def watch_log_event():
    if not client_login_required():
        return {"ok": False}, 401
    slug = session.get("client_slug", "")
    data = request.get_json(silent=True) or {}
    ch = data.get("channel", "")
    ev = data.get("event", "event")
    try:
        increment_channel_stat(slug, ch)
    except Exception:
        pass
    try:
        log_event(ev, slug, ch, status="client")
    except Exception:
        pass
    return {"ok": True}



@app.route("/watch/stream/<int:channel_id>")
def watch_stream_proxy(channel_id):
    if not client_login_required():
        return Response("Not logged in", status=401)
    slug = session["client_slug"]
    try:
        text = get_playlist_for_client(slug, force_refresh=False)
        items = parse_m3u_items(text)
        if channel_id < 0 or channel_id >= len(items):
            return Response("Channel not found", status=404)
        stream_url = items[channel_id]["url"]
        headers = {"User-Agent":"VLC/3.0.20 LibVLC/3.0.20","Accept":"*/*","Accept-Encoding":"identity","Connection":"keep-alive"}
        upstream = requests.get(stream_url, headers=headers, stream=True, timeout=(8, None), allow_redirects=True)
        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=32*1024):
                    if chunk: yield chunk
            finally:
                try: upstream.close()
                except Exception: pass
        return Response(generate(), mimetype="video/mp2t", headers={"Cache-Control":"no-cache","Access-Control-Allow-Origin":"*","X-Accel-Buffering":"no"}, direct_passthrough=True)
    except Exception as e:
        return Response(f"Stream proxy error: {e}", status=500)


# ---------------- Native Android App API ----------------

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form
    u = (data.get("username") or "").strip()
    p = (data.get("password") or "").strip()
    clients = load_clients()
    for slug, c in clients.items():
        if not c.get("allow_watch", True):
            continue
        if c.get("portal_user") == u and c.get("portal_password") == p:
            return {
                "ok": True,
                "slug": slug,
                "name": c.get("name", slug),
                "m3u_url": request.url_root.rstrip("/") + url_for("playlist_alias_for_vlc", slug=slug),
            }
    return {"ok": False, "error": "Login gabim"}, 401


@app.route("/api/channels", methods=["POST"])
def api_channels():
    data = request.get_json(silent=True) or request.form
    u = (data.get("username") or "").strip()
    p = (data.get("password") or "").strip()
    clients = load_clients()
    found_slug = None
    found_client = None
    for slug, c in clients.items():
        if not c.get("allow_watch", True):
            continue
        if c.get("portal_user") == u and c.get("portal_password") == p:
            found_slug = slug
            found_client = c
            break
    if not found_client:
        return {"ok": False, "error": "Login gabim"}, 401
    try:
        text = get_playlist_for_client(found_slug, force_refresh=False)
        items = parse_m3u_items(text)
        groups = sorted(set(i["group"] for i in items))
        channels = []
        for idx, it in enumerate(items):
            channels.append({
                "id": idx,
                "name": it.get("name", ""),
                "group": it.get("group", "Pa grup"),
                "logo": it.get("logo", ""),
                "url": it.get("url", ""),
            })
        return {
            "ok": True,
            "client": found_client.get("name", found_slug),
            "slug": found_slug,
            "count": len(channels),
            "groups": groups,
            "channels": channels,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500



@app.route("/warm")
def warm():
    return {
        "ok": True,
        "message": "warm",
        "time": datetime.now().isoformat(),
    }


@app.route("/logs")
def logs_page():
    if not login_required():
        return redirect("/login")
    logs = read_logs(500)
    rows = "".join(f"<tr><td>{x.get('time')}</td><td>{x.get('client')}</td><td>{x.get('event')}</td><td>{x.get('channel')}</td><td>{x.get('status')}</td><td>{x.get('ip')}</td><td class='small'>{x.get('ua','')[:80]}</td></tr>" for x in logs)
    return admin_page(f"<div class='card'><h2>Admin Logs</h2><table><tr><th>Time</th><th>Client</th><th>Event</th><th>Channel</th><th>Status</th><th>IP</th><th>Device</th></tr>{rows}</table></div>")


@app.route("/analytics")
def analytics_page():
    if not login_required():
        return redirect("/login")
    stats = load_json_file(CHANNEL_STATS_FILE, {})
    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:100]
    rows = ""
    for key, count in top:
        client, channel = key.split("::", 1) if "::" in key else ("", key)
        rows += f"<tr><td>{client}</td><td>{channel}</td><td>{count}</td></tr>"
    return admin_page(f"<div class='card'><h2>Analytics</h2><table><tr><th>Client</th><th>Channel</th><th>Views</th></tr>{rows}</table></div>")


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if not login_required():
        return redirect("/login")
    s = get_settings()
    msg = ""

    presets = {
        "modern_blue": {"brand_color":"#2563eb","accent_color":"#22c55e","background_color":"#0b1220","card_color":"#111827","text_color":"#e5e7eb"},
        "premium_gold": {"brand_color":"#d97706","accent_color":"#facc15","background_color":"#111827","card_color":"#1f2937","text_color":"#fff7ed"},
        "neon_purple": {"brand_color":"#7c3aed","accent_color":"#06b6d4","background_color":"#09090b","card_color":"#18181b","text_color":"#f4f4f5"},
        "red_sport": {"brand_color":"#dc2626","accent_color":"#f97316","background_color":"#0f172a","card_color":"#1e293b","text_color":"#f8fafc"},
        "light_clean": {"brand_color":"#2563eb","accent_color":"#16a34a","background_color":"#f1f5f9","card_color":"#ffffff","text_color":"#0f172a"}
    }

    if request.method == "POST":
        preset = request.form.get("theme_preset", s.get("theme_preset", "modern_blue"))
        s["theme_preset"] = preset
        if request.form.get("apply_preset") == "on" and preset in presets:
            s.update(presets[preset])

        s["brand_name"] = request.form.get("brand_name", "NOX IPTV")
        s["logo_text"] = request.form.get("logo_text", "NOX")
        s["logo_url"] = request.form.get("logo_url", "/static/nox_logo.svg")
        s["brand_color"] = request.form.get("brand_color", s.get("brand_color", "#2563eb"))
        s["accent_color"] = request.form.get("accent_color", s.get("accent_color", "#16a34a"))
        s["background_color"] = request.form.get("background_color", s.get("background_color", "#0b1220"))
        s["card_color"] = request.form.get("card_color", s.get("card_color", "#111827"))
        s["text_color"] = request.form.get("text_color", s.get("text_color", "#e5e7eb"))
        s["layout_mode"] = request.form.get("layout_mode", "sidebar")
        s["player_position"] = request.form.get("player_position", "top")
        s["card_style"] = request.form.get("card_style", "rounded")
        s["smart_engine"] = request.form.get("smart_engine") == "on"
        s["auto_fallback"] = request.form.get("auto_fallback") == "on"
        s["vlc_auto_fallback"] = request.form.get("vlc_auto_fallback") == "on"
        save_settings(s)
        msg = "<p class='ok'>Settings u ruajtën.</p>"

    def sel(name):
        return "selected" if s.get("theme_preset") == name else ""

    body = f"""
    <style>
      .preview {{ background:{s.get('background_color','#0b1220')}; color:{s.get('text_color','#e5e7eb')}; padding:18px; border-radius:18px; }}
      .preview-card {{ background:{s.get('card_color','#111827')}; padding:15px; border-radius:16px; margin-top:10px; }}
      .colorrow {{ display:grid; grid-template-columns:160px 1fr 90px; gap:10px; align-items:center; }}
      .colorrow input[type=color] {{ height:44px; padding:2px; }}
    </style>
    <div class="card">
      <h2>Branding / Smart Engine Settings</h2>
      {msg}
      <form method="post">
        <div class="grid">
          <div class="card">
            <h3>Logo / Brand</h3>
            <label>Brand name</label>
            <input name="brand_name" value="{s.get('brand_name','NOX IPTV')}">
            <label>Logo text</label>
            <input name="logo_text" value="{s.get('logo_text','NOX')}">
            <label>Logo image URL optional</label>
            <input name="logo_url" value="{s.get('logo_url','/static/nox_logo.svg')}" placeholder="/static/nox_logo.svg ose https://.../logo.png">
          </div>

          <div class="card">
            <h3>Theme Preset</h3>
            <label>Choose design</label>
            <select name="theme_preset">
              <option value="modern_blue" {sel('modern_blue')}>Modern Blue</option>
              <option value="premium_gold" {sel('premium_gold')}>Premium Gold</option>
              <option value="neon_purple" {sel('neon_purple')}>Neon Purple</option>
              <option value="red_sport" {sel('red_sport')}>Red Sport</option>
              <option value="light_clean" {sel('light_clean')}>Light Clean</option>
            </select>
            <label><input style="width:auto" type="checkbox" name="apply_preset"> Apply preset colors</label>
          </div>
        </div>

        <div class="card">
          <h3>Advanced Colors</h3>
          <div class="colorrow"><label>Main color</label><input type="color" name="brand_color" value="{s.get('brand_color','#2563eb')}"><input name="brand_color_text" value="{s.get('brand_color','#2563eb')}" disabled></div>
          <div class="colorrow"><label>Accent color</label><input type="color" name="accent_color" value="{s.get('accent_color','#16a34a')}"><input value="{s.get('accent_color','#16a34a')}" disabled></div>
          <div class="colorrow"><label>Background</label><input type="color" name="background_color" value="{s.get('background_color','#0b1220')}"><input value="{s.get('background_color','#0b1220')}" disabled></div>
          <div class="colorrow"><label>Cards</label><input type="color" name="card_color" value="{s.get('card_color','#111827')}"><input value="{s.get('card_color','#111827')}" disabled></div>
          <div class="colorrow"><label>Text</label><input type="color" name="text_color" value="{s.get('text_color','#e5e7eb')}"><input value="{s.get('text_color','#e5e7eb')}" disabled></div>
        </div>

        <div class="grid">
          <div class="card">
            <h3>Layout</h3>
            <label>Layout mode</label>
            <select name="layout_mode">
              <option value="sidebar" {'selected' if s.get('layout_mode')=='sidebar' else ''}>Sidebar categories</option>
              <option value="topbar" {'selected' if s.get('layout_mode')=='topbar' else ''}>Topbar compact</option>
            </select>
            <label>Player position</label>
            <select name="player_position">
              <option value="top" {'selected' if s.get('player_position')=='top' else ''}>Top</option>
              <option value="sticky" {'selected' if s.get('player_position')=='sticky' else ''}>Sticky</option>
            </select>
            <label>Card style</label>
            <select name="card_style">
              <option value="rounded" {'selected' if s.get('card_style')=='rounded' else ''}>Rounded</option>
              <option value="sharp" {'selected' if s.get('card_style')=='sharp' else ''}>Sharp</option>
              <option value="glass" {'selected' if s.get('card_style')=='glass' else ''}>Glass</option>
            </select>
          </div>

          <div class="card">
            <h3>Smart Engine</h3>
            <label><input style="width:auto" type="checkbox" name="smart_engine" {'checked' if s.get('smart_engine') else ''}> Smart stream engine</label><br>
            <label><input style="width:auto" type="checkbox" name="auto_fallback" {'checked' if s.get('auto_fallback') else ''}> Auto fallback browser/proxy</label><br>
            <label><input style="width:auto" type="checkbox" name="vlc_auto_fallback" {'checked' if s.get('vlc_auto_fallback') else ''}> Auto VLC fallback Android</label>
          </div>
        </div>

        <div class="preview">
          <h3>Live Preview</h3>
          <div class="preview-card">
            <b>{s.get('brand_name','NOX IPTV')}</b><br>
            Channel card preview · Sport · Live
          </div>
        </div>
        <br>
        <button>Save Settings</button>
      </form>
    </div>
    """
    return admin_page(body)


@app.route("/manifest.json")
def pwa_manifest():
    s = get_settings()
    return {"name": s.get("brand_name","NOX IPTV"), "short_name": s.get("brand_name","NOX IPTV"), "start_url": "/watch", "display": "standalone", "background_color": "#0b1220", "theme_color": s.get("brand_color","#2563eb"), "icons": []}


@app.route("/sw.js")
def service_worker():
    return Response("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());", mimetype="application/javascript")


@app.route("/watch/capabilities")
def watch_capabilities():
    return {
        "ok": True,
        "browser_methods": ["hls_proxy", "hls_direct", "mpegts_proxy", "direct_video", "proxy_direct_video"],
        "note": "V6.3."
    }

@app.route("/health")
def health():
    return {
        "ok": True,
        "service": "noxiptv",
        "version": API_VERSION,
        "time": datetime.now().isoformat(),
        "clients": len(load_clients()),
        "template_channels": get_template_text().count("#EXTINF"),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
@app.route("/c/<slug>/<token>")
def client_direct_login(slug, token):
    """
    Direct client login link. Works only if enabled in admin.
    Normal /watch user/pass login continues to work.
    """
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        return redirect("/watch")
    if not c.get("enabled", True) or not c.get("allow_watch", True):
        return redirect("/watch")
    if not c.get("public_enabled", False):
        return redirect("/watch")
    if not c.get("public_token") or c.get("public_token") != token:
        return redirect("/watch")
    session["client_slug"] = slug
    try:
        log_event(slug, "direct_login", "Direct client link login")
    except Exception:
        pass
    return redirect("/watch/home")


@app.route("/client-direct-toggle/<slug>", methods=["POST", "GET"])
def client_direct_toggle(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        return redirect("/dashboard")
    ensure_client_public_token(slug, c)
    c["public_enabled"] = not c.get("public_enabled", False)
    clients[slug] = c
    save_clients(clients)
    return redirect("/dashboard")


@app.route("/client-direct-reset/<slug>", methods=["POST", "GET"])
def client_direct_reset(slug):
    if not login_required():
        return redirect("/login")
    clients = load_clients()
    c = clients.get(slug)
    if not c:
        return redirect("/dashboard")
    c["public_token"] = secrets.token_urlsafe(18)
    c["public_enabled"] = True
    clients[slug] = c
    save_clients(clients)
    return redirect("/dashboard")



