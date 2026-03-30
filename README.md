<a id="readme-top"></a>

<p align="center">
  <img src="app/static/img/ResolveLogo.png" alt="Resolve Logo" width="220" />
</p>

# Resolve - IT Ticketing System

Resolve is a web-based IT ticketing system designed to help organizations manage technical support requests efficiently. Users can create tickets, track progress, communicate with IT staff, and receive email notifications when ticket statuses change.

This project was created to be the Advanced Project for my Lakehead Computer Science Degree in a team of three!

To view the project, click here! https://resolve.solargames.ca/login

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#how-its-made">How It's Made</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#features">Features</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

# How It's Made:

**Front End:** HTML, CSS, JavaScript, Datatables

**Back End:** Python, Flask, SQLite

**User Authentication/Email Notifications**: Flask-Login, Flask-Mail, PyJWT

The ticketing system is built with HTML, CSS, and Javascript as the Front End technologies. Jinja templates are used to generate HTML templates that integrate with the Flask backend. The Datatables library is also used to generate the table that houses all of the IT tickets. This table allows users to sort and/or filter certain columns and search for specific tickets by ID.

The Back End is built using Python, Flask and SQLite. Flask handles all of the routing to different templates, form generation with WTForms for forms such as the login, register, ticket creation and others, and integration with the SQLite database via Flask-SQLAlchemy, which is a popular ORM that allows applications to manage a database using classes, objects and methods.

The SQLite database consists of many tables including the User, TicketStatus, Tickets, TicketPriority, TicketComment, TicketCategories, and Roles tables. Corresponding model classes for these tables include User, Role, Status, Ticket, Priority, Category, TicketComment

User authentication is handled using Flask-Login built in functionalities. The User model extends UserMixin, allowing Flask-Login to automatically handle functionailty such as tracking logged in usrs and restricting access to protected routes. Werkzueg is used to generate password hashes to ensure secure storage of user data. Email notifications are handled using Flask-Mail. We used a Gmail SMTP connection to send email notifications from resolveticketing@gmail.com. PyJWT is used to generate a JSON web token which is used when sending password reset emails to users that request one.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

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
   ```
   git clone https://github.com/BenYoung03/resolve.git`
   ```
2. Create a python virtual environment
   ```
   python -m venv venv
   ```
3. Activate the virtual environment, there are three ways to do so

* Windows (CMD):
  ```
  venv\Scripts\activate
  ```
* Windows (PowerShell):
  ```
  venv\Scripts\Activate.ps1
  ```
* Mac/Linux:
  ```
  source venv/bin/activate
  ```
4. Install project dependencies
   ```
   pip install -r packages.txt
   ```
5. Create .env file for email sending and place in root of project directory (*Optional*)
   ```
   MAIL_SERVER=smtp.googlemail.com
   MAIL_PORT=587
   MAIL_USE_TLS=1
   MAIL_USERNAME=<email-here>
   MAIL_PASSWORD=<gmail-app-password-here>
   ```
6. Run the setup.ps1 PowerShell script which creates the SQLite database with the required tables and a test admin account.
    ```
   .\setup.ps1
   ```
7. Run the application:
   ```
   flask --app resolve run
   ```
8. Open Application in browser
   ```
   http://127.0.0.1:5000
   ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Features

Resolve has many features that are essential to any IT ticketing system.

### Ticket Management
With Resolve, Users are able to create tickets by filling out the create ticket form. Employees who need to create a ticket are able to input a subject, description, category, and priority for their ticket. Upon creation, the ticket is assigned a unique ticket number, and agents/admins will receive the ticket and will be able to view, update, and monitor the details, and the employee who created the ticket can monitor the ticket for any updates.

![Ticket Form](README%20Images/NewTicket.png)

Users are able to view tickets on the home page of Resolve. The home page features buttons that allow users to submit a new ticket and filter tickets by open, closed, and ticket assignment if the user is an agent/admin. The table that contains the ticket information is built using the DataTables library. Users are able to filter each column as well as search for individual tickets as a result. 

![Home Page](README%20Images/HomePage.png)

### Role-Based Access

Resolve implements a role-based access system that ensures users of certain roles only have access to the features and data appropriate for their use case. For example, users with the "Employee" role are only able to view tickets that they created, whereas agents/admins can view all tickets created in order to provide support to all users. 

The implementation of role-based access can be seen prominently throughout the individual ticket view page. For agents and admins, there exists a "update ticket" form which allows users with correct permissions to update the ticket priority, assignee, and status. For employees, this feature is not present, as employees are only able to monitor tickets, and no modification is allowed. 

<p align="center">
  <img src="README%20Images/AgentTicketView.png" alt="Agent View" width="49%">
  <img src="README%20Images/EmployeeTicketView.png" alt="Employee View" width="49%">
</p>

### Email Notifications 

Resolve also features automated email notifications, which keep users informed about important updates related to their tickets. These notifications are triggered when key events occur. Examples of said events that have a coinciding email notification include ticket status changes, ticket creation, ticket assignment to an agent, and new comments. Furthermore, Flask is also able to send password reset emails to users who forget their passwords. This is performed by generating a JSON Web Token, which expires after a short period of time, and sending an email to the user containing the time-limited password reset link. Each email notification uses a corresponding HTML template with custom styling to ensure a consistent and professional appearance. Below is an example of the password reset email template:

![Password Reset](README%20Images/PasswordReset.png)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Contact
Benjamin Young - bryoung1@lakeheadu.ca

LinkedIn: [Benjamin Young](https://www.linkedin.com/in/benjamin-young-2b5497282/)  
GitHub: [BenYoung03](https://github.com/BenYoung03)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

