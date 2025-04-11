import os

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///oguardiao.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Email configuration
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@oguardiao.com.br")

# AWS S3 configuration for certificate storage
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", "oguardiao-certificates")
AWS_S3_REGION = os.environ.get("AWS_S3_REGION", "us-east-1")

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "desenvolvimento-seguro-temporario")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_HTTPONLY = True
WTF_CSRF_ENABLED = True

# Application settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
CERTIFICATE_EXTENSIONS = ['pfx', 'p12', 'cer']
