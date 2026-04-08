import os
from dotenv import load_dotenv

# Load .env only if it exists (local dev)
# On Railway, environment variables are injected directly — no .env file needed
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

class Config:
    # Redshift
    REDSHIFT_HOST = os.environ.get("REDSHIFT_HOST", "")
    REDSHIFT_PORT = int(os.environ.get("REDSHIFT_PORT", 5439))
    REDSHIFT_DB = os.environ.get("REDSHIFT_DB", "")
    REDSHIFT_USER = os.environ.get("REDSHIFT_USER", "")
    REDSHIFT_PASSWORD = os.environ.get("REDSHIFT_PASSWORD", "")
    REDSHIFT_SCHEMA = os.environ.get("REDSHIFT_SCHEMA", "")

    # Tableau
    TABLEAU_URL = os.environ.get("TABLEAU_URL", "")
    TABLEAU_PAT_NAME = os.environ.get("TABLEAU_PAT_NAME", "")
    TABLEAU_PAT_SECRET = os.environ.get("TABLEAU_PAT_SECRET", "")
    TABLEAU_SITE = os.environ.get("TABLEAU_SITE", "")

    # Auth
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
    JWT_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", 24))
    INVITE_EXPIRE_HOURS = int(os.environ.get("INVITE_EXPIRE_HOURS", 48))

    # Super Admin
    SUPER_ADMIN_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL", "")
    SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "")

    # SMTP
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Dashboard Cloning Tool")

    # App — Railway injects PORT automatically
    APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.environ.get("PORT", os.environ.get("APP_PORT", 8000)))
    OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")
    TEMPLATES_DIR = os.environ.get("TEMPLATES_DIR", "templates")

    # Paths — use /tmp on Railway (ephemeral cloud), local dirs otherwise
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    IS_CLOUD = os.environ.get("RAILWAY_ENVIRONMENT") is not None

    @classmethod
    def get_db_path(cls):
        if cls.IS_CLOUD:
            return "/tmp/app.db"
        return os.path.join(cls.BASE_DIR, "database", "app.db")

    @classmethod
    def get_outputs_dir(cls):
        if cls.IS_CLOUD:
            return "/tmp/outputs"
        return os.path.join(cls.BASE_DIR, cls.OUTPUT_DIR)

    @classmethod
    def get_templates_dir(cls):
        return os.path.join(cls.BASE_DIR, cls.TEMPLATES_DIR)

config = Config()
