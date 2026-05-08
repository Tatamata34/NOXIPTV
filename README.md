# Nox IPTV Cloud Panel V4

## Çka shton V4

- Client Portal: `/watch`
- Çdo klient ka portal username/password
- Klienti sheh kanalet nga telefoni/laptopi
- Search + group filter
- Web player për HLS/M3U8
- Për TS/MPEGTS: Open Stream / Copy URL / Download M3U
- Admin panel mbetet si më parë

## E rëndësishme

Paneli nuk e kalon video stream-in përmes Render. Stream hapet direkt te provider-i nga pajisja e klientit.
Kjo e mban bandwidth-in e Render shumë të ulët.

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
