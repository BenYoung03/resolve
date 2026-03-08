from app import app, db
from flask import render_template, flash, redirect, url_for, request
import sqlalchemy as sa
from app.forms import LoginForm, RegistrationForm, CreateTicketForm
from app.models import User, Role, Category, Status, Priority, Ticket
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    tickets = (
        db.session.scalars(
            sa.select(Ticket)
            .where(Ticket.CreatedBy == current_user.UserID)
            .order_by(Ticket.CreatedAt.desc())
        ).all()
        if current_user.is_authenticated
        else []
    )
    return render_template('index.html', title='Home', tickets=tickets)

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
        email = form.email.data
        password = form.password.data
        confirmPassword = form.confirmPassword.data

        if password != confirmPassword:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        # If register form filled in correctly, make sure user doesn't exist by finding
        # If a matching email is already in the database
        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))  
        
        # Commit new user to database if no user already exists
        new_user = User(email=email, password_hash=generate_password_hash(password), roleId=1)
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
            CreatedAt=datetime.utcnow(),
            ClosedAt=None
        )

        db.session.add(newTicket)
        db.session.flush() 

        newTicket.ticketNumber = f"ID-{newTicket.TicketID:06d}"

        db.session.commit()

        flash(f'Ticket {newTicket.ticketNumber} created successfully.')
        return redirect(url_for('index'))

    return render_template('newticket.html', form=form)
