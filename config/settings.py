import os
from dotenv import load_dotenv

load_dotenv()

CWA_API_KEY = os.getenv('CWA_API_KEY')

if not CWA_API_KEY:
    raise ValueError("CWA_API_KEY environment variable is required")

# Database Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'cwa_weather'),
    'charset': 'utf8mb4'
}