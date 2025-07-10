# @Shrimadhav Uk | @LISA_FAN_LK

import logging
import asyncio
import aiohttp
import json
import math
import os
import shutil
import time
from datetime import datetime
from plugins.config import Config
from plugins.script import Translation
from plugins.thumbnail import *
from plugins.database.database import db
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from plugins.functions.help_uploadbot import upload_file_local_api, upload_video_local_api, upload_audio_local_api
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import enums

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

async def ddl_call_back(bot, update):
    logger.info(f"Direct download callback: {update.data}")
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("=")
    
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = os.path.basename(youtube_dl_url)
    
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
                    
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        
        logger.info(f"URL: {youtube_dl_url}")
        logger.info(f"Filename: {custom_file_name}")
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]
    
    description = Translation.CUSTOM_CAPTION_UL_FILE
    start = datetime.now()
    
    await update.message.edit_caption(
        caption=Translation.DOWNLOAD_START,
        parse_mode=enums.ParseMode.HTML
    )
    
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    
    # Enhanced download with better error handling
    async with aiohttp.ClientSession() as session:
        c_time = time.time()
        try:
            await download_coroutine(
                bot,
                session,
                youtube_dl_url,
                download_directory,
                update.message.chat.id,
                update.message.id,
                c_time
            )
        except asyncio.TimeoutError:
            await bot.edit_message_text(
                text=Translation.SLOW_URL_DECED,
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            await bot.edit_message_text(
                text=f"❌ Download failed: {str(e)}",
                chat_id=update.message.chat.id,
                message_id=update.message.id
            )
            return False
    
    if os.path.exists(download_directory):
        end_one = datetime.now()
        await update.message.edit_caption(
            caption=Translation.UPLOAD_START,
            parse_mode=enums.ParseMode.HTML
        )
        
        file_size = Config.TG_MAX_FILE_SIZE + 1
        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError as exc:
            download_directory = os.path.splitext(download_directory)[0] + ".mkv"
            file_size = os.stat(download_directory).st_size
        
        if file_size > Config.TG_MAX_FILE_SIZE:
            await update.message.edit_caption(
                caption=Translation.RCHD_TG_API_LIMIT,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            start_time = time.time()
            
            try:
                # Enhanced upload using local Bot API functions
                if tg_send_type == "audio":
                    duration = await Mdata03(download_directory)
                    thumbnail = await Gthumb01(bot, update)
                    
                    await upload_audio_local_api(
                        bot,
                        download_directory,
                        update.message.chat.id,
                        caption=description,
                        duration=duration,
                        thumb=thumbnail,
                        progress_callback=progress_for_pyrogram
                    )
                    
                elif tg_send_type == "vm":
                    width, duration = await Mdata02(download_directory)
                    thumbnail = await Gthumb02(bot, update, duration, download_directory)
                    
                    await bot.send_video_note(
                        chat_id=update.message.chat.id,
                        video_note=download_directory,
                        duration=duration,
                        length=width,
                        thumb=thumbnail,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                    
                elif (await db.get_upload_as_doc(update.from_user.id)) is False:
                    # Upload as document
                    thumbnail = await Gthumb01(bot, update)
                    
                    await upload_file_local_api(
                        bot,
                        download_directory,
                        update.message.chat.id,
                        caption=description,
                        progress_callback=progress_for_pyrogram
                    )
                    
                else:
                    # Upload as video
                    width, height, duration = await Mdata01(download_directory)
                    thumb_image_path = await Gthumb02(bot, update, duration, download_directory)
                    
                    await upload_video_local_api(
                        bot,
                        download_directory,
                        update.message.chat.id,
                        caption=description,
                        duration=duration,
                        width=width,
                        height=height,
                        thumb=thumb_image_path,
                        progress_callback=progress_for_pyrogram
                    )
                
                end_two = datetime.now()
                
                try:
                    os.remove(download_directory)
                    if 'thumbnail' in locals():
                        os.remove(thumbnail)
                    if 'thumb_image_path' in locals():
                        os.remove(thumb_image_path)
                except Exception as e:
                    logger.error(f"Error cleaning up: {e}")
                
                time_taken_for_download = (end_one - start).seconds
                time_taken_for_upload = (end_two - end_one).seconds
                
                await update.message.edit_caption(
                    caption=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                        time_taken_for_download, 
                        time_taken_for_upload
                    ),
                    parse_mode=enums.ParseMode.HTML
                )
                
            except Exception as upload_error:
                logger.error(f"Upload error: {upload_error}")
                await update.message.edit_caption(
                    caption=f"❌ Upload failed: {str(upload_error)}",
                    parse_mode=enums.ParseMode.HTML
                )
                return False
    else:
        await update.message.edit_caption(
            caption=Translation.NO_VOID_FORMAT_FOUND.format("File not found"),
            parse_mode=enums.ParseMode.HTML
        )

async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    """Enhanced download coroutine with better progress tracking"""
    downloaded = 0
    display_message = ""
    
    try:
        async with session.get(url, timeout=Config.PROCESS_MAX_TIMEOUT) as response:
            total_length = int(response.headers.get("Content-Length", 0))
            content_type = response.headers.get("Content-Type", "")
            
            if "text" in content_type and total_length < 500:
                return await response.release()
            
            await bot.edit_message_text(
                chat_id,
                message_id,
                text=f"""🔄 Initiating Download
📎 URL: {url[:50]}...
📊 File Size: {humanbytes(total_length)}
🚀 Using {"Local Bot API" if Config.USE_LOCAL_API else "Regular Bot API"}"""
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            
            with open(file_name, "wb") as f_handle:
                while True:
                    chunk = await response.content.read(Config.CHUNK_SIZE)
                    if not chunk:
                        break
                    f_handle.write(chunk)
                    downloaded += len(chunk)
                    
                    now = time.time()
                    diff = now - start
                    
                    if round(diff % 3.00) == 0 or downloaded == total_length:
                        if total_length > 0:
                            percentage = downloaded * 100 / total_length
                            speed = downloaded / diff if diff > 0 else 0
                            elapsed_time = round(diff) * 1000
                            time_to_completion = round((total_length - downloaded) / speed) * 1000 if speed > 0 else 0
                            estimated_total_time = elapsed_time + time_to_completion
                            
                            try:
                                current_message = f"""📥 **Download Status**
📎 URL: {url[:30]}...
📊 File Size: {humanbytes(total_length)}
✅ Downloaded: {humanbytes(downloaded)} ({percentage:.1f}%)
⚡ Speed: {humanbytes(speed)}/s
⏱️ ETA: {TimeFormatter(estimated_total_time)}
🔧 Method: {"Local Bot API" if Config.USE_LOCAL_API else "Regular Bot API"}"""
                                
                                if current_message != display_message:
                                    await bot.edit_message_text(
                                        chat_id,
                                        message_id,
                                        text=current_message
                                    )
                                    display_message = current_message
                            except Exception as e:
                                logger.error(f"Progress update error: {e}")
                                pass
            
            return await response.release()
            
    except Exception as e:
        logger.error(f"Download coroutine error: {e}")
        raise e
