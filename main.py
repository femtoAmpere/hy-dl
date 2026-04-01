
import config
import os

import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import subprocess


last_downloaders_update = datetime.datetime.min


def sh_mount(fspath=config.downloads):
    cmd = ''

    try:
        cmd += subprocess.check_output(['umount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f'*WARNING* Failed to unmount target with {e.returncode}. Output: {e.output}')
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to unmount target with {e.returncode}. Output: {e.output}'
    
    try:
        cmd += subprocess.check_output(['mount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return e.returncode, f'*WARNING* Failed to mount target with {e.returncode}. Output: {e.output}'
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to mount target with {e.returncode}. Output: {e.output}'

    return 0, cmd

def sh_download_gallery_dl(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/gallery-dl/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'gallery-dl'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['downloaders/gallery-dl/bin/gallery-dl', '--config', '.gallery-dl.conf', '--dest', f'{config.downloads}/gallery-dl', url], shell=False, text=True, stderr=subprocess.STDOUT)
        return 0, f'+**gallery-dl**\n```\n{cmd}\n```\n'
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**gallery-dl** error {e.returncode}:\n```\n{e.output}\n```\n'
    except Exception as e:
        return e.returncode, f'-**gallery-dl** error {e}\n'
    
    return 0, cmd

def sh_download_yt_dlp(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/yt-dlp', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['../../downloaders/yt-dlp', url], shell=False, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'), stderr=subprocess.STDOUT)
        return 0, f'+**yt-dlp**\n```\n{cmd}\n```\n'
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**yt-dlp** error {e.returncode}:\n```\n{e.output}\n```\n'
    except Exception as e:
        return e.returncode, f'-**yt-dlp** error {e}\n'
    
    return 0, cmd

async def download(urls: str, update_downloader=False) -> str:

    ret, mounted = sh_mount()
    if ret != 0:
        return mounted

    telegrams = []

    for url in urls:
        url = url.strip()

        msg = ''
        msg += f'Download Receipt for `{url}`\n\n'

        if not url.lower().startswith(('http://', 'https://')):
            msg += 'Please send a valid URL starting with http:// or https://\n'
            continue
        
        if 'furaffinity.net' in url.lower():
            with open(os.path.join(config.downloads, 'FurAffinity.txt'), 'a+') as f:
                f.write(url + '\n')
            msg += f'+FurAffinity.txt: `{url}`'
            continue

        with open(os.path.join(config.downloads, 'hydrus-import.txt'), 'a+') as f:
            f.write(url + '\n')
        msg += f'+hydrus-import.txt: `{url}`\n\n'

        any_downloader_success = False

        ret, gdl = sh_download_gallery_dl(url, update_downloader=update_downloader)
        if ret == 0: any_downloader_success = True
        msg += gdl

        ret, ytdlp = sh_download_yt_dlp(url, update_downloader=update_downloader)
        if ret == 0: any_downloader_success = True
        msg += ytdlp

        if not any_downloader_success:
            with open(os.path.join(config.downloads, 'failed.txt'), 'a+') as f:
                f.write(url + '\n')
            msg += f'+failed.txt: `{url}`\n\n'

        telegrams.append(msg)
        
    return telegrams

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.telegram_users:
        await update.message.reply_text('Unauthorized user.')
        return
    
    now, update_pending = datetime.datetime.now(), False
    global last_downloaders_update
    if (now - last_downloaders_update).total_seconds() > 60*60*2:
        update_pending = True
        last_downloaders_update = now

    urls = update.message.text.strip().split('\n')
    await update.message.reply_text(f'Downloading {len(urls)} URLs...', parse_mode='Markdown')

    telegrams = await download(urls, update_downloader=update_pending)
    for msg in telegrams:
        await update.message.reply_text(msg, parse_mode='Markdown')

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Version: {config.version}\nStartup: {config.startup}\nUptime: {datetime.datetime.now() - config.startup}\nLast Downloaders Update: {last_downloaders_update}')

print(f'Starting hy-dl version {config.version} at {config.startup}.')

app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("info", info))

app.run_polling()
