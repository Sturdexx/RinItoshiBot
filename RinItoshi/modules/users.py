#  RinItoshiBot
#  Copyright (C) 2017-2019, Paul Larsen
#  Copyright (C) 2022, IDNCoderX Team, <https://github.com/IDN-C-X/RinItoshiBot>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.


import contextlib

from io import BytesIO
from time import sleep

from telegram import TelegramError, Update
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler, CallbackContext

import RinItoshi.modules.no_sql.users_db as users_db
from RinItoshi import dispatcher, OWNER_ID, LOGGER
from RinItoshi.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4
CHAT_GROUP = 10


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = users_db.get_userid_by_name(username)

    if not users:
        return None

    if len(users) == 1:
        return users[0]["_id"]
    for user_obj in users:
        try:
            userdat = dispatcher.bot.get_chat(user_obj["_id"])
            if userdat.username == username:
                return userdat.id

        except BadRequest as excp:
            if excp.message != "Chat not found":
                LOGGER.exception("Error extracting user ID")

    return None


def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats_ = users_db.get_all_chats() or []
        failed = 0
        for chat in chats_:
            try:
                context.bot.sendMessage(int(chat["chat_id"]), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning(
                    "Couldn't send broadcast to %s, group name %s",
                    str(chat["chat_id"]),
                    str(chat["chat_name"]),
                )

        update.effective_message.reply_text(
            f"Broadcast complete. {failed} groups failed to receive the message, probably due to being kicked."
        )


def log_user(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    users_db.update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if rep := msg.reply_to_message:
        users_db.update_user(
            rep.from_user.id,
            rep.from_user.username,
            chat.id,
            chat.title,
        )

        if rep.forward_from:
            users_db.update_user(
                rep.forward_from.id,
                rep.forward_from.username,
            )

        if rep.entities:
            for entity in rep.entities:
                if entity.type in ["text_mention", "mention"]:
                    with contextlib.suppress(AttributeError):
                        users_db.update_user(entity.user.id, entity.user.username)
        if rep.sender_chat and not rep.is_automatic_forward:
            users_db.update_user(
                rep.sender_chat.id,
                rep.sender_chat.username,
                chat.id,
                chat.title,
            )

    if msg.forward_from:
        users_db.update_user(msg.forward_from.id, msg.forward_from.username)

    if msg.entities:
        for entity in msg.entities:
            if entity.type in ["text_mention", "mention"]:
                with contextlib.suppress(AttributeError):
                    users_db.update_user(entity.user.id, entity.user.username)
    if msg.sender_chat and not msg.is_automatic_forward:
        users_db.update_user(
            msg.sender_chat.id, msg.sender_chat.username, chat.id, chat.title
        )

    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == msg.from_user.id:  # we already added that in the first place
                continue
            users_db.update_user(user.id, user.username, chat.id, chat.title)

    if req := update.chat_join_request:
        users_db.update_user(
            req.from_user.id, req.from_user.username, chat.id, chat.title
        )


def chats(update: Update, _: CallbackContext):
    all_chats = users_db.get_all_chats() or []
    chatfile = "List of chats.\n"
    for chat in all_chats:
        chatfile += "{} - ({})\n".format(chat["chat_name"], chat["chat_id"])

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="chatlist.txt",
            caption="Here is the list of chats in my database.",
        )


def chat_checker(update: Update, context: CallbackContext):
    if (
        update.effective_message.chat.get_member(context.bot.id).can_send_messages
        is False
    ):
        context.bot.leaveChat(update.effective_message.chat.id)


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """I've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me."""
    num_chats = users_db.get_user_num_chats(user_id)
    return f"""I've seen them in <code>{num_chats}</code> chats in total."""


def __stats__():
    return f"× {users_db.num_users()} users, across {users_db.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    users_db.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler(
    "broadcast", broadcast, filters=Filters.user(OWNER_ID), run_async=True
)
USER_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, log_user)
CHATLIST_HANDLER = CommandHandler(
    "chatlist", chats, filters=CustomFilters.dev_filter, run_async=True
)
CHAT_CHECKER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, chat_checker
)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)
