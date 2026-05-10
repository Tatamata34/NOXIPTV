# NOX IPTV V6.1 Stable Live Fix

Fixes:
1. VLC iPhone uses vlc-x-callback encoded stream URL.
2. VLC Android uses intent:// with correct http/https scheme.
3. Browser live has auto-reconnect if stream pauses/ends/stalls.
4. mpegts.js buffer increased for longer stable playback.
5. 2-screen mode remains.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
