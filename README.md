# NOX IPTV V7.2 Server Templates + TEST ALL + VLC Playlist

Added:
- Your 26 servers are preloaded as server templates.
- Admin /servers has TEST ALL button.
- TEST ALL shows passing servers in green and failing in red.
- Test can use selected client's username/password.
- VLC iPhone and Android now open the full client playlist /p/<slug>.m3u,
  because that method is confirmed to work.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
