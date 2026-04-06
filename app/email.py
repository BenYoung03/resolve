# Contains all of the preset email notifications that are sent upon certain actions, such as ticket creation, ticket status change, and password reset requests. 
# Each function takes in the relevant information for the email being sent and uses Flask-Mail to send the email asynchronously in a separate thread.

from flask_mail import Message
from app import mail
from threading import Thread
from flask import render_template, url_for

from app import app

# Sends email asynchronously in a separate thread to avoid blocking the main application thread
def sendAsyncEmail(app, msg):
    with app.app_context():
        mail.send(msg)

# Email that is sent upon a ticket status change to the user who created the ticket
def ticketStatusChangeNotification(ticket, recipient, oldStatus, newStatus):
    msg = Message(
        subject=f"Update for Ticket {ticket.ticketNumber}",
        recipients=[recipient]
    )

    # Plaintext template to fall back upon if user cannot receive HTML emails
    msg.body = f"""
    Hello,

    The status of your ticket has been updated.

    Ticket Details:
    Ticket: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Previous Status: {oldStatus}
    New Status: {newStatus}

    Thank you,
    Resolve Ticketing
    """
    # Renders HTML template for ticket status change email
    msg.html = render_template(
        'email/ticketStatusChange.html',
        ticket=ticket,
        oldStatus=oldStatus,
        newStatus=newStatus
    )

    # Starts a new thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Email notification that is sent upon ticket resolution to the user who created the ticket. 
def ticketResolvedNotification(ticket, recipient):
    msg = Message(
        subject=f"{ticket.ticketNumber} resolved",
        recipients=[recipient]
    )

    # Plaintext fallback template for ticket resolved email
    msg.body = f"""
    Hello,

    Your ticket has been resolved.

    Ticket Details:
    Ticket: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Resolution: {ticket.ResolutionReasoning}
    Agent: {ticket.assignee.email}

    If you have any issues, please contact the agent or leave a comment to have the ticket reopened.

    Thank you,
    Resolve Ticketing
    """
    # Renders HTML template for ticket resolved email
    msg.html = render_template(
        'email/ticketResolved.html',
        ticket=ticket
    )

    # Starts a new thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Email notification that is sent upon ticket creation to the user who created the ticket
def ticketCreated(ticket, recipient):
    msg = Message(
        subject=f"Ticket Created: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    msg.body = f"""
    Hello {ticket.creator.username},

    Your support request has been successfully submitted.

    Ticket Details:
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Created: {ticket.CreatedAt.strftime('%b %d, %Y, %I:%M %p')}

    Our team will review your request and begin working on it shortly.
    You will receive email updates when the status of your ticket changes.

    You can view your ticket and add additional comments by logging into resolve.

    Thank you,
    Resolve Ticketing
    """

    msg.html = render_template(
        'email/ticketCreated.html',
        ticket=ticket
    )

    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Email notification that is sent to agents when a new ticket is created
def notifyAgentsOfNewTicket(ticket, recipients):
    if not recipients:
        return

    msg = Message(
        subject=f"New Ticket Created: {ticket.ticketNumber}",
        # Sends to all agents that have notifications enabled
        recipients=recipients
    )

    # Plaintext fallback template for new ticket creation notification email to agents
    msg.body = f"""
    Hello Agent,

    A new support ticket has been created.

    Ticket Details:
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Created: {ticket.CreatedAt.strftime('%b %d, %Y, %I:%M %p')}

    Please log in to Resolve Ticketing to review and assign the ticket.

    Thank you,
    Resolve Ticketing
    """
    # Renders HTML template for new ticket creation notification email to agents
    msg.html = render_template(
        'email/notifyAgentsOfNewTicket.html',
        ticket=ticket
    )

    # Starts a new thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Email template notifying an agent that a ticket has been assigned to them.
def ticketAssignedNotification(ticket, recipient):
    msg = Message(
        subject=f"Ticket Has Been Assigned To You: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    # Plaintext fallback template for ticket assignment notification email to agents
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

    # Renders HTML template for ticket assignment notification email to agents
    msg.html = render_template(
        'email/ticketAssigned.html',
        ticket=ticket
    )

    # Starts a new thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Email notification that is sent to the ticket creator upon a new comment being added to their ticket
# Uses comment author, text, who created the comment and the commenter role to render the email template differently based on whether the comment was made by an agent or the ticket creator themselves.
def commentAddedNotification(ticket, recipient, commentAuthor, commentText, commentCreatedAt, commenterRole):
    msg = Message(
        subject=f"New Comment Added: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    # Plaintext fallback template for new comment added notification email to ticket creator
    msg.body = f"""
    Hello {ticket.creator.username},

    A new comment was added to your ticket.

    Ticket Details:
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Comment Author: {commentAuthor}
    Comment: {commentText}

    Please login to resolve to see further details.

    Thank you,
    Resolve Ticketing
    """

    # Renders HTML template for new comment added notification email to ticket creator
    msg.html = render_template(
        'email/commentAdded.html',
        ticket=ticket,
        commentAuthor=commentAuthor,
        commentText=commentText,
        commentCreatedAt=commentCreatedAt,
        commenterRole=commenterRole
    )

    # Starts a new thread to send the email asynchronously
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

# Password reset email template that is sent to users who request a password reset
def passwordResetEmail(user):
    # Gets the users password reset token
    token = user.get_reset_password_token()
    msg = Message(
        subject="Password Reset Request",
        recipients=[user.email]
    )

    # Plaintext fallback template for password reset email
    msg.body = f"""Hello {user.username},

    We received a request to reset your password.
    Reset link: {url_for('reset_password', token=token, _external=True)}

    If you did not request a password reset, please ignore this email.

    Thank you,
    Resolve Ticketing
    """
    # Renders HTML template for password reset email. Includes the reset link with the token.
    msg.html = render_template(
        'email/resetPassword.html', 
        user=user, 
        token=token)
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

    