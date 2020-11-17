import shutil, psutil import signal import pickle

from os import execl, path, remove
from sys import executable
import time

from telegram.ext import CommandHandler, run_async
from bot import dispatcher, updater, botStartTime
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, delete
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError


@run_async
def stats(update, context):
    currentTime = get_readable_time((time.time() - botStartTime))
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>Bot Uptime:</b> {currentTime}\n' \
            f'<b>Total disk space:</b> {total}\n' \
            f'<b>Used:</b> {used}\n' \
            f'<b>Free:</b> {free}\n' \
            f'📊<b>Data Usage</b>📊\n' \
            f'<b>Upload:</b> {sent}\n' \
            f'<b>Down:</b> {recv}\n\n' \
            f'<b>CPU:</b> {cpuUsage}%\n' \
            f'<b>RAM:</b> {memory}%\n' \
            f'<b>Disk:</b> {disk}%'
    sendMessage(stats, context.bot, update)


@run_async
def start(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(
        update.message.chat.id, update.message.chat.username,
        update.message.text))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private":
            sendMessage(
                f"Hey <b>{update.message.chat.first_name}</b>. Welcome to <b>GPXCloud Bot</b>",
                context.bot, update)
        else:
            sendMessage("I'm alive :)", context.bot, update)
    else:
        sendMessage("Oops! not a authorized user.", context.bot, update)


def gen_chlog(repo, diff):
    ch_log = ''
    d_form = "%d/%m/%y"
    for c in repo.iter_commits(diff):
        ch_log += f'• [{c.committed_datetime.strftime(d_form)}]: {c.summary} <{c.author}>\n'
    return ch_log


@run_async
def update(update, context):
    branches = ["master", "staging"]
    text = update.effective_message.text
    msg = sendMessage("Fetching Updates....", context.bot, update)
    repo_url = "https://github.com/AnggaR96s/python-aria-mirror-bot.git"
    try:
        repo = Repo()
    except NoSuchPathError as error:
        msg.edit_text(f'`directory {error} is not found`',
                      parse_mode="Markdown")
        return
    except InvalidGitRepositoryError as error:
        msg.edit_text(
            f'`directory {error} does not seems to be a git repository`',
            parse_mode="Markdown")
        return
    except GitCommandError as error:
        msg.edit_text(f'`Early failure! {error}`', parse_mode="Markdown")
        return
    except:
        msg.edit_text("Something's Wrong, Please manually pull.")
    branch = repo.active_branch.name
    if branch not in branches:
        msg.edit_text("Seems like you are using a custom branch!")
        return
    try:
        repo.create_remote('upstream', repo_url)
    except:
        pass
    remote = repo.remote('upstream')
    remote.fetch(branch)
    clogs = gen_chlog(repo, f'HEAD..upstream/{branch}')

    if not clogs:
        msg.edit_text(f"Bot up-to-date with *{branch}*", parse_mode="Markdown")
        return
    if "now" not in text:
        msg.edit_text(
            f"*New Update Available*\nCHANGELOG:\n\n{clogs}\n\n\nDo `/update now` to Update BOT.",
            parse_mode="Markdown")
        return
    try:
        remote.pull(branch)
        msg.edit_text(f"*Successfully Updated BOT, Attempting to restart!*",
                      parse_mode="Markdown")
        _restart(msg)

    except GitCommandError:
        remote.git.reset('--hard')
        msg.edit_text(f"*Successfully Updated BOT, Attempting to restart!*",
                      parse_mode="Markdown")
        _restart(msg)


def _restart(reply):
    # Save restart message object in order to reply to it after restarting
    fs_utils.clean_all()
    with open('restart.pickle', 'wb') as status:
        pickle.dump(reply, status)
    execl(executable, executable, "-m", "bot")


@run_async
def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot,
                                  update)
    _restart(restart_message)


@run_async
def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


@run_async
def log(update, context):
    sendLogFile(context.bot, update)


@run_async
def bot_help(update, context):
    help_string_adm = f'''
/{BotCommands.StartCommand} <b>: Alive or Not</b>
/{BotCommands.MirrorCommand} <b>[url OR magnet_link]: Mirror & upload</b>
/{BotCommands.TarMirrorCommand} <b>[url OR magnet_link]: Mirror & upload as .tar</b>
/{BotCommands.UnzipMirrorCommand} <b>[url OR magnet_link] : Unzip & mirror</b>
/{BotCommands.WatchCommand} <b>[link]: Mirror YT video</b>
/{BotCommands.TarWatchCommand} <b>[link]: Mirror YT video & upload as .tar</b>
/{BotCommands.CloneCommand} <b>[link]: Mirror drive folder</b>
/{BotCommands.CancelMirror} <b>: Reply to dwnld cmd</b>
/{BotCommands.CancelAllCommand} <b>: Cancel all</b>
/{BotCommands.StatusCommand} <b>: Shows a status of all the downloads</b>
/{BotCommands.ListCommand} <b>[name]: Searches in the drive folder</b>
/{BotCommands.deleteCommand} <b>[link]: Delete from drive[Only owner & sudo]</b>
/{BotCommands.StatsCommand} <b>: Show Stats of the machine</b>
/{BotCommands.PingCommand} <b>: Check ping!</b>
/{BotCommands.RestartCommand} <b>: Restart bot[Only owner & sudo]</b>
/{BotCommands.AuthorizeCommand} <b>: Authorize[Only owner & sudo]</b>
/{BotCommands.UnAuthorizeCommand} <b>: Unauthorize[Only owner & sudo]</b>
/{BotCommands.AuthorizedUsersCommand} <b>: authorized users[Only owner & sudo]</b>
/{BotCommands.AddSudoCommand} <b>: Add sudo user[Only owner]</b>
/{BotCommands.RmSudoCommand} <b>: Remove sudo users[Only owner]</b>
/{BotCommands.LogCommand} <b>: Get log file[Only owner & sudo]</b>
/{BotCommands.UpdateCommand} <b>: Update the BOT with git repository</b>

'''

    help_string = f'''
/{BotCommands.StartCommand} <b>: Alive or Not</b>
/{BotCommands.MirrorCommand} <b>[url OR magnet_link]: Mirror & upload</b>
/{BotCommands.TarMirrorCommand} <b>[url OR magnet_link]: Mirror & upload as .tar</b>
/{BotCommands.UnzipMirrorCommand} <b>[url OR magnet_link] : Unzip & mirror</b>
/{BotCommands.WatchCommand} <b>[link]: Mirror YT video</b>
/{BotCommands.TarWatchCommand} <b>[link]: Mirror YT video & upload as .tar</b>
/{BotCommands.CloneCommand} <b>[link]: Mirror drive folder</b>
/{BotCommands.CancelMirror} <b>: Reply to dwnld cmd</b>
/{BotCommands.CancelAllCommand} <b>: Reply to dwnld cmd</b>
/{BotCommands.StatusCommand} <b>: Shows a status of all the downloads</b>
/{BotCommands.ListCommand} <b>[name]: Searches in the drive folder</b>
/{BotCommands.StatsCommand} <b>: Show Stats of the machine</b>
/{BotCommands.PingCommand} <b>: Check ping!</b>

'''

    if CustomFilters.sudo_user(update) or CustomFilters.owner_filter(update):
        sendMessage(help_string_adm, context.bot, update)
    else:
        sendMessage(help_string, context.bot, update)


def main():
    fs_utils.start_cleanup()
    # Check if the bot is restarting
    if path.exists('restart.pickle'):
        with open('restart.pickle', 'rb') as status:
            restart_message = pickle.load(status)
        restart_message.edit_text("Restarted Successfully!")
        remove('restart.pickle')

    start_handler = CommandHandler(BotCommands.StartCommand, start)
    ping_handler = CommandHandler(BotCommands.PingCommand,
                                  ping,
                                  filters=CustomFilters.authorized_chat |
                                  CustomFilters.authorized_user)
    restart_handler = CommandHandler(BotCommands.RestartCommand,
                                     restart,
                                     filters=CustomFilters.owner_filter |
                                     CustomFilters.sudo_user)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help,
                                  filters=CustomFilters.authorized_chat |
                                  CustomFilters.authorized_user)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats,
                                   filters=CustomFilters.authorized_chat |
                                   CustomFilters.authorized_user)
    log_handler = CommandHandler(BotCommands.LogCommand,
                                 log,
                                 filters=CustomFilters.owner_filter |
                                 CustomFilters.sudo_user)
    update_handler = CommandHandler(BotCommands.UpdateCommand,
                                    update,
                                    filters=CustomFilters.owner_filter |
                                    CustomFilters.sudo_user)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    dispatcher.add_handler(update_handler)
    updater.start_polling()
    LOGGER.info("Yeah I'm running!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)


main()
