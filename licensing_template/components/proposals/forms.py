from django import forms
from django.db import models
from django.forms import Textarea
from django.utils.safestring import mark_safe
from licensing_template.components.proposals.models import HelpPage, SectionChecklist
from licensing_template.components.main.models import SystemMaintenance
from ckeditor.widgets import CKEditorWidget
from django.conf import settings
import pytz
from datetime import datetime, timedelta


class LicensingTemplateHelpPageAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = HelpPage
        fields = "__all__"


class SectionChecklistForm(forms.ModelForm):
    class Meta:
        model = SectionChecklist
        fields = "__all__"

    def clean(self):
        cleaned_data = super(SectionChecklistForm, self).clean()
        if cleaned_data["enabled"] is False:
            # We don't mind any disabled record
            return cleaned_data
        if (
            len(self.changed_data) == 1
            and self.changed_data[0] == "enabled"
            and cleaned_data["enabled"] is False
        ):
            # When change is only setting 'enabled' field to False, no validation required
            return cleaned_data

        cleaned_application_type = cleaned_data.get("application_type", None)
        cleaned_section = cleaned_data.get("section", None)
        cleaned_list_type = cleaned_data.get("list_type", None)
        cleaned_enabled = cleaned_data.get("enabled", None)

        # Check if there is alreay a set of questions for the section
        existings = SectionChecklist.objects.filter(
            application_type=cleaned_application_type,
            section=cleaned_section,
            list_type=cleaned_list_type,
            enabled=True,
        ).exclude(id=self.instance.id)

        if existings:
            existing = existings.first()
            raise forms.ValidationError(
                [
                    mark_safe(
                        "There is already an enabled 'Section Questions' for the Application Type:{}, Section:{} and Checklist type:{}"
                    ).format(
                        existing.application_type.get_name_display(),
                        existing.get_section_display(),
                        existing.get_list_type_display(),
                    ),
                    "You can create new one after making the existing 'Section Questions' disabled.",
                ]
            )


class SystemMaintenanceAdminForm(forms.ModelForm):
    class Meta:
        model = SystemMaintenance
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        try:
            latest_obj = SystemMaintenance.objects.exclude(id=self.instance.id).latest(
                "start_date"
            )
        except:
            latest_obj = SystemMaintenance.objects.none()
        tz_local = pytz.timezone(settings.TIME_ZONE)  # start_date.tzinfo
        tz_utc = pytz.timezone("utc")  # latest_obj.start_date.tzinfo

        if latest_obj:
            latest_end_date = latest_obj.end_date.astimezone(tz=tz_local)
            if self.instance.id:
                if (
                    start_date < latest_end_date
                    and start_date < self.instance.start_date.astimezone(tz_local)
                ):
                    raise forms.ValidationError(
                        "Start date cannot be before an existing records latest end_date. Start Date must be after {}".format(
                            latest_end_date.ctime()
                        )
                    )
            else:
                if start_date < latest_end_date:
                    raise forms.ValidationError(
                        "Start date cannot be before an existing records latest end_date. Start Date must be after {}".format(
                            latest_end_date.ctime()
                        )
                    )

        if self.instance.id:
            if start_date < datetime.now(tz=tz_local) - timedelta(
                minutes=5
            ) and start_date < self.instance.start_date.astimezone(tz_local):
                raise forms.ValidationError(
                    "Start date cannot be edited to be further in the past"
                )
        else:
            if start_date < datetime.now(tz=tz_local) - timedelta(minutes=5):
                raise forms.ValidationError("Start date cannot be in the past")

        if end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date")

        super(SystemMaintenanceAdminForm, self).clean()
        return cleaned_data
