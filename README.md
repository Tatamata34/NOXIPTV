# NOX IPTV V6.3 GitHub Backup + HLS Stability

Version:
- APP_VERSION = V6.3
- API_VERSION = v6.3

Backup persistence:
- noxiptv_backup.json is included in the repository.
- On first deploy, clients and master template are loaded from noxiptv_backup.json.
- When clients/template change, app writes data/auto_backup.json.
- Optional true GitHub overwrite is supported.

Render Environment variables for GitHub auto overwrite:
GITHUB_TOKEN = your GitHub token with repo contents permission
GITHUB_REPO = username/NOXIPTV
GITHUB_BRANCH = main
GITHUB_BACKUP_PATH = noxiptv_backup.json

Admin buttons:
- Auto Backup downloads latest backup.
- GitHub Sync manually pushes backup to GitHub if env vars are set.

Playback:
- Template mode now creates HLS URLs when client output = m3u8:
  /live/user/pass/streamid.m3u8
- This improves iPhone Safari compatibility.
- VLC iPhone/Android buttons remain.
- Copy URL button added for debugging.

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 --threads 8 --timeout 0 app:app
