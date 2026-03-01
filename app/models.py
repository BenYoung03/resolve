from datetime import datetime
from datetime import date
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from resolve import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash