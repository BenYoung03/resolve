from datetime import datetime
from datetime import date
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    __tablename__ = "roles"
    
    RoleID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    
    users: so.WriteOnlyMapped['User'] = so.relationship(back_populates='role')
    
    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model, UserMixin):
    __tablename__ = "User"
    
    UserID: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String)
    roleId: so.Mapped[int] = so.mapped_column(sa.ForeignKey('roles.RoleID'), nullable=False)

    role: so.Mapped['Role'] = so.relationship(back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.UserID)
