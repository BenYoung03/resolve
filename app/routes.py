from app import app, db
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
# from app.forms import CommentForm, LoginForm, PasswordResetForm, RegistrationForm, CreateTicketForm, ResetPasswordForm, UpdateTicket
from app.forms import (
    CommentForm, LoginForm, RegistrationForm, CreateTicketForm, UpdateTicket,
    AdminSettingsForm, AdminProfileForm, AdminNewClientForm, AdminRoleForm,
    AdminResetPasswordForm, AdminNewUserForm, PasswordResetForm, ResetPasswordForm
)
from app.models import TicketComment, User, Role, Category, Status, Priority, Ticket
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

from flask_mail import Message
from app import mail
from app.email import notifyAgentsOfNewTicket, ticketAssignedNotification, ticketCreated, ticketStatusChangeNotification, passwordResetEmail, commentAddedNotification

#Role required route. If you place @role_required("Role here") under any of the routes, the user will
#Have to have that role to run the route
def role_required(*role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role):
                flash('Access denied. Insufficient permissions.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
@app.route('/index')
def index():

    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    # This currently finds only tickets that are not resolved or closed. Perhaps change logic later
    elif current_user.has_role('Employee'):
        tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.notin_([5, 6])).order_by(Ticket.CreatedAt.desc())).all())
    else:
        tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.StatusID.notin_([5, 6])).order_by(Ticket.CreatedAt.desc())).all())

    return render_template('index.html', title='Home', tickets=tickets)

@app.route('/index/closed')
def closed_tickets():
    if not current_user.is_authenticated:
        tickets = []
    elif current_user.has_role('Employee'):
        tickets = (db.session.scalars(sa.select(Ticket).where(
            sa.and_(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.in_([5, 6]))
        ).order_by(Ticket.CreatedAt.desc())).all())
    else:
        tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.StatusID.in_([5, 6])).order_by(Ticket.CreatedAt.desc())).all())

    return render_template('index.html', title='Closed Tickets', tickets=tickets)

@app.route('/index/open')
def open_tickets():
    if not current_user.is_authenticated:
        tickets = []
    elif current_user.has_role('Employee'):
        tickets = (db.session.scalars(sa.select(Ticket).where(
            sa.and_(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.notin_([5,6]))
        ).order_by(Ticket.CreatedAt.desc())).all())
    else:
        tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.StatusID.notin_([5,6])).order_by(Ticket.CreatedAt.desc())).all())

    return render_template('index.html', title='Open Tickets', tickets=tickets)

@app.route('/index/assigned/<int:UserID>', methods=['GET', 'POST'])
@role_required("Agent", "Admin")
def assigned_tickets(UserID):
    if not current_user.is_authenticated:
        tickets = []
    else:
        tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.AssignedTo == current_user.UserID, Ticket.StatusID.notin_([5,6])).order_by(Ticket.CreatedAt.desc())).all())

    return render_template('index.html', title='Assigned Tickets', tickets=tickets)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Get form data on submission
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        # If password incorrect or email doesnt exist do not login
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        # If details correct, run Flask-Login "login_user"
        login_user(user, remember=True)
        return redirect(url_for('index'))

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():  
        # On form submission, get the data from the form
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirmPassword = form.confirmPassword.data

        if password != confirmPassword:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        # If register form filled in correctly, make sure user doesn't exist by finding
        # If a matching email is already in the database
        user = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()

        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))  

        if existing_username:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Commit new user to database if no user already exists
        new_user = User(username=username, email=email, password_hash=generate_password_hash(password), roleId=1)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/password-reset-request', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordResetForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            passwordResetEmail(user)
        flash('If an account with that email exists, a password reset email has been sent.')
        return redirect(url_for('login'))
    
    if request.method == 'POST' and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'error')
    return render_template('resetPasswordReq.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token. Please try again.')
        return redirect(url_for('login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    
    if request.method == 'POST' and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'error')

    return render_template('resetPassword.html', form=form)

#Logout route
@app.route('/logout')
#If user is logged in allow them to run this route
@login_required
def logout():
    # Run logout_user and redirect to home page
    logout_user()
    return redirect(url_for('index'))

@app.route('/createticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    form = CreateTicketForm()

    form.category.choices = [(c.CategoryID, c.name) for c in Category.query.all()]
    form.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]
    if form.validate_on_submit():
        newTicket = Ticket(
            subject=form.subject.data,
            description=form.description.data,
            CategoryID=form.category.data,
            PriorityID=form.priority.data,
            StatusID=1,  # Sets status to open by default
            CreatedBy=current_user.UserID,
            AssignedTo=None,
            CreatedAt=datetime.now(),
            ClosedAt=None
        )

        db.session.add(newTicket)
        db.session.flush() 

        newTicket.ticketNumber = f"ID-{newTicket.TicketID:06d}"

        db.session.commit()
        ticketCreated(newTicket, current_user.email)

        agents = (db.session.scalars(sa.select(User).where(User.roleId.in_([2, 3]))).all())
        agentsEmails = [agent.email for agent in agents]
        notifyAgentsOfNewTicket(newTicket, agentsEmails)

        flash(f'Ticket {newTicket.ticketNumber} created successfully.')
        return redirect(url_for('index'))
    
    if request.method == "POST" and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "warning")

    return render_template('newticket.html', form=form)

@app.route('/ticket/<int:TicketID>', methods=['GET', 'POST'])
@login_required
def view_ticket(TicketID):

    if current_user.has_role('Employee'):
        ticket = db.session.scalar(sa.select(Ticket).where(Ticket.TicketID == TicketID))
        if not ticket or ticket.CreatedBy != current_user.UserID:
            flash('You do not have permission to view this ticket.')
            return redirect(url_for('index'))
        
    addCommentForm = CommentForm()
    updateTicketForm = UpdateTicket()

    updateTicketForm.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]
    updateTicketForm.status.choices = [(s.StatusID, s.name) for s in Status.query.all()]
    updateTicketForm.assignedTo.choices = [(0, 'Unassigned')] + [
        (u.UserID, u.username) 
        for u in User.query.join(Role).filter(Role.name.in_(["Agent", "Admin"])).all()
    ]

    currentTicket = db.session.scalar(sa.select(Ticket).where(Ticket.TicketID == TicketID))
    comments = db.session.scalars(
        sa.select(TicketComment).where(TicketComment.TicketID == TicketID).order_by(TicketComment.CreatedAt.asc())
    ).all()

    temp = (currentTicket.ClosedAt if currentTicket.ClosedAt else datetime.now()) - currentTicket.CreatedAt    
    totalSeconds = int(temp.total_seconds())
    hours = totalSeconds // 3600
    minutes = (totalSeconds % 3600) // 60
    if hours >= 24:
        days = hours // 24
        hours = hours % 24
        ticketAge = f"{days} day {hours}h {minutes}m" if days == 1 else f"{days} days {hours}h {minutes}m"
    else:
        ticketAge = f"{hours}h {minutes}m"

    if request.method == 'GET':
        updateTicketForm.priority.data = currentTicket.PriorityID
        updateTicketForm.status.data = currentTicket.StatusID
        updateTicketForm.assignedTo.data = currentTicket.assignee.UserID if currentTicket.assignee else 0
        updateTicketForm.resolutionReasoning.data = currentTicket.ResolutionReasoning or ""

    if addCommentForm.validate_on_submit():
        newComment = TicketComment(
            comment=addCommentForm.comment.data,
            TicketID=TicketID,
            UserID=current_user.UserID,
            CreatedAt=datetime.now()
        )
        commentAddedNotification(
            currentTicket,
            currentTicket.creator.email,
            current_user.email,
            addCommentForm.comment.data,
            newComment.CreatedAt,
            current_user.role.name if current_user.role else None,
        )
        db.session.add(newComment)
        db.session.commit()
        
        return redirect(url_for('view_ticket', TicketID=TicketID))
    
    # TODO: Add more flash style error messages
    if updateTicketForm.validate_on_submit():
        # Only agents and admins can update tickets
        if not current_user.has_role(['Agent', 'Admin']):
            flash('Access denied. Only agents and admins can update tickets.')
            return redirect(url_for('view_ticket', TicketID=TicketID))
        
        oldStatus = currentTicket.StatusID
        currentTicket.PriorityID = updateTicketForm.priority.data
        currentTicket.StatusID = updateTicketForm.status.data
        oldAssigned = currentTicket.assignee.UserID if currentTicket.assignee else None
        currentTicket.AssignedTo = updateTicketForm.assignedTo.data if updateTicketForm.assignedTo.data != 0 else None
        # Makes it so ticket cannot be set to open if it is assigned
        if updateTicketForm.assignedTo.data != 0 and updateTicketForm.status.data == 1:
            flash("Assigned tickets cannot have status 'Open'")
            return redirect(url_for("view_ticket", TicketID=TicketID))

        if updateTicketForm.status.data in [5, 6] and not currentTicket.ClosedAt:
            currentTicket.ClosedAt = datetime.now()
        elif updateTicketForm.status.data not in [5, 6]:
            currentTicket.ClosedAt = None

        if updateTicketForm.resolutionReasoning.data:
            currentTicket.ResolutionReasoning = updateTicketForm.resolutionReasoning.data

        db.session.commit()

        if oldStatus != currentTicket.StatusID:
            recipient = currentTicket.creator.email
            oldStatusName = db.session.scalar(sa.select(Status.name).where(Status.StatusID == oldStatus))
            newStatusName = db.session.scalar(sa.select(Status.name).where(Status.StatusID == currentTicket.StatusID))
            if app.config['MAIL_SUPPRESS_SEND']:
                print(f"email failed to send")
            else:
                ticketStatusChangeNotification(currentTicket, recipient, oldStatusName, newStatusName)
        
        newAssigned = currentTicket.assignee.UserID if currentTicket.assignee else None
        if oldAssigned != newAssigned and newAssigned is not None:
            recipient = currentTicket.assignee.email
            ticketAssignedNotification(currentTicket, recipient)
        if currentTicket.StatusID == 5:
            return redirect(url_for('view_ticket', TicketID=TicketID, confetti=1))
        return redirect(url_for('view_ticket', TicketID=TicketID))

    return render_template('ticketview.html', ticket_id=TicketID, ticket=currentTicket,
                           comments=comments, commentForm=addCommentForm, updateTicketForm=updateTicketForm,
                           ticketAge=ticketAge, show_confetti=request.args.get('confetti') == '1')
@app.route('/admin')
@login_required
@role_required("Admin")
def admin_functionalities():
    return render_template('admin_functionalities.html')

@app.route('/admin/users')
@login_required
@role_required("Admin")
def admin_users():
    users = db.session.scalars(sa.select(User).order_by(User.username.asc())).all()

    role_choices = [
        (role.RoleID, role.name)
        for role in db.session.scalars(sa.select(Role).order_by(Role.name.asc())).all()
    ]

    role_form = AdminRoleForm()
    role_form.role.choices = role_choices

    reset_form = AdminResetPasswordForm()

    new_user_form = AdminNewUserForm()
    new_user_form.role.choices = role_choices

    return render_template(
        'admin_users.html',
        users=users,
        role_form=role_form,
        reset_form=reset_form,
        new_user_form=new_user_form
    )


@app.route('/admin/clients')
@login_required
@role_required("Admin")
def admin_clients():
    clients = db.session.scalars(
        sa.select(User).join(Role).where(Role.name == "Employee").order_by(User.username.asc())
    ).all()
    new_client_form = AdminNewClientForm()
    return render_template('admin_clients.html', clients=clients, new_client_form=new_client_form)


@app.route('/admin/roles')
@login_required
@role_required("Admin")
def admin_roles():
    roles = db.session.scalars(sa.select(Role).order_by(Role.name.asc())).all()
    form = AdminRoleForm()
    return render_template('admin_roles.html', roles=roles, form=form)


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@role_required("Admin")
def admin_settings():
    form = AdminSettingsForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.old_password.data):
            flash('Old password is incorrect.')
            return redirect(url_for('admin_settings'))
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Password updated.')
        return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html', form=form)


@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
@role_required("Admin")
def admin_profile():
    form = AdminProfileForm()

    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.language.data = 'English'

    if form.validate_on_submit():
        duplicate_username = db.session.scalar(
            sa.select(User).where(
                sa.and_(User.username == form.username.data, User.UserID != current_user.UserID)
            )
        )
        duplicate_email = db.session.scalar(
            sa.select(User).where(
                sa.and_(User.email == form.email.data, User.UserID != current_user.UserID)
            )
        )

        if duplicate_username:
            flash('Username already exists.')
            return redirect(url_for('admin_profile'))

        if duplicate_email:
            flash('Email already exists.')
            return redirect(url_for('admin_profile'))

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated.')
        return redirect(url_for('admin_profile'))

    return render_template('admin_profile.html', form=form)

@app.route('/admin/change-role/<int:user_id>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_change_role(user_id):
    form = AdminRoleForm()
    form.role.choices = [
        (role.RoleID, role.name)
        for role in db.session.scalars(sa.select(Role).order_by(Role.name.asc())).all()
    ]

    if not form.validate_on_submit():
        flash('Invalid role form.')
        return redirect(url_for('admin_users'))

    user = db.session.get(User, user_id)
    role = db.session.get(Role, form.role.data)

    if not user or not role:
        flash('User or role not found.')
        return redirect(url_for('admin_users'))

    user.roleId = role.RoleID
    db.session.commit()
    flash(f'Role for {user.username} updated to {role.name}.')
    return redirect(url_for('admin_users'))
@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_reset_password(user_id):
    form = AdminResetPasswordForm()

    if not form.validate_on_submit():
        flash('Invalid reset password form.')
        return redirect(url_for('admin_users'))

    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('admin_users'))

    user.password_hash = generate_password_hash(form.new_password.data)
    db.session.commit()
    flash(f'Password reset for {user.username}.')
    return redirect(url_for('admin_users'))

@app.route('/admin/new-user', methods=['POST'])
@login_required
@role_required("Admin")
def admin_new_user():
    form = AdminNewUserForm()
    form.role.choices = [
        (role.RoleID, role.name)
        for role in db.session.scalars(sa.select(Role).order_by(Role.name.asc())).all()
    ]

    if not form.validate_on_submit():
        flash('Invalid new user form.')
        return redirect(url_for('admin_users'))

    existing_user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
    existing_name = db.session.scalar(sa.select(User).where(User.username == form.username.data))

    if existing_user or existing_name:
        flash('User username or email already exists.')
        return redirect(url_for('admin_users'))

    role = db.session.get(Role, form.role.data)
    if not role:
        flash('Selected role does not exist.')
        return redirect(url_for('admin_users'))

    user = User(
        username=form.username.data,
        email=form.email.data,
        password_hash=generate_password_hash(form.password.data),
        roleId=role.RoleID
    )
    db.session.add(user)
    db.session.commit()
    flash('User created.')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_delete_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        flash('User not found.')
        return redirect(url_for('admin_users'))

    if user.UserID == current_user.UserID:
        flash('You cannot delete your own account.')
        return redirect(url_for('admin_users'))

    has_tickets = db.session.scalar(
        sa.select(Ticket.TicketID).where(
            sa.or_(Ticket.CreatedBy == user.UserID, Ticket.AssignedTo == user.UserID)
        ).limit(1)
    )
    has_comments = db.session.scalar(
        sa.select(TicketComment.CommentID).where(TicketComment.UserID == user.UserID).limit(1)
    )

    if has_tickets or has_comments:
        flash('Cannot delete user because they are linked to tickets or comments.')
        return redirect(url_for('admin_users'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('admin_users'))


@app.route('/admin/new-client', methods=['POST'])
@login_required
@role_required("Admin")
def admin_new_client():
    form = AdminNewClientForm()
    if not form.validate_on_submit():
        flash('Invalid client form.')
        return redirect(url_for('admin_clients'))

    existing_user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
    existing_name = db.session.scalar(sa.select(User).where(User.username == form.username.data))
    if existing_user or existing_name:
        flash('Client username or email already exists.')
        return redirect(url_for('admin_clients'))

    employee_role = db.session.scalar(sa.select(Role).where(Role.name == "Employee"))
    if not employee_role:
        flash('Employee role is missing.')
        return redirect(url_for('admin_clients'))

    user = User(
        username=form.username.data,
        email=form.email.data,
        password_hash=generate_password_hash(form.password.data),
        roleId=employee_role.RoleID
    )
    db.session.add(user)
    db.session.commit()
    flash('Client created.')
    return redirect(url_for('admin_clients'))


@app.route('/admin/toggle-all-roles/<int:active>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_toggle_all_roles(active):
    roles = db.session.scalars(sa.select(Role)).all()
    core_roles = {"Admin", "Agent", "Employee"}

    for role in roles:
        if hasattr(role, 'active') and role.name not in core_roles:
            role.active = bool(active)

    db.session.commit()
    flash('Custom roles updated.')
    return redirect(url_for('admin_roles'))

@app.route('/admin/toggle-role/<int:role_id>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_toggle_role(role_id):
    role = db.session.get(Role, role_id)

    if not role:
        flash('Role not found.')
        return redirect(url_for('admin_roles'))

    if role.name in {"Admin", "Agent", "Employee"}:
        flash('Core roles cannot be disabled here.')
        return redirect(url_for('admin_roles'))

    if hasattr(role, 'active'):
        role.active = not role.active
        db.session.commit()
        flash('Role updated.')

    return redirect(url_for('admin_roles'))

@app.route('/admin/edit-role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@role_required("Admin")
def admin_edit_role(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        flash('Role not found.')
        return redirect(url_for('admin_roles'))

    form = AdminRoleForm()
    form.role.choices = [(role.RoleID, role.name)]

    if request.method == 'GET':
        form.role_name.data = role.name

    if form.validate_on_submit():
        if role.name in {"Admin", "Agent", "Employee"}:
            flash('Core roles cannot be renamed.')
            return redirect(url_for('admin_roles'))

        existing = db.session.scalar(
            sa.select(Role).where(
                sa.and_(Role.name == form.role_name.data, Role.RoleID != role.RoleID)
            )
        )
        if existing:
            flash('A role with that name already exists.')
            return redirect(url_for('admin_edit_role', role_id=role_id))

        role.name = form.role_name.data
        db.session.commit()
        flash('Role updated.')
        return redirect(url_for('admin_roles'))

    return render_template('admin_edit_role.html', form=form, role=role)

@app.route('/admin/delete-role/<int:role_id>', methods=['POST'])
@login_required
@role_required("Admin")
def admin_delete_role(role_id):
    role = db.session.get(Role, role_id)

    if not role:
        flash('Role not found.')
        return redirect(url_for('admin_roles'))

    if role.name in {"Admin", "Agent", "Employee"}:
        flash('Core roles cannot be deleted.')
        return redirect(url_for('admin_roles'))

    if role.users:
        flash('Cannot delete a role that is still assigned to users.')
        return redirect(url_for('admin_roles'))

    db.session.delete(role)
    db.session.commit()
    flash('Role deleted.')
    return redirect(url_for('admin_roles'))


@app.route('/admin/create-role', methods=['POST'])
@login_required
@role_required("Admin")
def admin_create_role_step1():
    form = AdminRoleForm()
    if not form.validate_on_submit():
        flash('Invalid role form.')
        return redirect(url_for('admin_roles'))

    role_name = form.role_name.data
    permissions = request.form.getlist('permissions')
    agents = db.session.scalars(
        sa.select(User).join(Role).where(Role.name.in_(["Agent", "Admin"])).order_by(User.email.asc())
    ).all()

    return render_template(
        'admin_role_assign.html',
        form=form,
        role_name=role_name,
        permissions=permissions,
        agents=agents
    )


@app.route('/admin/create-role/assign', methods=['POST'])
@login_required
@role_required("Admin")
def admin_create_role_step2():
    role_name = (request.form.get('role_name') or '').strip()
    user_ids = request.form.getlist('user_ids')

    if not role_name:
        flash('Role name is required.')
        return redirect(url_for('admin_roles'))

    existing = db.session.scalar(sa.select(Role).where(Role.name == role_name))
    if existing:
        flash('Role already exists.')
        return redirect(url_for('admin_roles'))

    new_role = Role(name=role_name, active=True)
    db.session.add(new_role)
    db.session.flush()

    if user_ids:
        users = db.session.scalars(
            sa.select(User).where(User.UserID.in_([int(uid) for uid in user_ids]))
        ).all()
        for user in users:
            user.roleId = new_role.RoleID

    db.session.commit()
    flash('Role created. Selected permissions were not saved because no permission table exists yet.')
    return redirect(url_for('admin_roles'))

