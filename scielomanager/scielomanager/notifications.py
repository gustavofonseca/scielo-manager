# coding: utf-8
import logging
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from . import tasks

logger = logging.getLogger(__name__)


class Message(object):
    subject = ''
    recipients = []
    template_path = ''
    body = ''
    EMAIL_DATA_BY_ACTION = None # dict must be defined for each subclass mapping action's name (key), and a dict with keys: 'subject_sufix' and 'template_path'

    def __init__(self, action, subject='', recipients=[], template_path=None):
        """
        @param ``action``: key of self.EMAIL_DATA_BY_ACTION dict, will define some message presets
        @param ``subject``: middle text of the message subject, prepended by:
            settings.EMAIL_SUBJECT_PREFIX, appended by self.EMAIL_DATA_BY_ACTION[action]['subject_sufix']
        @param ``recipients`` (optional), set the list of recipients of the message
        @param ``template_path`` (optional), is the path of the templated used to render the message body,
            if not provided, the template defined in self.EMAIL_DATA_BY_ACTION[action]['template_path'] will be used.
        """
        if not self.EMAIL_DATA_BY_ACTION.has_key(action):
            raise ValueError("This action: %s is not available. Please use one of this: %s " % (action, self.EMAIL_DATA_BY_ACTION.keys()))

        subject_sequence = [
            settings.EMAIL_SUBJECT_PREFIX,
            subject,
            self.EMAIL_DATA_BY_ACTION[action]['subject_sufix'],
        ]
        self.subject = ' '.join(subject_sequence)
        self.recipients = recipients

        if template_path:
            self.template_path = template_path
        else:
            self.template_path = self.EMAIL_DATA_BY_ACTION[action]['template_path']

    def render_body(self, context=None):
        """
        render to string the body content.
        Will include a default context, and also the @param context dict.
        The result will be in self.body
        """
        domain = Site.objects.get_current().domain
        default_context = {
            'domain': domain,
        }
        if context:
            context.update(default_context)
        else:
            context = default_context

        self.body = render_to_string(self.template_path, context)


    def set_recipients(self, *args, **kwargs):
        """
        Implement this method to update the recipients list, based in args and kwargs data.
        """
        raise NotImplementedError("Please Implement this method")

    def send_mail(self):
        """
        if self.recipients is not empty, will call task.send_mail
        """
        if self.recipients:
            return tasks.send_mail.delay(self.subject, self.body, self.recipients)
        else:
            logger.info("[Message.send_mail] Can't send a message without recipients, did you call 'set_recipients(...)'?")