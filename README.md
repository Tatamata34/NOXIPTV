# Nox IPTV Cloud Panel V4.1

## Ndryshimet V4.1

- Client Portal: `/watch`
- Nuk ka më Download M3U te klienti
- Nuk ka Copy URL / Open Stream te klienti
- Klienti shikon vetëm brenda web player-it
- Player provon HLS/M3U8 me hls.js
- Për TS/MPEGTS provon direct playback në browser, por jo çdo browser e suporton

## Shënim teknik

Për shikim 100% brenda browserit, stream-et duhet të jenë HLS/M3U8.
Nëse provider-i jep vetëm TS/MPEGTS, disa browsera mund të mos e hapin.

Paneli nuk e proxy-on video stream-in përmes Render, prandaj nuk harxhon shumë bandwidth.
