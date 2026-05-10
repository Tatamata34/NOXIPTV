# NOX IPTV V6.5 Stable Revert

Fix:
- Reverted forced /live/*.m3u8 URL conversion.
- Generated channel URLs are direct Xtream stream paths again:
  http://host:port/user/pass/streamid
- This should restore VLC/browser behavior from older versions.
- Added /watch/debug to verify generated URLs.
- Removed problematic Android onclick JS.
- Keeps GitHub backup, auto backup, logo, and modern UI.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
