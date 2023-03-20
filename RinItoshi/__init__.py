# RinItoshiBot
# Copyright (C) 2017-2019, Paul Larsen
# Copyright (C) 2022, IDNCoderX Team, <https://github.com/IDN-C-X/RinItoshiBot>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# sourcery skip: raise-specific-error
import logging
import os
import sys
import time

import spamwatch
import telegram.ext as tg
from redis import StrictRedis
from telethon import TelegramClient
from telethon.sessions import MemorySession

StartTime = time.time()

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

LOGGER = logging.getLogger(__name__)

LOGGER.info("[RinItoshi] Starting RinItoshi...")

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "[RinItoshi] You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting."
    )
    sys.exit(1)

ENV = bool(os.environ.get("ENV", False))

if ENV:
    TOKEN = os.environ.get("TOKEN", None)
    try:
        OWNER_ID = int(os.environ.get("OWNER_ID", None))
    except ValueError as e:
        raise Exception(
            "[RinItoshi] Your OWNER_ID env variable is not a valid integer."
        ) from e

    MESSAGE_DUMP = os.environ.get("MESSAGE_DUMP", None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

    try:
        DEV_USERS = {int(x) for x in os.environ.get("DEV_USERS", "").split()}
    except ValueError as exc:
        raise Exception(
            "[RinItoshi] Your dev users list does not contain valid integers."
        ) from exc

    try:
        SUPPORT_USERS = {int(x) for x in os.environ.get("SUPPORT_USERS", "").split()}
    except ValueError as err:
        raise Exception(
            "[RinItoshi] Your support users list does not contain valid integers."
        ) from err

    try:
        WHITELIST_USERS = {
            int(x) for x in os.environ.get("WHITELIST_USERS", "").split()
        }
    except ValueError as exception:
        raise Exception(
            "[RinItoshi] Your whitelisted users list does not contain valid integers."
        ) from exception

    try:
        WHITELIST_CHATS = {
            int(x) for x in os.environ.get("WHITELIST_CHATS", "").split()
        }
    except ValueError as error:
        raise Exception(
            "[RinItoshi] Your whitelisted chats list does not contain valid integers."
        ) from error

    try:
        BLACKLIST_CHATS = {
            int(x) for x in os.environ.get("BLACKLIST_CHATS", "").split()
        }
    except ValueError as an_exception:
        raise Exception(
            "[RinItoshi] Your blacklisted chats list does not contain valid integers."
        ) from an_exception

    WEBHOOK = bool(os.environ.get("WEBHOOK", False))
    URL = os.environ.get("URL", "")  # Does not contain token
    PORT = int(os.environ.get("PORT", 5000))
    CERT_PATH = os.environ.get("CERT_PATH")
    MONGO_URI = os.environ.get("MONGO_URI", None)
    MONGO_DB = os.environ.get("MONGO_DB", "RinItoshi")
    MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
    DB_URL = os.environ.get("DATABASE_URL").replace("postgres://", "postgresql://")
    REDIS_URL = os.environ.get("REDIS_URL")
    DONATION_LINK = os.environ.get("DONATION_LINK")
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "").split()
    DEL_CMDS = bool(os.environ.get("DEL_CMDS", False))
    STRICT_GBAN = bool(os.environ.get("STRICT_GBAN", False))
    WORKERS = int(os.environ.get("WORKERS", 8))
    BAN_STICKER = os.environ.get("BAN_STICKER", "CAADAgADOwADPPEcAXkko5EB3YGYAg")
    ALLOW_EXCL = os.environ.get("ALLOW_EXCL", False)
    CUSTOM_CMD = os.environ.get("CUSTOM_CMD", False)
    API_WEATHER = os.environ.get("API_OPENWEATHER", None)
    WALL_API = os.environ.get("WALL_API", None)
    API_ID = int(os.environ.get("API_ID", None))
    API_HASH = os.environ.get("API_HASH", None)
    SPAMWATCH = os.environ.get("SPAMWATCH_API", None)
    SPAMMERS = os.environ.get("SPAMMERS", None)

else:
    from RinItoshi.config import Development as Config

    TOKEN = Config.TOKEN
    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError as e:
        raise Exception(
            "[RinItoshi] Your OWNER_ID variable is not a valid integer."
        ) from e

    MESSAGE_DUMP = Config.MESSAGE_DUMP
    OWNER_USERNAME = Config.OWNER_USERNAME

    try:
        DEV_USERS = {int(x) for x in Config.DEV_USERS or []}
    except ValueError as exc:
        raise Exception(
            "[RinItoshi] Your dev users list does not contain valid integers."
        ) from exc

    try:
        SUPPORT_USERS = {int(x) for x in Config.SUPPORT_USERS or []}
    except ValueError as err:
        raise Exception(
            "[RinItoshi] Your support users list does not contain valid integers."
        ) from err

    try:
        WHITELIST_USERS = {int(x) for x in Config.WHITELIST_USERS or []}
    except ValueError as exception:
        raise Exception(
            "[RinItoshi] Your whitelisted users list does not contain valid integers."
        ) from exception

    try:
        WHITELIST_CHATS = {int(x) for x in Config.WHITELIST_CHATS or []}
    except ValueError as error:
        raise Exception(
            "[RinItoshi] Your whitelisted chats list does not contain valid integers."
        ) from error

    try:
        BLACKLIST_CHATS = {int(x) for x in Config.BLACKLIST_CHATS or []}
    except ValueError as an_exception:
        raise Exception(
            "[RinItoshi] Your blacklisted users list does not contain valid integers."
        ) from an_exception

    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    CERT_PATH = Config.CERT_PATH
    MONGO_PORT = Config.MONGO_PORT
    MONGO_URI = Config.MONGO_URI
    MONGO_DB = Config.MONGO_DB
    DB_URL = Config.SQLALCHEMY_DATABASE_URI
    REDIS_URL = Config.REDIS_URL
    DONATION_LINK = Config.DONATION_LINK
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    DEL_CMDS = Config.DEL_CMDS
    STRICT_GBAN = Config.STRICT_GBAN
    WORKERS = Config.WORKERS
    BAN_STICKER = Config.BAN_STICKER
    ALLOW_EXCL = Config.ALLOW_EXCL
    CUSTOM_CMD = Config.CUSTOM_CMD
    API_WEATHER = Config.API_OPENWEATHER
    WALL_API = Config.WALL_API
    API_HASH = Config.API_HASH
    API_ID = Config.API_ID
    SPAMWATCH = Config.SPAMWATCH_API
    SPAMMERS = Config.SPAMMERS

# Count owner as dev users
DEV_USERS.add(OWNER_ID)


# Pass if SpamWatch token not set.
if SPAMWATCH is None:
    spamwtc = None
    LOGGER.warning("[RinItoshi] Invalid spamwatch api")
else:
    try:
        spamwtc = spamwatch.Client(SPAMWATCH)
    except spamwatch.errors.Error as err:
        LOGGER.warning(f"{err}")

REDIS = StrictRedis.from_url(REDIS_URL, decode_responses=True)
try:
    REDIS.ping()
    LOGGER.info("[RinItoshi] Your redis server is now alive!")
except BaseException as an_error:
    raise Exception(
        "[RinItoshi] Your redis server is not alive, please check again."
    ) from an_error

finally:
    REDIS.ping()
    LOGGER.info("[RinItoshi] Your redis server is now alive!")

# Telethon
client = TelegramClient(MemorySession(), API_ID, API_HASH)
updater = tg.Updater(
    TOKEN,
    workers=min(32, os.cpu_count() + 4),
    request_kwargs={"read_timeout": 10, "connect_timeout": 10},
)
dispatcher = updater.dispatcher

DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)

# Load at end to ensure all prev variables have been set
# pylint: disable=C0413
from RinItoshiBot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


def spamfilters(text, user_id, chat_id):
    # print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) not in SPAMMERS:
        return False

    print("[RinItoshi] This user is a spammer!")
    return True
