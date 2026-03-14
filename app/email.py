from flask_mail import Message
from app import mail

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

    mail.send(msg)