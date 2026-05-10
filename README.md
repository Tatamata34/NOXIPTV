# NOX IPTV V6.6 VLC Icons

Changes:
- Removed Android Alt, VLC Classic, Copy URL, Debug URLs buttons from /watch.
- iPhone VLC button now uses a public single-channel .m3u playlist:
  /c/<slug>/<channel_id>.m3u
- Android VLC button remains intent:// direct stream.
- Buttons now show VLC + iPhone/Android icons.
- Compile tested OK.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
