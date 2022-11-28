from random import SystemRandom
from string import ascii_letters, digits

from bot import download_dict, download_dict_lock, LOGGER, config_dict, CHECK_FILE_SIZE
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.status_utils.gd_download_status import GdDownloadStatus
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage, sendMarkup
from bot.helper.ext_utils.fs_utils import get_base_name, check_storage_threshold
from bot.helper.ext_utils.bot_utils import get_readable_file_size


def add_gd_download(link, path, listener, newname):
    res, size, name, files = GoogleDriveHelper().helper(link)
    if res != "":
        return sendMessage(res, listener.bot, listener.message)
    if newname:
        name = newname
    if config_dict['STOP_DUPLICATE'] and not listener.isLeech:
        LOGGER.info('Checking File/Folder if already in Drive...')
        if listener.isZip:
            gname = f"{name}.zip"
        elif listener.extract:
            try:
                gname = get_base_name(name)
            except:
                gname = None
        if gname is not None:
            gmsg, button = GoogleDriveHelper().drive_list(gname, True)
            if gmsg:
                msg = "File/Folder is already available in Drive.\nHere are the search results:"
                return sendMarkup(msg, listener.bot, listener.message, button)
    if CHECK_FILE_SIZE:
        ZIP_UNZIP_LIMIT = config_dict['ZIP_UNZIP_LIMIT']
        LEECH_LIMIT = config_dict['LEECH_LIMIT']
        TORRENT_LIMIT = config_dict['TORRENT_LIMIT']
        STORAGE_THRESHOLD = config_dict['STORAGE_THRESHOLD']
        arch = any([listener.extract, listener.isZip])
        limit = None
        user_id = listener.message.from_user.id
        if user_id != config_dict['OWNER_ID']:
            if STORAGE_THRESHOLD:
                acpt = check_storage_threshold(size, arch)
                if not acpt:
                    msg = f'You must leave {STORAGE_THRESHOLD}GB free storage.'
                    msg += f'\nYour File/Folder size is {get_readable_file_size(size)}'
                    return sendMessage(msg, listener.bot, listener.message)
            if ZIP_UNZIP_LIMIT and arch:
                msg = f'Zip/Unzip limit is {ZIP_UNZIP_LIMIT}GB'
                limit = ZIP_UNZIP_LIMIT
            if LEECH_LIMIT and listener.isLeech:
                msg = f'Leech limit is {LEECH_LIMIT}GB'
                limit = LEECH_LIMIT
            elif TORRENT_LIMIT:
                msg = f'Torrent/Direct limit is {TORRENT_LIMIT}GB'
                limit = TORRENT_LIMIT
            if limit is not None:
                LOGGER.info('Checking File/Folder Size...')
                if size > limit * 1024**3:
                    msg = f'{msg}.\nYour File/Folder size is {get_readable_file_size(size)}.'
                    return sendMessage(msg, listener.bot, listener.message)
    LOGGER.info(f"Download Name: {name}")
    drive = GoogleDriveHelper(name, path, size, listener)
    gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
    download_status = GdDownloadStatus(drive, size, listener, gid)
    with download_dict_lock:
        download_dict[listener.uid] = download_status
    listener.onDownloadStart()
    sendStatusMessage(listener.message, listener.bot)
    drive.download(link)
