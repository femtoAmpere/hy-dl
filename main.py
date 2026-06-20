
import config.config as config
import datetime
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from app import downloader


def e6w_bot_url_extract(update: Update, fallback: str = "") -> str:
    msg = update.message
    entities = getattr(msg, "caption_entities") or getattr(msg, "entities") or []
    for entity in entities:
        if entity.url and 'e621.net/posts/' in entity.url.lower():
            return entity.url
    
    return fallback


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in config.telegram_users:
        await update.message.reply_text('Unauthorized user.')
        return

    urls = update.message.text.strip().split('\n')
    acknowledge = f'Downloading {len(urls)} URLs...'
    
    if update.message.text.startswith('New file matches your tags '):  # e6 watch bot
        e6url = e6w_bot_url_extract(update)
        if e6url:
            urls = [e6url]
            acknowledge = f'Downloading URL from E621.net watch bot: {e6url}...'

    await update.message.reply_text(acknowledge, parse_mode='Markdown')

    downloader.downloader_queue.put(downloader.DownloadJob(
        urls=urls,
        chat_id=update.effective_chat.id,
        update_downloader=downloader.update_required(),
        bot=context.bot,
        loop=asyncio.get_running_loop(),
    ))


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Version: {config.version}\nStartup: {config.startup}\nUptime: {datetime.datetime.now() - config.startup}\nLast Downloaders Update: {downloader.last_downloaders_update}')


print(f'Starting hy-dl version {config.version} at {config.startup}.')

app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("info", info))

app.run_polling()
