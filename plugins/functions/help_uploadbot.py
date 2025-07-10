import logging
import os
import requests
import time
from plugins.config import Config
from plugins.functions.display_progress import humanbytes

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def DetectFileSize(url):
    """Detect file size from URL"""
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        total_size = int(r.headers.get("content-length", 0))
        return total_size
    except Exception as e:
        logger.error(f"Error detecting file size: {e}")
        return 0

def DownLoadFile(url, file_name, chunk_size, client, ud_type, message_id, chat_id):
    """Enhanced download function with better error handling"""
    if os.path.exists(file_name):
        os.remove(file_name)
    if not url:
        return file_name
    
    try:
        r = requests.get(url, allow_redirects=True, stream=True, timeout=Config.PROCESS_MAX_TIMEOUT)
        total_size = int(r.headers.get("content-length", 0))
        downloaded_size = 0
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        
        with open(file_name, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fd.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Update progress every 5% or 5MB
                    if client is not None and total_size > 0:
                        progress_percent = (downloaded_size / total_size) * 100
                        if downloaded_size % (5 * 1024 * 1024) == 0 or progress_percent % 5 == 0:  # Every 5MB or 5%
                            try:
                                client.edit_message_text(
                                    chat_id,
                                    message_id,
                                    text="{}: {} of {} ({:.1f}%)".format(
                                        ud_type,
                                        humanbytes(downloaded_size),
                                        humanbytes(total_size),
                                        progress_percent
                                    )
                                )
                            except Exception as e:
                                logger.error(f"Error updating progress: {e}")
                                pass
        
        logger.info(f"Downloaded {file_name} successfully ({humanbytes(downloaded_size)})")
        return file_name
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        if os.path.exists(file_name):
            os.remove(file_name)
        return None

# Enhanced upload functions for local Bot API
async def upload_file_local_api(client, file_path, chat_id, caption="", progress_callback=None):
    """
    Enhanced upload function that takes advantage of local Bot API features
    """
    try:
        file_size = os.path.getsize(file_path)
        
        if Config.USE_LOCAL_API:
            # Use local Bot API advantages
            if file_size > Config.LARGE_FILE_THRESHOLD and Config.USE_FILE_URI:
                # Use file URI for large files (most efficient)
                file_uri = f"file://{os.path.abspath(file_path)}"
                logger.info(f"Using file URI for large file: {file_uri}")
                
                return await client.send_document(
                    chat_id=chat_id,
                    document=file_uri,
                    caption=caption,
                    progress=progress_callback if progress_callback else None
                )
            else:
                # Use direct file path
                logger.info(f"Using direct file path: {file_path}")
                
                return await client.send_document(
                    chat_id=chat_id,
                    document=file_path,
                    caption=caption,
                    progress=progress_callback if progress_callback else None
                )
        else:
            # Fallback to traditional upload for regular Bot API
            logger.info("Using traditional upload method")
            
            with open(file_path, "rb") as f:
                return await client.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=caption,
                    progress=progress_callback if progress_callback else None
                )
                
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise e

async def upload_video_local_api(client, file_path, chat_id, caption="", duration=0, width=0, height=0, thumb=None, progress_callback=None):
    """
    Enhanced video upload function for local Bot API
    """
    try:
        file_size = os.path.getsize(file_path)
        
        if Config.USE_LOCAL_API:
            # Use local Bot API advantages
            if file_size > Config.LARGE_FILE_THRESHOLD and Config.USE_FILE_URI:
                # Use file URI for large files
                file_uri = f"file://{os.path.abspath(file_path)}"
                logger.info(f"Using file URI for large video: {file_uri}")
                
                return await client.send_video(
                    chat_id=chat_id,
                    video=file_uri,
                    caption=caption,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    supports_streaming=True,
                    progress=progress_callback if progress_callback else None
                )
            else:
                # Use direct file path
                logger.info(f"Using direct file path for video: {file_path}")
                
                return await client.send_video(
                    chat_id=chat_id,
                    video=file_path,
                    caption=caption,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    supports_streaming=True,
                    progress=progress_callback if progress_callback else None
                )
        else:
            # Fallback to traditional upload
            logger.info("Using traditional video upload method")
            
            with open(file_path, "rb") as f:
                return await client.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=caption,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    supports_streaming=True,
                    progress=progress_callback if progress_callback else None
                )
                
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise e

async def upload_audio_local_api(client, file_path, chat_id, caption="", duration=0, thumb=None, progress_callback=None):
    """
    Enhanced audio upload function for local Bot API
    """
    try:
        file_size = os.path.getsize(file_path)
        
        if Config.USE_LOCAL_API:
            # Use local Bot API advantages
            if file_size > Config.LARGE_FILE_THRESHOLD and Config.USE_FILE_URI:
                # Use file URI for large files
                file_uri = f"file://{os.path.abspath(file_path)}"
                logger.info(f"Using file URI for large audio: {file_uri}")
                
                return await client.send_audio(
                    chat_id=chat_id,
                    audio=file_uri,
                    caption=caption,
                    duration=duration,
                    thumb=thumb,
                    progress=progress_callback if progress_callback else None
                )
            else:
                # Use direct file path
                logger.info(f"Using direct file path for audio: {file_path}")
                
                return await client.send_audio(
                    chat_id=chat_id,
                    audio=file_path,
                    caption=caption,
                    duration=duration,
                    thumb=thumb,
                    progress=progress_callback if progress_callback else None
                )
        else:
            # Fallback to traditional upload
            logger.info("Using traditional audio upload method")
            
            with open(file_path, "rb") as f:
                return await client.send_audio(
                    chat_id=chat_id,
                    audio=f,
                    caption=caption,
                    duration=duration,
                    thumb=thumb,
                    progress=progress_callback if progress_callback else None
                )
                
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise e
