from app import app, db
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
# from app.forms import CommentForm, LoginForm, PasswordResetForm, RegistrationForm, CreateTicketForm, ResetPasswordForm, UpdateTicket
from app.forms import (
    CommentForm, LoginForm, RegistrationForm, CreateTicketForm, UpdateTicket,
    AdminSettingsForm, AdminProfileForm, AdminNewClientForm, AdminRoleForm,
    AdminResetPasswordForm, AdminNewUserForm, PasswordResetForm, ResetPasswordForm, EditProfileForm, ChangePasswordForm
)
from app.models import TicketComment, User, Role, Category, Status, Priority, Ticket, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

from flask_mail import Message
from app import mail
from app.email import notifyAgentsOfNewTicket, ticketAssignedNotification, ticketCreated, ticketResolvedNotification, ticketStatusChangeNotification, passwordResetEmail, commentAddedNotification

#Role required route. If you place @role_required("Role here") under any of the routes, the user will
#Have to have that role to run the route
def role_required(*role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(*role):
                flash('Access denied. Insufficient permissions.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_or_permission_required(roles=None, permissions=None):
    roles = roles or []
    permissions = permissions or []

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Access denied. Insufficient permissions.')
                return redirect(url_for('index'))

            if current_user.has_role(*roles) or current_user.has_permission(*permissions):
                return f(*args, **kwargs)

            flash('Access denied. Insufficient permissions.')
            return redirect(url_for('index'))
        return decorated_function
    return decorator


def can_view_all_tickets(user):
    return user.has_role('Agent', 'Admin') or user.has_permission('view_all_tickets')


def can_assign_tickets(user):
    return user.has_role('Agent', 'Admin') or user.has_permission('assign_tickets')


def can_be_assigned_tickets(user):
    return user.has_role('Agent', 'Admin') or user.has_permission('ticket_agent')


def can_update_ticket_priority(user):
    return user.has_role('Agent', 'Admin') or user.has_permission('update_ticket_priority')


def can_update_ticket_status(user):
    return user.has_role('Agent', 'Admin') or user.has_permission('update_ticket_status')

def can_use_assigned_queue(user):
    return (
        user.has_role('Agent', 'Admin') or
        user.has_permission('assign_tickets', 'ticket_agent')
    )

@app.route('/')
@app.route('/index')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    # Gets all tickets not resolved or closed
    elif can_view_all_tickets(current_user):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.notin_([5, 6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        # Gets all tickets created by the user that are not resolved or closed
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(
                sa.and_(
                    Ticket.CreatedBy == current_user.UserID,
                    Ticket.StatusID.notin_([5, 6])
                )
            )
            .order_by(Ticket.CreatedAt.desc())
        ).all()

    return render_template('index.html', title='Home', tickets=tickets)


@app.route('/index/closed')
def closed_tickets():
    if not current_user.is_authenticated:
        tickets = []
        # Gets all closed/resolved tickets
    elif can_view_all_tickets(current_user):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.in_([5, 6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        # Gets all closed/resolved tickets created by the user
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(
                sa.and_(
                    Ticket.CreatedBy == current_user.UserID,
                    Ticket.StatusID.in_([5, 6])
                )
            )
            .order_by(Ticket.CreatedAt.desc())
        ).all()

    return render_template('index.html', title='Closed Tickets', tickets=tickets)


@app.route('/index/open')
def open_tickets():
    if not current_user.is_authenticated:
        tickets = []
        # Gets all open tickets that are not resolved or closed
    elif can_view_all_tickets(current_user):
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.StatusID.notin_([5, 6]))
            .order_by(Ticket.CreatedAt.desc())
        ).all()
    else:
        # Gets all open tickets that are not resolved or closed created by the user
        tickets = db.session.scalars(
            sa.select(Ticket)
            .where(
                sa.and_(
                    Ticket.CreatedBy == current_user.UserID,
                    Ticket.StatusID.notin_([5, 6])
                )
            )
            .order_by(Ticket.CreatedAt.desc())
        ).all()

    return render_template('index.html', title='Open Tickets', tickets=tickets)

@app.route('/index/assigned')
@login_required
# Users must be an agent or admin or be able to assign tickets/have the ticket agent permission
@role_or_permission_required(
    roles=['Agent', 'Admin'],
    permissions=['assign_tickets', 'ticket_agent']
)
def assigned_tickets():
    # Gets all tickets assigned to the user that are not resolved or closed
    tickets = db.session.scalars(
        sa.select(Ticket).where(
            sa.and_(
                Ticket.AssignedTo == current_user.UserID,
                Ticket.StatusID.notin_([5, 6])
            )
        ).order_by(Ticket.CreatedAt.desc())
    ).all()

    return render_template('index.html', title='Assigned Tickets', tickets=tickets)

# @login_required
# @role_or_permission_required(
#     roles=['Agent', 'Admin'],
#     permissions=['assign_tickets', 'ticket_agent']
# )


# def assigned_tickets(UserID):
#     if not current_user.is_authenticated:
#         tickets = []
#     else:
#         tickets = (db.session.scalars(sa.select(Ticket).where(Ticket.AssignedTo == current_user.UserID, Ticket.StatusID.notin_([5,6])).order_by(Ticket.CreatedAt.desc())).all())

#     return render_template('index.html', title='Assigned Tickets', tickets=tickets)


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
        login_user(user, remember=form.remember_me.data)
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
        new_user = User(
            username=username, 
            email=email, 
            password_hash=generate_password_hash(password), roleId=1,
            notifications=True
        )
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
        # If there is a user matching the provided email, send them the password reset email
        if user:
            passwordResetEmail(user)
        flash('If an account with that email exists, a password reset email has been sent.')
        return redirect(url_for('login'))

    # Flash errors if form was submitted but not validated
    if request.method == 'POST' and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'error')
    return render_template('resetPasswordReq.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # Verify the token and get the user associated with it. Token is passed from the password reset email that is generated when a user requests a password reset.
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired token. Please try again.')
        return redirect(url_for('login'))
    form = ResetPasswordForm()
    # Set new password on form submission
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))

    # Flash errors if form was submitted but not validated
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

    # Populate create ticket form category and priority selection choices
    form.category.choices = [(c.CategoryID, c.name) for c in Category.query.all()]
    form.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]
    if form.validate_on_submit():
        # Creates new ticket with form data
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

        # Add ticket to the database and flush so that the ticket ID is generated but not committed to the database

        db.session.add(newTicket)
        db.session.flush() 

        # Generates ticket number in format ID-000001 with leading zeros based on the ticket ID and adds it to the ticket
        newTicket.ticketNumber = f"ID-{newTicket.TicketID:06d}"

        # Log new activity for ticket creation
        newActivity = ActivityLog(
            UserID = newTicket.CreatedBy,
            TicketID = newTicket.TicketID,
            action = "Ticket created",
            CreatedAt=datetime.now(),
        )

        # Commit new activity to the database
        db.session.add(newActivity)
        db.session.commit()

        # If the user who created the ticket has notifications enabled, push an email notification about creation 
        if current_user.notifications:
            ticketCreated(newTicket, current_user.email)

        # Gets all agents and admins and sends them an email if they have notifications enabled
        agents = (db.session.scalars(sa.select(User).where(User.roleId.in_([2, 3]))).all())
        agentsEmails = [agent.email for agent in agents]
        notifyAgentsOfNewTicket(newTicket, [email for agent, email in zip(agents, agentsEmails) if agent.notifications])

        flash(f'Ticket {newTicket.ticketNumber} created successfully.')
        return redirect(url_for('index'))

    # flash form validation errors
    if request.method == "POST" and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "warning")

    return render_template('newticket.html', form=form)

@app.route('/ticket/<int:TicketID>', methods=['GET', 'POST'])
@login_required
def view_ticket(TicketID):

    # Get current ticket
    currentTicket = db.session.scalar(sa.select(Ticket).where(Ticket.TicketID == TicketID))
    if not currentTicket:
        flash('Ticket not found.')
        return redirect(url_for('index'))

    # User can view ticket if they have the view all tickets permission, or if they created the ticket or are assigned the ticket
    allowed_to_view = (
        can_view_all_tickets(current_user) or
        currentTicket.CreatedBy == current_user.UserID or
        currentTicket.AssignedTo == current_user.UserID
    )

    # flash error message if not allowed to view
    if not allowed_to_view:
        flash('You do not have permission to view this ticket.')
        return redirect(url_for('index'))

    addCommentForm = CommentForm()
    updateTicketForm = UpdateTicket()

    # populate update ticket from with priorities and choices from the database. Also get all users who can be assigned tickets
    updateTicketForm.priority.choices = [(p.PriorityID, p.name) for p in Priority.query.all()]
    updateTicketForm.status.choices = [(s.StatusID, s.name) for s in Status.query.all()]
    updateTicketForm.assignedTo.choices = [(0, 'Unassigned')] + [
        (u.UserID, u.username) 
        for u in User.query.join(Role).all()
        if can_be_assigned_tickets(u)
    ]

    # Get all comments associated with the ticket
    comments = db.session.scalars(
        sa.select(TicketComment).where(TicketComment.TicketID == TicketID).order_by(TicketComment.CreatedAt.asc())
    ).all()
    #Get all activities associated with the ticket
    #TODO: Pagination for activities if time
    activities = db.session.scalars(
        sa.select(ActivityLog).where(ActivityLog.TicketID == TicketID).order_by(ActivityLog.CreatedAt.desc())
    ).all()

    # Calculate ticket age by finding the difference between the current time and the ticket creation time. If the ticket is closed, find the difference between the closed time and the creation time. 
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

    # If loading the page, get the current ticket info and prepopulate the modify ticket form options with the current data
    if request.method == 'GET':
        updateTicketForm.priority.data = currentTicket.PriorityID
        updateTicketForm.status.data = currentTicket.StatusID
        updateTicketForm.assignedTo.data = currentTicket.assignee.UserID if currentTicket.assignee else 0
        updateTicketForm.resolutionReasoning.data = currentTicket.ResolutionReasoning or ""

    if addCommentForm.validate_on_submit():
        # Create new comment on comment form submission
        newComment = TicketComment(
            comment=addCommentForm.comment.data,
            TicketID=TicketID,
            UserID=current_user.UserID,
            CreatedAt=datetime.now()
        )

        # Send email updating ticket creator about new comment if they have notifications enabled.
        if currentTicket.creator.notifications:
            commentAddedNotification(
                currentTicket,
                currentTicket.creator.email,
                current_user.email,
                addCommentForm.comment.data,
                newComment.CreatedAt,
                current_user.role.name if current_user.role else None,
            )

        # Commit to DB
        db.session.add(newComment)
        db.session.commit()

        return redirect(url_for('view_ticket', TicketID=TicketID))

    # TODO: Add more flash style error messages

    # All of the actions that take place upon update ticket form submission (there is a lot)
    if updateTicketForm.validate_on_submit():
        # Track old status, priority and assigned for comparison with the new data
        oldStatus = currentTicket.StatusID
        oldPriority = currentTicket.PriorityID
        oldAssigned = currentTicket.assignee.UserID if currentTicket.assignee else None

        newPriority = updateTicketForm.priority.data
        newStatus = updateTicketForm.status.data
        newAssigned = updateTicketForm.assignedTo.data if updateTicketForm.assignedTo.data != 0 else None

        # Permission handling to check if the user can update the priority, status or assignee
        if oldPriority != newPriority and not can_update_ticket_priority(current_user):
            flash('Access denied. You do not have permission to update priority.')
            return redirect(url_for('view_ticket', TicketID=TicketID))

        if oldStatus != newStatus and not can_update_ticket_status(current_user):
            flash('Access denied. You do not have permission to update status.')
            return redirect(url_for('view_ticket', TicketID=TicketID))

        if oldAssigned != newAssigned and not can_assign_tickets(current_user):
            flash('Access denied. You do not have permission to assign tickets.')
            return redirect(url_for('view_ticket', TicketID=TicketID))

        # Check if the assigned user can be assigned tickets
        if newAssigned is not None:
            assigned_user = db.session.get(User, newAssigned)
            if not assigned_user or not can_be_assigned_tickets(assigned_user):
                flash('Selected user cannot be assigned tickets.')
                return redirect(url_for('view_ticket', TicketID=TicketID))
            
        # Flashes error if user tries to set an unassigned ticket to a status other than open or closed
        if newAssigned is None and newStatus not in [1, 6]:  
            flash('Unassigned tickets must have status Open or Closed')
            return redirect(url_for('view_ticket', TicketID=TicketID))
            
        # Update ticket with new data from the form
        currentTicket.PriorityID = newPriority
        currentTicket.StatusID = newStatus
        currentTicket.AssignedTo = newAssigned

        # Makes it so ticket cannot be set to open if it is assigned
        if updateTicketForm.assignedTo.data != 0 and updateTicketForm.status.data == 1:
            flash("Assigned tickets cannot have status 'Open'")
            return redirect(url_for("view_ticket", TicketID=TicketID))

        # Sets closed at date and resolution reasoning if the ticket is being closed or resolved
        if newStatus in [5, 6]:
            if not currentTicket.ClosedAt:
                currentTicket.ClosedAt = datetime.now()
            if updateTicketForm.resolutionReasoning.data:
                currentTicket.ResolutionReasoning = updateTicketForm.resolutionReasoning.data
                recipient = currentTicket.creator.email
                newActivity = ActivityLog(
                    UserID = current_user.UserID,
                    TicketID = currentTicket.TicketID,
                    action = f"Ticket resolved by {current_user.username} with resolution reasoning: {updateTicketForm.resolutionReasoning.data}",
                    CreatedAt=datetime.now(),
                )
                db.session.add(newActivity)
                db.session.commit()

                if currentTicket.creator.notifications:
                    ticketResolvedNotification(currentTicket, recipient)
        else:
            currentTicket.ClosedAt = None
            currentTicket.ResolutionReasoning = None

        # If status is being changed and new status is not resolved, then send an email to the creator if notifications are enabled and create new activity log
        if oldStatus != currentTicket.StatusID and currentTicket.StatusID not in [5]:
            recipient = currentTicket.creator.email
            oldStatusName = db.session.scalar(sa.select(Status.name).where(Status.StatusID == oldStatus))
            newStatusName = db.session.scalar(sa.select(Status.name).where(Status.StatusID == currentTicket.StatusID))

            # Create new activity and commit
            newActivity = ActivityLog(
                UserID = current_user.UserID,
                TicketID = currentTicket.TicketID,
                action = f"Status changed from {oldStatusName} to {newStatusName}",
                CreatedAt=datetime.now(),
            )

            db.session.add(newActivity)
            db.session.commit()

            if app.config['MAIL_SUPPRESS_SEND']:
                print(f"email failed to send")
            elif currentTicket.creator.notifications:
                ticketStatusChangeNotification(currentTicket, recipient, oldStatusName, newStatusName)

        # If assignment has changed, log a new activity for ticket assignment and send an email to the new assignee if they have notifications enabled.
        if oldAssigned != newAssigned:
            newActivity = ActivityLog(
                UserID = current_user.UserID,
                TicketID = currentTicket.TicketID,
                action = "Ticket unassigned" if newAssigned is None else "Ticket assigned to " + currentTicket.assignee.username,
                CreatedAt=datetime.now(),
            )
            db.session.add(newActivity)
            db.session.commit()
            if newAssigned is not None:
                recipient = currentTicket.assignee.email
                if currentTicket.assignee.notifications:
                    ticketAssignedNotification(currentTicket, recipient)

        # If priority has changed log an activity indicating so
        if oldPriority != currentTicket.PriorityID:
            recipient = currentTicket.creator.email
            oldPriorityName = db.session.scalar(sa.select(Priority.name).where(Priority.PriorityID == oldPriority))
            newPriorityName = db.session.scalar(sa.select(Priority.name).where(Priority.PriorityID == currentTicket.PriorityID))

            newActivity = ActivityLog(
                UserID = current_user.UserID,
                TicketID = currentTicket.TicketID,
                action = f"Priority changed from {oldPriorityName} to {newPriorityName}",
                CreatedAt=datetime.now(),
            )
            db.session.add(newActivity)
            db.session.commit()

            # TODO: Maybe add priority notification email later

        if currentTicket.StatusID == 5:
            return redirect(url_for('view_ticket', TicketID=TicketID, confetti=1))
        return redirect(url_for('view_ticket', TicketID=TicketID))

    return render_template('ticketview.html', ticket_id=TicketID, ticket=currentTicket,
                            comments=comments, commentForm=addCommentForm, updateTicketForm=updateTicketForm,
                            ticketAge=ticketAge, show_confetti=request.args.get('confetti') == '1', activities=activities)

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_profile(user_id):
    passwordForm = ChangePasswordForm()
    profileForm = EditProfileForm()

    # Gets the user. If the current user does not match the profile they are attempting to view then flash access denied message
    user = db.session.scalars(sa.select(User).where(User.UserID == user_id)).first()
    if user and user.UserID != current_user.UserID and not current_user.has_permission('view_profile'):
        flash('Access denied. You do not have permission to view this profile.')
        return redirect(url_for('index'))
    if not user:
        flash('User not found.')
    
    # Prepopulate the profile form with the current user data on page load
    if request.method == 'GET':
        profileForm.username.data = user.username
        profileForm.email.data = user.email
        profileForm.notifications.data = user.notifications

    if profileForm.validate_on_submit():

        # Checks for duplicate emails and usernames upon attempt to change email or username
        duplicate_username = db.session.scalar(
            sa.select(User).where(
                sa.and_(User.username == profileForm.username.data, User.UserID != user.UserID)
            )
        )
        duplicate_email = db.session.scalar(
            sa.select(User).where(
                sa.and_(User.email == profileForm.email.data, User.UserID != user.UserID)
            )
        )

        # Flash Error message if duplicate
        if duplicate_username:
            flash('Username already exists.')
            return redirect(url_for('view_profile', user_id=user_id))

        if duplicate_email:
            flash('Email already exists.')
            return redirect(url_for('view_profile', user_id=user_id))

        # Set user data to the form data and commit to database
        user.username = profileForm.username.data
        user.email = profileForm.email.data
        user.notifications = profileForm.notifications.data
        db.session.commit()
        
        flash('Profile updated.')
        return redirect(url_for('view_profile', user_id=user_id))

    if passwordForm.validate_on_submit():
        # If the password hash generated from the current password does not match the password hash in the database, flash error message indicating password is incorrect
        if not check_password_hash(user.password_hash, passwordForm.current_password.data):
            flash('Current password is incorrect.')
            return redirect(url_for('view_profile', user_id=user_id))
        # Flash error message if passwords do not match
        if passwordForm.new_password.data != passwordForm.confirm_new_password.data:
            flash('New passwords do not match.')
        # Generate new password hash and commit to database
        user.password_hash = generate_password_hash(passwordForm.new_password.data)
        db.session.commit()
        flash('Password updated.')

    # Gets number of tickets assigned to user
    assigned_to_me_count = db.session.scalar(
        sa.select(sa.func.count()).where(
            sa.and_(
                Ticket.AssignedTo == user.UserID,
                Ticket.StatusID.notin_([5, 6])
            )
        )
    )

    # Get number of tickets that are unassigned
    unassigned_count = db.session.scalar(
        sa.select(sa.func.count()).where(
            sa.and_(
                Ticket.AssignedTo == None,
                Ticket.StatusID.notin_([5, 6])
            )
        )
    )

    # Get number of tickets the user has resolved
    resolved_count = db.session.scalar(
        sa.select(sa.func.count()).where(
            sa.and_(
                Ticket.AssignedTo == user.UserID,
                Ticket.StatusID == 5
            )
        )
    )

    # Get number of tickets the user has created
    tickets_created_count = db.session.scalar(sa.select(sa.func.count()).where(Ticket.CreatedBy == user.UserID))

    # Get number of tickets the user has created that is open
    open_tickets_count = db.session.scalar(
        sa.select(sa.func.count()).where(
            sa.and_(
                Ticket.CreatedBy == user.UserID,
                Ticket.StatusID.notin_([5, 6])
            )
        )
    )

    # Get number of tickets the user has created that has been resolved
    resolved_count_employee = db.session.scalar(
        sa.select(sa.func.count()).where(
            sa.and_(
                Ticket.CreatedBy == user.UserID,
                Ticket.StatusID == 5
            )
        )
    )

    # Get last 5 activities in the activity log associated with the user
    activities = db.session.scalars(
        sa.select(ActivityLog).where(
            ActivityLog.UserID == user.UserID)
            .order_by(ActivityLog.CreatedAt.desc())
            .limit(5)
        ).all()


    return render_template('profile.html', user=user, passwordForm=passwordForm, profileForm=profileForm, can_view_profile=current_user.has_permission('view_profile'), can_change_settings=current_user.has_permission('change_settings')
                            , assigned_to_me_count=assigned_to_me_count, unassigned_count = unassigned_count, resolved_count=resolved_count,
                            tickets_created_count=tickets_created_count, open_tickets_count=open_tickets_count, resolved_count_employee=resolved_count_employee, activities=activities)


@app.route('/admin')
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=[
        'view_roles', 'create_roles',
        'view_users', 'create_users',
        'view_clients',
        'change_settings',
        'view_profile'
    ]
)
def admin_functionalities():
    return render_template('admin_functionalities.html')

@app.route('/admin/users')
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['view_users', 'create_users']
)
def admin_users():
    users = db.session.scalars(sa.select(User).order_by(User.username.asc())).all()

    role_choices = [
        (role.RoleID, role.name)
        for role in db.session.scalars(
            sa.select(Role).where(Role.active == True).order_by(Role.name.asc())
        ).all()
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


# @app.route('/admin/clients')
# @login_required
# @role_or_permission_required(
#     roles=['Admin'],
#     permissions=['view_clients']
# )
# def admin_clients():
#     clients = db.session.scalars(
#         sa.select(User).join(Role).where(Role.name == "Employee").order_by(User.username.asc())
#     ).all()
#     new_client_form = AdminNewClientForm()
#     return render_template('admin_clients.html', clients=clients, new_client_form=new_client_form)
@app.route('/admin/clients')
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['view_clients']
)
def admin_clients():
    clients = db.session.scalars(
        sa.select(User)
        .join(Role)
        .where(
            sa.and_(
                Role.name != "Admin",
                Role.name != "Agent"
            )
        )
        .order_by(User.username.asc())
    ).all()

    new_client_form = AdminNewClientForm()
    return render_template('admin_clients.html', clients=clients, new_client_form=new_client_form)

@app.route('/admin/roles')
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['view_roles', 'create_roles']
)
def admin_roles():
    roles = db.session.scalars(sa.select(Role).order_by(Role.name.asc())).all()
    form = AdminRoleForm()
    form.role.choices = []
    return render_template('admin_roles.html', roles=roles, form=form)


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['change_settings']
)
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['view_profile']
)
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_users']
)
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

    if not role or not role.active:
        flash('Selected role is disabled or not found.')
        return redirect(url_for('admin_users'))
    
    if not user or not role:
        flash('User or role not found.')
        return redirect(url_for('admin_users'))

    user.roleId = role.RoleID
    db.session.commit()
    flash(f'Role for {user.username} updated to {role.name}.')
    return redirect(url_for('admin_users'))

@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_users']
)
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_users']
)
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
    if not role or not role.active:
        flash('Selected role does not exist or is disabled.')
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_users']
)
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
def admin_toggle_all_roles(active):
    roles = db.session.scalars(sa.select(Role)).all()
    core_roles = {"Admin", "Agent", "Employee"}

    employee_role = db.session.scalar(
        sa.select(Role).where(Role.name == "Employee")
    )

    if not employee_role:
        flash('Employee role not found.')
        return redirect(url_for('admin_roles'))

    make_active = bool(active)

    for role in roles:
        if role.name in core_roles:
            continue

        was_active = role.active
        role.active = make_active

        if was_active and not role.active:
            users_with_role = db.session.scalars(
                sa.select(User).where(User.roleId == role.RoleID)
            ).all()

            for user in users_with_role:
                user.roleId = employee_role.RoleID

    db.session.commit()
    flash('Custom roles updated.')
    return redirect(url_for('admin_roles'))

@app.route('/admin/toggle-role/<int:role_id>', methods=['POST'])
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
def admin_toggle_role(role_id):
    role = db.session.get(Role, role_id)

    if not role:
        flash('Role not found.')
        return redirect(url_for('admin_roles'))

    if role.name in {"Admin", "Agent", "Employee"}:
        flash('Core roles cannot be disabled here.')
        return redirect(url_for('admin_roles'))

    employee_role = db.session.scalar(
        sa.select(Role).where(Role.name == "Employee")
    )

    if not employee_role:
        flash('Employee role not found.')
        return redirect(url_for('admin_roles'))

    role.active = not role.active

    if not role.active:
        users_with_role = db.session.scalars(
            sa.select(User).where(User.roleId == role.RoleID)
        ).all()

        for user in users_with_role:
            user.roleId = employee_role.RoleID

    db.session.commit()
    flash('Role updated.')
    return redirect(url_for('admin_roles'))

@app.route('/admin/edit-role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
def admin_edit_role(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        flash('Role not found.')
        return redirect(url_for('admin_roles'))

    form = AdminRoleForm()
    form.role.choices = [(role.RoleID, role.name)]

    if request.method == 'GET':
        form.role_name.data = role.name
        form.permissions.data = role.permission_list()

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
        # role.set_permissions(request.form.getlist('permissions'))
        permissions = request.form.getlist('permissions')

        if 'assign_tickets' in permissions and 'update_ticket_status' not in permissions:
            permissions.append('update_ticket_status')

        role.set_permissions(permissions)
        
        db.session.commit()
        flash('Role updated.')
        return redirect(url_for('admin_roles'))

    return render_template('admin_edit_role.html', form=form, role=role)

@app.route('/admin/delete-role/<int:role_id>', methods=['POST'])
@login_required
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
def admin_create_role_step1():
    form = AdminRoleForm()
    form.role.choices = []
    if not form.validate_on_submit():
        print(form.errors)
        flash(f'Invalid role form: {form.errors}')
        return redirect(url_for('admin_roles'))

    role_name = form.role_name.data
    permissions = request.form.getlist('permissions')
    agents = db.session.scalars(
        sa.select(User).order_by(User.email.asc())
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
@role_or_permission_required(
    roles=['Admin'],
    permissions=['create_roles']
)
def admin_create_role_step2():
    role_name = (request.form.get('role_name') or '').strip()
    user_ids = request.form.getlist('user_ids')
    # permissions = request.form.getlist('permissions')
    permissions = request.form.getlist('permissions')

    if 'assign_tickets' in permissions and 'update_ticket_status' not in permissions:
        permissions.append('update_ticket_status')

    if not role_name:
        flash('Role name is required.')
        return redirect(url_for('admin_roles'))

    existing = db.session.scalar(sa.select(Role).where(Role.name == role_name))
    if existing:
        flash('Role already exists.')
        return redirect(url_for('admin_roles'))

    new_role = Role(name=role_name, active=True)
    new_role.set_permissions(permissions)
    db.session.add(new_role)
    db.session.flush()

    if user_ids:
        users = db.session.scalars(
            sa.select(User).where(User.UserID.in_([int(uid) for uid in user_ids]))
        ).all()
        for user in users:
            user.roleId = new_role.RoleID

    db.session.commit()
    flash('Role created.')
    return redirect(url_for('admin_roles'))
