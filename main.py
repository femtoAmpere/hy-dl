
import config.config as config
import os
import io
import datetime
import asyncio
import subprocess
import queue
import threading
from typing import NamedTuple

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


last_downloaders_update = datetime.datetime.min
downloads_queue: queue.Queue["DownloadJob"] = queue.Queue()


class DownloadJob(NamedTuple):
    urls: list[str]
    chat_id: int
    update_downloader: bool
    bot: object
    loop: asyncio.AbstractEventLoop


async def send_download_result(bot, chat_id: int, receipt: str, docs: list[io.StringIO]):
    await bot.send_message(chat_id=chat_id, text=receipt, parse_mode='Markdown')
    for doc in docs:
        await bot.send_document(chat_id=chat_id, document=doc, caption=f'{doc.name} receipt')

def downloader() -> None:
    while True:
        job = downloads_queue.get()
        if job is None:
            break
        for index, url in enumerate(job.urls):
            update_pending, remount = (job.update_downloader, True) if index == 0 else (False, False)
            receipt, docs = download(url, remount=remount, update_downloader=update_pending)
            if len(job.urls) > 1: receipt = f'*{index + 1}/{len(job.urls)+downloads_queue.qsize()} downloads queued.*\n{receipt}'
            future = asyncio.run_coroutine_threadsafe(send_download_result(job.bot, job.chat_id, receipt, docs), job.loop)
            try:
                future.result()
            except Exception as exc:
                print(f'Error sending download result: {exc}')
        downloads_queue.task_done()

consumer_thread = threading.Thread(target=downloader, daemon=True)
consumer_thread.start()

def sh_mount(fspath=config.downloads):
    cmd = ''

    try:
        cmd += subprocess.check_output(['umount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f'*WARNING* Failed to unmount target with {e.returncode}. Output: {e.output}')
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to unmount target with {e.returncode}', e.output
    
    try:
        cmd += subprocess.check_output(['mount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return e.returncode, f'*WARNING* Failed to mount target with {e.returncode}', e.output
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to mount target with {e.returncode}', e.output

    return 0, cmd, ''

def sh_download_gallery_dl(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/gallery-dl/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'gallery-dl'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['downloaders/gallery-dl/bin/gallery-dl', '--config', 'config/.gallery-dl.conf', '--dest', f'{config.downloads}/gallery-dl', url], shell=False, text=True, stderr=subprocess.STDOUT)
        return 0, f'+**gallery-dl**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**gallery-dl** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**gallery-dl** error {e}\n', e.output

def sh_download_yt_dlp(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'yt-dlp'), exist_ok=True)
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/yt-dlp', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['../../downloaders/yt-dlp', url], shell=False, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'), stderr=subprocess.STDOUT)
        return 0, f'+**yt-dlp**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**yt-dlp** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**yt-dlp** error {e}\n', e.output

def sh_download_megadl(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'megadl'), exist_ok=True)
    try:
        cmd = ''
        if update_downloader:
        #     cmd += subprocess.check_output(['downloaders/megadl', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
            cmd += "No update possible for megadl.\n"
        cmd += subprocess.check_output(f'megadl {url}', shell=True, text=True, cwd=os.path.join(config.downloads, 'megadl'), stderr=subprocess.STDOUT)
        return 0, f'+**megadl**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**megadl** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**megadl** error {e}\n', e.output

def e6w_bot_url_extract(update: Update, fallback: str = "") -> str:
    msg = update.message
    entities = getattr(msg, "caption_entities") or getattr(msg, "entities") or []
    for entity in entities:
        if entity.url and 'e621.net/posts/' in entity.url.lower():
            return entity.url
    
    return fallback

def download(url: str, remount=False, update_downloader=False) -> tuple[str, list[io.StringIO]]:
    url = url.strip()

    receipt = ''
    docs = []

    if remount:
        ret, mounted, _ = sh_mount()
        if ret != 0:
            return mounted, docs

    receipt += f'Download Receipt for `{url}`\n\n'

    if not url.lower().startswith(('http://', 'https://')):
        receipt += 'Please send a valid URL starting with http:// or https://\n'
        return receipt, docs
    
    if 'furaffinity.net' in url.lower():
        with open(os.path.join(config.downloads, 'FurAffinity.txt'), 'a+') as f:
            f.write(url + '\n')
        receipt += f'+FurAffinity.txt'
        return receipt, docs

    with open(os.path.join(config.downloads, 'hydrus-import.txt'), 'a+') as f:
        f.write(url + '\n')
    receipt += f'+hydrus-import.txt\n\n'

    if url.lower().startswith(('https://mega.nz/', 'mega.nz', 'www.mega.nz', 'https://www.mega.nz/')):
        ret, msg, rio = sh_download_megadl(url, update_downloader=update_downloader)
        receipt += msg
        if rio and len(rio) > 0:
            doc = io.StringIO(rio)
            doc.name = 'megadl.txt'
            docs.append(doc)
        if ret == 0:
            return receipt, docs

    any_downloader_success = False

    ret, msg, rio = sh_download_gallery_dl(url, update_downloader=update_downloader)
    if ret == 0: any_downloader_success = True
    receipt += msg
    if rio and len(rio) > 0:
        doc = io.StringIO(rio)
        doc.name = 'gallery-dl.txt'
        docs.append(doc)

    ret, msg, rio = sh_download_yt_dlp(url, update_downloader=update_downloader)
    if ret == 0: any_downloader_success = True
    receipt += msg
    if rio and len(rio) > 0:
        doc = io.StringIO(rio)
        doc.name = 'yt-dlp.txt'
        docs.append(doc)

    if not any_downloader_success:
        with open(os.path.join(config.downloads, 'failed.txt'), 'a+') as f:
            f.write(url + '\n')
        receipt += f'+failed.txt\n\n'
    
    return receipt, docs

def update_required() -> bool:
    now, update_pending = datetime.datetime.now(), False
    global last_downloaders_update
    if (now - last_downloaders_update).total_seconds() > 60*60*2:
        update_pending = True
        last_downloaders_update = now
    return update_pending

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.telegram_users:
        await update.message.reply_text('Unauthorized user.')
        return

    urls = update.message.text.strip().split('\n')
    acknowledge = f'Downloading {len(urls)} URLs...'
    
    if update.message.text.startswith('New file matches your tags '):  # e6 watch bot
        e6url = await e6w_bot_url_extract(update)
        if e6url:
            urls = [e6url]
            acknowledge = f'Downloading URL from E621.net watch bot: {e6url}...'
    
    await update.message.reply_text(acknowledge, parse_mode='Markdown')

    downloads_queue.put(DownloadJob(
        urls=urls,
        chat_id=update.effective_chat.id,
        update_downloader=update_required(),
        bot=context.bot,
        loop=asyncio.get_running_loop(),
    ))

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Version: {config.version}\nStartup: {config.startup}\nUptime: {datetime.datetime.now() - config.startup}\nLast Downloaders Update: {last_downloaders_update}')


print(f'Starting hy-dl version {config.version} at {config.startup}.')

app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("info", info))

app.run_polling()
