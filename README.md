# Nox IPTV Cloud Panel V5.0 FULL FIXED

Ky version është V5.0 i plotë, por pa gevent sepse gevent po dështon në Render build.
Përdor gunicorn threaded worker:

web: gunicorn --workers 1 --threads 8 --timeout 0 app:app

Included:
- Auto fallback
- Browser player
- Stream proxy
- VLC Android/Classic fallback
- Favorites
- Recently watched
- Categories: Shqip, Sport, Gjermani
- Device limit
- Enable/Disable client
- Logs
- Analytics
- Branding/settings
- PWA
- Backup/Restore
- Import Clients
- Import/Export Template
- Status
- Quick actions

Render:
Build command:
pip install -r requirements.txt

Start command:
gunicorn --workers 1 --threads 8 --timeout 0 app:app
