# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | TG-SORRY

import logging
import requests
import urllib.parse
import filetype
import os
import time
import shutil
import tldextract
import asyncio
import json
import math
from PIL import Image
from plugins.config import Config
from plugins.script import Translation
from plugins.functions.verify import verify_user, check_token, check_verification, get_token
from plugins.functions.forcesub import handle_force_subscribe
from plugins.functions.display_progress import humanbytes
from plugins.functions.help_uploadbot import DownLoadFile
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from plugins.functions.ran_text import random_char
from plugins.database.database import db
from plugins.database.add import AddUser
from pyrogram.types import Thumbnail
from pyrogram import filters, enums, Client
import random

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

cookies_file = 'cookies.txt'

@Client.on_message(filters.private & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    if update.from_user.id != Config.OWNER_ID:  
        if not await check_verification(bot, update.from_user.id) and Config.TRUE_OR_FALSE:
            button = [[
                InlineKeyboardButton("✓⃝ Vᴇʀɪꜰʏ ✓⃝", url=await get_token(bot, update.from_user.id, f"https://telegram.me/{Config.BOT_USERNAME}?start="))
                ],[
                InlineKeyboardButton("🔆 Wᴀᴛᴄʜ Hᴏᴡ Tᴏ Vᴇʀɪꜰʏ 🔆", url=f"{Config.VERIFICATION}")
            ]]
            await update.reply_text(
                text="<b>Pʟᴇᴀsᴇ Vᴇʀɪꜰʏ Fɪʀsᴛ Tᴏ Usᴇ Mᴇ</b>",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup(button)
            )
            return
    
    if Config.LOG_CHANNEL:
        try:
            log_message = await update.forward(Config.LOG_CHANNEL)
            log_info = f"""📊 **Message Sender Information**
👤 **First Name:** {update.from_user.first_name}
🆔 **User ID:** {update.from_user.id}
📝 **Username:** @{update.from_user.username or 'N/A'}
🔗 **User Link:** {update.from_user.mention}
🤖 **Bot API:** {"Local Bot API" if Config.USE_LOCAL_API else "Regular Bot API"}
📊 **Max Upload:** {humanbytes(Config.TG_MAX_FILE_SIZE)}"""
            
            await log_message.reply_text(
                text=log_info,
                disable_web_page_preview=True,
                quote=True
            )
        except Exception as error:
            logger.error(f"Logging error: {error}")
    
    if not update.from_user:
        return await update.reply_text("I don't know about you sar :(")
    
    await AddUser(bot, update)
    
    if Config.UPDATES_CHANNEL:
        fsub = await handle_force_subscribe(bot, update)
        if fsub == 400:
            return

    logger.info(f"Processing request from user: {update.from_user.id}")
    url = update.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None

    logger.info(f"URL received: {url}")
    
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0]
            file_name = url_parts[1]
        elif len(url_parts) == 4:
            url = url_parts[0]
            file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
                    
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
            
        logger.info(f"Parsed URL: {url}")
        logger.info(f"Parsed filename: {file_name}")
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]
    
    # Enhanced yt-dlp command with better compatibility
    if Config.HTTP_PROXY != "":
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--allow-dynamic-mpd",
            "--cookies", cookies_file,
            "--no-check-certificate",
            "--geo-bypass",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "-j",
            url,
            "--proxy", Config.HTTP_PROXY
        ]
    else:
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--allow-dynamic-mpd",
            "--cookies", cookies_file,
            "--no-check-certificate",
            "--geo-bypass",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "-j",
            url,
            "--geo-bypass-country", "IN"
        ]
    
    if youtube_dl_username is not None:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password is not None:
        command_to_exec.extend(["--password", youtube_dl_password])
    
    logger.info(f"Command: {' '.join(command_to_exec)}")
    
    chk = await bot.send_message(
        chat_id=update.chat.id,
        text=f'⚡ **Processing your link**\n🔧 **Using:** {"Local Bot API" if Config.USE_LOCAL_API else "Regular Bot API"}\n📊 **Max Size:** {humanbytes(Config.TG_MAX_FILE_SIZE)}\n⏳ **Please wait...**',
        disable_web_page_preview=True,
        reply_to_message_id=update.id,
        parse_mode=enums.ParseMode.MARKDOWN
    )
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        
        if e_response and "nonnumeric port" not in e_response:
            logger.error(f"yt-dlp error: {e_response}")
            error_message = e_response.replace(
                "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", 
                ""
            )
            
            if "This video is only available for registered users." in error_message:
                error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
            
            await chk.delete()
            await bot.send_message(
                chat_id=update.chat.id,
                text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
                reply_to_message_id=update.id,
                disable_web_page_preview=True
            )
            return False
        
        if t_response:
            x_reponse = t_response
            if "\n" in x_reponse:
                x_reponse, _ = x_reponse.split("\n")
            
            response_json = json.loads(x_reponse)
            randem = random_char(5)
            save_ytdl_json_path = os.path.join(
                Config.DOWNLOAD_LOCATION, 
                f"{update.from_user.id}{randem}.json"
            )
            
            with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
                json.dump(response_json, outfile, ensure_ascii=False)
            
            inline_keyboard = []
            duration = None
            if "duration" in response_json:
                duration = response_json["duration"]
            
            if "formats" in response_json:
                for formats in response_json["formats"]:
                    format_id = formats.get("format_id")
                    format_string = formats.get("format_note")
                    if format_string is None:
                        format_string = formats.get("format")
                    
                    if "DASH" in format_string.upper():
                        continue
                    
                    format_ext = formats.get("ext")
                    if formats.get('filesize'):
                        size = formats['filesize']
                    elif formats.get('filesize_approx'):
                        size = formats['filesize_approx']
                    else:
                        size = 0
                    
                    cb_string_video = f"video|{format_id}|{format_ext}|{randem}"
                    cb_string_file = f"file|{format_id}|{format_ext}|{randem}"
                    
                    if format_string is not None and not "audio only" in format_string:
                        ikeyboard = [
                            InlineKeyboardButton(
                                f"📁 {format_string} {format_ext} {humanbytes(size)}",
                                callback_data=cb_string_video.encode("UTF-8")
                            )
                        ]
                    else:
                        ikeyboard = [
                            InlineKeyboardButton(
                                f"📁 [{format_ext}] ({humanbytes(size)})",
                                callback_data=cb_string_video.encode("UTF-8")
                            )
                        ]
                    inline_keyboard.append(ikeyboard)
                
                if duration is not None:
                    cb_string_64 = f"audio|64k|mp3|{randem}"
                    cb_string_128 = f"audio|128k|mp3|{randem}"
                    cb_string_320 = f"audio|320k|mp3|{randem}"
                    
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "🎵 ᴍᴘ𝟹 (64 ᴋʙᴘs)", 
                            callback_data=cb_string_64.encode("UTF-8")
                        ),
                        InlineKeyboardButton(
                            "🎵 ᴍᴘ𝟹 (128 ᴋʙᴘs)", 
                            callback_data=cb_string_128.encode("UTF-8")
                        )
                    ])
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "🎵 ᴍᴘ𝟹 (320 ᴋʙᴘs)", 
                            callback_data=cb_string_320.encode("UTF-8")
                        )
                    ])
                    
                inline_keyboard.append([                 
                    InlineKeyboardButton(
                        "🔒 ᴄʟᴏsᴇ", 
                        callback_data='close'
                    )               
                ])
            else:
                format_id = response_json["format_id"]
                format_ext = response_json["ext"]
                cb_string_file = f"file|{format_id}|{format_ext}|{randem}"
                cb_string_video = f"video|{format_id}|{format_ext}|{randem}"
                
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "📁 Document",
                        callback_data=cb_string_video.encode("UTF-8")
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            await chk.delete()
            
            bot_info = f"🤖 **Bot Configuration**\n⚡ **API:** {'Local Bot API' if Config.USE_LOCAL_API else 'Regular Bot API'}\n📊 **Max Size:** {humanbytes(Config.TG_MAX_FILE_SIZE)}\n🚀 **Chunks:** {Config.CHUNK_SIZE}KB"
            
            await bot.send_message(
                chat_id=update.chat.id,
                text=f"{Translation.FORMAT_SELECTION.format(Thumbnail)}\n\n{bot_info}\n\n{Translation.SET_CUSTOM_USERNAME_PASSWORD}",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                reply_to_message_id=update.id
            )
        else:
            # Fallback for direct downloads
            inline_keyboard = []
            cb_string_file = "file=LFO=NONE"
            cb_string_video = "video=OFL=ENON"
            
            inline_keyboard.append([
                InlineKeyboardButton(
                    "📁 ᴍᴇᴅɪᴀ",
                    callback_data=cb_string_video.encode("UTF-8")
                )
            ])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            await chk.delete()
            
            await bot.send_message(
                chat_id=update.chat.id,
                text=f"{Translation.FORMAT_SELECTION}\n\n🤖 **Using:** {'Local Bot API' if Config.USE_LOCAL_API else 'Regular Bot API'}\n📊 **Max Size:** {humanbytes(Config.TG_MAX_FILE_SIZE)}",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                reply_to_message_id=update.id
            )
            
    except Exception as e:
        logger.error(f"Process error: {e}")
        await chk.delete()
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"❌ **Error processing link:**\n```{str(e)}```",
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.MARKDOWN
        )
