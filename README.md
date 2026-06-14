
# requirements

## apt
`apt update && apt install megatools git cifs-utils python-venv -y`

## /etc/fstab
```
# hy-dl
//snas.berry/botspace/downloads/hy-dl /home/femto/src/hy-dl/downloads cifs noauto,user,rw,uid=femto,gid=femto,credentials=/home/femto/src/hy-dl/config/.downloads 0 0
```

## folder structure
```bash
mkdir downloads downloaders
mount downloads
mkdir downloads/yt-dlp
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o downloaders/yt-dlp
chmod +x downloaders/yt-dlp
python3 -m venv downloaders/gallery-dl

nano config/.downloads
nano config/.gallery-dl.conf
nano secrets.py
```

### .downloads
```bash
username=usr
password=pas
```

### .gallery-dl.conf
```bash
{
  "extractor": {
    "deviantart": {
      "client-id": "12345",
      "client-secret": "00000000000000000000000000000000",
      "refresh-token": "cache"
    },
    "twitter": {
      "cookies": "./x.com"
    }
  }
}
```

```bash
TELEGRAM_TOKEN = '0000000000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
TELEGRAM_USERS = [91140953]
```

```bash
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

## twitter / x.com
Get cookies from https://x.com and put them into `config/x.com` file. For example, via https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc.
