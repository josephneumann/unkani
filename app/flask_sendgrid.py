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
from . import celery


@celery.task(name='app.flask_sendgrid.send_async_email')
def send_async_email(data):
    app = current_app._get_current_object()
    api_key = app.config['SENDGRID_API_KEY']
    sg = SendGridAPIClient(apikey=api_key)
    response = sg.client.mail.send.post(request_body=data)
    print(response.status_code)
    print(response.headers)
    print(response.body)


def send_email(**kwargs):
    app = current_app._get_current_object()
    default_from = app.config['SENDGRID_DEFAULT_FROM']
    if not kwargs.get('from_email', None) and not default_from:
        raise ValueError('No from email or default_from email configured')

    if not kwargs.get('subject', None):
        raise ValueError('No subject configured')

    if not kwargs.get('to', None):
        raise ValueError('No to_email configured')

    message = Mail()
    message.set_from(Email(kwargs.get('from_email', None) or default_from))
    message.set_subject(kwargs.get('subject', None))
    message.add_content(Content("text/plain", render_template(kwargs.get('template') + '.txt', **kwargs)))
    message.add_content(Content("text/html", render_template(kwargs.get('template') + '.html', **kwargs)))

    personalization = Personalization()
    for email in kwargs['to']:
        personalization.add_to(Email(email))
    message.add_personalization(personalization)

    data = message.get()
    send_async_email.delay(data=data)
