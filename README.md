# Nox IPTV Cloud Panel V4.2

## Ndryshimet V4.2

- Client Portal: `/watch`
- Pa Download M3U për klient
- Pa Open Stream / Copy URL
- Player provon:
  1. HLS/M3U8 me hls.js
  2. MPEG-TS me mpegts.js
  3. direct playback fallback

## E rëndësishme

Në iPhone/Safari, TS/MPEGTS mund të mos punojë edhe me mpegts.js.
Nëse provider-i nuk jep HLS/M3U8 ose CORS, zgjidhja reale është VPS HLS relay/transcoding.
