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
    Note: If the setup script does not work, this is likely due to an error with the ExecutionPolicy. If this occurs, please run PowerShell as administrator and run the following command:
   ```powershell
   Set-ExecutionPolicy RemoteSigned
   ```
8. Run the application:
   ```
   flask --app resolve run
   ```
9. Open Application in browser
   ```
   http://127.0.0.1:5000
   ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Features

Resolve has many features that are essential to any IT ticketing system.

### Ticket Management
With Resolve, Users are able to create tickets by filling out the create ticket form. Employees who need to create a ticket are able to input a subject, description, category, and priority for their ticket. Upon creation, the ticket is assigned a unique ticket number, and agents/admins will receive the ticket and will be able to view, update, and monitor the details, and the employee who created the ticket can monitor the ticket for any updates.

![Ticket Form](README%20Images/NewTicket.png)

This code snippet shows the route that is run when a ticket is created. The category and priority select field in the CreateTicketForm are populated dynamically using information from the database. On form submission, the data from the form is read and used to create a new ticket. This ticket is then created and added to the database. Before committing the new ticket to the database, a ticket number is generated, in the format of the TicketID with leading 0s appended to the text "ID-". db.session.flush() is used so the TicketID is available before committing the ticket to the database. A new ActivityLog entry is also created, tracking the user who created the ticket, the associated TicketID, the action, being ticket creation, and the time of the activity. If the user has email notifications enabled, a notification email is sent indicating that the ticket was successfully created. Agents with email notifications enabled are also subsequently notified upon creation.

```python
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
            CreatedAt=datetime.now(),
            ClosedAt=None
        )

        db.session.add(newTicket)
        db.session.flush() 

        newTicket.ticketNumber = f"ID-{newTicket.TicketID:06d}"

        newActivity = ActivityLog(
            UserID = newTicket.CreatedBy,
            TicketID = newTicket.TicketID,
            action = "Ticket created",
            CreatedAt=datetime.now(),
        )

        db.session.add(newActivity)

        db.session.commit()

        if current_user.notifications:
            ticketCreated(newTicket, current_user.email)

        agents = (db.session.scalars(sa.select(User).where(User.roleId.in_([2, 3]))).all())
        agentsEmails = [agent.email for agent in agents]
        # Notify agents who have notifications enabled
        notifyAgentsOfNewTicket(newTicket, [email for agent, email in zip(agents, agentsEmails) if agent.notifications])

        flash(f'Ticket {newTicket.ticketNumber} created successfully.')
        return redirect(url_for('index'))

    if request.method == "POST" and not form.validate():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "warning")

    return render_template('newticket.html', form=form)
```

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

The following is a code snippet showing one of the Flask Mail email templates. This function sends an email to the agent that a ticket has been assigned too. Using python threads, we have implemented aysnchronous email sending. The sendAsyncEmail function is passed the application context and the Flask Mail message object and the message is then sent as a background thread. This allows users to continue using Resolve while the email sends in the background.

```python
def ticketAssignedNotification(ticket, recipient):
    msg = Message(
        subject=f"Ticket Has Been Assigned To You: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    msg.body = f"""
    Hello {ticket.assignee.username},

    A support ticket has been assigned to you.

    Ticket Details:
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Created: {ticket.CreatedAt.strftime('%b %d, %Y, %I:%M %p')}

    Please log in to Resolve Ticketing to review the ticket.

    Thank you,
    Resolve Ticketing
    """

    msg.html = render_template(
        'email/ticketAssigned.html',
        ticket=ticket
    )

    Thread(target=sendAsyncEmail, args=(app, msg)).start()
```

### Profile Page

Resolve also features a profile page. This profile page allows users to modify their account information. This information includes email, username and password. Furthermore, users are able to view information related to tickets. Support staff are able to view the number of tickets assigned to them, the number of unassigned tickets that are open, and the amount of tickets they have resolved since their account has been created.

Users without any ticket modification permissions (i.e. employees) can see how many tickets they have created, how many of those tickets are open, and how many of their tickets they have created have been resolved.

Furthermore, all users are able to view the last five actions they have performed on tickets via the profile activity log. For example, agents can see the last tickets they have assigned, changed the status of, etc.

![Profile Page](README%20Images/Profile.png)

The following is the HTML template code for the ticket overview. This is a great demonstration on how Resolve handles role based access via Jinja templates.

```html
<div class="ticket-overview">
    <h2>Ticket Overview</h2>

    {% if current_user.has_role(['Agent', 'Admin']) or
          current_user.has_permission('ticket_agent') or
          current_user.has_permission('assign_tickets') %}
        <!--Support Staff-->
        <div class="overview-element">
            <div class="overview-title">Assigned to Me:</div>
            <div class="overview-info">{{ assigned_to_me_count }}</div>
        </div>
        <!--Remaining overview here...-->
    {% else %}
        <!--Employees-->
        <div class="overview-element">
            <div class="overview-title">Tickets Created:</div>
            <div class="overview-info">{{ tickets_created_count }}</div>
        </div>
        <!--Remaining overview here...-->
    {% endif %}
</div>
```
### Admin Panel

Resolve includes an admin panel protected by role-based and permission-based access control. Rather than giving every staff member full administrator access, the system allows access to specific admin pages based on the user's role or assigned permissions. The admin area currently includes Users, Clients, and Roles pages, and each section is only visible to users with the required access.

#### User Management
The Users page allows authorized staff to manage internal user accounts. From this page, users with the correct permissions can view all users, create new internal users, change user roles, reset passwords, and delete accounts. The system validates submitted data, ensures the selected role exists and is active, securely stores passwords using hashing, and prevents invalid actions such as deleting your own account.

<p align="center">
  <img src="README%20Images/admin-users.png" alt="Users Page" width="850" />
</p>

#### Client Management
The Clients page is used to manage client accounts separately from internal support staff. It displays client users, includes a basic name filter, and allows authorized users to create new client accounts or delete existing ones. This keeps customer account management separate from staff account administration.

<p align="center">
  <img src="README%20Images/admin-clients.png" alt="Clients Page" width="850" />
</p>

#### Role and Permission Management
Resolve starts with three built-in roles: Admin, Agent, and Employee. These are the default system roles and cannot be deleted, renamed, disabled, or changed. Their default permissions are also fixed and cannot be modified. Only custom roles can be created, edited, enabled, disabled, or deleted. This protects the core access structure of the system and ensures the main roles always keep their intended behavior.

The Roles page allows authorized users to manage custom roles and assign permissions for both ticket handling and admin access, such as viewing all tickets, assigning tickets, updating ticket priority or status, viewing users, creating users, viewing clients, viewing roles, and creating roles. Role creation is handled in two steps: permissions are selected first, then users can optionally be assigned to the new role.

If a custom role is disabled, any users assigned to it are moved back to the Employee role. This allows the system to support more flexible staff access without affecting the required default roles.

<p align="center">
  <img src="README%20Images/admin-roles.png" alt="Roles Page" width="850" />
</p>
#### Settings Management
The Settings page is used to manage the system email configuration directly through the admin panel. Instead of manually creating and editing the `.env` file, an authorized admin can configure the mail settings from the web interface.

If a `.env` file already exists, the system reads the current values and displays the mail server, port, TLS setting, and username in the form. For security reasons, the stored mail password is never shown back to the user. If no `.env` file is present, filling in the settings form and saving will create the file automatically.

This allows the email system to be configured more easily while still protecting sensitive credentials.

<p align="center">
  <img src="README%20Images/admin-settings.png" alt="Roles Page" width="850" />
</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>


# Contact
Benjamin Young - bryoung1@lakeheadu.ca

LinkedIn: [Benjamin Young](https://www.linkedin.com/in/benjamin-young-2b5497282/)  
GitHub: [BenYoung03](https://github.com/BenYoung03)


Cameron McFayden - cmmcfayd@lakeheadu.ca

<p align="right">(<a href="#readme-top">back to top</a>)</p>

