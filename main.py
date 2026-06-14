
import config.config as config
import os
import io
import datetime
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


last_downloaders_update = datetime.datetime.min

async def sh_mount(fspath=config.downloads):
    cmd = ''

    proc = await asyncio.create_subprocess_shell(f'umount {fspath}', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')
    if proc.returncode != 0:
        print(f'*WARNING* Failed to unmount target with {proc.returncode}. Output: {stderr}')
        #return proc.returncode, stderr
    
    proc = await asyncio.create_subprocess_shell(f'mount {fspath}', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')
    if proc.returncode != 0:
        print(f'*ERROR* Failed to mount target with {proc.returncode}. Output: {stderr}')
        return proc.returncode, stderr
        
    return 0, cmd, ''

async def sh_download_gallery_dl(url: str, update_downloader=False) -> str:
    cmd = ''
    if update_downloader:
        proc = await asyncio.create_subprocess_shell(f'downloaders/gallery-dl/bin/python -m pip install --upgrade pip gallery-dl', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')
    
    proc = await asyncio.create_subprocess_shell(f'downloaders/gallery-dl/bin/gallery-dl --config config/.gallery-dl.conf --dest {config.downloads}/gallery-dl {url}', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')

    return proc.returncode, f'+**gallery-dl**\n', cmd

async def sh_download_yt_dlp(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'yt-dlp'), exist_ok=True)

    cmd = ''
    if update_downloader:
        proc = await asyncio.create_subprocess_shell(f'downloaders/yt-dlp --update-to nightly', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')
    
    proc = await asyncio.create_subprocess_shell(f'../../downloaders/yt-dlp {url}', cwd=os.path.join(config.downloads, 'yt-dlp'))
    stdout, stderr = await proc.communicate()
    cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')

    return proc.returncode, f'+**yt-dlp**\n', cmd

async def sh_download_megadl(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'megadl'), exist_ok=True)
    cmd = ''
    if update_downloader:
    #     cmd += await a_check_output(['downloaders/megadl', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += "No update possible for megadl.\n"
    proc = await asyncio.create_subprocess_shell(f'megadl {url}', cwd=os.path.join(config.downloads, 'megadl'), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    cmd += (stdout.decode() + '\n' if stdout else '') + (stderr.decode() + ' \n' if stderr else '')
    
    return proc.returncode, f'+**megadl**\n', cmd

async def e6w_bot_url_extract(update: Update, fallback: str = "") -> str:
    msg = update.message
    entities = getattr(msg, "caption_entities") or getattr(msg, "entities") or []
    for entity in entities:
        if entity.url and 'e621.net/posts/' in entity.url.lower():
            return entity.url
    
    return fallback

async def download(urls: str, update, update_downloader=False) -> str:

    ret, mounted, _ = await sh_mount()
    if ret != 0:
        return mounted

    msgs = []

    for url in urls:
        url = url.strip()

        receipt = ''

        receipt += f'Download Receipt for `{url}`\n\n'

        if not url.lower().startswith(('http://', 'https://')):
            receipt += 'Please send a valid URL starting with http:// or https://\n'
            msgs.append(receipt)
            continue
        
        if 'furaffinity.net' in url.lower():
            with open(os.path.join(config.downloads, 'FurAffinity.txt'), 'a+') as f:
                f.write(url + '\n')
            receipt += f'+FurAffinity.txt'
            msgs.append(receipt)
            continue

        with open(os.path.join(config.downloads, 'hydrus-import.txt'), 'a+') as f:
            f.write(url + '\n')
        receipt += f'+hydrus-import.txt\n\n'

        if url.lower().startswith(('https://mega.nz/', 'mega.nz', 'www.mega.nz', 'https://www.mega.nz/')):
            ret, msg, rio = await sh_download_megadl(url, update_downloader=update_downloader)
            receipt += msg
            if rio and len(rio) > 0:
                with io.StringIO(rio) as document:
                    document.name = 'megadl.txt'
                    await update.message.reply_document(document=document, caption='megadl receipt')
            if ret == 0:
                msgs.append(receipt)
                continue

        any_downloader_success = False

        ret, msg, rio = await sh_download_gallery_dl(url, update_downloader=update_downloader)
        if ret == 0: any_downloader_success = True
        receipt += msg
        if rio and len(rio) > 0:
            with io.StringIO(rio) as document:
                document.name = 'gallery-dl.txt'
                await update.message.reply_document(document=document, caption='gallery-dl receipt')

        ret, msg, rio = await sh_download_yt_dlp(url, update_downloader=update_downloader)
        if ret == 0: any_downloader_success = True
        receipt += msg
        if rio and len(rio) > 0:
            with io.StringIO(rio) as document:
                document.name = 'yt-dlp.txt'
                await update.message.reply_document(document=document, caption='yt-dlp receipt')

        if not any_downloader_success:
            with open(os.path.join(config.downloads, 'failed.txt'), 'a+') as f:
                f.write(url + '\n')
            receipt += f'+failed.txt\n\n'
        
        msgs.append(receipt)

    return msgs


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
    acknowledge = f'Downloading {len(urls)} URLs...'
    
    if update.message.text.startswith('New file matches your tags '):  # e6 watch bot
        e6url = await e6w_bot_url_extract(update)
        if e6url:
            urls = [e6url]
            acknowledge = f'Downloading URL from E621.net watch bot: {e6url}...'

    await update.message.reply_text(acknowledge, parse_mode='Markdown')

    messages = await download(urls, update, update_downloader=update_pending)
    for msg in messages:
        await update.message.reply_text(msg, parse_mode='Markdown')


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Version: {config.version}\nStartup: {config.startup}\nUptime: {datetime.datetime.now() - config.startup}\nLast Downloaders Update: {last_downloaders_update}')


print(f'Starting hy-dl version {config.version} at {config.startup}.')

app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("info", info))

app.run_polling()
