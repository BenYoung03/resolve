from app import app, db
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
from app.forms import CommentForm, LoginForm, RegistrationForm, CreateTicketForm, UpdateTicket
from app.models import TicketComment, User, Role, Category, Status, Priority, Ticket
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps
from app.forms import AdminNewClientForm, AdminNewRoleForm, AdminChangeRoleForm, AdminResetPasswordForm, AdminSettingsForm, AdminProfileForm  


from flask_mail import Message
from app import mail
from app.email import notifyAgentsOfNewTicket, ticketAssignedNotification, ticketCreated, ticketStatusChangeNotification

def has_role(self, roles):
    if self.role is None:
        return False
    if isinstance(roles, str):
        roles = [roles]
    return self.role.name in roles

#Role required route. If you place @role_required("Role here") under any of the routes, the user will
#Have to have that role to run the route
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
        db.session.add(newComment)
        db.session.commit()
        
        return redirect(url_for('view_ticket', TicketID=TicketID))
    
    # TODO: Add more flash style error messages
    if updateTicketForm.validate_on_submit():
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
        new_role = Role(name=form.role_name.data)
        db.session.add(new_role)
        db.session.commit()
        flash(f"Role '{form.role_name.data}' created successfully!")
        return redirect(url_for('admin_roles'))
    return render_template('admin_roles.html', title='Admin Roles', form=form)


@app.route('/admin/roles/toggle_all/<int:active>', methods=['POST'])
@login_required
@role_required('Admin')
def admin_toggle_all_roles(active):
    for role in Role.query.all():
        role.active = bool(active)
    db.session.commit()
    flash("All roles updated.")
    return redirect(url_for('admin_roles'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_users():
    from app.forms import AdminNewUserForm, AdminChangeRoleForm, AdminResetPasswordForm

    new_user_form = AdminNewUserForm()
    role_form = AdminChangeRoleForm()
    reset_form = AdminResetPasswordForm()

    # Populate role choices for new user
    new_user_form.role.choices = [(r.RoleID, r.name) for r in Role.query.all()]

    users = User.query.all()

    if new_user_form.validate_on_submit():
        username = new_user_form.username.data
        email = new_user_form.email.data
        password = new_user_form.password.data
        role_id = new_user_form.role.data

        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('admin_users'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin_users'))

        role = Role.query.get(role_id)
        new_user = User(username=username, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('New user created successfully!')
        return redirect(url_for('admin_users'))

    return render_template('admin_users.html',
                           title='Admin Users',
                           new_user_form=new_user_form,
                           role_form=role_form,
                           reset_form=reset_form,
                           users=users)


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


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} has been deleted.")
    return redirect(url_for('admin_users'))


@app.route('/admin/clients', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_clients():
    new_client_form = AdminNewClientForm()
    if new_client_form.validate_on_submit():
        client_name = new_client_form.client_name.data
        new_client = Client(name=client_name)
        db.session.add(new_client)
        db.session.commit()
        flash(f"New client '{client_name}' added successfully!")
        return redirect(url_for('admin_clients'))

    return render_template('admin_clients.html', title='Admin Clients', new_client_form=new_client_form)


@app.route('/admin/clients/new', methods=['POST'])
@login_required
@role_required('Admin')
def admin_new_client():
    client_name = request.form.get('client_name')
    if not client_name:
        flash("Client name is required.")
        return redirect(url_for('admin_clients'))

    new_client = Client(name=client_name)
    db.session.add(new_client)
    db.session.commit()
    flash(f"New client '{client_name}' created successfully.")
    return redirect(url_for('admin_clients'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def admin_settings():
    form = AdminSettingsForm()
    if form.validate_on_submit():
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin_settings'))
    return render_template('admin_settings.html', title='Admin Settings', form=form)


@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    form = AdminProfileForm()
    if form.validate_on_submit():
        # Example: update current admin profile
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('admin_profile'))

    return render_template('admin_profile.html', title='Admin Profile', form=form)

@app.route('/admin/roles/create', methods=['GET', 'POST'])
@login_required
def admin_create_role_step1():
    form = CreateRoleForm()
    if form.validate_on_submit():
        # handle creating the role
        pass
    return render_template('admin_create_role.html', form=form)