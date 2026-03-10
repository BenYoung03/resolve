from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, NewUserForm, ResetPasswordForm, NewClientForm, RolePermissionForm, RoleUserAssignForm
from app.models import User, Role, Permission, RolePermission
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_login import current_user


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

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
        if user.has_role(['Admin']):
            return redirect(url_for('admin_home'))
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



@app.route('/admin')
@login_required
def admin_home():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    
    # Replace these once the Issue model exists
    open_count = 0
    closed_count = 0
    unassigned_count = 0
    issues = []

    return render_template('admin_home.html',
                           open_count=open_count, closed_count=closed_count,unassigned_count=unassigned_count, issues=issues)


@app.route('/admin/panel')
@login_required
def admin_panel():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    return render_template('admin_functionalities.html')

from app.forms import ProfileForm, SettingsForm

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated.')
    return render_template('admin_profile.html', form=form)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = SettingsForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.old_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Password updated.')
        else:
            flash('Old password is incorrect.')
    return render_template('admin_settings.html', form=form)





@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    users = User.query.join(Role).filter(Role.name.in_(['Agent', 'Admin'])).all()
    return render_template('admin_users.html',
                           users=users,
                           new_user_form=NewUserForm(),
                           reset_form=ResetPasswordForm(),
                           role_form=NewUserForm())

@app.route('/admin/users/new', methods=['POST'])
@login_required
def admin_new_user():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = NewUserForm()
    if form.validate_on_submit():
        new_user = User(name=form.name.data, email=form.email.data,
                        password_hash=generate_password_hash(form.password.data),
                        roleId=int(form.role.data))
        db.session.add(new_user)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/reset/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(user_id)
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/role/<int:user_id>', methods=['POST'])
@login_required
def admin_change_role(user_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = NewUserForm()
    if form.validate_on_submit():
        user = User.query.get(user_id)
        user.roleId = int(form.role.data)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/clients')
@login_required
def admin_clients():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    clients = User.query.join(Role).filter(Role.name == 'Employee').all()
    return render_template('admin_clients.html',
                           clients=clients,
                           new_client_form=NewClientForm())

@app.route('/admin/clients/new', methods=['POST'])
@login_required
def admin_new_client():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    form = NewClientForm()
    if form.validate_on_submit():
        employee_role = Role.query.filter_by(name='Employee').first()
        new_client = User(name=form.name.data, email=form.email.data,
                          password_hash=generate_password_hash(form.password.data),
                          roleId=employee_role.RoleID)
        db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('admin_clients'))





@app.route('/admin/roles')
@login_required
def admin_roles():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    roles = Role.query.all()
    return render_template('admin_roles.html', roles=roles, form=RolePermissionForm())

@app.route('/admin/roles/create/step1', methods=['POST'])
@login_required
def admin_create_role_step1():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    role_name = request.form.get('role_name')
    permissions = request.form.getlist('permissions')
    agents = User.query.join(Role).filter(Role.name.in_(['Agent', 'Admin'])).all()
    return render_template('admin_role_assign.html',
                           role_name=role_name,
                           permissions=','.join(permissions),
                           agents=agents,
                           form=RoleUserAssignForm())

@app.route('/admin/roles/create/step2', methods=['POST'])
@login_required
def admin_create_role_step2():
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    role_name = request.form.get('role_name')
    permissions = request.form.get('permissions').split(',')
    user_ids = request.form.getlist('user_ids')

    new_role = Role(name=role_name, active=True)
    db.session.add(new_role)
    db.session.flush()

    for perm_name in permissions:
        perm = Permission.query.filter_by(name=perm_name).first()
        if perm:
            db.session.add(RolePermission(role_id=new_role.RoleID, permission_id=perm.id))

    for user_id in user_ids:
        user = User.query.get(int(user_id))
        if user:
            user.roleId = new_role.RoleID

    db.session.commit()
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/toggle/<int:role_id>', methods=['POST'])
@login_required
def admin_toggle_role(role_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    role = Role.query.get(role_id)
    role.active = not role.active
    db.session.commit()
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/toggle-all/<int:active>', methods=['POST'])
@login_required
def admin_toggle_all_roles(active):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    Role.query.update({Role.active: bool(active)})
    db.session.commit()
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
@login_required
def admin_delete_role(role_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    RolePermission.query.filter_by(role_id=role_id).delete()
    Role.query.filter_by(RoleID=role_id).delete()
    db.session.commit()
    return redirect(url_for('admin_roles'))

@app.route('/admin/roles/edit/<int:role_id>')
@login_required
def admin_edit_role(role_id):
    if not current_user.has_role(['Admin']):
        return redirect(url_for('index'))
    # Placeholder for now
    return redirect(url_for('admin_roles'))