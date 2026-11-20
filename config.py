import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "it-asset-platform-enterprise-secret-key-2026-prod-jwt-safe")
    
    # MySQL Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Mysql@123")
    DB_NAME = os.getenv("DB_NAME", "it_asset_management")
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Pagination
    ITEMS_PER_PAGE = 10

class TestConfig(Config):
    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "it_asset_management")
