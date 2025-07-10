# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL

import logging
import asyncio
import json
import os
import shutil
import time
from datetime import datetime
from pyrogram import enums
from pyrogram.types import InputMediaPhoto
from plugins.config import Config
from plugins.script import Translation
from plugins.thumbnail import *
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes
from plugins.functions.help_uploadbot import upload_file_local_api, upload_video_local_api, upload_audio_local_api
from plugins.database.database import db
from PIL import Image
from plugins.functions.ran_text import random_char
cookies_file = 'cookies.txt'

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext, ranom = cb_data.split("|")
    random1 = random_char(5)
    
    save_ytdl_json_path = os.path.join(Config.DOWNLOAD_LOCATION, f"{update.from_user.id}{ranom}.json")
    
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"JSON file not found: {e}")
        await update.message.delete()
        return False
    
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = f"{response_json.get('title', 'video')}_{youtube_dl_format}.{youtube_dl_ext}"
    youtube_dl_username = None
    youtube_dl_password = None
    
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url, custom_file_name = url_parts
        elif len(url_parts) == 4:
            youtube_dl_url, custom_file_name, youtube_dl_username, youtube_dl_password = url_parts
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
                    
        youtube_dl_url = youtube_dl_url.strip()
        custom_file_name = custom_file_name.strip()
        if youtube_dl_username:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password:
            youtube_dl_password = youtube_dl_password.strip()
        
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

    await update.message.edit_caption(
        caption=Translation.DOWNLOAD_START.format(custom_file_name)
    )
    
    description = Translation.CUSTOM_CAPTION_UL_FILE
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]
    
    tmp_directory_for_each_user = os.path.join(Config.DOWNLOAD_LOCATION, f"{update.from_user.id}{random1}")
    os.makedirs(tmp_directory_for_each_user, exist_ok=True)
    download_directory = os.path.join(tmp_directory_for_each_user, custom_file_name)
    
    # Enhanced command for better compatibility
    command_to_exec = [
        "yt-dlp",
        "-c",
        "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
        "--embed-subs",
        "-f", f"{youtube_dl_format}+bestaudio/best" if youtube_dl_format != "best" else "best",
        "--hls-prefer-ffmpeg",
        "--cookies", cookies_file,
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "--no-warnings",
        "--no-check-certificate",
        "--geo-bypass",
        "--merge-output-format", "mp4",
        youtube_dl_url,
        "-o", download_directory
    ]
    
    if tg_send_type == "audio":
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--extract-audio",
            "--cookies", cookies_file,
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            "--embed-thumbnail",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "--no-warnings",
            "--no-check-certificate",
            "--geo-bypass",
            youtube_dl_url,
            "-o", download_directory
        ]
    
    if Config.HTTP_PROXY:
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])
    if youtube_dl_username:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password:
        command_to_exec.extend(["--password", youtube_dl_password])
    
    logger.info(f"Command: {' '.join(command_to_exec)}")
    start = datetime.now()
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        
        if e_response:
            logger.error(f"yt-dlp stderr: {e_response}")
        if t_response:
            logger.info(f"yt-dlp stdout: {t_response}")
        
        if process.returncode != 0:
            logger.error(f"yt-dlp failed with return code {process.returncode}")
            await update.message.edit_caption(
                caption=f"❌ Download failed: {e_response}"
            )
            return False
        
        # Clean up JSON file
        try:
            os.remove(save_ytdl_json_path)
        except FileNotFoundError:
            pass
        
        end_one = datetime.now()
        time_taken_for_download = (end_one - start).seconds
        
        # Find the downloaded file
        downloaded_file = None
        for file_name in os.listdir(tmp_directory_for_each_user):
            if file_name.startswith(custom_file_name.split('.')[0]):
                downloaded_file = os.path.join(tmp_directory_for_each_user, file_name)
                break
        
        if not downloaded_file or not os.path.isfile(downloaded_file):
            logger.error(f"Downloaded file not found in {tmp_directory_for_each_user}")
            await update.message.edit_caption(
                caption="❌ Download failed: File not found"
            )
            return False
        
        file_size = os.path.getsize(downloaded_file)
        logger.info(f"Downloaded file: {downloaded_file} ({humanbytes(file_size)})")
        
        if file_size > Config.TG_MAX_FILE_SIZE:
            await update.message.edit_caption(
                caption=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size))
            )
            return False
        
        # Upload phase
        await update.message.edit_caption(
            caption=Translation.UPLOAD_START.format(os.path.basename(downloaded_file))
        )
        
        start_time = time.time()
        
        # Enhanced upload with local Bot API support
        try:
            if tg_send_type == "audio":
                duration = await Mdata03(downloaded_file)
                thumbnail = await Gthumb01(bot, update)
                
                await upload_audio_local_api(
                    bot,
                    downloaded_file,
                    update.message.chat.id,
                    caption=description,
                    duration=duration,
                    thumb=thumbnail,
                    progress_callback=progress_for_pyrogram
                )
                
            elif not await db.get_upload_as_doc(update.from_user.id):
                # Upload as document
                thumbnail = await Gthumb01(bot, update)
                
                await upload_file_local_api(
                    bot,
                    downloaded_file,
                    update.message.chat.id,
                    caption=description,
                    progress_callback=progress_for_pyrogram
                )
                
            else:
                # Upload as video
                width, height, duration = await Mdata01(downloaded_file)
                thumb_image_path = await Gthumb02(bot, update, duration, downloaded_file)
                
                await upload_video_local_api(
                    bot,
                    downloaded_file,
                    update.message.chat.id,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb_image_path,
                    progress_callback=progress_for_pyrogram
                )
            
            end_two = datetime.now()
            time_taken_for_upload = (end_two - end_one).seconds
            
            # Clean up
            try:
                shutil.rmtree(tmp_directory_for_each_user)
            except Exception as e:
                logger.error(f"Error cleaning up: {e}")
            
            await update.message.edit_caption(
                caption=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                    time_taken_for_download, 
                    time_taken_for_upload
                )
            )
            
            logger.info(f"✅ Upload completed - Download: {time_taken_for_download}s, Upload: {time_taken_for_upload}s")
            
        except Exception as upload_error:
            logger.error(f"Upload error: {upload_error}")
            await update.message.edit_caption(
                caption=f"❌ Upload failed: {str(upload_error)}"
            )
            return False
    
    except Exception as e:
        logger.error(f"Process error: {e}")
        await update.message.edit_caption(
            caption=f"❌ Process failed: {str(e)}"
        )
        return False
