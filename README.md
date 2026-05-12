# NOX IPTV V8.0 Railway Native Engine

Base:
- Modern app with working V7.8.4/V7.9.1 VLC logic preserved.

Changed only browser playback:
- Fast router per channel.
- Channel method memory.
- Railway optimized TS proxy.
- Fast HLS route for iPhone-compatible channels.
- No slow multi-fallback waiting.

VLC logic:
- Not changed.

Run:
gunicorn --workers 1 --threads 8 --timeout 0 app:app
