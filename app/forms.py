from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, SelectMultipleField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired, ValidationError

PERMISSION_CHOICES = [
    ('view_all_tickets', 'View all tickets'),
    ('assign_tickets', 'Assign tickets'),
    ('ticket_agent', 'Ticket agent'),
    ('update_ticket_priority', 'Update ticket priority'),
    ('update_ticket_status', 'Update ticket status'),
    ('view_roles', 'View roles'),
    ('create_roles', 'Create roles'),
    ('view_users', 'View users'),
    ('create_users', 'Create users'),
    ('view_clients', 'View clients'),
    ('change_settings', 'Change settings'),
    ('view_profile', 'View profile'),
]

class LoginForm(FlaskForm):
    # Login form with email, password, remember me checkbox, and submit button
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    # Registration form with username, email, password, confirm password, and submit button
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=15, message='Username must be between 3 and 15 characters.')
    ])

    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])

    confirmPassword = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')])
    submit = SubmitField('Register')

class PasswordResetForm(FlaskForm):
    # Password reset form with email field and submit button
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    # Password reset form with new password, confirm password, and submit button
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirmPassword = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')])
    submit = SubmitField('Reset Password')

class CreateTicketForm(FlaskForm):
    # Takes subject, description, category, priority, and submit button from user input and uses that info to create a ticket
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=3, max=200, message="Subject must be between 3 and 200 characters long")]
    )

    description = TextAreaField(
        "Description",
        # Description must be at least 10 characters to ensure proper level of detail
        validators=[DataRequired(), Length(min=10, message="Description must be 10 characters long")]
    )

    category = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired()]
    )

    priority = SelectField(
        "Priority",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Create Ticket")
    
class CommentForm(FlaskForm):
    comment = TextAreaField(
        "Comment",
        validators=[DataRequired(), Length(min=1)]
    )
    submit = SubmitField("Add Comment")

class UpdateTicket(FlaskForm):
    # Form for updating a ticket's status, priority, assignee, and resolution reasoning
    status = SelectField(
        "Status",
        coerce=int,
        validators=[DataRequired()]
    )

    priority = SelectField(
        "Priority",
        coerce=int,
        validators=[DataRequired()]
    )

    assignedTo = SelectField(
        "Assign To",
        coerce=int,
        validators=[InputRequired()]
    )

    resolutionReasoning = TextAreaField(
        "Resolution Reasoning",
        validators=[Length(max=1000)]
    )

    submit = SubmitField("Update Ticket")

    # Does not validate the form if a ticket is being resolved without a resolution reasoning
    def validate_resolutionReasoning(self, field):
        if self.status.data in [5] and not field.data:
            raise ValidationError("Resolution reasoning is required when closing or resolving a ticket.")
        
class AdminSettingsForm(FlaskForm):
    mail_server = StringField('Mail Server', validators=[DataRequired()])
    mail_port = StringField('Mail Port', validators=[DataRequired()])
    mail_use_tls = RadioField('Use TLS',choices=[('yes', 'Yes'), ('no', 'No')],default='yes',validators=[DataRequired()])
    mail_username = StringField('Mail Username', validators=[DataRequired(), Email()])
    mail_password = PasswordField('Mail Password', validators=[DataRequired()])
    submit = SubmitField('Save')
# class AdminSettingsForm(FlaskForm):
#     old_password = PasswordField('Old Password', validators=[DataRequired()])
#     new_password = PasswordField('New Password', validators=[DataRequired()])
#     submit = SubmitField('Save')

# class AdminProfileForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     language = SelectField('Language', choices=[('English', 'English')])
#     submit = SubmitField('Save')

class AdminNewClientForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Create Client')

# class AdminRoleForm(FlaskForm):
#     role_name = StringField('Role Name', validators=[DataRequired()])
#     role = SelectField('Role', coerce=int)
#     permissions = SelectMultipleField('Permissions', choices=PERMISSION_CHOICES)
#     submit = SubmitField('Save')
class AdminRoleForm(FlaskForm):
    role_name = StringField('Role Name')
    role = SelectField('Role', coerce=int, choices=[], validate_choice=False)
    permissions = SelectMultipleField('Permissions', choices=[
        ('view_all_tickets', 'View all tickets'),
        ('assign_tickets', 'Assign tickets'),
        ('ticket_agent', 'Ticket agent'),
        ('update_ticket_priority', 'Update ticket priority'),
        ('update_ticket_status', 'Update ticket status'),
        ('view_roles', 'View roles'),
        ('create_roles', 'Create roles'),
        ('view_users', 'View users'),
        ('create_users', 'Create users'),
        ('view_clients', 'View clients'),
        ('change_settings', 'Change settings'),
    ])
    submit = SubmitField('Save')

class AdminResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    submit = SubmitField('Reset Password')


class AdminNewUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=15, message='Username must be between 3 and 15 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create User')

class EditProfileForm(FlaskForm):
    # Form for users to edit their profile information, including username, email, and notification preferences
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=15, message='Username must be between 3 and 15 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    notifications = BooleanField('Email Notifications?')
    submit = SubmitField('Save Changes')

class ChangePasswordForm(FlaskForm):
    # Change password form for user profile page
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Save Changes')