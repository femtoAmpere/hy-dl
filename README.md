
# requirements

## apt
`apt update && apt install megatools git cifs-utils python-venv -y`

## /etc/fstab
```
# hy-dl
//snas.berry/botspace/downloads/hy-dl /home/femto/src/hy-dl/downloads cifs noauto,user,rw,uid=femto,gid=femto,credentials=/home/femto/src/hy-dl/.downloads 0 0
```

## folder structure
```bash
mkdir downloads downloaders
mount downloads
mkdir downloads/yt-dlp
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o downloaders/yt-dlp
chmod +x downloaders/yt-dlp
python3 -m venv downloaders/gallery-dl
```

## crontab -e
```bash
@reboot cd /home/femto/src/hy-dl && sleep 32 && screen -S hy-dl -dm bash -c 'while true; do sleep 8; .venv/bin/python main.py; done'
```

# site-specific tasks
## deviantart
You need to run this every three months to refresh the token:
```bash
ssh -L 6414:127.0.0.1:6414 host.local 'cd src/hy-dl && ./downloaders/gallery-dl/bin/gallery-dl --config .gallery-dl.conf oauth:deviantart'
```
