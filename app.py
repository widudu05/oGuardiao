import os
import logging
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()

# Create the app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "oguardiao-dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///oguardiao.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Security configurations
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Mail configuration
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@oguardiao.com")

# Initialize extensions with app
db.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Login manager configuration
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# Import models and routes after initializing app to avoid circular imports
with app.app_context():
    # Import all models so they are registered with SQLAlchemy
    from models import User, Organization, Company, Certificate, AuditLog, UserInvite, Group

    # Create all tables
    db.create_all()

# Import route modules
from auth import *

# Register error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=404, message="Página não encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error=500, message="Erro interno do servidor"), 500

# Context processor for global template variables
@app.context_processor
def utility_processor():
    def check_expiring_certificates():
        if current_user.is_authenticated:
            from models import Certificate
            from datetime import datetime, timedelta
            
            today = datetime.now().date()
            expiring_soon = Certificate.query.filter(
                Certificate.expiry_date <= today + timedelta(days=30),
                Certificate.expiry_date > today
            ).count()
            
            return expiring_soon
        return 0
    
    return {
        'check_expiring_certificates': check_expiring_certificates,
        'now': datetime.now()
    }

# Middleware to track last activity
@app.before_request
def update_last_activity():
    if current_user.is_authenticated:
        current_user.last_active = datetime.utcnow()
        db.session.commit()

# Note: Role decorator functions are defined in auth.py

if __name__ == "__main__":
    # Only for development
    app.run(host="0.0.0.0", port=5000, debug=True)
