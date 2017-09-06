"""
Author: Joseph Neumann, 2016
Flask wrapper for python SendGrid support
Usage:

from flask_sendgrid import send_email

send_email(
    from_email='someone@yourdomain.com',
    to=['someone@domain.com','someoneelse@someotherdomain.com'],
    subject='Subject',
    text='Hello World'
)
"""
from sendgrid import *
from sendgrid.helpers.mail import *
from flask import render_template, current_app
from celery_worker import celery
import re, os


@celery.task()
def send_async_email(data):
    app = current_app._get_current_object()
    api_key = os.environ.get('SENDGRID_API_KEY')
    sg = SendGridAPIClient(apikey=api_key)
    response = sg.client.mail.send.post(request_body=data)


def send_email(**kwargs):
    app = current_app._get_current_object()
    default_from = app.config['SENDGRID_DEFAULT_FROM']
    dummy_email = False
    if not kwargs.get('from_email', None) and not default_from:
        raise ValueError('No from email or default_from email configured')

    if not kwargs.get('subject', None):
        raise ValueError('No subject configured')

    if not kwargs.get('to', None):
        raise ValueError('No to_email configured')

    message = Mail()
    # message.set_from(Email(kwargs.get('from_email', None) or default_from))
    message.from_email = Email(kwargs.get('from_email', None) or default_from)
    # message.set_subject(kwargs.get('subject', None))
    message.subject = kwargs.get('subject', None)
    message.add_content(Content("text/plain", render_template(kwargs.get('template') + '.txt', **kwargs)))
    message.add_content(Content("text/html", render_template(kwargs.get('template') + '.html', **kwargs)))

    personalization = Personalization()
    to_emails = []
    for email in kwargs['to']:
        to_emails.append(email)
        personalization.add_to(Email(email))
    message.add_personalization(personalization)

    for email in to_emails:
        if re.search(r'(@EXAMPLE)+', email):
            dummy_email = True

    if current_app.config['EMAIL_OFF']:
        pass
    elif dummy_email:
        pass
    else:
        data = message.get()
        send_async_email.delay(data=data)
