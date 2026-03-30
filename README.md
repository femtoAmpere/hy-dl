
# requirements

## apt
`apt update && apt install git cifs-utils python-venv -y`

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

## crontab
```bash
cd /home/femto/src/hy-dl
```