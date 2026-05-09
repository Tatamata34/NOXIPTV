# Nox IPTV Cloud Panel V5.3 Browser HLS + Advanced Branding

Fixes:
- Removed Open Direct button.
- Adds browser HLS proxy/rewrite:
  /watch/hls/<id>
  /watch/hls-seg/<encoded>
- Browser now tries:
  1) HLS proxy/rewrite
  2) original HLS
  3) MPEG-TS proxy
  4) VLC buttons as fallback
- Improved Branding / Smart Engine Settings:
  - Theme presets
  - Color picker inputs
  - Brand name
  - Logo text
  - Logo image URL
  - Layout mode
  - Player position
  - Card style
  - Live preview
- Adds NOX IPTV default branding/logo.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
