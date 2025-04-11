import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temp_secret_key_change_in_production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Load config from config.py
app.config.from_pyfile('config.py')

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
mail.init_app(app)

# Configure login settings
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

with app.app_context():
    # Import models to ensure tables are created
    import models
    
    # Create all tables
    db.create_all()

# Import and register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

# Import user loader
from models import Usuario

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
