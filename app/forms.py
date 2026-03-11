from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo

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
        validators=[DataRequired()]
    )

    submit = SubmitField("Update Ticket")