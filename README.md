# NOX IPTV V9.2 Portal + Clean Client + PC Mode

Main changes:
- Public homepage on `/`
- Big buttons: `KYQU SI KLIENT` -> `/watch`, `ADMIN` -> `/login`
- Clean redesigned client page
- Hidden technical buttons from client view
- Only `⭐ Favorite` remains visible
- Channel click opens external app automatically on mobile
- `PC Browser` mode added for desktop viewing
- Sport category sorted so ART SPORT 1 FHD starts first
- Admin/client/core logic kept unchanged

Railway:
Build: `pip install -r requirements.txt`
Start: `gunicorn --workers 1 --threads 8 --timeout 0 app:app`

`nixpacks.toml` installs ffmpeg for PC Browser/HLS fallback.
