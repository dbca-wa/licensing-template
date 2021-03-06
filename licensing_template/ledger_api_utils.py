from __future__ import unicode_literals
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from licensing_template.components.main.decorators import basic_exception_handler

import logging

logger = logging.getLogger("licensing_template")


@basic_exception_handler
def retrieve_email_user(email_user_id):
    return EmailUser.objects.get(id=email_user_id)
