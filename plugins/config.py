import os
from os import environ, getenv
import logging

logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('log.txt'),
              logging.StreamHandler()],
    level=logging.INFO
)

class Config(object):
    
    # Basic Bot Configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", ""))
    API_HASH = os.environ.get("API_HASH", "")
    
    # Local Bot API Configuration
    USE_LOCAL_API = os.environ.get("USE_LOCAL_API", "True").lower() == "true"
    LOCAL_API_HOST = os.environ.get("LOCAL_API_HOST", "localhost")
    LOCAL_API_PORT = int(os.environ.get("LOCAL_API_PORT", "8081"))
    
    # File Upload Configuration
    DOWNLOAD_LOCATION = "./DOWNLOADS"
    
    # Dynamic file size limits based on Bot API type
    if USE_LOCAL_API:
        # Local Bot API limits (2GB default, can be increased)
        MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2147483648"))  # 2GB
        TG_MAX_FILE_SIZE = int(os.environ.get("TG_MAX_FILE_SIZE", "2147483648"))  # 2GB
        FREE_USER_MAX_FILE_SIZE = int(os.environ.get("FREE_USER_MAX_FILE_SIZE", "2147483648"))  # 2GB
        CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1024"))  # 1MB chunks for better performance
    else:
        # Regular Bot API limits
        MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2194304000"))  # ~2GB
        TG_MAX_FILE_SIZE = int(os.environ.get("TG_MAX_FILE_SIZE", "52428800"))  # 50MB
        FREE_USER_MAX_FILE_SIZE = int(os.environ.get("FREE_USER_MAX_FILE_SIZE", "52428800"))  # 50MB
        CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "128"))  # 128KB chunks
    
    # Upload Strategy Configuration
    USE_FILE_URI = os.environ.get("USE_FILE_URI", "True").lower() == "true"
    LARGE_FILE_THRESHOLD = int(os.environ.get("LARGE_FILE_THRESHOLD", "104857600"))  # 100MB
    
    # Other Configuration
    DEF_THUMB_NAIL_VID_S = os.environ.get("DEF_THUMB_NAIL_VID_S", "https://placehold.it/90x90")
    HTTP_PROXY = os.environ.get("HTTP_PROXY", "")
    
    OUO_IO_API_KEY = ""
    MAX_MESSAGE_LENGTH = 4096
    PROCESS_MAX_TIMEOUT = 3600
    DEF_WATER_MARK_FILE = "@UploaderXNTBot"

    BANNED_USERS = set(int(x) for x in os.environ.get("BANNED_USERS", "").split())

    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # Bot Configuration
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", ""))
    LOGGER = logging
    OWNER_ID = int(os.environ.get("OWNER_ID", ""))
    SESSION_NAME = "UploaderXNTBot"
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    
    # Advanced Configuration
    TG_MIN_FILE_SIZE = 2194304000
    ADL_BOT_RQ = {}

    # Shortlink Configuration
    TRUE_OR_FALSE = os.environ.get("TRUE_OR_FALSE", "").lower() == "true"
    SHORT_DOMAIN = environ.get("SHORT_DOMAIN", "")
    SHORT_API = environ.get("SHORT_API", "")
    VERIFICATION = os.environ.get("VERIFICATION", "")
    
    # *** REMOVED SESSION_STR - NO LONGER NEEDED ***
    # SESSION_STR = ""  # Not needed with local Bot API
