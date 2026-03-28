from flask_mail import Message
from app import mail
from threading import Thread
from flask import render_template, url_for

from app import app

def sendAsyncEmail(app, msg):
    with app.app_context():
        mail.send(msg)

#TODO: Update stylings for message using HTML instead of plaintext
def ticketStatusChangeNotification(ticket, recipient, oldStatus, newStatus):
    msg = Message(
        subject=f"Update for Ticket {ticket.ticketNumber}",
        recipients=[recipient]
    )

    msg.body = f"""
    Hello,

    The status of your ticket has been updated.

    Ticket: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Previous Status: {oldStatus}
    New Status: {newStatus}

    Thank you,
    Resolve Ticketing
    """
    msg.html = render_template(
        'email/ticketStatusChange.html',
        ticket=ticket,
        oldStatus=oldStatus,
        newStatus=newStatus
    )

    Thread(target=sendAsyncEmail, args=(app, msg)).start()

def ticketCreated(ticket, recipient):
    msg = Message(
        subject=f"Ticket Created: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    msg.body = f"""
    Hello {ticket.creator.username},

    Your support request has been successfully submitted.

    Ticket Details
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Status: Open
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

def notifyAgentsOfNewTicket(ticket, recipients):
    if not recipients:
        return

    msg = Message(
        subject=f"New Ticket Created: {ticket.ticketNumber}",
        recipients=recipients
    )

    msg.body = f"""
    Hello Agent,

    A new support ticket has been created.

    Ticket Details
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Created: {ticket.CreatedAt.strftime('%b %d, %Y, %I:%M %p')}

    Please log in to Resolve Ticketing to review and assign the ticket.

    Thank you,
    Resolve Ticketing
    """

    Thread(target=sendAsyncEmail, args=(app, msg)).start()

def ticketAssignedNotification(ticket, recipient):
    msg = Message(
        subject=f"Ticket Has Been Assigned To You: {ticket.ticketNumber}",
        recipients=[recipient]
    )

    msg.body = f"""
    Hello {ticket.assignee.username},

    A support ticket has been assigned to you.

    Ticket Details
    Ticket Number: {ticket.ticketNumber}
    Subject: {ticket.subject}
    Category: {ticket.category.name}
    Priority: {ticket.priority.name}
    Created: {ticket.CreatedAt.strftime('%b %d, %Y, %I:%M %p')}

    Please log in to Resolve Ticketing to review the ticket.

    Thank you,
    Resolve Ticketing
    """
    Thread(target=sendAsyncEmail, args=(app, msg)).start()

def passwordResetEmail(user):
    token = user.get_reset_password_token()
    msg = Message(
        subject="Password Reset Request",
        recipients=[user.email]
    )

    msg.body = f"""Hello {user.username},

    We received a request to reset your password.
    Reset link: {url_for('reset_password', token=token, _external=True)}

    If you did not request a password reset, please ignore this email.

    Thank you,
    Resolve Ticketing
    """
    msg.html = render_template('email/resetPassword.html', user=user, token=token)
    Thread(target=sendAsyncEmail, args=(app, msg)).start()
    