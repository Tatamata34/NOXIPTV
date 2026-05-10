# NOX IPTV V7.9 Browser Smart Engine

Only browser playback changed:
- HLS proxy/rewrite route added: /browser/hls/<slug>/<channel_id>
- HLS asset proxy route added.
- Browser tries:
  1. Direct HLS if channel is m3u8
  2. HLS candidate proxy
  3. TS/MPEGTS proxy through /proxy/<slug>/<channel_id>
  4. Direct video fallback
- VLC/admin/server templates are not intended to change.

Important:
iPhone Safari cannot play all raw TS channels without real ffmpeg transcoding.
This version improves channels where provider has hidden HLS or browser-compatible streams.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
