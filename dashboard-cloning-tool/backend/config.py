import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    # Redshift
    REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
    REDSHIFT_PORT = int(os.getenv("REDSHIFT_PORT", 5439))
    REDSHIFT_DB = os.getenv("REDSHIFT_DB")
    REDSHIFT_USER = os.getenv("REDSHIFT_USER")
    REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")
    REDSHIFT_SCHEMA = os.getenv("REDSHIFT_SCHEMA")

    # Tableau
    TABLEAU_URL = os.getenv("TABLEAU_URL")
    TABLEAU_PAT_NAME = os.getenv("TABLEAU_PAT_NAME")
    TABLEAU_PAT_SECRET = os.getenv("TABLEAU_PAT_SECRET")
    TABLEAU_SITE = os.getenv("TABLEAU_SITE")

    # Auth
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))
    INVITE_EXPIRE_HOURS = int(os.getenv("INVITE_EXPIRE_HOURS", 48))

    # Super Admin
    SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL")
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")

    # SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Dashboard Cloning Tool")

    # App
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
    TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")

config = Config()
