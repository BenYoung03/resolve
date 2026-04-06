from datetime import datetime
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from time import time

import jwt

class Role(db.Model):
    __tablename__ = "Roles"

    RoleID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    active: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    permissions: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True, default="")

    users: so.Mapped[list["User"]] = so.relationship(back_populates="role")

    def permission_list(self):
        if not self.permissions:
            return []
        return [p.strip() for p in self.permissions.split(",") if p.strip()]

    def has_permission(self, *permissions):
        if len(permissions) == 1 and isinstance(permissions[0], (list, tuple, set)):
            permissions = tuple(permissions[0])

        current_permissions = set(self.permission_list())
        return any(permission in current_permissions for permission in permissions)

    def set_permissions(self, permissions):
        cleaned = sorted({p.strip() for p in permissions if p and p.strip()})
        self.permissions = ",".join(cleaned)

    def __repr__(self):
        return f"<Role {self.name}>"

# User model
class User(db.Model, UserMixin):
    __tablename__ = "User"

    # Each user has an ID, username, email, password hash, role, and notification preference
    UserID: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    email: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    roleId: so.Mapped[int] = so.mapped_column(sa.ForeignKey("Roles.RoleID"), nullable=False)
    notifications: so.Mapped[bool] = so.mapped_column(sa.Boolean, nullable=False, server_default=sa.true())

    # Relationships to other models
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

    activity_logs: so.Mapped[list["ActivityLog"]] = so.relationship(
        back_populates="user"
    )

    # Set and check the password hash for the user
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    # Checks if a user has an indicated role
    def has_role(self, *roles):
        if len(roles) == 1:
            if isinstance(roles[0], str):
                roles = [roles[0]]
            else:
                roles = list(roles[0])
        else:
            roles = list(roles)

        return self.role.name in roles

    # Checks if a user has any of the indicated permissions
    def has_permission(self, *permissions):
        if not self.role:
            return False
        return self.role.has_permission(*permissions)

    # Checks if a user has any admin access
    def has_any_admin_access(self):
        return (
            self.has_role("Admin") or
            self.has_permission(
                "view_roles", "create_roles",
                "view_users", "create_users",
                "view_clients",
                "change_settings",
                "view_profile"
            )
        )

    def get_id(self):
        return str(self.UserID)

    # Gets the password reset token for the user and appends it to the URL for resetting the password
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.UserID, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )
    
    # Verifies the password reset token and returns the user associated with the token if valid
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return 
        return db.session.get(User, id)

    def __repr__(self):
        return f"<User {self.username or self.email}>"

# Ticket category model
class Category(db.Model):
    __tablename__ = "TicketCategories"

    CategoryID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


# Ticket priority model
class Priority(db.Model):
    __tablename__ = "TicketPriority"

    PriorityID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="priority")

    def __repr__(self):
        return f"<Priority {self.name}>"

# Ticket status model
class Status(db.Model):
    __tablename__ = "TicketStatus"

    StatusID: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[Optional[str]] = so.mapped_column(sa.String)

    tickets: so.Mapped[list["Ticket"]] = so.relationship(back_populates="status")

    def __repr__(self):
        return f"<Status {self.name}>"

# Ticket model
class Ticket(db.Model):
    __tablename__ = "Tickets"

    # Each ticket has an ID, number, subject and description
    TicketID: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    ticketNumber: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    subject: so.Mapped[Optional[str]] = so.mapped_column(sa.String)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)

    # Each ticket is also associated with a category, status, priority, creator, and assignee
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

    # Further ticket fields include resolution and timestamps for creation and closure
    ResolutionReasoning: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    CreatedAt: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)
    ClosedAt: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, nullable=True)

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

    activity_logs: so.Mapped[list["ActivityLog"]] = so.relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="desc(ActivityLog.CreatedAt)"
    )

    def __repr__(self):
        return f"<Ticket {self.TicketID}: {self.subject}>"

# Ticket comment model
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
    CreatedAt: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)


    ticket: so.Mapped["Ticket"] = so.relationship(back_populates="comments")
    user: so.Mapped["User"] = so.relationship(back_populates="comments")

    def __repr__(self):
        return f"<TicketComment {self.CommentID}>"

# Activity log model
class ActivityLog(db.Model):
    __tablename__ = "ActivityLog"

    LogID: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    UserID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("User.UserID"),
        nullable=False
    )
    TicketID: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("Tickets.TicketID"),
        nullable=False
    )
    action: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    CreatedAt: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)  

    user: so.Mapped["User"] = so.relationship(back_populates="activity_logs")
    ticket: so.Mapped["Ticket"] = so.relationship(back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.LogID}: {self.action} at {self.CreatedAt}>"