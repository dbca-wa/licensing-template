from __future__ import unicode_literals
from django.conf import settings

from django.apps import AppConfig


class LicensingTemplateConfig(AppConfig):
    name = "licensing_template"
    verbose_name = settings.SYSTEM_NAME

    run_once = False

    def ready(self):
        if not self.run_once:
            from licensing_template.components.organisations import signals
            from licensing_template.components.proposals import signals

        self.run_once = True
