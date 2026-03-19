from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput

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


class ProfileForm(FlaskForm):
    username = StringField('Name')
    email = StringField('Email')
    language = SelectField('Language', choices=[('en', 'English')])
    submit = SubmitField('Save And Reload')

class SettingsForm(FlaskForm):
    old_password = PasswordField('Old Password')
    new_password = PasswordField('New Password')
    submit = SubmitField('Update Password')


class NewUserForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('2', 'Agent'), ('3', 'Admin')])
    submit = SubmitField('Create User')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class NewClientForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')



class RolePermissionForm(FlaskForm):
    role_name = StringField('Role Name', validators=[DataRequired()])
    submit = SubmitField('Next')

class RoleUserAssignForm(FlaskForm):
    submit = SubmitField('Create Role')
class CreateTicketForm(FlaskForm):
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=3, max=200)]
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=10)]
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
        if self.status.data == 5 and not field.data:
            raise ValidationError("Resolution reasoning is required when closing or resolving a ticket.")
