# Nox IPTV Cloud Panel V5.2 Stable Watch

Fixes:
- Live streams no longer stop after 10-50 seconds due to proxy read timeout.
- Stream proxy uses long-lived live connection.
- Categories in client portal reduced to:
  - Të gjitha
  - Favorites
  - Recent
  - Sport
- Sport category includes ART SPORT, SUPER SPORT, TRING SPORT, KUJTESA SPORT, EUROSPORT, Fight Box.
- VLC buttons fixed: Android intent + Classic vlc:// + Open Direct.
- Auto VLC redirect disabled to avoid opening VLC without channel.
- More Branding/Settings: colors, background, cards, text, layout/player options.

Render:
Build command:
pip install -r requirements.txt

Start command:
gunicorn --workers 1 --threads 8 --timeout 0 app:app
