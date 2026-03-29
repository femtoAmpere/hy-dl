
import config
import os

from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

import subprocess


def download_gallery_dl(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/gallery-dl/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'gallery-dl'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['downloaders/gallery-dl/bin/gallery-dl', '--dest', f'{config.downloads}/gallery-dl', url], shell=False, text=True, stderr=subprocess.STDOUT)
        return f'+**gallery-dl**\n```\n{cmd}\n```\n'
    except subprocess.CalledProcessError as e:
        return f'-**gallery-dl** error {e.returncode}:\n```\n{e.output}\n```\n'
    except Exception as e:
        return f'-**gallery-dl** error {e}\n'
    
    return cmd

def download_yt_dlp(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/yt-dlp', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['../../downloaders/yt-dlp', url], shell=False, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'), stderr=subprocess.STDOUT)
        return f'+**yt-dlp**\n```\n{cmd}\n```\n'
    except subprocess.CalledProcessError as e:
        return f'-**yt-dlp** error {e.returncode}:\n```\n{e.output}\n```\n'
    except Exception as e:
        return f'-**yt-dlp** error {e}\n'
    
    return cmd

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.telegram_users:
        await update.message.reply_text('Unauthorized user.')
        return
    
    if not update.message.text.lower().startswith(('http://', 'https://')):
        await update.message.reply_text('Please send a valid URL starting with http:// or https://')
        return
    
    url = update.message.text.strip()
    msg = f'Download Report for `{url}`\n\n'
    
    if 'furaffinity.net' in url.lower():
        with open(os.path.join(config.downloads, 'FurAffinity.txt'), 'a+') as f:
            f.write(url + '\n')
        msg += f'+FurAffinity.txt: `{url}`'
        await update.message.reply_text(msg, parse_mode='Markdown')
        return

    with open(os.path.join(config.downloads, 'hydrus-import.txt'), 'a+') as f:
        f.write(url + '\n')
    msg += f'+hydrus-import.txt: `{url}`\n\n'
    
    hour, update_pending = datetime.now().hour, False
    if (hour - config.last_updated_hour) > 1: 
        update_pending = True
        config.last_updated_hour = hour
    
    any_downloader_success = False

    gdl = download_gallery_dl(url, update_downloader=update_pending)
    if gdl.startswith('+'): any_downloader_success = True
    msg += gdl

    ytdlp = download_yt_dlp(url, update_downloader=update_pending)
    if ytdlp.startswith('+'): any_downloader_success = True
    msg += ytdlp

    if not any_downloader_success:
        with open(os.path.join(config.downloads, 'failed.txt'), 'a+') as f:
            f.write(url + '\n')
        msg += f'+failed.txt: `{url}`\n\n'

    await update.message.reply_text(msg, parse_mode='Markdown')


app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
