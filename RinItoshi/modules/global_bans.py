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
import html
from io import BytesIO

from telegram import ParseMode, ChatAction, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

import RinItoshi.modules.no_sql.gban_db as db
from RinItoshi import (
    dispatcher,
    OWNER_ID,
    DEV_USERS,
    SUPPORT_USERS,
    STRICT_GBAN,
    MESSAGE_DUMP,
    spamwtc,
)
from RinItoshi.modules.helper_funcs.alternate import typing_action, send_action
from RinItoshi.modules.helper_funcs.chat_status import user_admin, is_user_admin
from RinItoshi.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from RinItoshi.modules.helper_funcs.filters import CustomFilters
from RinItoshi.modules.no_sql.users_db import get_user_com_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "Bots can't add new chat members",
    "Channel_private",
    "Chat not found",
    "Can't demote chat creator",
    "Chat_admin_required",
    "Group chat was deactivated",
    "Method is available for supergroup and channel chats only",
    "Method is available only for supergroups",
    "Need to be inviter of a user to kick it from a basic group",
    "Not enough rights to restrict/unrestrict chat member",
    "Not in the chat",
    "Only the creator of a basic group can kick group administrators",
    "Peer_id_invalid",
    "User is an administrator of the chat",
    "User_not_participant",
    "Reply message not found",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "Bots can't add new chat members",
    "Channel_private",
    "Chat not found",
    "Can't demote chat creator",
    "Chat_admin_required",
    "Group chat was deactivated",
    "Method is available for supergroup and channel chats only",
    "Method is available only for supergroups",
    "Need to be inviter of a user to kick it from a basic group",
    "Not enough rights to restrict/unrestrict chat member",
    "Not in the chat",
    "Only the creator of a basic group can kick group administrators",
    "Peer_id_invalid",
    "User is an administrator of the chat",
    "User_not_participant",
    "Reply message not found",
    "User not found",
}


@typing_action
def gban(update: Update, context: CallbackContext):  # sourcery skip: low-code-quality
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if user_id == OWNER_ID:
        message.reply_text("Nice try -_- but I'm never gonna gban him.")
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "I spy, with my little eye... a sudo user war! Why are you guys turning on each other?"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "OOOH someone's trying to gban a support user! *grabs popcorn*"
        )
        return

    if user_id in (777000, 1087968824):
        message.reply_text("How can i ban someone that i don't know who is it.")
        return

    if user_id == context.bot.id:
        message.reply_text("-_- So funny, lets gban myself why don't I? Nice try.")
        return

    if not reason:
        message.reply_text("Please Specified a reason. I won't allow a bare gban :)")
        return

    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if user_chat.first_name == "":
        message.reply_text("This is a deleted account! no point to gban them...")
        return

    if db.is_user_gbanned(user_id):
        if not reason:
            message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = db.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        user_id, new_reason = extract_user_and_text(message, args)

        if old_reason:
            banner = update.effective_user
            bannerid = banner.id
            bannername = banner.first_name
            new_reason = (
                f"{new_reason} // GBanned by {bannername} banner id: {bannerid}"
            )

            context.bot.sendMessage(
                MESSAGE_DUMP,
                "<b>Global Ban Reason Update</b>"
                "\n<b>Sudo Admin:</b> {}"
                "\n<b>User:</b> {}"
                "\n<b>ID:</b> <code>{}</code>"
                "\n<b>Previous Reason:</b> {}"
                "\n<b>New Reason:</b> {}".format(
                    mention_html(banner.id, banner.first_name),
                    mention_html(
                        user_chat.id, user_chat.first_name or "Deleted Account"
                    ),
                    user_chat.id,
                    old_reason,
                    new_reason,
                ),
                parse_mode=ParseMode.HTML,
            )

            message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text(
        f"<b>Beginning of Global Ban for</b> {mention_html(user_chat.id, user_chat.first_name)}"
        f"\n<b>With ID</b>: <code>{user_chat.id}</code>"
        f"\n<b>Reason</b>: <code>{reason or 'No reason given'}</code>",
        parse_mode=ParseMode.HTML,
    )

    banner = update.effective_user
    bannerid = banner.id
    bannername = banner.first_name
    reason = f"{reason} // GBanned by {bannername} banner id: {bannerid}"

    context.bot.sendMessage(
        MESSAGE_DUMP,
        "<b>New Global Ban</b>"
        "\n#GBAN"
        "\n<b>Status:</b> <code>Enforcing</code>"
        "\n<b>Sudo Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>ID:</b> <code>{}</code>"
        "\n<b>Reason:</b> {}".format(
            mention_html(banner.id, banner.first_name),
            mention_html(user_chat.id, user_chat.first_name),
            user_chat.id,
            reason or "No reason given",
        ),
        parse_mode=ParseMode.HTML,
    )

    with contextlib.suppress(BadRequest):
        context.bot.ban_chat_member(chat.id, user_chat.id)
    db.gban_user(user_id, user_chat.username or user_chat.first_name, reason)


@typing_action
def ungban(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = context.bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if not db.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    banner = update.effective_user

    pre = message.reply_text(
        f"I'll give {user_chat.first_name} a second chance, globally."
    )
    context.bot.sendMessage(
        MESSAGE_DUMP,
        "<b>Regression of Global Ban</b>"
        "\n#UNGBAN"
        "\n<b>Status:</b> <code>Ceased</code>"
        "\n<b>Sudo Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>ID:</b> <code>{}</code>".format(
            mention_html(banner.id, banner.first_name),
            mention_html(user_chat.id, user_chat.first_name),
            user_chat.id,
        ),
        parse_mode=ParseMode.HTML,
    )

    chats = get_user_com_chats(user_id)
    for lol in chats:
        chat_id = lol["chat_id"]

        # Check if this group has disabled gbans
        if not db.does_chat_gban(chat_id):
            continue

        try:
            member = context.bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                context.bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message not in UNGBAN_ERRORS:
                pre.edit_text(f"Could not un-gban due to: {excp.message}")
                context.bot.send_message(
                    MESSAGE_DUMP, f"Could not un-gban due to: {excp.message}"
                )
                return
        except TelegramError:
            pass

    db.ungban_user(user_id)

    context.bot.sendMessage(
        MESSAGE_DUMP,
        f"User {mention_html(user_chat.id, user_chat.first_name)} has been successfully un-gbanned!",
        parse_mode=ParseMode.HTML,
    )
    pre.edit_text("Person has been un-gbanned.")


@send_action(ChatAction.UPLOAD_DOCUMENT)
def gbanlist(update: Update, _: CallbackContext):
    banned_users = db.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected..."
        )
        return

    banfile = "List of retards.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


def check_and_ban(update, user_id, should_message=True):
    with contextlib.suppress(BadRequest, TelegramError, Unauthorized):
        if spmban := spamwtc.get_ban(int(user_id)):
            update.effective_chat.ban_member(user_id)
            if should_message:
                update.effective_message.reply_text(
                    f"This person has been detected as spambot by @SpamWatch and has been removed!"
                    f"\nReason: <code>{spmban.reason}</code>",
                    parse_mode=ParseMode.HTML,
                )
            return

    if db.is_user_gbanned(user_id):
        update.effective_chat.ban_member(user_id)
        if should_message:
            usr = db.get_gbanned_user(user_id)
            greason = usr["reason"]
            if not greason:
                greason = "No reason given"

            update.effective_message.reply_text(
                f"*Alert! this user was GBanned and have been removed!*\n*Reason*: {greason}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return


def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if (
        not db.does_chat_gban(update.effective_chat.id)
        or not update.effective_chat.get_member(context.bot.id).can_restrict_members
    ):
        return
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if user and not is_user_admin(chat, user.id):
        check_and_ban(update, user.id)

    if msg.new_chat_members:
        new_members = update.effective_message.new_chat_members
        for mem in new_members:
            check_and_ban(update, mem.id)

    if msg.reply_to_message:
        user = msg.reply_to_message.from_user
        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id, should_message=False)


@user_admin
@typing_action
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            db.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled Spam Shield in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls."
            )
        elif args[0].lower() in ["off", "no"]:
            db.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled Spam Shield in this group. GBans wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(db.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return f"× {db.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    is_gbanned = db.is_user_gbanned(user_id)

    text = "<b>Globally banned</b>: {}"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DEV_USERS + SUPPORT_USERS:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = db.get_gbanned_user(user_id)
        if user["reason"]:
            text += f"\nReason: {html.escape(user['reason'])}"
            text += "\n\nAppeal at @IDNCoderX if you think it's invalid."
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    db.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"This chat is enforcing *gbans*: `{db.does_chat_gban(chat_id)}`."


__help__ = """
*Admin only:*
× /spamshield <on/off/yes/no>: Will disable or enable the effect of Spam protection in your group.

Spam shield uses @Spamwatch API and Global bans to remove Spammers as much as possible from your chatroom!

*What is SpamWatch?*

SpamWatch maintains a large constantly updated ban-list of spambots, trolls, bitcoin spammers and unsavoury 
characters. RinItoshi will constantly help banning spammers off from your group automatically So, you don't have to 
worry about spammers storming your group[.](https://telegra.ph/file/c1051d264a5b4146bd71e.jpg) 
"""

__mod_name__ = "Spam Shield"

GBAN_HANDLER = CommandHandler(
    "gban",
    gban,
    pass_args=True,
    filters=CustomFilters.dev_filter | CustomFilters.support_filter,
)
UNGBAN_HANDLER = CommandHandler(
    "ungban",
    ungban,
    pass_args=True,
    filters=CustomFilters.dev_filter | CustomFilters.support_filter,
)
GBAN_LIST = CommandHandler(
    "gbanlist",
    gbanlist,
    filters=CustomFilters.dev_filter | CustomFilters.support_filter,
)

GBAN_STATUS = CommandHandler(
    "spamshield", gbanstat, pass_args=True, filters=Filters.chat_type.groups
)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.chat_type.groups, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
