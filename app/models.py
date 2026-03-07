from datetime import datetime
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Role(db.Model):
    __tablename__ = "Roles"

    RoleID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)

    users: so.Mapped[list["User"]] = so.relationship(back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"



class User(db.Model, UserMixin):
    __tablename__ = "User"

    UserID: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    roleId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Roles.RoleID"), nullable=False)

    role: so.Mapped["Role"] = so.relationship(back_populates="users")

    created_tickets: so.Mapped[list["Ticket"]] = so.relationship(
        foreign_keys="Ticket.CreatedBy",
        back_populates="creator"
    )

    assigned_tickets: so.Mapped[list["Ticket"]] = so.relationship(
        foreign_keys="Ticket.AssignedTo",
        back_populates="assignee"
    )

    comments: so.Mapped[list["TicketComment"]] = so.relationship(
        back_populates="user"
    )

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

    def __repr__(self):
        return f"<User {self.email}>"



class Category(db.Model):
    __tablename__ = "TicketCategories"

    CategoryID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"



class Priority(db.Model):
    __tablename__ = "TicketPriority"

    PriorityID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="priority")

    def __repr__(self):
        return f"<Priority {self.name}>"



class Status(db.Model):
    __tablename__ = "TicketStatus"

    StatusID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="status")

    def __repr__(self):
        return f"<Status {self.name}>"



class Ticket(db.Model):
    __tablename__ = "Tickets"

    TicketID: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    subject: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)

    CategoryID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("TicketCategories.CategoryID"),
        nullable=False
    )
    StatusID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("TicketStatus.StatusID"),
        nullable=False
    )
    PriorityID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("TicketPriority.PriorityID"),
        nullable=False
    )
    CreatedBy: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("User.UserID"),
        nullable=False
    )
    AssignedTo: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey("User.UserID"),
        nullable=True
    )
    CreatedAt: so.Mapped[str] = so.mapped_column(nullable=False)
    ClosedAt: so.Mapped[Optional[str]] = so.mapped_column(nullable=True)

    category: so.Mapped["Category"] = so.relationship(back_populates="tickets")
    status: so.Mapped["Status"] = so.relationship(back_populates="tickets")
    priority: so.Mapped["Priority"] = so.relationship(back_populates="tickets")

    creator: so.Mapped["User"] = so.relationship(
        foreign_keys=[CreatedBy],
        back_populates="created_tickets"
    )
    assignee: so.Mapped[Optional["User"]] = so.relationship(
        foreign_keys=[AssignedTo],
        back_populates="assigned_tickets"
    )

    comments: so.Mapped[list["TicketComment"]] = so.relationship(
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ticket {self.TicketID}: {self.subject}>"



class TicketComment(db.Model):
    __tablename__ = "TicketComment"

    CommentID: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    TicketID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("Tickets.TicketID"),
        nullable=False
    )
    UserID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("User.UserID"),
        nullable=False
    )
    comment: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    CreatedAt: so.Mapped[str] = so.mapped_column(
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP")
    )

    ticket: so.Mapped["Ticket"] = so.relationship(back_populates="comments")
    user: so.Mapped["User"] = so.relationship(back_populates="comments")

    def __repr__(self):
        return f"<TicketComment {self.CommentID}>"