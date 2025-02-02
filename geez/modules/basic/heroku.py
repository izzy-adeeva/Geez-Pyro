import asyncio
import config
import math
import sys

import dotenv
import heroku3
import socket
import requests
import urllib3
from pyrogram import Client, filters
from pyrogram.types import Message

from config import *
from geez.helper import restart
from geez.helper.basic import edit_or_reply
from geez.helper.misc import in_heroku
from config import GIT_TOKEN, REPO_URL, BRANCH

from geez.modules.help import add_command_help


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if (config.HEROKU_API_KEY and config.HEROKU_APP_NAME):
    HAPP = heroku3.from_key(app.HEROKU_API_KEY).apps()[config.HEROKU_APP_NAME]
else:
    HAPP = None

@Client.on_message(filters.command("setvar", CMD_HANDLER) & filters.me)
async def set_var(client: Client, message: Message):
    if len(message.command) < 3:
        return await edit_or_reply(
            message, f"<b>Usage:</b> {CMD_HANDLER}setvar [Var Name] [Var Value]"
        )
    Puki = await edit_or_reply(message, "`Processing...`")
    to_set = message.text.split(None, 2)[1].strip()
    value = message.text.split(None, 2)[2].strip()
    if await in_heroku():
        if HAPP is None:
            return await Puki.edit(
                "Pastikan HEROKU_API_KEY dan HEROKU_APP_NAME anda dikonfigurasi dengan benar di config vars heroku"
            )
        heroku_config = HAPP.config()
        if to_set in heroku_config:
            await Puki.edit(f"Berhasil Mengubah var {to_set} menjadi {value}")
        else:
            await Puki.edit(f"Berhasil Menambahkan var {to_set} menjadi {value}")
        heroku_config[to_set] = value
    else:
        path = dotenv.find_dotenv("config.env")
        if not path:
            return await Puki.edit(".env file not found.")
        dotenv.set_key(path, to_set, value)
        if dotenv.get_key(path, to_set):
            await Puki.edit(f"Berhasil Mengubah var {to_set} menjadi {value}")
        else:
            await Puki.edit(f"Berhasil Menambahkan var {to_set} menjadi {value}")
        restart()


@Client.on_message(filters.command("getvar", CMD_HANDLER) & filters.me)
async def varget_(client: Client, message: Message):
    if len(message.command) != 2:
        return await edit_or_reply(
            message, f"<b>Usage:</b> {CMD_HANDLER}getvar [Var Name]"
        )
    Puki = await edit_or_reply(message, "`Processing...`")
    check_var = message.text.split(None, 2)[1]
    if await in_heroku():
        if HAPP is None:
            return await Puki.edit(
                "Pastikan HEROKU_API_KEY dan HEROKU_APP_NAME anda dikonfigurasi dengan benar di config vars heroku"
            )
        heroku_config = HAPP.config()
        if check_var in heroku_config:
            return await Puki.edit(
                f"<b>{check_var}:</b> <code>{heroku_config[check_var]}</code>"
            )
        else:
            return await Puki.edit(f"Tidak dapat menemukan var {check_var}")
    else:
        path = dotenv.find_dotenv("config.env")
        if not path:
            return await Puki.edit(".env file not found.")
        output = dotenv.get_key(path, check_var)
        if not output:
            await Puki.edit(f"Tidak dapat menemukan var {check_var}")
        else:
            return await Puki.edit(f"<b>{check_var}:</b> <code>{str(output)}</code>")


@Client.on_message(filters.command("delvar", CMD_HANDLER) & filters.me)
async def vardel_(client: Client, message: Message):
    if len(message.command) != 2:
        return await message.edit(f"<b>Usage:</b> {CMD_HANDLER}delvar [Var Name]")
    Puki = await edit_or_reply(message, "`Processing...`")
    check_var = message.text.split(None, 2)[1]
    if await in_heroku():
        if HAPP is None:
            return await Puki.edit(
                "Pastikan HEROKU_API_KEY dan HEROKU_APP_NAME anda dikonfigurasi dengan benar di config vars heroku"
            )
        heroku_config = HAPP.config()
        if check_var in heroku_config:
            await message.edit(f"Berhasil Menghapus var {check_var}")
            del heroku_config[check_var]
        else:
            return await message.edit(f"Tidak dapat menemukan var {check_var}")
    else:
        path = dotenv.find_dotenv("config.env")
        if not path:
            return await message.edit(".env file not found.")
        output = dotenv.unset_key(path, check_var)
        if not output[0]:
            return await message.edit(f"Tidak dapat menemukan var {check_var}")
        else:
            await message.edit(f"Berhasil Menghapus var {check_var}")
        restart()


@Client.on_message(filters.command("usage", CMD_HANDLER) & filters.me)
async def usage_heroku(client: Client, message: Message):
    ### Credits CatUserbot
    if await in_heroku():
        if HAPP is None:
            return await message.edit(
                "Pastikan HEROKU_API_KEY dan HEROKU_APP_NAME anda dikonfigurasi dengan benar di config vars heroku"
            )
    else:
        return await edit_or_reply(message, "Only for Heroku Apps")
    dyno = await edit_or_reply(message, "`Checking Heroku Usage. Please Wait...`")
    Heroku = heroku3.from_key(HEROKU_API_KEY)
    account_id = Heroku.account().id
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.149 Mobile Safari/537.36"
    )
    headers = {
        "User-Agent": useragent,
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3.account-quotas",
    }
    path = "/accounts/" + account_id + "/actions/get-quota"
    r = requests.get("https://api.heroku.com" + path, headers=headers)
    if r.status_code != 200:
        return await dyno.edit("Unable to fetch.")
    result = r.json()
    quota = result["account_quota"]
    quota_used = result["quota_used"]
    remaining_quota = quota - quota_used
    percentage = math.floor(remaining_quota / quota * 100)
    minutes_remaining = remaining_quota / 60
    hours = math.floor(minutes_remaining / 60)
    minutes = math.floor(minutes_remaining % 60)
    day = math.floor(hours / 24)
    App = result["apps"]
    try:
        App[0]["quota_used"]
    except IndexError:
        AppQuotaUsed = 0
        AppPercentage = 0
    else:
        AppQuotaUsed = App[0]["quota_used"] / 60
        AppPercentage = math.floor(App[0]["quota_used"] * 100 / quota)
    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)
    await asyncio.sleep(1.5)
    text =f"""
𝗜𝗡𝗙𝗢 𝗞𝗘𝗞𝗨𝗔𝗧𝗔𝗡 𝗥𝗔𝗠-𝗨𝗕𝗢𝗧!!

╭✠╼━━━━━━❖━━━━━━━✠╮
┣•𝗣𝗘𝗡𝗚𝗚𝗨𝗡𝗔𝗔𝗡 𝗦𝗔𝗔𝗧 𝗜𝗡𝗜 : 
┣•   ▸ {AppHours} ᴊᴀᴍ - {AppMinutes} ᴍᴇɴɪᴛ.
┣•   ▸ ᴘʀᴇꜱᴇɴᴛᴀꜱᴇ : {AppPercentage}% 
╰✠╼━━━━━━❖━━━━━━━✠╯
╼┅━━━━━━━━╍━━━━━━━━┅╾ 
╭✠╼━━━━━━❖━━━━━━━✠╮ 
┣•𝗣𝗘𝗡𝗚𝗚𝗨𝗡𝗔𝗔𝗡 𝗕𝗨𝗟𝗔𝗡 𝗜𝗡𝗜 : 
┣•  ▸ {hours} ᴊᴀᴍ - {minutes} ᴍᴇɴɪᴛ. 
┣•  ▸ ᴘʀᴇꜱᴇɴᴛᴀꜱᴇ : {percentage}%. 
╰✠╼━━━━━━❖━━━━━━━✠╯
• 𝗦𝗜𝗦𝗔 𝗗𝗬𝗡𝗢  : `{day}` Hari"""
    return await dyno.edit(text)


@Client.on_message(filters.command("usange", CMD_HANDLER) & filters.me)
async def usange_heroku(client: Client, message: Message):
    xx = await edit_or_reply(message, "`Processing...`")
    await xx.edit(
        "✥ **Informasi Dyno Heroku :**"
        "\n╔════════════════════╗\n"
        f" ➠ **Penggunaan Dyno** `{HEROKU_APP_NAME}` :\n"
        f"     •  `0`**Jam**  `0`**Menit**  "
        f"**|**  [`0`**%**]"
        "\n◖════════════════════◗\n"
        " ➠ **Sisa kuota dyno bulan ini** :\n"
        f"     •  `1000`**Jam**  `0`**Menit**  "
        f"**|**  [`100`**%**]"
        "\n╚════════════════════╝\n"
    )

add_command_help(
    "Heroku",
    [
        [".usage", "gatau."],
        [".setvar", "gatau."],
    ],
)
