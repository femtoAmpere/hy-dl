
import config
import os

from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

import subprocess

def download_gallery_dl(url: str, updateDownloaders=False) -> str:
    try:
        cmd = ''
        if updateDownloaders:
            cmd += subprocess.check_output([r'.venv\Scripts\python' if os.name == 'nt' else '.venv/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'gallery-dl'], shell=False, text=True, cwd=config.downloads)
        cmd += subprocess.check_output([r'.venv\Scripts\gallery-dl' if os.name == 'nt' else '.venv/bin/gallery-dl', url], shell=False, text=True, cwd=config.downloads)
        return f'**gallery-dl**\n```\n{cmd}\n```'
    except subprocess.CalledProcessError as e:
        return f'**gallery-dl** error {e.returncode}:\n```\n{e.output}\n```'
    except Exception as e:
        return f'**gallery-dl** error: {e}'
    
    return cmd

def download_yt_dlp(url: str, updateDownloaders=False) -> str:
    try:
        cmd = ''
        if updateDownloaders:
            cmd += subprocess.check_output([os.path.join('..', 'yt-dlp'), '--update-to', 'nightly'], shell=True, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'))
        cmd += subprocess.check_output([os.path.join('..', 'yt-dlp'), url], shell=True, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'))
        return f'**yt-dlp**\n```\n{cmd}\n```'
    except subprocess.CalledProcessError as e:
        return f'**yt-dlp** error {e.returncode}:\n```\n{e.output}\n```'
    except Exception as e:
        return f'**yt-dlp** error: {e}'
    
    return cmd

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.telegram_users:
        await update.message.reply_text('Unauthorized user.')
        return
    
    if not update.message.text.lower().startswith(('http://', 'https://')):
        await update.message.reply_text('Please send a valid URL starting with http:// or https://')
        return
    
    url = update.message.text
    if 'furaffinity.net' in url.lower():
        with open(os.path.join(config.downloads, 'FurAffinity.txt'), 'a+') as f:
            f.write(url + '\n')
        await update.message.reply_text(f'+FurAffinity.txt: `{url}`', parse_mode='Markdown')
        return
    
    with open(os.path.join(config.downloads, 'hydrus-import.txt'), 'a+') as f:
        f.write(url + '\n')
    await update.message.reply_text(f'+hydrus-import.txt: `{url}`', parse_mode='Markdown')
    
    hour, do_update = datetime.now().hour, False
    if (hour - config.last_updated_hour) > 1: 
        do_update = True
        config.last_updated_hour = hour
    
    gdl = download_gallery_dl(url, updateDownloaders=do_update)
    await update.message.reply_text(gdl, parse_mode='Markdown')

    ytdlp = download_yt_dlp(url, updateDownloaders=do_update)
    await update.message.reply_text(ytdlp, parse_mode='Markdown')


app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
