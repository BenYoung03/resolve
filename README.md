# Resolve - IT Ticketing System

Resolve is a web-based IT ticketing system designed to help organizations manage technical support requests efficiently. Users can create tickets, track progress, communicate with IT staff, and receive email notifications when ticket statuses change.

This project was created to be the Advanced Project for my Lakehead Computer Science Degree in a team of three!

To view the project, click here! **ADD LINK HERE**

# How It's Made:

**Front End:** HTML, CSS, JavaScript, Datatables

**Back End:** Python, Flask, SQLite

**User Authentication/Email Notifications**: Flask-Login, Flask-Mail, PyJWT

The ticketing system is built with HTML, CSS, and Javascript as the Front End technologies. Jinja templates are used to generate HTML templates that integrate with the Flask backend. The Datatables library is also used to generate the table that houses all of the IT tickets. This table allows users to sort and/or filter certain columns and search for specific tickets by ID.

The Back End is built using Python, Flask and SQLite. Flask handles all of the routing to different templates, form generation with WTForms for forms such as the login, register, ticket creation and others, and integration with the SQLite database via Flask-SQLAlchemy, which is a popular ORM that allows applications to manage a database using classes, objects and methods.

The SQLite database consists of many tables including the User, TicketStatus, Tickets, TicketPriority, TicketComment, TicketCategories, and Roles tables. Corresponding model classes for these tables include User, Role, Status, Ticket, Priority, Category, TicketComment

User authentication is handled using Flask-Login built in functionalities. The User model extends UserMixin, allowing Flask-Login to automatically handle functionailty such as tracking logged in usrs and restricting access to protected routes. Werkzueg is used to generate password hashes to ensure secure storage of user data. Email notifications are handled using Flask-Mail. We used a Gmail SMTP connection to send email notifications from resolveticketing@gmail.com. PyJWT is used to generate a JSON web token which is used when sending password reset emails to users that request one.

# Getting Started

To run the project on your local environment, please perform the following steps.

### Prerequisites

Before cloning the repository and setting up the virtual environment, please ensure the latest version of Python and pip is installed. To check, please run the following command:

`pip --version`

This will allow you to see what version of pip you have, and if it is installed in the first place. To upgrade to the latest version, please peform the following:

`python -m pip install --upgrade pip`

### Installation

You can now follow these steps to install Resolve locally:

1. Clone the Repo
   `git clone https://github.com/BenYoung03/resolve.git`'
2. Create a python virtual environment
   `python -m venv venv`
3. Activate the virtual enviornment, there are three ways to do so

* Windows (CMD):
  `venv\Scripts\activate`
* Windows (PowerShell):
  `venv\Scripts\Activate.ps1`
* Mac/Linux:
  `source venv/bin/activate`

4. Install project dependencies
   `pip install -r packages.txt`
5. Create .env file for email sending and place in root of project directory (*Optional*)
   ```
   MAIL_SERVER=smtp.googlemail.com
   MAIL_PORT=587
   MAIL_USE_TLS=1
   MAIL_USERNAME=<email-here>
   MAIL_PASSWORD=<gmail-app-password-here>
   ```
6. Run the application:
   `flask run`
7. Open Application in browser
   `http://127.0.0.1:5000`
