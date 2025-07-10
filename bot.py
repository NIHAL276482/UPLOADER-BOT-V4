# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | @NT_BOTS_SUPPORT | LISA-KOREA/UPLOADER-BOT-V4

# [⚠️ Do not change this repo link ⚠️] :- https://github.com/LISA-KOREA/UPLOADER-BOT-V4

import os
from plugins.config import Config
from pyrogram import Client

if __name__ == "__main__":
    
    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)
    
    plugins = dict(root="plugins")
    
    # Enhanced Client configuration for local Bot API
    client_config = {
        "name": "@UploaderXNTBot",
        "bot_token": Config.BOT_TOKEN,
        "api_id": Config.API_ID,
        "api_hash": Config.API_HASH,
        "plugins": plugins,
        "upload_boost": True,
        "sleep_threshold": 300,
    }
    
    # Add local Bot API configuration if enabled
    if Config.USE_LOCAL_API:
        client_config.update({
            "local_mode": True,
            "local_api_host": Config.LOCAL_API_HOST,
            "local_api_port": Config.LOCAL_API_PORT,
        })
        print(f"🌐 Local Bot API Enabled: {Config.LOCAL_API_HOST}:{Config.LOCAL_API_PORT}")
    else:
        print("🌐 Using Official Telegram Bot API")
    
    Client = Client(**client_config)
    
    print("🎊 I AM ALIVE 🎊  • Support @NT_BOTS_SUPPORT")
    print(f"⚡ Max File Size: {Config.TG_MAX_FILE_SIZE // (1024**3):.1f} GB")
    print(f"📁 Download Location: {Config.DOWNLOAD_LOCATION}")
    
    Client.run()
