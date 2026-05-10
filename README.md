# NOX IPTV V7.7 Proxy Playlist Mode

Main change:
- VLC playlist no longer contains direct provider URLs.
- /vlc-list/<slug>.m3u contains only NOX proxy URLs:
  https://your-domain/proxy/<slug>/<channel_id>

Why:
- Browser was working because it used proxy/retry/buffer behavior.
- VLC was failing on raw provider URLs.
- Now VLC uses the same NOX relay layer.

New:
- /proxy/<slug>/<channel_id>
- /vlc-list/<slug>.m3u
- /playlist/<slug>.m3u alias

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app

Note:
Proxying streams uses your Render bandwidth and one server connection per active VLC stream.
