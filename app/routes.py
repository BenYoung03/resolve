from app import app
from flask import render_template, flash, redirect
from app.forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for email: {}, remember_me={}'.format(
            form.email.data, form.remember_me.data))
        return redirect('/index')
    return render_template('login.html', title='Sign In', form=form)