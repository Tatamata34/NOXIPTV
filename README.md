# IPTV Cloud Panel V3

## Çka ka të re

- UI më moderne
- Dashboard me statistika
- Download playlist direkt
- Bulk refresh
- Clear cache
- Export/Import JSON
- Master Template preview
- Template mode me host/user/pass për çdo klient
- Optional Proxy URL / VPN gateway field

## VPN / ExpressVPN

ExpressVPN në PC nuk funksionon automatikisht për Render.
Render është server online i ndarë nga kompjuteri yt.

Nëse do realisht VPN/proxy:
- duhet VPS ku e instalon VPN/proxy
- ose një proxy endpoint që paneli e përdor te fusha `Proxy URL`

Për shumicën e rasteve nuk nevojitet, sepse paneli vetëm gjeneron M3U, nuk hoston stream-in.

## Deploy

Build:
pip install -r requirements.txt

Start:
gunicorn app:app

Env:
ADMIN_PASSWORD=...
SECRET_KEY=...
CACHE_SECONDS=300
REQUEST_TIMEOUT=120
