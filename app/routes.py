from app import app, db
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
from app.forms import CommentForm, LoginForm, PasswordResetForm, RegistrationForm, CreateTicketForm, ResetPasswordForm, UpdateTicket
from app.models import TicketComment, User, Role, Category, Status, Priority, Ticket
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from functools import wraps

from flask_mail import Message
from app import mail
from app.email import notifyAgentsOfNewTicket, ticketAssignedNotification, ticketCreated, ticketStatusChangeNotification, passwordResetEmail

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
        return redirect(url_for('index'))
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
