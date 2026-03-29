
# requirements

## apt
`apt update && apt install git cifs-utils python-venv -y`

## /etc/fstab
```
# hy-dl
//snas.berry/private/data/download/hy-dl /home/femto/src/hy-dl/downloads cifs noauto,rw,uid=femto,gid=femto,credentials=/home/femto/src/hy-dl/.downloads 0 0
```

## folder structure
```bash
mount -a
mkdir -p downloads/yt-dlp
cd downloads
curl https://github.com/yt-dlp/yt-dlp/releases/download/latest/yt-dlp -o yt-dlp
python -m venv .venv
```
