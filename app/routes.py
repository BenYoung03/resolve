from app import app, db, mail
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
from app.forms import CommentForm, LoginForm, RegistrationForm, CreateTicketForm, UpdateTicket
from app.models import TicketComment, User, Role, Category, Status, Priority, Ticket
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from app.email import notifyAgentsOfNewTicket, ticketAssignedNotification, ticketCreated, ticketStatusChangeNotification
from app.forms import AdminNewClientForm
from app.forms import AdminNewRoleForm
from app.forms import AdminSettingsForm
from app.forms import AdminProfileForm



def has_role(self, roles):
    if self.role is None:
        return False
    if isinstance(roles, str):
        roles = [roles]
    return self.role.name in roles
# -------------------------
# Role Required Decorator
# -------------------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(roles):
                flash('Access denied. Insufficient permissions.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -------------------------
# Home / Ticket Views
# -------------------------
@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.has_role('Employee'):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.notin_([5,6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.notin_([5,6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    return render_template('index.html', title='Home', tickets=tickets)


@app.route('/index/closed')
@login_required
def closed_tickets():
    if current_user.has_role('Employee'):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(sa.and_(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.in_([5,6])))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.in_([5,6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    return render_template('index.html', title='Closed Tickets', tickets=tickets)


@app.route('/index/open')
@login_required
def open_tickets():
    if current_user.has_role('Employee'):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(sa.and_(Ticket.CreatedBy == current_user.UserID, Ticket.StatusID.notin_([5,6])))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.notin_([5,6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    return render_template('index.html', title='Open Tickets', tickets=tickets)


@app.route('/index/assigned/<int:UserID>', methods=['GET', 'POST'])
@role_required('Agent', 'Admin')
@login_required
def assigned_tickets(UserID):
    tickets = db.session.scalars(
        sa.select(Ticket)
        .where(Ticket.AssignedTo == current_user.UserID, Ticket.StatusID.notin_([5,6]))
        .order_by(Ticket.CreatedAt.desc())
    ).all()
    return render_template('index.html', title='Assigned Tickets', tickets=tickets)


# -------------------------
# Login / Register / Logout
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not check_password_hash(user.password_hash, form.password.data):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.confirmPassword.data:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        # Assign default role (User)
        default_role = Role.query.filter_by(name='User').first()
        if not default_role:
            flash('Default role not found. Contact admin.')
            return redirect(url_for('register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role=default_role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


# -------------------------
# Create Ticket
# -------------------------
@app.route('/createticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    form = CreateTicketForm()
    form.category.choices = [(c.CategoryID, c.name) for c in Category.query.all()]
    form.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]

    if form.validate_on_submit():
        ticket = Ticket(
            subject=form.subject.data,
            description=form.description.data,
            CategoryID=form.category.data,
            PriorityID=form.priority.data,
            StatusID=1,
            CreatedBy=current_user.UserID,
            AssignedTo=None,
            CreatedAt=datetime.now(),
            ClosedAt=None
        )
        db.session.add(ticket)
        db.session.flush()
        ticket.ticketNumber = f"ID-{ticket.TicketID:06d}"
        db.session.commit()

        ticketCreated(ticket, current_user.email)

        # Notify all agents
        agents = db.session.scalars(sa.select(User).join(Role).where(Role.name.in_(["Agent", "Admin"]))).all()
        agent_emails = [a.email for a in agents]
        notifyAgentsOfNewTicket(ticket, agent_emails)

        flash(f'Ticket {ticket.ticketNumber} created successfully.')
        return redirect(url_for('index'))

    if request.method == 'POST' and not form.validate():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "warning")

    return render_template('newticket.html', form=form)


# -------------------------
# View / Update Ticket
# -------------------------
@app.route('/ticket/<int:TicketID>', methods=['GET', 'POST'])
@login_required
def view_ticket(TicketID):
    ticket = db.session.scalar(sa.select(Ticket).where(Ticket.TicketID == TicketID))
    if not ticket:
        flash('Ticket not found.')
        return redirect(url_for('index'))

    comments = db.session.scalars(
        sa.select(TicketComment)
        .where(TicketComment.TicketID == TicketID)
        .order_by(TicketComment.CreatedAt.asc())
    ).all()

    add_comment_form = CommentForm()
    update_ticket_form = UpdateTicket()

    # Populate select fields
    update_ticket_form.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]
    update_ticket_form.status.choices = [(s.StatusID, s.name) for s in Status.query.all()]
    update_ticket_form.assignedTo.choices = [(0, 'Unassigned')] + [
        (u.UserID, u.username)
        for u in User.query.join(Role).filter(Role.name.in_(["Agent", "Admin"])).all()
    ]

    # Ticket age calculation
    delta = (ticket.ClosedAt if ticket.ClosedAt else datetime.now()) - ticket.CreatedAt
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    days, hours = divmod(hours, 24)
    ticket_age = f"{days} day{'s' if days != 1 else ''} {hours}h {minutes}m" if days else f"{hours}h {minutes}m"

    # GET pre-fill
    if request.method == 'GET':
        update_ticket_form.priority.data = ticket.PriorityID
        update_ticket_form.status.data = ticket.StatusID
        update_ticket_form.assignedTo.data = ticket.assignee.UserID if ticket.assignee else 0
        update_ticket_form.resolutionReasoning.data = ticket.ResolutionReasoning or ""

    # Add comment
    if add_comment_form.validate_on_submit():
        new_comment = TicketComment(
            comment=add_comment_form.comment.data,
            TicketID=TicketID,
            UserID=current_user.UserID,
            CreatedAt=datetime.now()
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('view_ticket', TicketID=TicketID))

    # Update ticket
    if update_ticket_form.validate_on_submit():
        old_status = ticket.StatusID
        old_assigned = ticket.assignee.UserID if ticket.assignee else None

        ticket.PriorityID = update_ticket_form.priority.data
        ticket.StatusID = update_ticket_form.status.data
        ticket.AssignedTo = update_ticket_form.assignedTo.data if update_ticket_form.assignedTo.data != 0 else None
        ticket.ResolutionReasoning = update_ticket_form.resolutionReasoning.data or ticket.ResolutionReasoning

        # Prevent open + assigned
        if update_ticket_form.assignedTo.data != 0 and update_ticket_form.status.data == 1:
            flash("Assigned tickets cannot have status 'Open'.")
            return redirect(url_for('view_ticket', TicketID=TicketID))

        # Set closed time
        if update_ticket_form.status.data in [5,6] and not ticket.ClosedAt:
            ticket.ClosedAt = datetime.now()
        elif update_ticket_form.status.data not in [5,6]:
            ticket.ClosedAt = None

        db.session.commit()

        # Send notifications
        if old_status != ticket.StatusID:
            ticketStatusChangeNotification(
                ticket,
                ticket.creator.email,
                db.session.scalar(sa.select(Status.name).where(Status.StatusID == old_status)),
                db.session.scalar(sa.select(Status.name).where(Status.StatusID == ticket.StatusID))
            )

        new_assigned = ticket.assignee.UserID if ticket.assignee else None
        if old_assigned != new_assigned and new_assigned is not None:
            ticketAssignedNotification(ticket, ticket.assignee.email)

        if ticket.StatusID == 5:
            return redirect(url_for('view_ticket', TicketID=TicketID, confetti=1))

        return redirect(url_for('view_ticket', TicketID=TicketID))

    return render_template(
        'ticketview.html',
        ticket_id=TicketID,
        ticket=ticket,
        comments=comments,
        commentForm=add_comment_form,
        updateTicketForm=update_ticket_form,
        ticketAge=ticket_age,
        show_confetti=request.args.get('confetti') == '1'
    )


@app.route('/admin/panel')
@login_required
@role_required('Admin')
def admin_panel():
    return render_template('admin_panel.html', title='Admin Panel')





@app.route('/admin/roles', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_roles():
    form = AdminNewRoleForm()
    if form.validate_on_submit():
        # Create a new role logic here
        new_role = Role(name=form.role_name.data)
        db.session.add(new_role)
        db.session.commit()
        flash(f"Role '{form.role_name.data}' created successfully!")
        return redirect(url_for('admin_roles'))
    return render_template('admin_roles.html', title='Admin Roles', form=form)



@app.route('/admin/profile')
@login_required
@role_required('Admin')
def admin_profile():
    form = AdminProfileForm()
    return render_template(
        'admin_profile.html',
        title='Admin Profile',
        form=form
    )

# -------------------------
# Admin: Create New User
# -------------------------
from app.forms import AdminNewUserForm

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_users():
    # Forms
    from app.forms import AdminNewUserForm, AdminChangeRoleForm, AdminResetPasswordForm
    new_user_form = AdminNewUserForm()
    role_form = AdminChangeRoleForm()
    reset_form = AdminResetPasswordForm()

    # Populate role choices for new user
    new_user_form.role.choices = [(r.RoleID, r.name) for r in Role.query.all()]

    # Fetch all users
    users = User.query.all()

    # Handle new user form submission
    if new_user_form.validate_on_submit():
        username = new_user_form.username.data
        email = new_user_form.email.data
        password = new_user_form.password.data
        role_id = new_user_form.role.data

        # Check duplicates
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('admin_users'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin_users'))

        role = Role.query.get(role_id)
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('New user created successfully!')
        return redirect(url_for('admin_users'))

    return render_template(
        'admin_users.html',
        title='Admin Users',
        new_user_form=new_user_form,
        role_form=role_form,
        reset_form=reset_form,
        users=users
    )


# Change user role
@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@role_required('Admin')
def admin_change_role(user_id):
    form = AdminChangeRoleForm()
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        role = Role.query.get(form.role.data)
        user.role = role
        db.session.commit()
        flash(f"{user.username}'s role updated to {role.name}.")
    return redirect(url_for('admin_users'))

# Reset user password
@app.route('/admin/users/<int:user_id>/reset', methods=['POST'])
@login_required
@role_required('Admin')
def admin_reset_password(user_id):
    form = AdminResetPasswordForm()
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash(f"{user.username}'s password has been reset.")
    return redirect(url_for('admin_users'))

# Delete user
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} has been deleted.")
    return redirect(url_for('admin_users'))


# Admin: Create New Client
@app.route('/admin/clients/new', methods=['POST'])
@login_required
@role_required('Admin')
def admin_new_client():
    
    client_name = request.form.get('client_name')
    if not client_name:
        flash("Client name is required.")
        return redirect(url_for('admin_clients'))

    from app.models import Client
    new_client = Client(name=client_name)
    db.session.add(new_client)
    db.session.commit()
    flash(f"New client '{client_name}' created successfully.")
    return redirect(url_for('admin_clients'))

@app.route('/admin/clients', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_clients():
    new_client_form = AdminNewClientForm()
    if new_client_form.validate_on_submit():
        # Process the new client
        client_name = new_client_form.client_name.data
        new_client = Client(name=client_name)
        db.session.add(new_client)
        db.session.commit()
        flash(f"New client '{client_name}' added successfully!")
        return redirect(url_for('admin_clients'))

    return render_template(
        'admin_clients.html',
        title='Admin Clients',
        new_client_form=new_client_form
    )


@app.route('/admin/roles/toggle_all/<int:active>', methods=['POST'])
@login_required
@role_required('Admin')
def admin_toggle_all_roles(active):
    # Example: activate/deactivate all roles
    for role in Role.query.all():
        role.active = bool(active)
    db.session.commit()
    flash("All roles updated.")
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/create_step1', methods=['POST'])
@login_required
@role_required('Admin')
def admin_create_role_step1():
    # code to handle creating the role step 1
    return redirect(url_for('admin_roles'))



@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_settings():
    form = AdminSettingsForm()
    if form.validate_on_submit():
        # save settings and passwords
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html', title='Admin Settings', form=form)


# the route below is just a placeholder to redirect to home after testing other routes, or can be changed to something else like /test
# @app.route('/')
# def home():
#     return render_template('index.html')

# use the line below to redirect to home after testing other routes, or change the route above to something else like /test
#  return redirect(url_for('home'))