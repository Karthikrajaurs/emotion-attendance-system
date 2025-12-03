# config.py - Keep your secrets here
import os

# EMAIL CONFIG (Gmail example)
SMTP_EMAIL = "your_email@gmail.com"                    # CHANGE
SMTP_PASSWORD = "your_app_password"                    # CHANGE (16-char app password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces", "photos")
DATABASE_PATH = os.path.join(BASE_DIR, "database", "attendance.db")