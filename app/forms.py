from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
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
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
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
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirmPassword = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')])
    submit = SubmitField('Reset Password')

class CreateTicketForm(FlaskForm):
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=3, max=200, message="Subject must be between 3 and 200 characters long")]
    )

    description = TextAreaField(
        "Description",
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

    def validate_resolutionReasoning(self, field):
        if self.status.data in [5, 6] and not field.data:
            raise ValidationError("Resolution reasoning is required when closing or resolving a ticket.")
        

class AdminSettingsForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Save')

class AdminProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    language = SelectField('Language', choices=[('English', 'English')])
    submit = SubmitField('Save')

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
        ('view_profile', 'View profile'),
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
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=15, message='Username must be between 3 and 15 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    submit = SubmitField('Save Changes')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')