# IPTV Cloud Panel V5.6 Latest + V4.4 Browser Player

This version keeps the latest advanced admin/system features,
but replaces only /watch browser player with the V4.4 player behavior that worked better.

Kept from latest:
- Admin features/settings/logs/analytics if present
- Branding/static NOX logo
- Backup/restore/import/export
- Client/device systems where present

Restored from V4.4:
- Client /watch browser player logic
- HLS/mpegts simple player behavior

Added:
- Open VLC Android
- Open VLC Classic
- Copy URL
- channel click logging

Render:
Build command:
pip install -r requirements.txt

Start command:
gunicorn --workers 1 --threads 8 --timeout 0 app:app
