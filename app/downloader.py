
import asyncio
import io
import os
import queue
import datetime
import threading
from typing import NamedTuple

from app import shell_commands
import config.config as config

last_downloaders_update = datetime.datetime.min
downloader_queue: queue.Queue["DownloadJob"] = queue.Queue()


class DownloadJob(NamedTuple):
    urls: list[str]
    chat_id: int
    update_downloader: bool
    bot: object
    loop: asyncio.AbstractEventLoop


def downloader() -> None:
    while True:
        job = downloader_queue.get()
        if job is None:
            break
        for index, url in enumerate(job.urls):
            update_pending, remount = (job.update_downloader, True) if index == 0 else (False, False)
            receipt, docs = download(url, remount=remount, update_downloader=update_pending)
            if len(job.urls) > 1: receipt = f'*{index + 1}/{len(job.urls)+downloader_queue.qsize()} downloads queued.*\n{receipt}'
            future = asyncio.run_coroutine_threadsafe(send_download_result(job.bot, job.chat_id, receipt, docs), job.loop)
            try:
                future.result()
            except Exception as exc:
                print(f'Error sending download result: {exc}')
        downloader_queue.task_done()


downloader_thread = threading.Thread(target=downloader, daemon=True)
downloader_thread.start()


def update_required() -> bool:
    now, update_pending = datetime.datetime.now(), False
    global last_downloaders_update
    if (now - last_downloaders_update).total_seconds() > 60*60*2:
        update_pending = True
        last_downloaders_update = now
    return update_pending


async def send_download_result(bot, chat_id: int, receipt: str, docs: list[io.StringIO]):
    await bot.send_message(chat_id=chat_id, text=receipt, parse_mode='Markdown')
    for doc in docs:
        await bot.send_document(chat_id=chat_id, document=doc, caption=f'{doc.name} receipt')


def download(url: str, remount=False, update_downloader=False) -> tuple[str, list[io.StringIO]]:
    url = url.strip()

    receipt = ''
    docs = []

    if remount:
        ret, mounted, _ = shell_commands.sh_mount()
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
        ret, msg, rio = shell_commands.sh_download_megadl(url, update_downloader=update_downloader)
        receipt += msg
        if rio and len(rio) > 0:
            doc = io.StringIO(rio)
            doc.name = 'megadl.txt'
            docs.append(doc)
        if ret == 0:
            return receipt, docs

    any_downloader_success = False

    ret, msg, rio = shell_commands.sh_download_gallery_dl(url, update_downloader=update_downloader)
    if ret == 0: any_downloader_success = True
    receipt += msg
    if rio and len(rio) > 0:
        doc = io.StringIO(rio)
        doc.name = 'gallery-dl.txt'
        docs.append(doc)

    ret, msg, rio = shell_commands.sh_download_yt_dlp(url, update_downloader=update_downloader)
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
