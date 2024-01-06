from signal import signal, SIGINT
from aiofiles.os import path as aiopath, remove
from aiofiles import open as aiopen
from os import execl as osexecl
from time import time
from sys import executable
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from asyncio import gather, create_subprocess_exec
from psutil import (
    disk_usage,
    cpu_percent,
    swap_memory,
    cpu_count,
    virtual_memory,
    net_io_counters,
    boot_time,
)

from .helper.mirror_utils.rclone_utils.serve import rclone_serve_booter
from .helper.ext_utils.jdownloader_booter import jdownloader
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.files_utils import clean_all, exit_clean_up
from .helper.ext_utils.bot_utils import cmd_exec, sync_to_async, create_help_buttons
from .helper.ext_utils.status_utils import get_readable_file_size, get_readable_time, get_progress_bar_string
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, editMessage, sendFile
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from .helper.listeners.aria2_listener import start_aria2_listener
from bot import (
    bot,
    botStartTime,
    LOGGER,
    Intervals,
    DATABASE_URL,
    INCOMPLETE_TASK_NOTIFIER,
    scheduler,
)
from .modules import (
    authorize,
    cancel_task,
    clone,
    exec,
    gd_count,
    gd_delete,
    gd_search,
    mirror_leech,
    status,
    torrent_search,
    torrent_select,
    ytdlp,
    rss,
    shell,
    users_settings,
    bot_settings,
    help,
    speedtest,
)


async def stats(_, message, edit_mode=False):
    buttons = ButtonMaker()
    sysTime     = get_readable_time(time() - boot_time())
    botTime     = get_readable_time(time() - botStartTime)
    total, used, free, disk = disk_usage('/')
    total       = get_readable_file_size(total)
    used        = get_readable_file_size(used)
    free        = get_readable_file_size(free)
    sent        = get_readable_file_size(net_io_counters().bytes_sent)
    recv        = get_readable_file_size(net_io_counters().bytes_recv)
    tb          = get_readable_file_size(net_io_counters().bytes_sent + net_io_counters().bytes_recv)
    cpuUsage    = cpu_percent(interval=0.1)
    v_core      = cpu_count(logical=True) - cpu_count(logical=False)
    freq_info   = cpu_freq(percpu=False)
    if freq_info is not None:
        frequency = freq_info.current / 1000
    else:
        frequency = '-_-'
    memory      = virtual_memory()
    mem_p       = memory.percent
    swap        = swap_memory()

    bot_stats = f"<b>Mirrorin Bot Statistics</b>\n\n"\
                f"<code>┌ CPU  : {get_progress_bar_string(cpuUsage)}</code> {cpuUsage}%\n" \
                f"<code>├ RAM  : {get_progress_bar_string(mem_p)}</code> {mem_p}%\n" \
                f"<code>├ SWAP : {get_progress_bar_string(swap.percent)}</code> {swap.percent}%\n" \
                f"<code>└ DISK : {get_progress_bar_string(disk)}</code> {disk}%\n\n" \
                f"<code>┌ Bot Uptime      : </code> {botTime}\n" \
                f"<code>├ Uploaded        : </code> {sent}\n" \
                f"<code>├ Downloaded      : </code> {recv}\n" \
                f"<code>└ Total Bandwidth : </code> {tb}"

    sys_stats = f"<b>Mirrorin System Statistics</b>\n\n"\
                f"<b>┌ System Uptime:</b> <code>{sysTime}</code>\n" \
                f"<b>├ CPU:</b> {get_progress_bar_string(cpuUsage)}<code> {cpuUsage}%</code>\n" \
                f"<b>├ CPU Total Core(s):</b> <code>{cpu_count(logical=True)}</code>\n" \
                f"<b>├ P-Core(s):</b> <code>{cpu_count(logical=False)}</code> | " \
                f"<b>V-Core(s):</b> <code>{v_core}</code>\n" \
                f"<b>└ Frequency:</b> <code>{frequency} GHz</code>\n\n" \
                f"<b>┌ RAM:</b> {get_progress_bar_string(mem_p)}<code> {mem_p}%</code>\n" \
                f"<b>└ Total:</b> <code>{get_readable_file_size(memory.total)}</code> | " \
                f"<b>Free:</b> <code>{get_readable_file_size(memory.available)}</code>\n\n" \
                f"<b>┌ SWAP:</b> {get_progress_bar_string(swap.percent)}<code> {swap.percent}%</code>\n" \
                f"<b>└ Total</b> <code>{get_readable_file_size(swap.ttotal)}</code> | " \
                f"<b>Free:</b> <code>{get_readable_file_size(swap.free)}</code>\n\n" \
                f"<b>┌ DISK:</b> {get_progress_bar_string(disk)}<code> {disk}%</code>\n" \
                f"<b>└ Total:</b> <code>{total}</code> | <b>Free:</b> <code>{free}</code>"

    credit_stats = f"""
                 <blockquote>
                 <b>Credit </b>
                 <b>Base Repo </b>
                 <b>┌ Anas</b>
                 <b>└ Github :</b>[Here](https://github.com/anasty17)
                 <b>Edit & Modded </b>
                 <b>┌ 𝐊𝐚𝐥𝐚𝐲𝐮𝐤𝐢-𝐅𝐞𝐥𝐢𝐜𝐞はなぶさ建設</b>
                 <b>├ Github :</b>[Here](https://github.com/saemfvck)
                 <b>├ ➤ 𝐄𝐫𝐢𝐭𝐬𝐮 𝐊𝐢𝐤𝐮𝐲𝐚</b>
                 <b>└ Github :</b>[Here](https://github.com/ZeynDev)
                 </blockquote>
                 """
 

    buttons.ibutton("Sys Stats",  "show_sys_stats")
    buttons.ibutton("Credit", "show_credit_stats")
    buttons.ibutton("Close", "close_signal")
    sbtns = buttons.build_menu(2)
    if not edit_mode:
        await message.reply(bot_stats, reply_markup=sbtns)
    return bot_stats, sys_stats, credit_stats


async def send_bot_stats(_, query):
    buttons = ButtonMaker()
    bot_stats, _ = await stats(_, query.message, edit_mode=True)
    buttons.ibutton("Sys Stats",  "show_sys_stats")
    buttons.ibutton("Credit", "show_credit_stats")
    buttons.ibutton("Close", "close_signal")
    sbtns = buttons.build_menu(2)
    await query.answer()
    await query.editMessage_text(bot_stats, reply_markup=sbtns)


async def send_sys_stats(_, query):
    buttons = ButtonMaker()
    _, sys_stats = await stats(_, query.message, edit_mode=True)
    buttons.ibutton("Bot Stats",  "show_bot_stats")
    buttons.ibutton("Credit", "show_credit_stats")
    buttons.ibutton("Close", "close_signal")
    sbtns = buttons.build_menu(2)
    await query.answer()
    await query.editMessage_text(sys_stats, reply_markup=sbtns)


async def send_credit_stats(_, query):
   buttons = ButtonMaker()
   credit_stats, _ = await stats(_, query.message, edit_mode=True)
   buttons.ibutton("Bot Stats", "show_bot_stats")
   buttons.ibutton("Sys Stats", "show_sys_stats")
   buttons.ibutton("Close", "close_signal")
   sbtns = buttons.build_menu(2)
   await query.answer()
   await query.editMessage_text(credit_stats, reply_markup=sbtns)


async def send_close_signal(_, query):
    await query.answer()
    try:
        await query.message.reply_to_message.delete()
    except Exception as e:
        LOGGER.error(e)
    await query.message.delete()
    
    async def start(client, message):
    buttons = ButtonMaker()
    buttons.ubutton("Channel", "https://t.me/DriveMirrorLeech")
    buttons.ubutton("Owner", "http://t.me/MathiasFelice")
    buttons.ubutton("Owner 2", "http://t.me/Eritsuu")
    buttons.ubutton("Group", "https://t.me/Mirrorinleech")
    reply_markup = buttons.build_menu(2)
    if await CustomFilters.authorized(client, message):
        start_string = f"""
Bot ini dapat mencerminkan semua tautan|file|torrent Anda ke Google Drive atau rclone cloud atau ke telegram. Ketik /{BotCommands.HelpCommand} untuk mendapatkan daftar perintah yang tersedia
"""
        await sendMessage(message, start_string, reply_markup)
    else:
        await sendMessage(
            message,
            "Maaf, Kamu tidak diizinkan menggunakan bot ini di PM. Gunakanlah bot ini digroup yang telah disediakan.",
            reply_markup,
        )

async def restart(_, message):
    restart_message = await sendMessage(message, "Restarting...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if qb := Intervals["qb"]:
        qb.cancel()
    if jd := Intervals["jd"]:
        jd.cancel()
    if st := Intervals["status"]:
        for intvl in list(st.values()):
            intvl.cancel()
    await sync_to_async(clean_all)
    proc1 = await create_subprocess_exec(
        "pkill", "-9", "-f", "gunicorn|aria2c|qbittorrent-nox|ffmpeg|rclone|java"
    )
    proc2 = await create_subprocess_exec("python3", "update.py")
    await gather(proc1.wait(), proc2.wait())
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    osexecl(executable, executable, "-m", "bot")


async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage(message, "Starting Ping")
    end_time = int(round(time() * 1000))
    await editMessage(reply, f"{end_time - start_time} ms")


async def log(_, message):
    await sendFile(message, "log.txt")


help_string = f"""
NOTE: Try each command without any argument to see more detalis.
/{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Start mirroring to Google Drive.
/{BotCommands.QbMirrorCommand[0]} or /{BotCommands.QbMirrorCommand[1]}: Start Mirroring to Google Drive using qBittorrent.
/{BotCommands.JdMirrorCommand[0]} or /{BotCommands.JdMirrorCommand[1]}: Start Mirroring to Google Drive using JDownloader.
/{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.
/{BotCommands.LeechCommand[0]} or /{BotCommands.LeechCommand[1]}: Start leeching to Telegram.
/{BotCommands.QbLeechCommand[0]} or /{BotCommands.QbLeechCommand[1]}: Start leeching using qBittorrent.
/{BotCommands.JdLeechCommand[0]} or /{BotCommands.JdLeechCommand[1]}: Start leeching using qBittorrent.
/{BotCommands.YtdlLeechCommand[0]} or /{BotCommands.YtdlLeechCommand[1]}: Leech yt-dlp supported link.
/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive.
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).
/{BotCommands.UserSetCommand} [query]: Users settings.
/{BotCommands.BotSetCommand} [query]: Bot settings.
/{BotCommands.BtSelectCommand}: Select files from torrents by gid or reply.
/{BotCommands.CancelTaskCommand}: Cancel task by gid or reply.
/{BotCommands.CancelAllCommand} [query]: Cancel all [status] tasks.
/{BotCommands.ListCommand} [query]: Search in Google Drive(s).
/{BotCommands.SearchCommand} [query]: Search for torrents with API.
/{BotCommands.StatusCommand}: Shows a status of all the downloads.
/{BotCommands.StatsCommand}: Show stats of the machine where the bot is hosted in.
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot (Only Owner & Sudo).
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UsersCommand}: show users settings (Only Owner & Sudo).
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).
/{BotCommands.RestartCommand}: Restart and update the bot (Only Owner & Sudo).
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).
/{BotCommands.ShellCommand}: Run shell commands (Only Owner).
/{BotCommands.AExecCommand}: Exec async functions (Only Owner).
/{BotCommands.ExecCommand}: Exec sync functions (Only Owner).
/{BotCommands.ClearLocalsCommand}: Clear {BotCommands.AExecCommand} or {BotCommands.ExecCommand} locals (Only Owner).
/{BotCommands.RssCommand}: RSS Menu.
"""


async def bot_help(_, message):
    await sendMessage(message, help_string)


async def restart_notification():
    if await aiopath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
    else:
        chat_id, msg_id = 0, 0

    async def send_incompelete_task_message(cid, msg):
        try:
            if msg.startswith("Restarted Successfully!"):
                await bot.edit_message_text(
                    chat_id=chat_id, message_id=msg_id, text=msg
                )
                await remove(".restartmsg")
            else:
                await bot.send_message(
                    chat_id=cid,
                    text=msg,
                    disable_web_page_preview=True,
                    disable_notification=True,
                )
        except Exception as e:
            LOGGER.error(e)

    if INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        if notifier_dict := await DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                msg = "Restarted Successfully!" if cid == chat_id else "Bot Restarted!"
                for tag, links in data.items():
                    msg += f"\n\n{tag}: "
                    for index, link in enumerate(links, start=1):
                        msg += f" <a href='{link}'>{index}</a> |"
                        if len(msg.encode()) > 4000:
                            await send_incompelete_task_message(cid, msg)
                            msg = ""
                if msg:
                    await send_incompelete_task_message(cid, msg)

    if await aiopath.isfile(".restartmsg"):
        try:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id, text="Restarted Successfully!"
            )
        except:
            pass
        await remove(".restartmsg")


async def main():
    jdownloader.initiate()
    await gather(
        sync_to_async(clean_all),
        torrent_search.initiate_search_tools(),
        restart_notification(),
        telegraph.create_account(),
        rclone_serve_booter(),
        sync_to_async(start_aria2_listener, wait=False),
    )
    create_help_buttons()

    bot.add_handler(MessageHandler(start, filters=command(BotCommands.StartCommand)))
    bot.add_handler(
        MessageHandler(
            log, filters=command(BotCommands.LogCommand) & CustomFilters.sudo
        )
    )
    bot.add_handler(
        MessageHandler(
            restart, filters=command(BotCommands.RestartCommand) & CustomFilters.sudo
        )
    )
    bot.add_handler(
        MessageHandler(
            ping, filters=command(BotCommands.PingCommand) & CustomFilters.authorized
        )
    )
    bot.add_handler(
        MessageHandler(
            bot_help,
            filters=command(BotCommands.HelpCommand) & CustomFilters.authorized,
        )
    )
    bot.add_handler(
        MessageHandler(
            stats, filters=command(BotCommands.StatsCommand) & CustomFilters.authorized
        )
    )
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)


bot.loop.run_until_complete(main())
bot.loop.run_forever()
