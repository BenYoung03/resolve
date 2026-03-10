from datetime import datetime
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

    users: so.WriteOnlyMapped["User"] = so.relationship(back_populates="role")
    active: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model, UserMixin):
    __tablename__ = "User"

    UserID: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, server_default="")
    password_hash: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    roleId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("roles.RoleID"), nullable=False)

    role: so.Mapped["Role"] = so.relationship(back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, roles):
        if isinstance(roles, str):
            roles = [roles]
        return self.role.name in roles

    def get_id(self):
        return str(self.UserID)


class Category(db.Model):
    __tablename__ = "Category"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    active: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, default=True)


class Status(db.Model):
    __tablename__ = "Status"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)


class Priority(db.Model):
    __tablename__ = "Priority"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    kind: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)


class Ticket(db.Model):
    __tablename__ = "Ticket"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("User.UserID"), nullable=False)
    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Category.id"), nullable=False)

    status: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Status.id"), nullable=False)

    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.utcnow)

    agent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("User.UserID"), nullable=True)
    priority_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Priority.id"), nullable=False)


class TicketComment(db.Model):
    __tablename__ = "Ticket_Comment"

    ticket_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Ticket.id"), nullable=False)
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("User.UserID"), nullable=False)
    text: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.utcnow)


class Permission(db.Model):
    __tablename__ = "Permission"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True)

class RolePermission(db.Model):
    __tablename__ = "RolePermission"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("roles.RoleID"), nullable=False)
    permission_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Permission.id"), nullable=False)