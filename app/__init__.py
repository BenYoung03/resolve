from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

from app import routes

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))