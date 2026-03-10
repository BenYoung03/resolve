from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo
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
    name = StringField('Name')
    email = StringField('Email')
    language = SelectField('Language', choices=[('en', 'English')])
    submit = SubmitField('Save And Reload')

class SettingsForm(FlaskForm):
    old_password = PasswordField('Old Password')
    new_password = PasswordField('New Password')
    submit = SubmitField('Update Password')


class NewUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('2', 'Agent'), ('3', 'Admin')])
    submit = SubmitField('Create User')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class NewClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')



class RolePermissionForm(FlaskForm):
    role_name = StringField('Role Name', validators=[DataRequired()])
    submit = SubmitField('Next')

class RoleUserAssignForm(FlaskForm):
    submit = SubmitField('Create Role')