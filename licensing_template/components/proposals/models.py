from __future__ import unicode_literals

import json
import os
import datetime
import string
from dateutil.relativedelta import relativedelta
from django.db import models, transaction
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.core.validators import MaxValueValidator, MinValueValidator

# from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField, Max, Min
from django.utils import timezone
from django.contrib.sites.models import Site
from django.conf import settings

# from ledger.accounts.models import OrganisationAddress
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Invoice
from ledger_api_client.country_models import Country
from ledger_api_client.managed_models import SystemGroup
from licensing_template import exceptions
from licensing_template.components.main.utils import get_department_user
from licensing_template.components.organisations.models import (
    Organisation,
    OrganisationContact,
    UserDelegation,
)
from licensing_template.components.main.models import (
    # Organisation as ledger_organisation, OrganisationAddress,
    CommunicationsLogEntry,
    UserAction,
    Document,
    ApplicationType,
    RequiredDocument,
    RevisionedMixin,
)
from licensing_template.components.proposals.email import (
    send_referral_email_notification,
    send_proposal_decline_email_notification,
    send_proposal_approval_email_notification,
    send_proposal_awaiting_payment_approval_email_notification,
    send_amendment_email_notification,
)
from licensing_template.ledger_api_utils import retrieve_email_user
from licensing_template.components.proposals.email import (
    send_submit_email_notification,
    send_external_submit_email_notification,
    send_approver_decline_email_notification,
    send_approver_approve_email_notification,
    send_referral_complete_email_notification,
    send_proposal_approver_sendback_email_notification,
)
import copy
import subprocess
from django.db.models import Q

# from reversion.models import Version
from dirtyfields import DirtyFieldsMixin
from decimal import Decimal as D
import csv
import time
from django.contrib.gis.db.models.fields import PointField, PolygonField


import logging

from licensing_template.settings import (
    APPLICATION_TYPE_REGISTRATION_OF_INTEREST,
    APPLICATION_TYPE_LEASE_LICENCE,
    GROUP_NAME_ASSESSOR,
    GROUP_NAME_APPROVER,
)

logger = logging.getLogger("licensing_template")


def update_proposal_doc_filename(instance, filename):
    return "{}/proposals/{}/documents/{}".format(
        settings.MEDIA_APP_DIR, instance.proposal.id, filename
    )


def update_onhold_doc_filename(instance, filename):
    return "{}/proposals/{}/on_hold/{}".format(
        settings.MEDIA_APP_DIR, instance.proposal.id, filename
    )


def update_qaofficer_doc_filename(instance, filename):
    return "{}/proposals/{}/qaofficer/{}".format(
        settings.MEDIA_APP_DIR, instance.proposal.id, filename
    )


def update_referral_doc_filename(instance, filename):
    return "{}/proposals/{}/referral/{}".format(
        settings.MEDIA_APP_DIR, instance.referral.proposal.id, filename
    )


def update_proposal_required_doc_filename(instance, filename):
    return "{}/proposals/{}/required_documents/{}".format(
        settings.MEDIA_APP_DIR, instance.proposal.id, filename
    )


def update_requirement_doc_filename(instance, filename):
    return "{}/proposals/{}/requirement_documents/{}".format(
        settings.MEDIA_APP_DIR, instance.requirement.proposal.id, filename
    )


def update_proposal_comms_log_filename(instance, filename):
    return "{}/proposals/{}/communications/{}".format(
        settings.MEDIA_APP_DIR, instance.log_entry.proposal.id, filename
    )


def update_filming_park_doc_filename(instance, filename):
    return "{}/proposals/{}/filming_park_documents/{}".format(
        settings.MEDIA_APP_DIR, instance.filming_park.proposal.id, filename
    )


def update_events_park_doc_filename(instance, filename):
    return "{}/proposals/{}/events_park_documents/{}".format(
        settings.MEDIA_APP_DIR, instance.events_park.proposal.id, filename
    )


def update_pre_event_park_doc_filename(instance, filename):
    return "{}/proposals/{}/pre_event_park_documents/{}".format(
        settings.MEDIA_APP_DIR, instance.pre_event_park.proposal.id, filename
    )


def update_additional_doc_filename(instance, filename):
    return "{}/proposals/{}/additional_documents/{}/{}".format(
        settings.MEDIA_APP_DIR,
        instance.proposal.id,
        instance.proposal_additional_document_type.additional_document_type.name,
        filename,
    )


class AdditionalDocumentType(RevisionedMixin):
    name = models.CharField(max_length=255, null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        app_label = "licensing_template"


class DefaultDocument(Document):
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    class Meta:
        app_label = "licensing_template"
        abstract = True

    def delete(self):
        if self.can_delete:
            return super(DefaultDocument, self).delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted (including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )


class ShapefileDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="shapefile_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=500)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            return super(ShapefileDocument, self).delete()
        logger.info(
            "Cannot delete existing document object after Proposal has been submitted (including document submitted before Proposal pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "licensing_template"


class DeedPollDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="deed_poll_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Deed Poll Document"


class LegislativeRequirementsDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="legislative_requirements_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class RiskFactorsDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="risk_factors_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class KeyMilestonesDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="key_milestones_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class KeyPersonnelDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="key_personnel_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class StaffingDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="staffing_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class MarketAnalysisDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="market_analysis_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class AvailableActivitiesDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="available_activities_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class FinancialCapacityDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="financial_capacity_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class CapitalInvestmentDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="capital_investment_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class CashFlowDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="cash_flow_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ProfitAndLossDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="profit_and_loss_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class MiningTenementDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="mining_tenement_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class NativeTitleConsultationDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="native_title_consultation_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class AboriginalSiteDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="aboriginal_site_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class SignificantChangeDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="significant_change_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class BuildingRequiredDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="building_required_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class WetlandsImpactDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="wetlands_impact_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class EnvironmentallySensitiveDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="environmentally_sensitive_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class HeritageSiteDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="heritage_site_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class GroundDisturbingWorksDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="ground_disturbing_works_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ClearingVegetationDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="clearing_vegetation_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ConsistentPlanDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="consistent_plan_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ConsistentPurposeDocument(Document):
    proposal = models.ForeignKey(
        "Proposal",
        related_name="consistent_purpose_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class LongTermUseDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="long_term_use_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ExclusiveUseDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="exclusive_use_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class ProposalDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="supporting_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Document"


class OnHoldDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="onhold_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_onhold_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    def delete(self):
        if self.can_delete:
            return super(ProposalDocument, self).delete()


# Documents on Activities(land)and Activities(Marine) tab for T-Class related to required document questions
class ProposalRequiredDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="required_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(
        upload_to=update_proposal_required_doc_filename, max_length=512
    )
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    required_doc = models.ForeignKey(
        "RequiredDocument", related_name="proposals", on_delete=models.CASCADE
    )
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            return super(ProposalRequiredDocument, self).delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted (including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "licensing_template"


class QAOfficerDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="qaofficer_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_qaofficer_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    def delete(self):
        if self.can_delete:
            return super(QAOfficerDocument, self).delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted (including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "licensing_template"


class ReferralDocument(Document):
    referral = models.ForeignKey(
        "Referral", related_name="referral_documents", on_delete=models.CASCADE
    )
    _file = models.FileField(upload_to=update_referral_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            return super(ProposalDocument, self).delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted (including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "licensing_template"


class RequirementDocument(Document):
    requirement = models.ForeignKey(
        "ProposalRequirement",
        related_name="requirement_documents",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(upload_to=update_requirement_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    def delete(self):
        if self.can_delete:
            return super(RequirementDocument, self).delete()


class ProposalApplicantDetails(models.Model):
    first_name = models.CharField(max_length=24, blank=True, default="")

    class Meta:
        app_label = "licensing_template"


class ProposalType(models.Model):
    # class ProposalType(RevisionedMixin):
    code = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        # return 'id: {} code: {}'.format(self.id, self.code)
        return self.description

    class Meta:
        app_label = "licensing_template"


class Proposal(DirtyFieldsMixin, models.Model):
    APPLICANT_TYPE_ORGANISATION = "ORG"
    APPLICANT_TYPE_INDIVIDUAL = "IND"
    APPLICANT_TYPE_PROXY = "PRX"
    APPLICANT_TYPE_SUBMITTER = "SUB"

    PROCESSING_STATUS_DRAFT = "draft"
    PROCESSING_STATUS_AMENDMENT_REQUIRED = "amendment_required"
    PROCESSING_STATUS_WITH_ASSESSOR = "with_assessor"
    PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS = "with_assessor_conditions"
    PROCESSING_STATUS_WITH_APPROVER = "with_approver"
    PROCESSING_STATUS_WITH_REFERRAL = "with_referral"
    PROCESSING_STATUS_WITH_REFERRAL_CONDITIONS = "with_referral_conditions"
    PROCESSING_STATUS_APPROVED_APPLICATION = "approved_application"
    PROCESSING_STATUS_APPROVED_COMPETITIVE_PROCESS = "approved_competitive_process"
    PROCESSING_STATUS_APPROVED_EDITING_INVOICING = "approved_editing_invoicing"
    PROCESSING_STATUS_APPROVED = "approved"
    PROCESSING_STATUS_DECLINED = "declined"
    PROCESSING_STATUS_DISCARDED = "discarded"
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, "Draft"),
        (PROCESSING_STATUS_WITH_ASSESSOR, "With Assessor"),
        (PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS, "With Assessor (Conditions)"),
        (PROCESSING_STATUS_WITH_APPROVER, "With Approver"),
        (PROCESSING_STATUS_WITH_REFERRAL, "With Referral"),
        (PROCESSING_STATUS_WITH_REFERRAL_CONDITIONS, "With Referral (Conditions)"),
        (PROCESSING_STATUS_APPROVED_APPLICATION, "Approved (Application)"),
        (
            PROCESSING_STATUS_APPROVED_COMPETITIVE_PROCESS,
            "Approved (Competitive Process)",
        ),
        (PROCESSING_STATUS_APPROVED_EDITING_INVOICING, "Approved (Editing Invoicing)"),
        (PROCESSING_STATUS_APPROVED, "Approved"),
        (PROCESSING_STATUS_DECLINED, "Declined"),
        (PROCESSING_STATUS_DISCARDED, "Discarded"),
    )

    # List of statuses from above that allow a customer to edit an application.
    CUSTOMER_EDITABLE_STATE = [
        PROCESSING_STATUS_DRAFT,
        PROCESSING_STATUS_AMENDMENT_REQUIRED,
    ]

    # List of statuses from above that allow a customer to view an application (read-only)
    CUSTOMER_VIEWABLE_STATE = [
        PROCESSING_STATUS_WITH_ASSESSOR,
        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        PROCESSING_STATUS_WITH_REFERRAL,
        PROCESSING_STATUS_WITH_REFERRAL_CONDITIONS,
        PROCESSING_STATUS_WITH_APPROVER,
        PROCESSING_STATUS_APPROVED_APPLICATION,
        PROCESSING_STATUS_APPROVED_COMPETITIVE_PROCESS,
        PROCESSING_STATUS_APPROVED_EDITING_INVOICING,
        PROCESSING_STATUS_APPROVED,
        PROCESSING_STATUS_DECLINED,
    ]

    OFFICER_PROCESSABLE_STATE = [
        PROCESSING_STATUS_WITH_ASSESSOR,
        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        PROCESSING_STATUS_WITH_REFERRAL,  # <-- Be aware
        PROCESSING_STATUS_WITH_REFERRAL_CONDITIONS,  # <-- Be aware
        PROCESSING_STATUS_WITH_APPROVER,
    ]

    ID_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("awaiting_update", "Awaiting Update"),
        ("updated", "Updated"),
        ("accepted", "Accepted"),
    )

    COMPLIANCE_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("awaiting_returns", "Awaiting Returns"),
        ("completed", "Completed"),
        ("accepted", "Accepted"),
    )

    CHARACTER_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("accepted", "Accepted"),
    )

    REVIEW_STATUS_CHOICES = (
        ("not_reviewed", "Not Reviewed"),
        ("awaiting_amendments", "Awaiting Amendments"),
        ("amended", "Amended"),
        ("accepted", "Accepted"),
    )

    proposal_type = models.ForeignKey(
        ProposalType, blank=True, null=True, on_delete=models.SET_NULL
    )
    proposed_issuance_approval = JSONField(blank=True, null=True)
    ind_applicant = models.IntegerField(null=True, blank=True)  # EmailUserRO
    org_applicant = models.ForeignKey(
        Organisation,
        blank=True,
        null=True,
        related_name="org_applications",
        on_delete=models.SET_NULL,
    )
    proxy_applicant = models.IntegerField(null=True, blank=True)  # EmailUserRO
    lodgement_number = models.CharField(max_length=9, blank=True, default="")
    lodgement_sequence = models.IntegerField(blank=True, default=0)
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True)  # EmailUserRO
    assigned_officer = models.IntegerField(null=True)  # EmailUserRO
    assigned_approver = models.IntegerField(null=True)  # EmailUserRO
    approved_by = models.IntegerField(null=True)  # EmailUserRO
    processing_status = models.CharField(
        "Processing Status",
        max_length=30,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
    id_check_status = models.CharField(
        "Identification Check Status",
        max_length=30,
        choices=ID_CHECK_STATUS_CHOICES,
        default=ID_CHECK_STATUS_CHOICES[0][0],
    )
    compliance_check_status = models.CharField(
        "Return Check Status",
        max_length=30,
        choices=COMPLIANCE_CHECK_STATUS_CHOICES,
        default=COMPLIANCE_CHECK_STATUS_CHOICES[0][0],
    )
    character_check_status = models.CharField(
        "Character Check Status",
        max_length=30,
        choices=CHARACTER_CHECK_STATUS_CHOICES,
        default=CHARACTER_CHECK_STATUS_CHOICES[0][0],
    )
    review_status = models.CharField(
        "Review Status",
        max_length=30,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_CHOICES[0][0],
    )

    approval = models.ForeignKey(
        "licensing_template.Approval", null=True, blank=True, on_delete=models.SET_NULL
    )
    previous_application = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    proposed_decline_status = models.BooleanField(default=False)
    # Special Fields
    title = models.CharField(max_length=255, null=True, blank=True)
    application_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT)
    approval_level = models.CharField(
        "Activity matrix approval level", max_length=255, null=True, blank=True
    )
    approval_level_document = models.ForeignKey(
        ProposalDocument,
        blank=True,
        null=True,
        related_name="approval_level_document",
        on_delete=models.SET_NULL,
    )
    approval_comment = models.TextField(blank=True)
    details_text = models.TextField(blank=True)
    # If the proposal is created as part of migration of approvals
    migrated = models.BooleanField(default=False)
    # Registration of Interest generates a Lease Licence
    generated_proposal = models.ForeignKey(
        "self",
        related_name="originating_proposal",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    ## Registration of Interest additional form fields
    # proposal details
    exclusive_use = models.BooleanField(null=True)
    exclusive_use_text = models.TextField(blank=True)
    long_term_use = models.BooleanField(null=True)
    long_term_use_text = models.TextField(blank=True)
    consistent_purpose = models.BooleanField(null=True)
    consistent_purpose_text = models.TextField(blank=True)
    consistent_plan = models.BooleanField(null=True)
    consistent_plan_text = models.TextField(blank=True)
    # proposal impact
    clearing_vegetation = models.BooleanField(null=True)
    clearing_vegetation_text = models.TextField(blank=True)
    ground_disturbing_works = models.BooleanField(null=True)
    ground_disturbing_works_text = models.TextField(blank=True)
    heritage_site = models.BooleanField(null=True)
    heritage_site_text = models.TextField(blank=True)
    environmentally_sensitive = models.BooleanField(null=True)
    environmentally_sensitive_text = models.TextField(blank=True)
    wetlands_impact = models.BooleanField(null=True)
    wetlands_impact_text = models.TextField(blank=True)
    building_required = models.BooleanField(null=True)
    building_required_text = models.TextField(blank=True)
    significant_change = models.BooleanField(null=True)
    significant_change_text = models.TextField(blank=True)
    aboriginal_site = models.BooleanField(null=True)
    aboriginal_site_text = models.TextField(blank=True)
    native_title_consultation = models.BooleanField(null=True)
    native_title_consultation_text = models.TextField(blank=True)
    mining_tenement = models.BooleanField(null=True)
    mining_tenement_text = models.TextField(blank=True)
    ## Lease Licence additional form fields
    # proposal details
    profit_and_loss_text = models.TextField(blank=True)
    cash_flow_text = models.TextField(blank=True)
    capital_investment_text = models.TextField(blank=True)
    financial_capacity_text = models.TextField(blank=True)
    available_activities_text = models.TextField(blank=True)
    market_analysis_text = models.TextField(blank=True)
    staffing_text = models.TextField(blank=True)
    # proposal impact
    key_personnel_text = models.TextField(blank=True)
    key_milestones_text = models.TextField(blank=True)
    risk_factors_text = models.TextField(blank=True)
    legislative_requirements_text = models.TextField(blank=True)
    shapefile_json = JSONField(blank=True, null=True)

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return str(self.id)

    # Append 'P' to Proposal id to generate Lodgement number. Lodgement number and lodgement sequence are used to generate Reference.
    def save(self, *args, **kwargs):
        super(Proposal, self).save(*args, **kwargs)

        if self.lodgement_number == "":
            new_lodgment_id = "A{0:06d}".format(self.pk)
            self.lodgement_number = new_lodgment_id
            self.save()

    @property
    def can_create_final_approval(self):
        return (
            self.fee_paid
            and self.processing_status == Proposal.PROCESSING_STATUS_AWAITING_PAYMENT
        )

    @property
    def reference(self):
        return "{}-{}".format(self.lodgement_number, self.lodgement_sequence)

    @property
    def reversion_ids(self):
        current_revision_id = Version.objects.get_for_object(self).first().revision_id
        versions = (
            Version.objects.get_for_object(self)
            .select_related("revision__user")
            .filter(
                Q(revision__comment__icontains="status")
                | Q(revision_id=current_revision_id)
            )
        )
        version_ids = [[i.id, i.revision.date_created] for i in versions]
        return [
            dict(
                cur_version_id=version_ids[0][0],
                prev_version_id=version_ids[i + 1][0],
                created=version_ids[i][1],
            )
            for i in range(len(version_ids) - 1)
        ]

    @property
    def applicant(self):
        if self.org_applicant:
            return self.org_applicant.organisation
        elif self.ind_applicant:
            email_user = retrieve_email_user(self.ind_applicant)
        elif self.proxy_applicant:
            email_user = retrieve_email_user(self.proxy_applicant)
        else:
            logger.warning(
                "Applicant for the proposal {} not found".format(self.lodgement_number)
            )
            email_user = retrieve_email_user(self.submitter)

        return email_user

    @property
    def applicant_email(self):
        if (
            self.org_applicant
            and hasattr(self.org_applicant.organisation, "email")
            and self.org_applicant.organisation.email
        ):
            return self.org_applicant.organisation.email
        elif self.ind_applicant:
            email_user = retrieve_email_user(self.ind_applicant)
        elif self.proxy_applicant:
            email_user = retrieve_email_user(self.proxy_applicant)
        else:
            email_user = retrieve_email_user(self.submitter)

        return email_user.email

    @property
    def applicant_name(self):
        if isinstance(self.applicant, Organisation):
            return "{}".format(self.org_applicant.organisation.name)
        else:
            names = " ".join(
                [
                    self.applicant.first_name,
                    self.applicant.last_name,
                ]
            )
            return names if names else ""

    @property
    def applicant_details(self):
        if isinstance(self.applicant, Organisation):
            return "{} \n{}".format(
                self.org_applicant.organisation.name, self.org_applicant.address
            )
        else:
            # return "{} {}\n{}".format(
            return "{} {}".format(
                self.applicant.first_name,
                self.applicant.last_name,
                # self.applicant.addresses.all().first()
            )

    @property
    def applicant_address(self):
        if isinstance(self.applicant, Organisation):
            return self.org_applicant.address
        else:
            return self.applicant.residential_address

    @property
    def applicant_id(self):
        return self.applicant.id

    @property
    def applicant_type(self):
        if self.org_applicant:
            return self.APPLICANT_TYPE_ORGANISATION
        elif self.ind_applicant:
            return self.APPLICANT_TYPE_INDIVIDUAL
        elif self.proxy_applicant:
            return self.APPLICANT_TYPE_PROXY
        else:
            return self.APPLICANT_TYPE_SUBMITTER

    @property
    def applicant_field(self):
        if self.org_applicant:
            return "org_applicant"
        elif self.ind_applicant:
            return "ind_applicant"
        elif self.proxy_applicant:
            return "proxy_applicant"
        else:
            return "submitter"

    def qa_officers(self, name=None):
        if not name:
            return (
                QAOfficerGroup.objects.get(default=True)
                .members.all()
                .values_list("email", flat=True)
            )
        else:
            return (
                QAOfficerGroup.objects.get(name=name)
                .members.all()
                .values_list("email", flat=True)
            )

    @property
    def get_history(self):
        """Return the prev proposal versions"""
        l = []
        p = copy.deepcopy(self)
        while p.previous_application:
            l.append(
                dict(
                    id=p.previous_application.id,
                    modified=p.previous_application.modified_date,
                )
            )
            p = p.previous_application
        return l

    #    def _get_history(self):
    #        """ Return the prev proposal versions """
    #        l = []
    #        p = copy.deepcopy(self)
    #        while (p.previous_application):
    #            l.append( [p.id, p.previous_application.id] )
    #            p = p.previous_application
    #        return l

    @property
    def is_assigned(self):
        return self.assigned_officer is not None

    @property
    def is_temporary(self):
        # return self.customer_status == 'temp' and self.processing_status == 'temp'
        return self.processing_status == "temp"

    @property
    def can_user_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.processing_status in self.CUSTOMER_EDITABLE_STATE

    @property
    def can_user_view(self):
        """
        :return: True if the application is in one of the approved status.
        """
        return self.processing_status in self.CUSTOMER_VIEWABLE_STATE

    @property
    def is_discardable(self):
        """
        An application can be discarded by a customer if:
        1 - It is a draft
        2- or if the application has been pushed back to the user
        """
        # return self.customer_status == 'draft' or self.processing_status == 'awaiting_applicant_response'
        return (
            self.processing_status == "draft"
            or self.processing_status == "awaiting_applicant_response"
        )

    @property
    def is_deletable(self):
        """
        An application can be deleted only if it is a draft and it hasn't been lodged yet
        :return:
        """
        # return self.customer_status == 'draft' and not self.lodgement_number
        return self.processing_status == "draft" and not self.lodgement_number

    @property
    def latest_referrals(self):
        referrals = self.referrals
        for referral in referrals.all():
            print(referral)
        return referrals.all()[:3]

    @property
    def assessor_assessment(self):
        qs = self.assessment.filter(referral=None)
        return qs[0] if qs else None

    @property
    def referral_assessments(self):
        qs = self.assessment.exclude(referral=None)
        return qs if qs else None

    @property
    def permit(self):
        return self.approval.licence_document._file.url if self.approval else None

    @property
    def allowed_assessors(self):
        group = None
        # TODO: Take application_type into account
        if self.processing_status in [
            Proposal.PROCESSING_STATUS_WITH_APPROVER,
        ]:
            group = self.get_approver_group()
        elif self.processing_status in [
            Proposal.PROCESSING_STATUS_WITH_REFERRAL,
            Proposal.PROCESSING_STATUS_WITH_REFERRAL_CONDITIONS,
            Proposal.PROCESSING_STATUS_WITH_ASSESSOR,
            Proposal.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        ]:
            group = self.get_assessor_group()
        users = (
            list(
                map(
                    lambda id: retrieve_email_user(id),
                    group.get_system_group_member_ids(),
                )
            )
            if group
            else []
        )
        return users

    @property
    def compliance_assessors(self):
        group = self.get_assessor_group()
        return group.members if group else []

    @property
    def can_officer_process(self):
        """:return: True if the application is in one of the processable status for Assessor role."""
        return (
            True
            if self.processing_status in Proposal.OFFICER_PROCESSABLE_STATE
            else True
        )

    @property
    def amendment_requests(self):
        qs = AmendmentRequest.objects.filter(proposal=self)
        return qs

    # Check if there is an pending amendment request exist for the proposal
    @property
    def pending_amendment_request(self):
        qs = AmendmentRequest.objects.filter(proposal=self, status="requested")
        if qs:
            return True
        return False

    @property
    def is_amendment_proposal(self):
        if self.proposal_type == "amendment":
            return True
        return False

    def get_assessor_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_ASSESSOR)

    def get_approver_group(self):
        # TODO: Take application_type into account
        return SystemGroup.objects.get(name=GROUP_NAME_APPROVER)

    def __check_proposal_filled_out(self):
        if not self.data:
            raise exceptions.ProposalNotComplete()
        missing_fields = []
        required_fields = {}
        for k, v in required_fields.items():
            val = getattr(self, k)
            if not val:
                missing_fields.append(v)
        return missing_fields

    @property
    def assessor_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_assessor_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    @property
    def approver_recipients(self):
        logger.info("assessor_recipients")
        recipients = []
        group_ids = self.get_approver_group().get_system_group_member_ids()
        for id in group_ids:
            logger.info(id)
            recipients.append(EmailUser.objects.get(id=id).email)
        return recipients

    # Check if the user is member of assessor group for the Proposal
    def is_assessor(self, user):
        return user.id in self.get_assessor_group().get_system_group_member_ids()

    # Check if the user is member of assessor group for the Proposal
    def is_approver(self, user):
        return user.id in self.get_assessor_group().get_system_group_member_ids()

    def can_assess(self, user):
        logger.info("can assess")
        logger.info("user")
        logger.info(type(user))
        logger.info(user)
        logger.info(user.id)
        if self.processing_status in [
            "on_hold",
            "with_qa_officer",
            "with_assessor",
            "with_referral",
            "with_assessor_conditions",
        ]:
            logger.info("self.__assessor_group().get_system_group_member_ids()")
            logger.info(self.get_assessor_group().get_system_group_member_ids())
            return user.id in self.get_assessor_group().get_system_group_member_ids()
        elif self.processing_status == Proposal.PROCESSING_STATUS_WITH_APPROVER:
            return user.id in self.get_approver_group().get_system_group_member_ids()
        else:
            return False

    def can_edit_period(self, user):
        if (
            self.processing_status == "with_assessor"
            or self.processing_status == "with_assessor_conditions"
        ):
            # return self.__assessor_group() in user.proposalassessorgroup_set.all()
            return user.id in self.get_assessor_group().get_system_group_member_ids()
        else:
            return False

    def assessor_comments_view(self, user):

        if (
            self.processing_status == "with_assessor"
            or self.processing_status == "with_referral"
            or self.processing_status == "with_assessor_conditions"
            or self.processing_status == "with_approver"
        ):
            try:
                referral = Referral.objects.get(proposal=self, referral=user)
            except:
                referral = None
            if referral:
                return True
            # elif self.__assessor_group() in user.proposalassessorgroup_set.all():
            elif user.id in self.get_assessor_group().get_system_group_member_ids():
                return True
            # elif self.__approver_group() in user.proposalapprovergroup_set.all():
            elif user.id in self.get_approver_group().get_system_group_member_ids():
                return True
            else:
                return False
        else:
            return False

    def has_assessor_mode(self, user):
        status_without_assessor = [
            "with_approver",
            "approved",
            "waiting_payment",
            "declined",
            "draft",
        ]
        if self.processing_status in status_without_assessor:
            return False
        else:
            if self.assigned_officer:
                if self.assigned_officer == user.id:
                    # return self.__assessor_group() in user.proposalassessorgroup_set.all()
                    return (
                        user.id
                        in self.get_assessor_group().get_system_group_member_ids()
                    )
                else:
                    return False
            else:
                # return self.__assessor_group() in user.proposalassessorgroup_set.all()
                return (
                    user.id in self.get_assessor_group().get_system_group_member_ids()
                )

    def log_user_action(self, action, request):
        return ProposalUserAction.log_action(self, action, request.user.id)

    # From DAS
    def validate_map_files(self, request):
        import geopandas as gpd

        try:
            shp_file_qs = self.map_documents.filter(name__endswith=".shp")
            # TODO : validate shapefile and all the other related filese are present
            if shp_file_qs:
                shp_file_obj = shp_file_qs[0]
                shp = gpd.read_file(shp_file_obj.path)
                shp_transform = shp.to_crs(crs=4326)
                shp_json = shp_transform.to_json()
                import json

                if type(shp_json) == str:
                    self.shapefile_json = json.loads(shp_json)
                else:
                    self.shapefile_json = shp_json
                self.save(version_comment="New Shapefile JSON saved.")
                # else:
                #     raise ValidationError('Please upload a valid shapefile')
            else:
                raise ValidationError("Please upload a valid shapefile")
        except:
            raise ValidationError("Please upload a valid shapefile")

    def make_questions_ready(self, referral=None):
        """
        Create checklist answers
        Assessment instance already exits then skip.
        """
        proposal_assessment, created = ProposalAssessment.objects.get_or_create(
            proposal=self, referral=referral
        )
        if created:
            list_type = (
                SectionChecklist.LIST_TYPE_REFERRAL
                if referral
                else SectionChecklist.LIST_TYPE_ASSESSOR
            )
            section_checklists = SectionChecklist.objects.filter(
                application_type=self.application_type,
                list_type=list_type,
                enabled=True,
            )
            for section_checklist in section_checklists:
                for checklist_question in section_checklist.questions.filter(
                    enabled=True
                ):
                    answer = ProposalAssessmentAnswer.objects.create(
                        proposal_assessment=proposal_assessment,
                        checklist_question=checklist_question,
                    )

    def update(self, request, viewset):
        from licensing_template.components.proposals.utils import save_proponent_data

        with transaction.atomic():
            if self.can_user_edit:
                # Save the data first
                save_proponent_data(self, request, viewset)
                self.save()
            else:
                raise ValidationError("You can't edit this proposal at this moment")

    def send_referral(self, request, referral_email, referral_text):
        with transaction.atomic():
            try:
                referral_email = referral_email.lower()
                if (
                    self.processing_status == Proposal.PROCESSING_STATUS_WITH_ASSESSOR
                    or self.processing_status
                    == Proposal.PROCESSING_STATUS_WITH_REFERRAL
                ):
                    self.processing_status = Proposal.PROCESSING_STATUS_WITH_REFERRAL
                    self.save()

                    # Check if the user is in ledger
                    try:
                        user = EmailUser.objects.get(email__icontains=referral_email)
                    except EmailUser.DoesNotExist:
                        # Validate if it is a deparment user
                        department_user = get_department_user(referral_email)
                        if not department_user:
                            raise ValidationError(
                                "The user you want to send the referral to is not a member of the department"
                            )
                        # Check if the user is in ledger or create

                        user, created = EmailUser.objects.get_or_create(
                            email=department_user["email"].lower()
                        )
                        if created:
                            user.first_name = department_user["given_name"]
                            user.last_name = department_user["surname"]
                            user.save()

                    referral = None
                    try:
                        referral = Referral.objects.get(referral=user.id, proposal=self)
                        raise ValidationError(
                            "A referral has already been sent to this user"
                        )
                    except Referral.DoesNotExist:
                        # Create Referral
                        referral = Referral.objects.create(
                            proposal=self,
                            referral=user.id,
                            sent_by=request.user.id,
                            text=referral_text,
                            assigned_officer=request.user.id,
                        )
                        # Create answers for this referral
                        self.make_questions_ready(referral)

                    # Create a log entry for the proposal
                    self.log_user_action(
                        ProposalUserAction.ACTION_SEND_REFERRAL_TO.format(
                            referral.id,
                            self.lodgement_number,
                            "{}({})".format(user.get_full_name(), user.email),
                        ),
                        request,
                    )
                    # Create a log entry for the organisation
                    if self.applicant:
                        pass
                        # TODO: implement logging to ledger/application???
                        # self.applicant.log_user_action(
                        #    ProposalUserAction.ACTION_SEND_REFERRAL_TO.format(
                        #        referral.id, self.lodgement_number, '{}({})'.format(user.get_full_name(), user.email)
                        #    ), request
                        # )
                    # send email
                    send_referral_email_notification(
                        referral,
                        [
                            user.email,
                        ],
                        request,
                    )
                else:
                    raise exceptions.ProposalReferralCannotBeSent()
            except:
                raise

    def assign_officer(self, request, officer):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if not self.can_assess(officer):
                    raise ValidationError(
                        "The selected person is not authorised to be assigned to this proposal"
                    )
                if self.processing_status == "with_approver":
                    if officer.id != self.assigned_approver:
                        self.assigned_approver = officer.id
                        self.save()
                        # Create a log entry for the proposal
                        self.log_user_action(
                            ProposalUserAction.ACTION_ASSIGN_TO_APPROVER.format(
                                self.id,
                                "{}({})".format(officer.get_full_name(), officer.email),
                            ),
                            request,
                        )
                        # Create a log entry for the organisation
                        # applicant_field=getattr(self, self.applicant_field)
                        # applicant_field.log_user_action(ProposalUserAction.ACTION_ASSIGN_TO_APPROVER.format(self.id,'{}({})'.format(officer.get_full_name(), officer.email)), request)
                else:
                    if officer.id != self.assigned_officer:
                        self.assigned_officer = officer.id
                        self.save()
                        # Create a log entry for the proposal
                        self.log_user_action(
                            ProposalUserAction.ACTION_ASSIGN_TO_ASSESSOR.format(
                                self.id,
                                "{}({})".format(officer.get_full_name(), officer.email),
                            ),
                            request,
                        )
                        # Create a log entry for the organisation
                        # applicant_field=getattr(self, self.applicant_field)
                        # applicant_field.log_user_action(ProposalUserAction.ACTION_ASSIGN_TO_ASSESSOR.format(self.id,'{}({})'.format(officer.get_full_name(), officer.email)), request)
            except:
                raise

    def assing_approval_level_document(self, request):
        with transaction.atomic():
            try:
                approval_level_document = request.data["approval_level_document"]
                if approval_level_document != "null":
                    try:
                        document = self.documents.get(
                            input_name=str(approval_level_document)
                        )
                    except ProposalDocument.DoesNotExist:
                        document = self.documents.get_or_create(
                            input_name=str(approval_level_document),
                            name=str(approval_level_document),
                        )[0]
                    document.name = str(approval_level_document)
                    # commenting out below tow lines - we want to retain all past attachments - reversion can use them
                    # if document._file and os.path.isfile(document._file.path):
                    #    os.remove(document._file.path)
                    document._file = approval_level_document
                    document.save()
                    d = ProposalDocument.objects.get(id=document.id)
                    self.approval_level_document = d
                    comment = "Approval Level Document Added: {}".format(document.name)
                else:
                    self.approval_level_document = None
                    comment = "Approval Level Document Deleted: {}".format(
                        request.data["approval_level_document_name"]
                    )
                # self.save()
                self.save(
                    version_comment=comment
                )  # to allow revision to be added to reversion history
                self.log_user_action(
                    ProposalUserAction.ACTION_APPROVAL_LEVEL_DOCUMENT.format(self.id),
                    request,
                )
                # Create a log entry for the organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_APPROVAL_LEVEL_DOCUMENT.format(self.id),
                    request,
                )
                return self
            except:
                raise

    def unassign(self, request):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.processing_status == "with_approver":
                    if self.assigned_approver:
                        self.assigned_approver = None
                        self.save()
                        # Create a log entry for the proposal
                        self.log_user_action(
                            ProposalUserAction.ACTION_UNASSIGN_APPROVER.format(self.id),
                            request,
                        )
                        # Create a log entry for the organisation
                        # applicant_field=getattr(self, self.applicant_field)
                        # applicant_field.log_user_action(ProposalUserAction.ACTION_UNASSIGN_APPROVER.format(self.id),request)
                else:
                    if self.assigned_officer:
                        self.assigned_officer = None
                        self.save()
                        # Create a log entry for the proposal
                        self.log_user_action(
                            ProposalUserAction.ACTION_UNASSIGN_ASSESSOR.format(self.id),
                            request,
                        )
                        # Create a log entry for the organisation
                        # applicant_field=getattr(self, self.applicant_field)
                        # applicant_field.log_user_action(ProposalUserAction.ACTION_UNASSIGN_ASSESSOR.format(self.id),request)
            except:
                raise

    def add_default_requirements(self):
        # Add default standard requirements to Proposal
        due_date = None
        default_requirements = ProposalStandardRequirement.objects.filter(
            application_type=self.application_type, default=True, obsolete=False
        )
        if default_requirements:
            for req in default_requirements:
                r, created = ProposalRequirement.objects.get_or_create(
                    proposal=self, standard_requirement=req, due_date=due_date
                )

    def move_to_status(self, request, status, approver_comment):
        if not self.can_assess(request.user):
            raise exceptions.ProposalNotAuthorized()
        if status in ["with_assessor", "with_assessor_conditions", "with_approver"]:
            if self.processing_status == "with_referral" or self.can_user_edit:
                raise ValidationError(
                    "You cannot change the current status at this time"
                )
            if self.processing_status != status:
                if self.processing_status == "with_approver":
                    self.approver_comment = ""
                    if approver_comment:
                        self.approver_comment = approver_comment
                        self.save()
                        send_proposal_approver_sendback_email_notification(
                            request, self
                        )
                self.processing_status = status
                self.save()
                if status == "with_assessor_conditions":
                    self.add_default_requirements()

                # Create a log entry for the proposal
                if self.processing_status == self.PROCESSING_STATUS_WITH_ASSESSOR:
                    self.log_user_action(
                        ProposalUserAction.ACTION_BACK_TO_PROCESSING.format(self.id),
                        request,
                    )
                elif (
                    self.processing_status
                    == self.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS
                ):
                    self.log_user_action(
                        ProposalUserAction.ACTION_ENTER_REQUIREMENTS.format(self.id),
                        request,
                    )
        else:
            raise ValidationError("The provided status cannot be found.")

    def reissue_approval(self, request, status):
        if not self.processing_status == "approved":
            raise ValidationError("You cannot change the current status at this time")
        elif self.approval and self.approval.can_reissue:
            if (
                self.get_approver_group()
                in request.user.proposalapprovergroup_set.all()
            ):
                self.processing_status = status
                # self.save()
                self.save(
                    version_comment="Reissue Approval: {}".format(
                        self.approval.lodgement_number
                    )
                )
                # Create a log entry for the proposal
                self.log_user_action(
                    ProposalUserAction.ACTION_REISSUE_APPROVAL.format(self.id), request
                )
            else:
                raise ValidationError("Cannot reissue Approval. User not permitted.")
        else:
            raise ValidationError("Cannot reissue Approval")

    def proposed_decline(self, request, details):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.processing_status != "with_assessor":
                    raise ValidationError(
                        "You cannot propose to decline if it is not with assessor"
                    )

                reason = details.get("reason")
                ProposalDeclinedDetails.objects.update_or_create(
                    proposal=self,
                    defaults={
                        "officer": request.user.id,
                        "reason": reason,
                        "cc_email": details.get("cc_email", None),
                    },
                )
                self.proposed_decline_status = True
                approver_comment = ""
                self.move_to_status(request, "with_approver", approver_comment)
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_PROPOSED_DECLINE.format(self.id), request
                )
                # Log entry for organisation
                # TODO: ledger must create EmailUser logs
                # applicant_field=getattr(self, self.applicant_field)
                # applicant_field.log_user_action(ProposalUserAction.ACTION_PROPOSED_DECLINE.format(self.id),request)

                send_approver_decline_email_notification(reason, request, self)
            except:
                raise

    def final_decline(self, request, details):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.processing_status != "with_approver":
                    raise ValidationError(
                        "You cannot decline if it is not with approver"
                    )

                (
                    proposal_decline,
                    success,
                ) = ProposalDeclinedDetails.objects.update_or_create(
                    proposal=self,
                    defaults={
                        "officer": request.user.id,
                        "reason": details.get("reason"),
                        "cc_email": details.get("cc_email", None),
                    },
                )
                self.proposed_decline_status = True
                self.processing_status = "declined"
                # self.customer_status = 'declined'
                self.save()
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_DECLINE.format(self.id), request
                )
                # Log entry for organisation
                # TODO: ledger must create EmailUser logs
                # applicant_field=getattr(self, self.applicant_field)
                # applicant_field.log_user_action(ProposalUserAction.ACTION_DECLINE.format(self.id),request)
                send_proposal_decline_email_notification(
                    self, request, proposal_decline
                )
            except:
                raise

    def on_hold(self, request):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if not (
                    self.processing_status == "with_assessor"
                    or self.processing_status == "with_referral"
                ):
                    raise ValidationError(
                        "You cannot put on hold if it is not with assessor or with referral"
                    )

                self.prev_processing_status = self.processing_status
                self.processing_status = self.PROCESSING_STATUS_ONHOLD
                self.save()
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_PUT_ONHOLD.format(self.id), request
                )
                # Log entry for organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_PUT_ONHOLD.format(self.id), request
                )

                # send_approver_decline_email_notification(reason, request, self)
            except:
                raise

    def on_hold_remove(self, request):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.processing_status != "on_hold":
                    raise ValidationError(
                        "You cannot remove on hold if it is not currently on hold"
                    )

                self.processing_status = self.prev_processing_status
                self.prev_processing_status = self.PROCESSING_STATUS_ONHOLD
                self.save()
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_REMOVE_ONHOLD.format(self.id), request
                )
                # Log entry for organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_REMOVE_ONHOLD.format(self.id), request
                )

                # send_approver_decline_email_notification(reason, request, self)
            except:
                raise

    def with_qaofficer(self, request):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if not (
                    self.processing_status == "with_assessor"
                    or self.processing_status == "with_referral"
                ):
                    raise ValidationError(
                        "You cannot send to QA Officer if it is not with assessor or with referral"
                    )

                self.prev_processing_status = self.processing_status
                self.processing_status = self.PROCESSING_STATUS_WITH_QA_OFFICER
                self.qaofficer_referral = True
                if self.qaofficer_referrals.exists():
                    qaofficer_referral = self.qaofficer_referrals.first()
                    qaofficer_referral.sent_by = request.user
                    qaofficer_referral.processing_status = "with_qaofficer"
                else:
                    qaofficer_referral = self.qaofficer_referrals.create(
                        sent_by=request.user
                    )

                qaofficer_referral.save()
                self.save()

                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_WITH_QA_OFFICER.format(self.id), request
                )
                # Log entry for organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_WITH_QA_OFFICER.format(self.id), request
                )

                # send_approver_decline_email_notification(reason, request, self)
                recipients = self.qa_officers()
                send_qaofficer_email_notification(self, recipients, request)

            except:
                raise

    def with_qaofficer_completed(self, request):
        with transaction.atomic():
            try:
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.processing_status != "with_qa_officer":
                    raise ValidationError(
                        "You cannot Complete QA Officer Assessment if processing status not currently With Assessor"
                    )

                self.processing_status = self.prev_processing_status
                self.prev_processing_status = self.PROCESSING_STATUS_WITH_QA_OFFICER

                qaofficer_referral = self.qaofficer_referrals.first()
                qaofficer_referral.qaofficer = request.user
                qaofficer_referral.qaofficer_group = QAOfficerGroup.objects.get(
                    default=True
                )
                qaofficer_referral.qaofficer_text = request.data["text"]
                qaofficer_referral.processing_status = "completed"

                qaofficer_referral.save()
                self.assigned_officer = None
                self.save()

                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_QA_OFFICER_COMPLETED.format(self.id),
                    request,
                )
                # Log entry for organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_QA_OFFICER_COMPLETED.format(self.id),
                    request,
                )

                # send_approver_decline_email_notification(reason, request, self)
                recipients = self.qa_officers()
                send_qaofficer_complete_email_notification(self, recipients, request)
            except:
                raise

    def proposed_approval(self, request, details):
        with transaction.atomic():
            try:
                print(details)
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if not (
                    (
                        self.application_type.name
                        == APPLICATION_TYPE_REGISTRATION_OF_INTEREST
                        and self.processing_status
                        == Proposal.PROCESSING_STATUS_WITH_ASSESSOR
                    )
                    or (
                        self.application_type.name == APPLICATION_TYPE_LEASE_LICENCE
                        and self.processing_status
                        == Proposal.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS
                    )
                ):
                    raise ValidationError("You cannot propose for approval")
                self.proposed_issuance_approval = {
                    "details": details.get("details"),
                    "cc_email": details.get("cc_email"),
                    "decision": details.get("decision"),
                }
                self.proposed_decline_status = False
                approver_comment = ""
                self.move_to_status(
                    request, Proposal.PROCESSING_STATUS_WITH_APPROVER, approver_comment
                )
                self.assigned_officer = None
                self.save()
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_PROPOSED_APPROVAL.format(self.id), request
                )
                # Log entry for organisation
                applicant_field = getattr(self, self.applicant_field)
                # applicant_field.log_user_action(ProposalUserAction.ACTION_PROPOSED_APPROVAL.format(self.id),request)

                send_approver_approve_email_notification(request, self)
            except Exception as e:
                logger.error(e)
                raise e

    def preview_approval(self, request, details):
        from licensing_template.components.approvals.models import PreviewTempApproval

        with transaction.atomic():
            try:
                # if self.processing_status != 'with_assessor_conditions' or self.processing_status != 'with_approver':
                if not (
                    self.processing_status == "with_assessor_conditions"
                    or self.processing_status == "with_approver"
                ):
                    raise ValidationError(
                        "Licence preview only available when processing status is with_approver. Current status {}".format(
                            self.processing_status
                        )
                    )
                if not self.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                # if not self.applicant.organisation.postal_address:
                if not self.applicant_address:
                    raise ValidationError(
                        "The applicant needs to have set their postal address before approving this proposal."
                    )

                lodgement_number = (
                    self.previous_application.approval.lodgement_number
                    if self.proposal_type in ["renewal", "amendment"]
                    else None
                )  # renewals/amendments keep same licence number
                preview_approval = PreviewTempApproval.objects.create(
                    current_proposal=self,
                    issue_date=timezone.now(),
                    expiry_date=datetime.datetime.strptime(
                        details.get("due_date"), "%d/%m/%Y"
                    ).date(),
                    start_date=datetime.datetime.strptime(
                        details.get("start_date"), "%d/%m/%Y"
                    ).date(),
                    submitter=self.submitter,
                    org_applicant=self.org_applicant,
                    proxy_applicant=self.proxy_applicant,
                    lodgement_number=lodgement_number,
                )

                # Generate the preview document - get the value of the BytesIO buffer
                licence_buffer = preview_approval.generate_doc(
                    request.user, preview=True
                )

                # clean temp preview licence object
                transaction.set_rollback(True)

                return licence_buffer
            except:
                raise

    def final_approval(self, request, details):
        from licensing_template.components.approvals.models import Approval
        from licensing_template.helpers import is_departmentUser

        with transaction.atomic():
            try:
                self.proposed_decline_status = False

                # if (self.processing_status==Proposal.PROCESSING_STATUS_AWAITING_PAYMENT and self.fee_paid) or (self.proposal_type=='amendment'):
                if self.proposal_type == "amendment":
                    #    # for 'Awaiting Payment' approval. External/Internal user fires this method after full payment via Make/Record Payment
                    pass
                else:
                    if not self.can_assess(request.user):
                        raise exceptions.ProposalNotAuthorized()
                    if self.processing_status != "with_approver":
                        raise ValidationError(
                            "You cannot issue the approval if it is not with an approver"
                        )
                    # if not self.applicant.organisation.postal_address:
                    # TODO: add this check after ledger forms are available
                    # if not self.applicant_address:
                    #   raise ValidationError('The applicant needs to have set their postal address before approving this proposal.')

                    self.proposed_issuance_approval = {
                        #'start_date' : details.get('start_date').strftime('%d/%m/%Y'),
                        #'expiry_date' : details.get('expiry_date').strftime('%d/%m/%Y'),
                        "decision": details.get("decision"),
                        "details": details.get("details"),
                        "cc_email": details.get("cc_email"),
                    }
                    # TODO: req for LL?
                    # if is_departmentUser(request):
                    # needed because external users come through this workflow following 'awaiting_payment; status
                    # self.approved_by = request.user

                self.processing_status = "approved"
                # self.customer_status = 'approved'
                # Log proposal action
                self.log_user_action(
                    ProposalUserAction.ACTION_ISSUE_APPROVAL_.format(self.id), request
                )
                # Log entry for organisation
                # applicant_field=getattr(self, self.applicant_field)
                # applicant_field.log_user_action(ProposalUserAction.ACTION_ISSUE_APPROVAL_.format(self.id),request)

                if self.processing_status == self.PROCESSING_STATUS_APPROVED:
                    # TODO if it is an ammendment proposal then check appropriately
                    checking_proposal = self
                    if (
                        self.proposal_type == "renewal"
                        and self.application_type.name == APPLICATION_TYPE_LEASE_LICENCE
                    ):
                        if self.previous_application:
                            previous_approval = self.previous_application.approval
                            approval, created = Approval.objects.update_or_create(
                                current_proposal=checking_proposal,
                                defaults={
                                    "issue_date": timezone.now(),
                                    #'expiry_date' : datetime.datetime.strptime(self.proposed_issuance_approval.get('expiry_date'), '%d/%m/%Y').date(),
                                    #'start_date' : datetime.datetime.strptime(self.proposed_issuance_approval.get('start_date'), '%d/%m/%Y').date(),
                                    "expiry_date": timezone.now().date()
                                    + relativedelta(years=1),
                                    "start_date": timezone.now().date(),
                                    "submitter": self.submitter,
                                    "org_applicant": self.org_applicant,
                                    "proxy_applicant": self.proxy_applicant,
                                    "lodgement_number": previous_approval.lodgement_number,
                                },
                            )
                            if created:
                                previous_approval.replaced_by = approval
                                previous_approval.save()

                            self.reset_licence_discount(request.user)

                    elif (
                        self.proposal_type == "amendment"
                        and self.application_type.name == APPLICATION_TYPE_LEASE_LICENCE
                    ):
                        if self.previous_application:
                            previous_approval = self.previous_application.approval
                            approval, created = Approval.objects.update_or_create(
                                current_proposal=checking_proposal,
                                defaults={
                                    "issue_date": timezone.now(),
                                    "expiry_date": timezone.now().date()
                                    + relativedelta(years=1),
                                    "start_date": timezone.now().date(),
                                    "submitter": self.submitter,
                                    "org_applicant": self.org_applicant,
                                    "proxy_applicant": self.proxy_applicant,
                                    "lodgement_number": previous_approval.lodgement_number,
                                },
                            )
                            if created:
                                previous_approval.replaced_by = approval
                                previous_approval.save()
                    else:
                        # can be rog, ll or cp
                        approval, created = Approval.objects.update_or_create(
                            current_proposal=checking_proposal,
                            defaults={
                                "issue_date": timezone.now(),
                                "expiry_date": timezone.now().date()
                                + relativedelta(years=1),
                                "start_date": timezone.now().date(),
                                "submitter": self.submitter,
                                "org_applicant": self.org_applicant,
                                "proxy_applicant": self.proxy_applicant,
                            },
                        )
                    if (
                        self.application_type.name
                        == APPLICATION_TYPE_REGISTRATION_OF_INTEREST
                    ):
                        if (
                            self.proposed_issuance_approval.get("decision")
                            == "approve_lease_licence"
                            and not self.generated_proposal
                        ):
                            lease_licence = (
                                self.create_lease_licence_from_registration_of_interest()
                            )
                            self.generated_proposal = lease_licence
                            self.save()
                        elif (
                            self.proposed_issuance_approval.get("decision")
                            == "approve_competitive_process"
                            and not self.generated_proposal
                        ):
                            # TODO: add logic
                            pass
                    elif (
                        self.application_type.name
                        == APPLICATION_TYPE_COMPETITIVE_PROCESS
                    ):
                        pass

                    # Generate compliances
                    from licensing_template.components.compliances.models import (
                        Compliance,
                        ComplianceUserAction,
                    )

                    if created:
                        if self.proposal_type == "amendment":
                            approval_compliances = Compliance.objects.filter(
                                approval=previous_approval,
                                proposal=self.previous_application,
                                processing_status="future",
                            )
                            if approval_compliances:
                                for c in approval_compliances:
                                    c.delete()
                        # Log creation
                        # Generate the document
                        # TODO: generate doc
                        # approval.generate_doc(request.user)
                        self.generate_compliances(approval, request)
                        # send the doc and log in approval and org
                    else:
                        # Generate the document
                        # TODO: generate doc
                        # approval.generate_doc(request.user)
                        # Delete the future compliances if Approval is reissued and generate the compliances again.
                        approval_compliances = Compliance.objects.filter(
                            approval=approval, proposal=self, processing_status="future"
                        )
                        if approval_compliances:
                            for c in approval_compliances:
                                c.delete()
                        self.generate_compliances(approval, request)
                        # Log proposal action
                        self.log_user_action(
                            ProposalUserAction.ACTION_UPDATE_APPROVAL_.format(self.id),
                            request,
                        )
                        # Log entry for organisation
                        applicant_field = getattr(self, self.applicant_field)
                        applicant_field.log_user_action(
                            ProposalUserAction.ACTION_UPDATE_APPROVAL_.format(self.id),
                            request,
                        )
                    self.approval = approval

                    # send Proposal approval email with attachment
                    # TODO: generate doc, then email
                    # send_proposal_approval_email_notification(self,request)
                    # TODO: add reversion
                    # self.save(version_comment='Final Approval: {}'.format(self.approval.lodgement_number))
                    self.save()
                    self.approval.documents.all().update(can_delete=False)

            except:
                raise

    def create_lease_licence_from_registration_of_interest(self):
        lease_licence = Proposal.objects.create(
            application_type=ApplicationType.objects.get(
                name=APPLICATION_TYPE_LEASE_LICENCE
            ),
            submitter=self.submitter,
            ind_applicant=self.ind_applicant,
            org_applicant=self.org_applicant,
            proposal_type_id=self.proposal_type.id,
        )
        # add geometry
        from copy import deepcopy

        for geo in self.proposalgeometry.all():
            new_geo = deepcopy(geo)
            new_geo.proposal = lease_licence
            new_geo.copied_from = geo
            new_geo.id = None
            new_geo.save()
        return lease_licence

    def generate_compliances(self, approval, request):
        today = timezone.now().date()
        timedelta = datetime.timedelta
        from licensing_template.components.compliances.models import (
            Compliance,
            ComplianceUserAction,
        )

        # For amendment type of Proposal, check for copied requirements from previous proposal
        if self.proposal_type == "amendment":
            try:
                for r in self.requirements.filter(copied_from__isnull=False):
                    cs = []
                    cs = Compliance.objects.filter(
                        requirement=r.copied_from,
                        proposal=self.previous_application,
                        processing_status="due",
                    )
                    if cs:
                        if r.is_deleted == True:
                            for c in cs:
                                c.processing_status = "discarded"
                                # c.customer_status = 'discarded'
                                c.reminder_sent = True
                                c.post_reminder_sent = True
                                c.save()
                        if r.is_deleted == False:
                            for c in cs:
                                c.proposal = self
                                c.approval = approval
                                c.requirement = r
                                c.save()
            except:
                raise
        # requirement_set= self.requirements.filter(copied_from__isnull=True).exclude(is_deleted=True)
        requirement_set = self.requirements.all().exclude(is_deleted=True)

        # for req in self.requirements.all():
        for req in requirement_set:
            try:
                if req.due_date and req.due_date >= today:
                    current_date = req.due_date
                    # create a first Compliance
                    try:
                        compliance = Compliance.objects.get(
                            requirement=req, due_date=current_date
                        )
                    except Compliance.DoesNotExist:
                        compliance = Compliance.objects.create(
                            proposal=self,
                            due_date=current_date,
                            processing_status="future",
                            approval=approval,
                            requirement=req,
                        )
                        compliance.log_user_action(
                            ComplianceUserAction.ACTION_CREATE.format(compliance.id),
                            request,
                        )
                    if req.recurrence:
                        while current_date < approval.expiry_date:
                            for x in range(req.recurrence_schedule):
                                # Weekly
                                if req.recurrence_pattern == 1:
                                    current_date += timedelta(weeks=1)
                                # Monthly
                                elif req.recurrence_pattern == 2:
                                    current_date += timedelta(weeks=4)
                                    pass
                                # Yearly
                                elif req.recurrence_pattern == 3:
                                    current_date += timedelta(days=365)
                            # Create the compliance
                            if current_date <= approval.expiry_date:
                                try:
                                    compliance = Compliance.objects.get(
                                        requirement=req, due_date=current_date
                                    )
                                except Compliance.DoesNotExist:
                                    compliance = Compliance.objects.create(
                                        proposal=self,
                                        due_date=current_date,
                                        processing_status="future",
                                        approval=approval,
                                        requirement=req,
                                    )
                                    compliance.log_user_action(
                                        ComplianceUserAction.ACTION_CREATE.format(
                                            compliance.id
                                        ),
                                        request,
                                    )
            except:
                raise

    def renew_approval(self, request):
        with transaction.atomic():
            previous_proposal = self
            try:
                renew_conditions = {
                    "previous_application": previous_proposal,
                    "customer_status": "with_assessor",
                }
                # proposal=Proposal.objects.get(previous_application = previous_proposal)
                proposal = Proposal.objects.get(**renew_conditions)
                # if proposal.customer_status=='with_assessor':
                if proposal:
                    raise ValidationError(
                        "A renewal/ amendment for this licence has already been lodged and is awaiting review."
                    )
            except Proposal.DoesNotExist:
                previous_proposal = Proposal.objects.get(id=self.id)
                proposal = clone_proposal_with_status_reset(previous_proposal)
                proposal.proposal_type = "renewal"
                proposal.training_completed = False
                # proposal.schema = ProposalType.objects.first().schema
                ptype = ProposalType.objects.filter(
                    name=proposal.application_type
                ).latest("version")
                proposal.schema = ptype.schema
                proposal.submitter = request.user
                proposal.previous_application = self
                proposal.proposed_issuance_approval = None

                if proposal.application_type.name == ApplicationType.TCLASS:
                    # require user to re-enter mandatory info in 'Other Details' tab, when renewing
                    proposal.other_details.insurance_expiry = None
                    proposal.other_details.preferred_licence_period = None
                    proposal.other_details.nominated_start_date = None
                    ProposalAccreditation.objects.filter(
                        proposal_other_details__proposal=proposal
                    ).delete()
                    proposal.documents.filter(
                        input_name__in=["deed_poll", "currency_certificate"]
                    ).delete()

                    # require  user to pay Application and Licence Fee again
                    proposal.fee_invoice_reference = None

                    try:
                        ProposalOtherDetails.objects.get(proposal=proposal)
                    except ProposalOtherDetails.DoesNotExist:
                        ProposalOtherDetails.objects.create(proposal=proposal)
                    # Create a log entry for the proposal
                    proposal.other_details.nominated_start_date = (
                        self.approval.expiry_date + datetime.timedelta(days=1)
                    )
                    proposal.other_details.save()
                if proposal.application_type.name == ApplicationType.FILMING:

                    proposal.filming_other_details.insurance_expiry = None
                    proposal.filming_other_details.save()
                    proposal.filming_activity.commencement_date = None
                    proposal.filming_activity.completion_date = None
                    proposal.filming_activity.save()
                    proposal.documents.filter(
                        input_name__in=["deed_poll", "currency_certificate"]
                    ).delete()

                    # require  user to pay Application and Licence Fee again
                    proposal.fee_invoice_reference = None

                if proposal.application_type.name == ApplicationType.EVENT:

                    proposal.event_other_details.insurance_expiry = None
                    proposal.event_other_details.save()
                    proposal.event_activity.commencement_date = None
                    proposal.event_activity.completion_date = None
                    proposal.event_activity.save()
                    proposal.documents.filter(
                        input_name__in=["deed_poll", "currency_certificate"]
                    ).delete()

                    # require  user to pay Application and Licence Fee again
                    proposal.fee_invoice_reference = None

                req = self.requirements.all().exclude(is_deleted=True)
                from copy import deepcopy

                if req:
                    for r in req:
                        old_r = deepcopy(r)
                        r.proposal = proposal
                        r.copied_from = None
                        r.copied_for_renewal = True
                        if r.due_date:
                            r.due_date = None
                            r.require_due_date = True
                        r.id = None
                        r.district_proposal = None
                        r.save()
                # copy all the requirement documents from previous proposal
                for requirement in proposal.requirements.all():
                    for requirement_document in RequirementDocument.objects.filter(
                        requirement=requirement.copied_from
                    ):
                        requirement_document.requirement = requirement
                        requirement_document.id = None
                        requirement_document._file.name = (
                            "{}/proposals/{}/requirement_documents/{}".format(
                                settings.MEDIA_APP_DIR,
                                proposal.id,
                                requirement_document.name,
                            )
                        )
                        requirement_document.can_delete = True
                        requirement_document.save()
                        # Create a log entry for the proposal
                self.log_user_action(
                    ProposalUserAction.ACTION_RENEW_PROPOSAL.format(self.id), request
                )
                # Create a log entry for the organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_RENEW_PROPOSAL.format(self.id), request
                )
                # Log entry for approval
                from licensing_template.components.approvals.models import (
                    ApprovalUserAction,
                )

                self.approval.log_user_action(
                    ApprovalUserAction.ACTION_RENEW_APPROVAL.format(self.approval.id),
                    request,
                )
                proposal.save(
                    version_comment="New Amendment/Renewal Application created, from origin {}".format(
                        proposal.previous_application_id
                    )
                )
                # proposal.save()
            return proposal

    def amend_approval(self, request):
        with transaction.atomic():
            previous_proposal = self
            try:
                amend_conditions = {
                    "previous_application": previous_proposal,
                    "proposal_type": "amendment",
                }
                proposal = Proposal.objects.get(**amend_conditions)
                # if proposal.customer_status=='with_assessor':
                if proposal.processing_status in ("with_assessor",):
                    raise ValidationError(
                        "An amendment for this licence has already been lodged and is awaiting review."
                    )
            except Proposal.DoesNotExist:
                previous_proposal = Proposal.objects.get(id=self.id)
                proposal = clone_proposal_with_status_reset(previous_proposal)
                proposal.proposal_type = "amendment"
                proposal.training_completed = True
                # proposal.schema = ProposalType.objects.first().schema
                ptype = ProposalType.objects.filter(
                    name=proposal.application_type
                ).latest("version")
                proposal.schema = ptype.schema
                proposal.submitter = request.user
                proposal.previous_application = self
                if proposal.application_type.name == ApplicationType.TCLASS:
                    try:
                        ProposalOtherDetails.objects.get(proposal=proposal)
                    except ProposalOtherDetails.DoesNotExist:
                        ProposalOtherDetails.objects.create(proposal=proposal)
                # copy all the requirements from the previous proposal
                # req=self.requirements.all()
                req = self.requirements.all().exclude(is_deleted=True)
                from copy import deepcopy

                if req:
                    for r in req:
                        old_r = deepcopy(r)
                        r.proposal = proposal
                        r.copied_from = old_r
                        r.id = None
                        r.district_proposal = None
                        r.save()
                # copy all the requirement documents from previous proposal
                for requirement in proposal.requirements.all():
                    for requirement_document in RequirementDocument.objects.filter(
                        requirement=requirement.copied_from
                    ):
                        requirement_document.requirement = requirement
                        requirement_document.id = None
                        requirement_document._file.name = (
                            "{}/proposals/{}/requirement_documents/{}".format(
                                settings.MEDIA_APP_DIR,
                                proposal.id,
                                requirement_document.name,
                            )
                        )
                        requirement_document.can_delete = True
                        requirement_document.save()
                        # Create a log entry for the proposal
                self.log_user_action(
                    ProposalUserAction.ACTION_AMEND_PROPOSAL.format(self.id), request
                )
                # Create a log entry for the organisation
                applicant_field = getattr(self, self.applicant_field)
                applicant_field.log_user_action(
                    ProposalUserAction.ACTION_AMEND_PROPOSAL.format(self.id), request
                )
                # Log entry for approval
                from licensing_template.components.approvals.models import (
                    ApprovalUserAction,
                )

                self.approval.log_user_action(
                    ApprovalUserAction.ACTION_AMEND_APPROVAL.format(self.approval.id),
                    request,
                )
                proposal.save(
                    version_comment="New Amendment/Renewal Application created, from origin {}".format(
                        proposal.previous_application_id
                    )
                )
                # proposal.save()
            return proposal


class ProposalAdditionalDocumentType(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    additional_document_type = models.ForeignKey(
        AdditionalDocumentType, on_delete=models.CASCADE
    )

    class Meta:
        app_label = "licensing_template"


class AdditionalDocument(Document):
    _file = models.FileField(upload_to=update_additional_doc_filename, max_length=512)
    proposal_additional_document_type = models.ForeignKey(
        ProposalAdditionalDocumentType, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        app_label = "licensing_template"


class ApplicationFeeDiscount(RevisionedMixin):
    DISCOUNT_TYPE_APPLICATION = 0
    DISCOUNT_TYPE_LICENCE = 1
    DISCOUNT_TYPE_CHOICES = (
        (DISCOUNT_TYPE_APPLICATION, "Discount application"),
        (DISCOUNT_TYPE_LICENCE, "Discount licence"),
    )
    proposal = models.ForeignKey(
        Proposal, related_name="fee_discounts", null=True, on_delete=models.CASCADE
    )
    discount_type = models.CharField(max_length=40, choices=DISCOUNT_TYPE_CHOICES)
    discount = models.FloatField(validators=[MinValueValidator(0.0)])
    created = models.DateTimeField(auto_now_add=True)
    user = models.IntegerField()  # EmailUserRO
    reset_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "{} - {}% - {}".format(
            self.get_discount_type_display(),
            self.discount,
            self.proposal.fee_invoice_reference,
        )

    @property
    def invoice(self):
        try:
            invoice = Invoice.objects.get(reference=self.proposal.fee_invoice_reference)
            return invoice
        except Invoice.DoesNotExist:
            pass
        return False

    @property
    def payment_amount(self):
        return self.invoice.amount

    class Meta:
        app_label = "licensing_template"


class ProposalGeometry(models.Model):
    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name="proposalgeometry"
    )
    polygon = PolygonField(srid=4326, blank=True, null=True)
    intersects = models.BooleanField(default=False)
    copied_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        app_label = "licensing_template"


class ProposalLogDocument(Document):
    log_entry = models.ForeignKey(
        "ProposalLogEntry", related_name="documents", on_delete=models.CASCADE
    )
    _file = models.FileField(
        upload_to=update_proposal_comms_log_filename, max_length=512
    )

    class Meta:
        app_label = "licensing_template"


class ProposalLogEntry(CommunicationsLogEntry):
    proposal = models.ForeignKey(
        Proposal, related_name="comms_logs", on_delete=models.CASCADE
    )

    def __str__(self):
        return "{} - {}".format(self.reference, self.subject)

    class Meta:
        app_label = "licensing_template"

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.proposal.reference
        super(ProposalLogEntry, self).save(**kwargs)


class ProposalOtherDetails(models.Model):
    LICENCE_PERIOD_CHOICES = (
        ("2_months", "2 months"),
        ("1_year", "1 Year"),
        ("3_year", "3 Years"),
        ("5_year", "5 Years"),
        ("7_year", "7 Years"),
        ("10_year", "10 Years"),
    )
    preferred_licence_period = models.CharField(
        "Preferred licence period",
        max_length=40,
        choices=LICENCE_PERIOD_CHOICES,
        null=True,
        blank=True,
    )
    nominated_start_date = models.DateField(blank=True, null=True)
    insurance_expiry = models.DateField(blank=True, null=True)
    other_comments = models.TextField(blank=True)
    # if credit facilities for payment of fees is required
    credit_fees = models.BooleanField(default=False)
    # if credit/ cash payment docket books are required
    credit_docket_books = models.BooleanField(default=False)
    docket_books_number = models.CharField(
        "Docket books number", max_length=20, blank=True
    )
    proposal = models.OneToOneField(
        Proposal, related_name="other_details", null=True, on_delete=models.CASCADE
    )

    class Meta:
        app_label = "licensing_template"

    @property
    def proposed_end_date(self):
        end_date = None
        if self.preferred_licence_period and self.nominated_start_date:
            if self.preferred_licence_period == "2_months":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+2)
                    - relativedelta(days=1)
                )
            if self.preferred_licence_period == "1_year":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+12)
                    - relativedelta(days=1)
                )
            if self.preferred_licence_period == "3_year":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+36)
                    - relativedelta(days=1)
                )
            if self.preferred_licence_period == "5_year":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+60)
                    - relativedelta(days=1)
                )
            if self.preferred_licence_period == "7_year":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+84)
                    - relativedelta(days=1)
                )
            if self.preferred_licence_period == "10_year":
                end_date = (
                    self.nominated_start_date
                    + relativedelta(months=+120)
                    - relativedelta(days=1)
                )
        return end_date


class ProposalRequest(models.Model):
    proposal = models.ForeignKey(
        Proposal, related_name="proposalrequest_set", on_delete=models.CASCADE
    )
    subject = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    # fficer = models.ForeignKey(EmailUser, null=True, on_delete=models.SET_NULL)
    officer = models.IntegerField()  # EmailUserRO

    def __str__(self):
        return "{} - {}".format(self.subject, self.text)

    class Meta:
        app_label = "licensing_template"


class ComplianceRequest(ProposalRequest):
    REASON_CHOICES = (
        (
            "outstanding",
            "There are currently outstanding returns for the previous licence",
        ),
        ("other", "Other"),
    )
    reason = models.CharField(
        "Reason", max_length=30, choices=REASON_CHOICES, default=REASON_CHOICES[0][0]
    )

    class Meta:
        app_label = "licensing_template"


class AmendmentReason(models.Model):
    reason = models.CharField("Reason", max_length=125)

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Amendment Reason"  # display name in Admin
        verbose_name_plural = "Application Amendment Reasons"

    def __str__(self):
        return self.reason


class AmendmentRequest(ProposalRequest):
    STATUS_CHOICES = (("requested", "Requested"), ("amended", "Amended"))
    # REASON_CHOICES = (('insufficient_detail', 'The information provided was insufficient'),
    #                  ('missing_information', 'There was missing information'),
    #                  ('other', 'Other'))
    # try:
    #     # model requires some choices if AmendmentReason does not yet exist or is empty
    #     REASON_CHOICES = list(AmendmentReason.objects.values_list('id', 'reason'))
    #     if not REASON_CHOICES:
    #         REASON_CHOICES = ((0, 'The information provided was insufficient'),
    #                           (1, 'There was missing information'),
    #                           (2, 'Other'))
    # except:
    #     REASON_CHOICES = ((0, 'The information provided was insufficient'),
    #                       (1, 'There was missing information'),
    #                       (2, 'Other'))

    status = models.CharField(
        "Status", max_length=30, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    # reason = models.CharField('Reason', max_length=30, choices=REASON_CHOICES, default=REASON_CHOICES[0][0])
    reason = models.ForeignKey(
        AmendmentReason, blank=True, null=True, on_delete=models.SET_NULL
    )
    # reason = models.ForeignKey(AmendmentReason)

    class Meta:
        app_label = "licensing_template"

    def generate_amendment(self, request):
        with transaction.atomic():
            try:
                if not self.proposal.can_assess(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.status == "requested":
                    proposal = self.proposal
                    if proposal.processing_status != "draft":
                        proposal.processing_status = "draft"
                        proposal.customer_status = "draft"
                        proposal.save()
                        proposal.documents.all().update(can_hide=True)
                        proposal.required_documents.all().update(can_hide=True)
                    # Create a log entry for the proposal
                    proposal.log_user_action(
                        ProposalUserAction.ACTION_ID_REQUEST_AMENDMENTS, request
                    )
                    # Create a log entry for the organisation
                    applicant_field = getattr(proposal, proposal.applicant_field)
                    applicant_field.log_user_action(
                        ProposalUserAction.ACTION_ID_REQUEST_AMENDMENTS, request
                    )

                    # send email

                    send_amendment_email_notification(self, request, proposal)

                self.save()
            except:
                raise


class Assessment(ProposalRequest):
    STATUS_CHOICES = (
        ("awaiting_assessment", "Awaiting Assessment"),
        ("assessed", "Assessed"),
        ("assessment_expired", "Assessment Period Expired"),
    )
    # assigned_assessor = models.ForeignKey(EmailUser, blank=True, null=True, on_delete=models.SET_NULL)
    assigned_assessor = models.IntegerField()  # EmailUserRO
    status = models.CharField(
        "Status", max_length=20, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    date_last_reminded = models.DateField(null=True, blank=True)
    # requirements = models.ManyToManyField('Requirement', through='AssessmentRequirement')
    comment = models.TextField(blank=True)
    purpose = models.TextField(blank=True)

    class Meta:
        app_label = "licensing_template"


class ProposalDeclinedDetails(models.Model):
    # proposal = models.OneToOneField(Proposal, related_name='declined_details')
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    # officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)
    officer = models.IntegerField()  # EmailUserRO
    reason = models.TextField(blank=True)
    cc_email = models.TextField(null=True)

    class Meta:
        app_label = "licensing_template"


class ProposalOnHold(models.Model):
    # proposal = models.OneToOneField(Proposal, related_name='onhold')
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    # officer = models.ForeignKey(EmailUser, null=False, on_delete=models.CASCADE)
    officer = models.IntegerField()  # EmailUserRO
    comment = models.TextField(blank=True)
    documents = models.ForeignKey(
        ProposalDocument,
        blank=True,
        null=True,
        related_name="onhold_documents",
        on_delete=models.SET_NULL,
    )

    class Meta:
        app_label = "licensing_template"


# class ProposalStandardRequirement(models.Model):
class ProposalStandardRequirement(RevisionedMixin):
    text = models.TextField()
    code = models.CharField(max_length=10, unique=True)
    obsolete = models.BooleanField(default=False)
    application_type = models.ForeignKey(
        ApplicationType, null=True, blank=True, on_delete=models.SET_NULL
    )
    participant_number_required = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    # require_due_date = models.BooleanField(default=False)

    def __str__(self):
        return self.code

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Application Standard Requirement"
        verbose_name_plural = "Application Standard Requirements"

    # def clean(self):
    #     if self.application_type:
    #         try:
    #             default = ProposalStandardRequirement.objects.get(default=True, application_type=self.application_type)
    #         except ProposalStandardRequirement.DoesNotExist:
    #             default = None

    #     if not self.pk:
    #         if default and self.default:
    #             raise ValidationError('There can only be one default Standard requirement per Application type')


class ProposalUserAction(UserAction):
    ACTION_CREATE_CUSTOMER_ = "Create customer {}"
    ACTION_CREATE_PROFILE_ = "Create profile {}"
    ACTION_LODGE_APPLICATION = "Lodge application {}"
    ACTION_ASSIGN_TO_ASSESSOR = "Assign application {} to {} as the assessor"
    ACTION_UNASSIGN_ASSESSOR = "Unassign assessor from application {}"
    ACTION_ASSIGN_TO_APPROVER = "Assign application {} to {} as the approver"
    ACTION_UNASSIGN_APPROVER = "Unassign approver from application {}"
    ACTION_ACCEPT_ID = "Accept ID"
    ACTION_RESET_ID = "Reset ID"
    ACTION_ID_REQUEST_UPDATE = "Request ID update"
    ACTION_ACCEPT_CHARACTER = "Accept character"
    ACTION_RESET_CHARACTER = "Reset character"
    ACTION_ACCEPT_REVIEW = "Accept review"
    ACTION_RESET_REVIEW = "Reset review"
    ACTION_ID_REQUEST_AMENDMENTS = "Request amendments"
    ACTION_SEND_FOR_ASSESSMENT_TO_ = "Send for assessment to {}"
    ACTION_SEND_ASSESSMENT_REMINDER_TO_ = "Send assessment reminder to {}"
    ACTION_DECLINE = "Decline application {}"
    ACTION_ENTER_CONDITIONS = "Enter requirement"
    ACTION_CREATE_CONDITION_ = "Create requirement {}"
    ACTION_ISSUE_APPROVAL_ = "Issue Licence for application {}"
    ACTION_AWAITING_PAYMENT_APPROVAL_ = "Awaiting Payment for application {}"
    ACTION_UPDATE_APPROVAL_ = "Update Licence for application {}"
    ACTION_EXPIRED_APPROVAL_ = "Expire Approval for proposal {}"
    ACTION_DISCARD_PROPOSAL = "Discard application {}"
    ACTION_APPROVAL_LEVEL_DOCUMENT = "Assign Approval level document {}"
    # T-Class licence
    ACTION_LINK_PARK = "Link park {} to application {}"
    ACTION_UNLINK_PARK = "Unlink park {} from application {}"
    ACTION_LINK_ACCESS = "Link access {} to park {}"
    ACTION_UNLINK_ACCESS = "Unlink access {} from park {}"
    ACTION_LINK_ACTIVITY = "Link activity {} to park {}"
    ACTION_UNLINK_ACTIVITY = "Unlink activity {} from park {}"
    ACTION_LINK_ACTIVITY_SECTION = "Link activity {} to section {} of trail {}"
    ACTION_UNLINK_ACTIVITY_SECTION = "Unlink activity {} from section {} of trail {}"
    ACTION_LINK_ACTIVITY_ZONE = "Link activity {} to zone {} of park {}"
    ACTION_UNLINK_ACTIVITY_ZONE = "Unlink activity {} from zone {} of park {}"
    ACTION_LINK_TRAIL = "Link trail {} to application {}"
    ACTION_UNLINK_TRAIL = "Unlink trail {} from application {}"
    ACTION_LINK_SECTION = "Link section {} to trail {}"
    ACTION_UNLINK_SECTION = "Unlink section {} from trail {}"
    ACTION_LINK_ZONE = "Link zone {} to park {}"
    ACTION_UNLINK_ZONE = "Unlink zone {} from park {}"
    SEND_TO_DISTRICTS = "Send Proposal {} to district assessors"
    # Assessors
    ACTION_SAVE_ASSESSMENT_ = "Save assessment {}"
    ACTION_CONCLUDE_ASSESSMENT_ = "Conclude assessment {}"
    ACTION_PROPOSED_APPROVAL = "Application {} has been proposed for approval"
    ACTION_PROPOSED_DECLINE = "Application {} has been proposed for decline"

    # Referrals
    ACTION_SEND_REFERRAL_TO = "Send referral {} for application {} to {}"
    ACTION_RESEND_REFERRAL_TO = "Resend referral {} for application {} to {}"
    ACTION_REMIND_REFERRAL = "Send reminder for referral {} for application {} to {}"
    ACTION_ENTER_REQUIREMENTS = "Enter Requirements for application {}"
    ACTION_BACK_TO_PROCESSING = "Back to processing for application {}"
    RECALL_REFERRAL = "Referral {} for application {} has been recalled"
    CONCLUDE_REFERRAL = "{}: Referral {} for application {} has been concluded"
    ACTION_REFERRAL_DOCUMENT = "Assign Referral document {}"
    ACTION_REFERRAL_ASSIGN_TO_ASSESSOR = (
        "Assign Referral  {} of application {} to {} as the assessor"
    )
    ACTION_REFERRAL_UNASSIGN_ASSESSOR = (
        "Unassign assessor from Referral {} of application {}"
    )

    # Approval
    ACTION_REISSUE_APPROVAL = "Reissue licence for application {}"
    ACTION_CANCEL_APPROVAL = "Cancel licence for application {}"
    ACTION_EXTEND_APPROVAL = "Extend licence"
    ACTION_SUSPEND_APPROVAL = "Suspend licence for application {}"
    ACTION_REINSTATE_APPROVAL = "Reinstate licence for application {}"
    ACTION_SURRENDER_APPROVAL = "Surrender licence for application {}"
    ACTION_RENEW_PROPOSAL = "Create Renewal application for application {}"
    ACTION_AMEND_PROPOSAL = "Create Amendment application for application {}"
    # Vehicle
    ACTION_CREATE_VEHICLE = "Create Vehicle {}"
    ACTION_EDIT_VEHICLE = "Edit Vehicle {}"
    # Vessel
    ACTION_CREATE_VESSEL = "Create Vessel {}"
    ACTION_EDIT_VESSEL = "Edit Vessel {}"
    ACTION_PUT_ONHOLD = "Put Application On-hold {}"
    ACTION_REMOVE_ONHOLD = "Remove Application On-hold {}"
    ACTION_WITH_QA_OFFICER = "Send Application QA Officer {}"
    ACTION_QA_OFFICER_COMPLETED = "QA Officer Assessment Completed {}"

    # Filming
    ACTION_CREATE_FILMING_PARK = "Create Filming Park {}"
    ACTION_EDIT_FILMING_PARK = "Edit Filming Park {}"
    ACTION_ASSIGN_TO_DISTRICT_APPROVER = (
        "Assign District application {} of application {} to {} as the approver"
    )
    ACTION_ASSIGN_TO_DISTRICT_ASSESSOR = (
        "Assign District application {} of application {} to {} as the assessor"
    )
    ACTION_UNASSIGN_DISTRICT_ASSESSOR = (
        "Unassign assessor from District application {} of application {}"
    )
    ACTION_UNASSIGN_DISTRICT_APPROVER = (
        "Unassign approver from District application {} of application {}"
    )
    ACTION_BACK_TO_PROCESSING_DISTRICT = (
        "Back to processing for district application {} of application {}"
    )
    ACTION_ENTER_REQUIREMENTS_DISTRICT = (
        "Enter Requirements for district application {} of application {}"
    )
    ACTION_DISTRICT_PROPOSED_APPROVAL = (
        "District application {} of application {} has been proposed for approval"
    )
    ACTION_DISTRICT_PROPOSED_DECLINE = (
        "District application {} of application {} has been proposed for decline"
    )
    ACTION_DISTRICT_DECLINE = (
        "District application {} of application {} has been declined"
    )
    ACTION_UPDATE_APPROVAL_DISTRICT = (
        "Update Licence by district application {} of application {}"
    )
    ACTION_ISSUE_APPROVAL_DISTRICT = (
        "Issue Licence by district application {} of application {}"
    )

    # Event
    ACTION_CREATE_EVENT_PARK = "Create Event Park {}"
    ACTION_EDIT_EVENT_PARK = "Edit Event Park {}"
    ACTION_CREATE_PRE_EVENT_PARK = "Create Pre Event Park {}"
    ACTION_EDIT_PRE_EVENT_PARK = "Edit Pre Event Park {}"
    ACTION_CREATE_ABSEILING_CLIMBING_ACTIVITY = "Create Abseiling Climbing Activity {}"
    ACTION_EDIT_ABSEILING_CLIMBING_ACTIVITY = "Edit Abseiling Climbing Activity {}"

    # monthly invoicing by cron
    ACTION_SEND_BPAY_INVOICE = "Send BPAY invoice {} for application {} to {}"
    ACTION_SEND_MONTHLY_INVOICE = "Send monthly invoice {} for application {} to {}"
    ACTION_SEND_MONTHLY_CONFIRMATION = (
        "Send monthly confirmation for booking ID {}, for application {} to {}"
    )
    ACTION_SEND_PAYMENT_DUE_NOTIFICATION = (
        "Send monthly invoice/BPAY payment due notification {} for application {} to {}"
    )

    class Meta:
        app_label = "licensing_template"
        ordering = ("-when",)

    @classmethod
    def log_action(cls, proposal, action, user):
        return cls.objects.create(proposal=proposal, who=user, what=str(action))

    proposal = models.ForeignKey(
        Proposal, related_name="action_logs", on_delete=models.CASCADE
    )


class ReferralRecipientGroup(models.Model):
    # site = models.OneToOneField(Site, default='1')
    name = models.CharField(max_length=30, unique=True)
    # members = models.ManyToManyField(EmailUser)
    members = ArrayField(models.IntegerField(), blank=True)  # EmailUserRO

    def __str__(self):
        # return 'Referral Recipient Group'
        return self.name

    @property
    def all_members(self):
        all_members = []
        all_members.extend(self.members.all())
        member_ids = [m.id for m in self.members.all()]
        # all_members.extend(EmailUser.objects.filter(is_superuser=True,is_staff=True,is_active=True).exclude(id__in=member_ids))
        return all_members

    @property
    def filtered_members(self):
        return self.members.all()

    @property
    def members_list(self):
        return list(self.members.all().values_list("email", flat=True))

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Referral group"
        verbose_name_plural = "Referral groups"


class QAOfficerGroup(models.Model):
    # site = models.OneToOneField(Site, default='1')
    name = models.CharField(max_length=30, unique=True)
    # members = models.ManyToManyField(EmailUser)
    members = ArrayField(models.IntegerField(), blank=True)  # EmailUserRO
    default = models.BooleanField(default=False)

    def __str__(self):
        return "QA Officer Group"

    @property
    def all_members(self):
        all_members = []
        all_members.extend(self.members.all())
        member_ids = [m.id for m in self.members.all()]
        # all_members.extend(EmailUser.objects.filter(is_superuser=True,is_staff=True,is_active=True).exclude(id__in=member_ids))
        return all_members

    @property
    def filtered_members(self):
        return self.members.all()

    @property
    def members_list(self):
        return list(self.members.all().values_list("email", flat=True))

    class Meta:
        app_label = "licensing_template"
        verbose_name = "QA group"
        verbose_name_plural = "QA group"

    def _clean(self):
        try:
            default = QAOfficerGroup.objects.get(default=True)
        except ProposalAssessorGroup.DoesNotExist:
            default = None

        if default and self.default:
            raise ValidationError(
                "There can only be one default proposal QA Officer group"
            )

    @property
    def current_proposals(self):
        assessable_states = ["with_qa_officer"]
        return Proposal.objects.filter(processing_status__in=assessable_states)


class Referral(RevisionedMixin):
    SENT_CHOICES = ((1, "Sent From Assessor"), (2, "Sent From Referral"))
    PROCESSING_STATUS_WITH_REFERRAL = "with_referral"
    PROCESSING_STATUS_RECALLED = "recalled"
    PROCESSING_STATUS_COMPLETED = "completed"
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_WITH_REFERRAL, "Awaiting"),
        (PROCESSING_STATUS_RECALLED, "Recalled"),
        (PROCESSING_STATUS_COMPLETED, "Completed"),
    )
    lodged_on = models.DateTimeField(auto_now_add=True)
    proposal = models.ForeignKey(
        Proposal, related_name="referrals", on_delete=models.CASCADE
    )
    sent_by = models.IntegerField()  # EmailUserRO
    referral = models.IntegerField()  # EmailUserRO
    linked = models.BooleanField(default=False)
    sent_from = models.SmallIntegerField(
        choices=SENT_CHOICES, default=SENT_CHOICES[0][0]
    )
    processing_status = models.CharField(
        "Processing Status",
        max_length=30,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    text = models.TextField(blank=True)  # Assessor text
    referral_text = models.TextField(blank=True)
    document = models.ForeignKey(
        ReferralDocument,
        blank=True,
        null=True,
        related_name="referral_document",
        on_delete=models.SET_NULL,
    )
    assigned_officer = models.IntegerField()  # EmailUserRO

    class Meta:
        app_label = "licensing_template"
        ordering = ("-lodged_on",)

    def __str__(self):
        return "Application {} - Referral {}".format(self.proposal.id, self.id)

    # Methods
    @property
    def application_type(self):
        return self.proposal.application_type.name

    @property
    def latest_referrals(self):
        return Referral.objects.filter(sent_by=self.referral, proposal=self.proposal)[
            :2
        ]

    @property
    def referral_assessment(self):
        # qs=self.assessment.filter(referral_assessment=True, referral_group=self.referral_group)
        qs = self.assessment.filter(referral_assessment=True)
        if qs:
            return qs[0]
        else:
            return None

    @property
    def can_be_completed(self):
        return True
        # Referral cannot be completed until second level referral sent by referral has been completed/recalled
        qs = Referral.objects.filter(
            sent_by=self.referral,
            proposal=self.proposal,
            processing_status=Referral.PROCESSING_STATUS_WITH_REFERRAL,
        )
        if qs:
            return False
        else:
            return True

    @property
    def allowed_assessors(self):
        ## must be SystemGroup
        # group = self.referral_group
        # return group.members.all() if group else []
        # return group.get_system_group_member_ids() if group else []
        return []  # TODO: correct this

    def can_process(self, user):
        return True  # TODO: implement
        # if self.processing_status == Referral.PROCESSING_STATUS_WITH_REFERRAL:
        #    group =  ReferralRecipientGroup.objects.filter(id=self.referral_group.id)
        #    #user=request.user
        #    if group and group[0] in user.referralrecipientgroup_set.all():
        #        return True
        #    else:
        #        return False
        # return False

    def assign_officer(self, request, officer):
        with transaction.atomic():
            try:
                if not self.can_process(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if not self.can_process(officer):
                    raise ValidationError(
                        "The selected person is not authorised to be assigned to this Referral"
                    )
                if officer != self.assigned_officer:
                    self.assigned_officer = officer
                    self.save()
                    self.proposal.log_user_action(
                        ProposalUserAction.ACTION_REFERRAL_ASSIGN_TO_ASSESSOR.format(
                            self.id,
                            self.proposal.id,
                            "{}({})".format(officer.get_full_name(), officer.email),
                        ),
                        request,
                    )
            except:
                raise

    def unassign(self, request):
        with transaction.atomic():
            try:
                if not self.can_process(request.user):
                    raise exceptions.ProposalNotAuthorized()
                if self.assigned_officer:
                    self.assigned_officer = None
                    self.save()
                    # Create a log entry for the proposal
                    self.proposal.log_user_action(
                        ProposalUserAction.ACTION_REFERRAL_UNASSIGN_ASSESSOR.format(
                            self.id, self.proposal.id
                        ),
                        request,
                    )
                    # Create a log entry for the organisation
                    applicant_field = getattr(
                        self.proposal, self.proposal.applicant_field
                    )
                    applicant_field = retrieve_email_user(applicant_field)
                    # TODO: implement logging
                    # applicant_field.log_user_action(ProposalUserAction.ACTION_REFERRAL_UNASSIGN_ASSESSOR.format(self.id, self.proposal.id),request)
            except:
                raise

    def recall(self, request):
        with transaction.atomic():
            if not self.proposal.can_assess(request.user):
                raise exceptions.ProposalNotAuthorized()
            self.processing_status = Referral.PROCESSING_STATUS_RECALLED
            self.save()
            # TODO Log proposal action
            self.proposal.log_user_action(
                ProposalUserAction.RECALL_REFERRAL.format(self.id, self.proposal.id),
                request,
            )
            # TODO log organisation action
            applicant_field = getattr(self.proposal, self.proposal.applicant_field)
            applicant_field = retrieve_email_user(applicant_field)
            # TODO: implement logging
            # applicant_field.log_user_action(ProposalUserAction.RECALL_REFERRAL.format(self.id,self.proposal.id),request)

    @property
    def referral_as_email_user(self):
        return retrieve_email_user(self.referral)

    def remind(self, request):
        with transaction.atomic():
            if not self.proposal.can_assess(request.user):
                raise exceptions.ProposalNotAuthorized()
            # Create a log entry for the proposal
            # self.proposal.log_user_action(ProposalUserAction.ACTION_REMIND_REFERRAL.format(self.id,self.proposal.id,'{}({})'.format(self.referral.get_full_name(),self.referral.email)),request)
            # self.proposal.log_user_action(ProposalUserAction.ACTION_REMIND_REFERRAL.format(self.id,self.proposal.id,'{}'.format(self.referral_group.name)),request)
            self.proposal.log_user_action(
                ProposalUserAction.ACTION_REMIND_REFERRAL.format(
                    self.id,
                    self.proposal.id,
                    "{}".format(self.referral_as_email_user.get_full_name()),
                ),
                request,
            )
            # Create a log entry for the organisation
            applicant_field = getattr(self.proposal, self.proposal.applicant_field)
            applicant_field = retrieve_email_user(applicant_field)
            # applicant_field.log_user_action(ProposalUserAction.ACTION_REMIND_REFERRAL.format(self.id,self.proposal.id,'{}'.format(self.referral_group.name)),request)

            # TODO: logging applicant_field
            # applicant_field.log_user_action(
            #     ProposalUserAction.ACTION_REMIND_REFERRAL.format(
            #         self.id, self.proposal.id, '{}'.format(self.referral_as_email_user.get_full_name())
            #         ), request
            #     )

            # send email
            # recipients = self.referral_group.members_list
            # send_referral_email_notification(self,recipients,request,reminder=True)
            send_referral_email_notification(
                self,
                [
                    self.referral_as_email_user.email,
                ],
                request,
                reminder=True,
            )

    def resend(self, request):
        with transaction.atomic():
            if not self.proposal.can_assess(request.user):
                raise exceptions.ProposalNotAuthorized()
            self.processing_status = Referral.PROCESSING_STATUS_WITH_REFERRAL
            self.proposal.processing_status = Proposal.PROCESSING_STATUS_WITH_REFERRAL
            self.proposal.save()
            self.sent_from = 1
            self.save()
            # Create a log entry for the proposal
            # self.proposal.log_user_action(ProposalUserAction.ACTION_RESEND_REFERRAL_TO.format(self.id,self.proposal.id,'{}({})'.format(self.referral.get_full_name(),self.referral.email)),request)
            # self.proposal.log_user_action(ProposalUserAction.ACTION_RESEND_REFERRAL_TO.format(self.id,self.proposal.id,'{}'.format(self.referral_group.name)),request)
            self.proposal.log_user_action(
                ProposalUserAction.ACTION_RESEND_REFERRAL_TO.format(
                    self.id,
                    self.proposal.id,
                    "{}".format(self.referral_as_email_user.get_full_name()),
                ),
                request,
            )
            # Create a log entry for the organisation
            # self.proposal.applicant.log_user_action(ProposalUserAction.ACTION_RESEND_REFERRAL_TO.format(self.id,self.proposal.id,'{}({})'.format(self.referral.get_full_name(),self.referral.email)),request)
            applicant_field = getattr(self.proposal, self.proposal.applicant_field)
            applicant_field = retrieve_email_user(applicant_field)

            # TODO: logging applicant_field
            # applicant_field.log_user_action(
            #     ProposalUserAction.ACTION_RESEND_REFERRAL_TO.format(
            #         self.id, self.proposal.id, '{}'.format(self.referral_as_email_user.get_full_name())
            #         ), request
            #     )

            # send email
            # recipients = self.referral_group.members_list
            # send_referral_email_notification(self,recipients,request)
            send_referral_email_notification(
                self,
                [
                    self.referral_as_email_user.email,
                ],
                request,
            )

    def complete(self, request):
        with transaction.atomic():
            try:
                self.processing_status = Referral.PROCESSING_STATUS_COMPLETED
                self.referral = request.user.id
                self.add_referral_document(request)
                self.save()

                # TODO Log proposal action
                # self.proposal.log_user_action(ProposalUserAction.CONCLUDE_REFERRAL.format(self.id,self.proposal.id,'{}({})'.format(self.referral.get_full_name(),self.referral.email)),request)
                self.proposal.log_user_action(
                    ProposalUserAction.CONCLUDE_REFERRAL.format(
                        request.user.get_full_name(), self.id, self.proposal.id
                    ),
                    request,
                )

                # TODO log organisation action
                # self.proposal.applicant.log_user_action(ProposalUserAction.CONCLUDE_REFERRAL.format(self.id,self.proposal.id,'{}({})'.format(self.referral.get_full_name(),self.referral.email)),request)
                applicant_field = getattr(self.proposal, self.proposal.applicant_field)
                applicant_field = retrieve_email_user(applicant_field)

                # TODO: logging applicant_field
                # applicant_field.log_user_action(ProposalUserAction.CONCLUDE_REFERRAL.format(request.user.get_full_name(), self.id,self.proposal.id,'{}'.format(self.referral_group.name)),request)

                send_referral_complete_email_notification(self, request)
            except:
                raise

    def add_referral_document(self, request):
        with transaction.atomic():
            try:
                # if request.data.has_key('referral_document'):
                if "referral_document" in request.data:
                    referral_document = request.data["referral_document"]
                    if referral_document != "null":
                        try:
                            document = self.referral_documents.get(
                                input_name=str(referral_document)
                            )
                        except ReferralDocument.DoesNotExist:
                            document = self.referral_documents.get_or_create(
                                input_name=str(referral_document),
                                name=str(referral_document),
                            )[0]
                        document.name = str(referral_document)
                        # commenting out below tow lines - we want to retain all past attachments - reversion can use them
                        # if document._file and os.path.isfile(document._file.path):
                        #    os.remove(document._file.path)
                        document._file = referral_document
                        document.save()
                        d = ReferralDocument.objects.get(id=document.id)
                        # self.referral_document = d
                        self.document = d
                        comment = "Referral Document Added: {}".format(document.name)
                    else:
                        # self.referral_document = None
                        self.document = None
                        # comment = 'Referral Document Deleted: {}'.format(request.data['referral_document_name'])
                        comment = "Referral Document Deleted"
                    # self.save()
                    self.save(
                        version_comment=comment
                    )  # to allow revision to be added to reversion history
                    self.proposal.log_user_action(
                        ProposalUserAction.ACTION_REFERRAL_DOCUMENT.format(self.id),
                        request,
                    )
                    # Create a log entry for the organisation
                    applicant_field = getattr(
                        self.proposal, self.proposal.applicant_field
                    )
                    applicant_field.log_user_action(
                        ProposalUserAction.ACTION_REFERRAL_DOCUMENT.format(self.id),
                        request,
                    )
                return self
            except:
                raise

    def send_referral(self, request, referral_email, referral_text):
        with transaction.atomic():
            try:
                if (
                    self.proposal.processing_status
                    == Proposal.PROCESSING_STATUS_WITH_REFERRAL
                ):
                    if request.user != self.referral:
                        raise exceptions.ReferralNotAuthorized()
                    if self.sent_from != 1:
                        raise exceptions.ReferralCanNotSend()
                    self.proposal.processing_status = (
                        Proposal.PROCESSING_STATUS_WITH_REFERRAL
                    )
                    self.proposal.save()
                    referral = None
                    # Check if the user is in ledger
                    try:
                        user = EmailUser.objects.get(
                            email__icontains=referral_email.lower()
                        )
                    except EmailUser.DoesNotExist:
                        # Validate if it is a deparment user
                        department_user = get_department_user(referral_email)
                        if not department_user:
                            raise ValidationError(
                                "The user you want to send the referral to is not a member of the department"
                            )
                        # Check if the user is in ledger or create

                        user, created = EmailUser.objects.get_or_create(
                            email=department_user["email"].lower()
                        )
                        if created:
                            user.first_name = department_user["given_name"]
                            user.last_name = department_user["surname"]
                            user.save()
                    qs = Referral.objects.filter(sent_by=user, proposal=self.proposal)
                    if qs:
                        raise ValidationError("You cannot send referral to this user")
                    try:
                        Referral.objects.get(referral=user, proposal=self.proposal)
                        raise ValidationError(
                            "A referral has already been sent to this user"
                        )
                    except Referral.DoesNotExist:
                        # Create Referral
                        referral = Referral.objects.create(
                            proposal=self.proposal,
                            referral=user,
                            sent_by=request.user,
                            sent_from=2,
                            text=referral_text,
                        )
                        # try:
                        #     referral_assessment=ProposalAssessment.objects.get(proposal=self,referral_group=referral_group, referral_assessment=True, referral=referral)
                        # except ProposalAssessment.DoesNotExist:
                        #     referral_assessment=ProposalAssessment.objects.create(proposal=self,referral_group=referral_group, referral_assessment=True, referral=referral)
                        #     checklist=ChecklistQuestion.objects.filter(list_type='referral_list', obsolete=False)
                        #     for chk in checklist:
                        #         try:
                        #             chk_instance=ProposalAssessmentAnswer.objects.get(question=chk, assessment=referral_assessment)
                        #         except ProposalAssessmentAnswer.DoesNotExist:
                        #             chk_instance=ProposalAssessmentAnswer.objects.create(question=chk, assessment=referral_assessment)
                    # Create a log entry for the proposal
                    self.proposal.log_user_action(
                        ProposalUserAction.ACTION_SEND_REFERRAL_TO.format(
                            referral.id,
                            self.proposal.id,
                            "{}({})".format(user.get_full_name(), user.email),
                        ),
                        request,
                    )
                    # Create a log entry for the organisation
                    applicant_field = getattr(
                        self.proposal, self.proposal.applicant_field
                    )
                    applicant_field.log_user_action(
                        ProposalUserAction.ACTION_SEND_REFERRAL_TO.format(
                            referral.id,
                            self.proposal.id,
                            "{}({})".format(user.get_full_name(), user.email),
                        ),
                        request,
                    )
                    # send email
                    recipients = self.email_group.members_list
                    send_referral_email_notification(referral, recipients, request)
                else:
                    raise exceptions.ProposalReferralCannotBeSent()
            except:
                raise

    @property
    def title(self):
        return self.proposal.title

    @property
    def applicant(self):
        return self.proposal.applicant

    @property
    def can_be_processed(self):
        return self.processing_status == "with_referral"

    def can_assess_referral(self, user):
        return self.processing_status == "with_referral"


class ProposalRequirement(RevisionedMixin):
    RECURRENCE_PATTERNS = [(1, "Weekly"), (2, "Monthly"), (3, "Yearly")]
    standard_requirement = models.ForeignKey(
        ProposalStandardRequirement, null=True, blank=True, on_delete=models.SET_NULL
    )
    free_requirement = models.TextField(null=True, blank=True)
    standard = models.BooleanField(default=True)
    proposal = models.ForeignKey(
        Proposal, related_name="requirements", on_delete=models.CASCADE
    )
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.BooleanField(default=False)
    recurrence_pattern = models.SmallIntegerField(
        choices=RECURRENCE_PATTERNS, default=1
    )
    recurrence_schedule = models.IntegerField(null=True, blank=True)
    copied_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )
    is_deleted = models.BooleanField(default=False)
    copied_for_renewal = models.BooleanField(default=False)
    require_due_date = models.BooleanField(default=False)
    # To determine if requirement has been added by referral and the group of referral who added it
    # Null if added by an assessor
    referral_group = models.ForeignKey(
        ReferralRecipientGroup,
        null=True,
        blank=True,
        related_name="requirement_referral_groups",
        on_delete=models.SET_NULL,
    )
    notification_only = models.BooleanField(default=False)
    req_order = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "licensing_template"
        ordering = ["proposal", "req_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "req_order"],
                name="unique requirement order per proposal",
            )
        ]

    def save(self, **kwargs):
        # import ipdb; ipdb.set_trace()
        # set the req_order if saving for the first time
        if not self.id:
            max_req_order = (
                ProposalRequirement.objects.filter(proposal_id=self.proposal_id)
                .aggregate(max_req_order=Max("req_order"))
                .get("max_req_order")
            )
            if not max_req_order:
                self.req_order = 1
            else:
                self.req_order = max_req_order + 1
        super(ProposalRequirement, self).save(**kwargs)

    def swap_obj(self, up):
        increment = -1
        swap_increment = None
        for req in ProposalRequirement.objects.filter(
            proposal_id=self.proposal_id, is_deleted=False
        ).order_by("req_order"):
            increment += 1
            if req.id == self.id:
                break
        if up:
            swap_increment = increment - 1
        else:
            swap_increment = increment + 1

        return ProposalRequirement.objects.filter(
            proposal_id=self.proposal_id, is_deleted=False
        ).order_by("req_order")[swap_increment]

    # def _next_req(self):
    #    increment = -1
    #    for req in ProposalRequirement.objects.filter(proposal_id=self.proposal_id, is_deleted=False).order_by('-req_order'):
    #        increment += 1
    #        if req.id == self.id:
    #            break
    #    return ProposalRequirement.objects.filter(proposal_id=self.proposal_id, is_deleted=False).order_by('req_order')[increment]

    def move_up(self):
        # ignore deleted reqs
        if self.req_order == ProposalRequirement.objects.filter(
            is_deleted=False, proposal_id=self.proposal_id
        ).aggregate(min_req_order=Min("req_order")).get("min_req_order"):
            pass
        else:
            # self.swap(ProposalRequirement.objects.get(proposal=self.proposal, req_order=self.req_order-1))
            self.swap(self.swap_obj(True))

    def move_down(self):
        # ignore deleted reqs
        if self.req_order == ProposalRequirement.objects.filter(
            is_deleted=False, proposal_id=self.proposal_id
        ).aggregate(max_req_order=Max("req_order")).get("max_req_order"):
            pass
        else:
            # self.swap(ProposalRequirement.objects.get(proposal=self.proposal, req_order=self.req_order-1))
            self.swap(self.swap_obj(False))
            # self.swap(self._next_req())

    def swap(self, other):
        new_self_position = other.req_order
        print(self.id)
        print("new_self_position")
        print(new_self_position)
        new_other_position = self.req_order
        print(other.id)
        print("new_other_position")
        print(new_other_position)
        # null out both values to prevent a db constraint error on save()
        self.req_order = None
        self.save()
        other.req_order = None
        other.save()
        # set new positions
        self.req_order = new_self_position
        self.save()
        other.req_order = new_other_position
        other.save()

    @property
    def requirement(self):
        return (
            self.standard_requirement.text if self.standard else self.free_requirement
        )

    def can_referral_edit(self, user):
        if self.proposal.processing_status == "with_referral":
            if self.referral_group:
                group = ReferralRecipientGroup.objects.filter(id=self.referral_group.id)
                # user=request.user
                if group and group[0] in user.referralrecipientgroup_set.all():
                    return True
                else:
                    return False
        return False

    def can_district_assessor_edit(self, user):
        allowed_status = [
            "with_district_assessor",
            "partially_approved",
            "partially_declined",
        ]
        if (
            self.district_proposal
            and self.district_proposal.processing_status == "with_assessor_conditions"
            and self.proposal.processing_status in allowed_status
        ):
            if self.district_proposal.can_process_requirements(user):
                return True
        return False

    def add_documents(self, request):
        with transaction.atomic():
            try:
                # save the files
                data = json.loads(request.data.get("data"))
                if not data.get("update"):
                    documents_qs = self.requirement_documents.filter(
                        input_name="requirement_doc", visible=True
                    )
                    documents_qs.delete()
                for idx in range(data["num_files"]):
                    _file = request.data.get("file-" + str(idx))
                    document = self.requirement_documents.create(
                        _file=_file, name=_file.name
                    )
                    document.input_name = data["input_name"]
                    document.can_delete = True
                    document.save()
                # end save documents
                self.save()
            except:
                raise
        return


class SectionChecklist(RevisionedMixin):
    """
    This object is per section per type(assessor/referral) grouping the ChecklistQuestion objects
    """

    SECTION_MAP = "map"
    SECTION_PROPOSAL_DETAILS = "proposal_details"
    SECTION_PROPOSAL_IMPACT = "proposal_impact"
    SECTION_OTHER = "other"
    SECTION_DEED_POLL = "deed_poll"
    SECTION_ADDITIONAL_DOCUMENTS = "additional_documents"
    SECTION_CHOICES = (
        (SECTION_MAP, "Map"),
        (SECTION_PROPOSAL_DETAILS, "Proposal Details"),
        (SECTION_PROPOSAL_IMPACT, "Proposal Impact"),
        (SECTION_OTHER, "Other"),
        (SECTION_DEED_POLL, "Deed Poll"),
        (SECTION_ADDITIONAL_DOCUMENTS, "Additional Documents"),
    )
    LIST_TYPE_ASSESSOR = "assessor_list"
    LIST_TYPE_REFERRAL = "referral_list"
    LIST_TYPE_CHOICES = (
        (LIST_TYPE_ASSESSOR, "Assessor Checklist"),
        (LIST_TYPE_REFERRAL, "Referral Checklist"),
    )

    application_type = models.ForeignKey(
        ApplicationType, blank=True, null=True, on_delete=models.SET_NULL
    )
    section = models.CharField(
        "Section", max_length=50, choices=SECTION_CHOICES, default=SECTION_CHOICES[0][0]
    )
    list_type = models.CharField(
        "Checklist type",
        max_length=30,
        choices=LIST_TYPE_CHOICES,
        default=LIST_TYPE_CHOICES[0][0],
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Section Questions"
        verbose_name_plural = "Section Questions"

    def __str__(self):
        return "Questions for {}:".format(self.get_section_display())

    @property
    def number_of_questions(self):
        return "{}/{}".format(
            self.number_of_enabled_questions, self.number_of_total_questions
        )

    @property
    def number_of_total_questions(self):
        return (
            self.questions.count() if self.questions else 0
        )  # 'questions' is a related_name of ChecklistQuestion

    @property
    def number_of_enabled_questions(self):
        return (
            self.questions.filter(enabled=True).count()
            if self.questions and self.questions.filter(enabled=True)
            else 0
        )  # 'questions' is a related_name of ChecklistQuestion


class ChecklistQuestion(RevisionedMixin):
    TYPE_CHOICES = (
        ("assessor_list", "Assessor Checklist"),
        ("referral_list", "Referral Checklist"),
    )
    ANSWER_TYPE_CHOICES = (("yes_no", "Yes/No type"), ("free_text", "Free text type"))
    text = models.TextField()  # This is question text
    answer_type = models.CharField(
        "Answer type",
        max_length=30,
        choices=ANSWER_TYPE_CHOICES,
        default=ANSWER_TYPE_CHOICES[0][0],
    )
    enabled = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=1)
    section_checklist = models.ForeignKey(
        SectionChecklist,
        blank=True,
        null=True,
        related_name="questions",
        on_delete=models.SET_NULL,
    )
    shown_to_others = models.BooleanField(
        "Comment", default=False, help_text="When checked, question is shown to others"
    )  # When True, this QA is shown to other parties.  Of course not editable, though.

    def __str__(self):
        return self.text

    class Meta:
        app_label = "licensing_template"
        ordering = [
            "order",
        ]


class ProposalAssessment(RevisionedMixin):
    proposal = models.ForeignKey(
        Proposal, related_name="assessment", on_delete=models.CASCADE
    )
    completed = models.BooleanField(default=False)
    submitter = models.IntegerField(blank=True, null=True)  # EmailUserRO
    referral = models.ForeignKey(
        Referral,
        related_name="assessment",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )  # When referral is none, this ProposalAssessment is for assessor.

    class Meta:
        app_label = "licensing_template"

    @property
    def checklist(self):
        return self.answers.all()

    @property
    def referral_assessment(self):
        # When referral exists, self is for referral otherwise for assessor
        return True if self.referral else False


class ProposalAssessmentAnswer(RevisionedMixin):
    checklist_question = models.ForeignKey(
        ChecklistQuestion, related_name="answers", on_delete=models.CASCADE
    )
    answer_yes_no = models.BooleanField(null=True)
    proposal_assessment = models.ForeignKey(
        ProposalAssessment,
        related_name="answers",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    answer_text = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.checklist_question.text

    @property
    def shown_to_others(self):
        return self.checklist_question.shown_to_others

    class Meta:
        app_label = "licensing_template"
        verbose_name = "Assessment answer"
        verbose_name_plural = "Assessment answers"


class QAOfficerReferral(RevisionedMixin):
    SENT_CHOICES = ((1, "Sent From Assessor"), (2, "Sent From Referral"))
    PROCESSING_STATUS_CHOICES = (
        ("with_qaofficer", "Awaiting"),
        ("recalled", "Recalled"),
        ("completed", "Completed"),
    )
    lodged_on = models.DateTimeField(auto_now_add=True)
    proposal = models.ForeignKey(
        Proposal, related_name="qaofficer_referrals", on_delete=models.CASCADE
    )
    # sent_by = models.ForeignKey(EmailUser,related_name='assessor_qaofficer_referrals', on_delete=models.CASCADE)
    sent_by = models.IntegerField()  # EmailUserRO
    # qaofficer = models.ForeignKey(EmailUser, null=True, blank=True, related_name='qaofficers', on_delete=models.SET_NULL)
    qaofficer = models.IntegerField()  # EmailUserRO
    qaofficer_group = models.ForeignKey(
        QAOfficerGroup,
        null=True,
        blank=True,
        related_name="qaofficer_groups",
        on_delete=models.SET_NULL,
    )
    linked = models.BooleanField(default=False)
    sent_from = models.SmallIntegerField(
        choices=SENT_CHOICES, default=SENT_CHOICES[0][0]
    )
    processing_status = models.CharField(
        "Processing Status",
        max_length=30,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    text = models.TextField(blank=True)  # Assessor text
    qaofficer_text = models.TextField(blank=True)
    document = models.ForeignKey(
        QAOfficerDocument,
        blank=True,
        null=True,
        related_name="qaofficer_referral_document",
        on_delete=models.SET_NULL,
    )

    class Meta:
        app_label = "licensing_template"
        ordering = ("-lodged_on",)

    def __str__(self):
        return "Application {} - QA Officer referral {}".format(
            self.proposal.id, self.id
        )

    # Methods
    @property
    def latest_qaofficer_referrals(self):
        return QAOfficer.objects.filter(sent_by=self.qaofficer, proposal=self.proposal)[
            :2
        ]

    # Properties
    @property
    def title(self):
        return self.proposal.title

    @property
    def applicant(self):
        return self.proposal.applicant.name

    @property
    def can_be_processed(self):
        return self.processing_status == "with_qa_officer"

    def can_asses(self):
        return self.can_be_processed and self.proposal.is_qa_officer()


# @receiver(pre_delete, sender=Proposal)
# def delete_documents(sender, instance, *args, **kwargs):
#    for document in instance.documents.all():
#        document.delete()


def clone_proposal_with_status_reset(original_proposal):
    with transaction.atomic():
        try:
            proposal = Proposal.objects.create(
                application_type=ApplicationType.objects.get(name="lease_licence"),
                ind_applicant=original_proposal.ind_applicant,
                org_applicant=original_proposal.org_applicant,
                previous_application=original_proposal,
                approval=original_proposal.approval,
            )
            # proposal.save(no_revision=True)
            return proposal
        except:
            raise


def clone_documents(proposal, original_proposal, media_prefix):
    for proposal_document in ProposalDocument.objects.filter(proposal_id=proposal.id):
        proposal_document._file.name = "{}/proposals/{}/documents/{}".format(
            settings.MEDIA_APP_DIR, proposal.id, proposal_document.name
        )
        proposal_document.can_delete = True
        proposal_document.save()

    for proposal_required_document in ProposalRequiredDocument.objects.filter(
        proposal_id=proposal.id
    ):
        proposal_required_document._file.name = (
            "{}/proposals/{}/required_documents/{}".format(
                settings.MEDIA_APP_DIR, proposal.id, proposal_required_document.name
            )
        )
        proposal_required_document.can_delete = True
        proposal_required_document.save()

    for referral in proposal.referrals.all():
        for referral_document in ReferralDocument.objects.filter(referral=referral):
            referral_document._file.name = "{}/proposals/{}/referral/{}".format(
                settings.MEDIA_APP_DIR, proposal.id, referral_document.name
            )
            referral_document.can_delete = True
            referral_document.save()

    for qa_officer_document in QAOfficerDocument.objects.filter(
        proposal_id=proposal.id
    ):
        qa_officer_document._file.name = "{}/proposals/{}/qaofficer/{}".format(
            settings.MEDIA_APP_DIR, proposal.id, qa_officer_document.name
        )
        qa_officer_document.can_delete = True
        qa_officer_document.save()

    for onhold_document in OnHoldDocument.objects.filter(proposal_id=proposal.id):
        onhold_document._file.name = "{}/proposals/{}/on_hold/{}".format(
            settings.MEDIA_APP_DIR, proposal.id, onhold_document.name
        )
        onhold_document.can_delete = True
        onhold_document.save()

    for requirement in proposal.requirements.all():
        for requirement_document in RequirementDocument.objects.filter(
            requirement=requirement
        ):
            requirement_document._file.name = (
                "{}/proposals/{}/requirement_documents/{}".format(
                    settings.MEDIA_APP_DIR, proposal.id, requirement_document.name
                )
            )
            requirement_document.can_delete = True
            requirement_document.save()

    for log_entry_document in ProposalLogDocument.objects.filter(
        log_entry__proposal_id=proposal.id
    ):
        log_entry_document._file.name = log_entry_document._file.name.replace(
            str(original_proposal.id), str(proposal.id)
        )
        log_entry_document.can_delete = True
        log_entry_document.save()

    # copy documents on file system and reset can_delete flag
    media_dir = "{}/{}".format(media_prefix, settings.MEDIA_APP_DIR)
    subprocess.call(
        "cp -pr {0}/proposals/{1} {0}/proposals/{2}".format(
            media_dir, original_proposal.id, proposal.id
        ),
        shell=True,
    )


def _clone_documents(proposal, original_proposal, media_prefix):
    for proposal_document in ProposalDocument.objects.filter(
        proposal=original_proposal.id
    ):
        proposal_document.proposal = proposal
        proposal_document.id = None
        proposal_document._file.name = "{}/proposals/{}/documents/{}".format(
            settings.MEDIA_APP_DIR, proposal.id, proposal_document.name
        )
        proposal_document.can_delete = True
        proposal_document.save()

    for proposal_required_document in ProposalRequiredDocument.objects.filter(
        proposal=original_proposal.id
    ):
        proposal_required_document.proposal = proposal
        proposal_required_document.id = None
        proposal_required_document._file.name = (
            "{}/proposals/{}/required_documents/{}".format(
                settings.MEDIA_APP_DIR, proposal.id, proposal_required_document.name
            )
        )
        proposal_required_document.can_delete = True
        proposal_required_document.save()

    # copy documents on file system and reset can_delete flag
    media_dir = "{}/{}".format(media_prefix, settings.MEDIA_APP_DIR)
    subprocess.call(
        "cp -pr {0}/proposals/{1} {0}/proposals/{2}".format(
            media_dir, original_proposal.id, proposal.id
        ),
        shell=True,
    )


def _clone_requirement_documents(proposal, original_proposal, media_prefix):
    for proposal_required_document in ProposalRequiredDocument.objects.filter(
        proposal=original_proposal.id
    ):
        proposal_required_document.proposal = proposal
        proposal_required_document.id = None
        proposal_required_document._file.name = (
            "{}/proposals/{}/required_documents/{}".format(
                settings.MEDIA_APP_DIR, proposal.id, proposal_required_document.name
            )
        )
        proposal_required_document.can_delete = True
        proposal_required_document.save()

    # copy documents on file system and reset can_delete flag
    media_dir = "{}/{}".format(media_prefix, settings.MEDIA_APP_DIR)
    subprocess.call(
        "cp -pr {0}/proposals/{1} {0}/proposals/{2}".format(
            media_dir, original_proposal.id, proposal.id
        ),
        shell=True,
    )


def duplicate_object(self):
    """
    Duplicate a model instance, making copies of all foreign keys pointing to it.
    There are 3 steps that need to occur in order:

        1.  Enumerate the related child objects and m2m relations, saving in lists/dicts
        2.  Copy the parent object per django docs (doesn't copy relations)
        3a. Copy the child objects, relating to the copied parent object
        3b. Re-create the m2m relations on the copied parent object

    """
    related_objects_to_copy = []
    relations_to_set = {}
    # Iterate through all the fields in the parent object looking for related fields
    for field in self._meta.get_fields():
        if field.name in ["proposal", "approval"]:
            print("Continuing ...")
            pass
        elif field.one_to_many:
            # One to many fields are backward relationships where many child objects are related to the
            # parent (i.e. SelectedPhrases). Enumerate them and save a list so we can copy them after
            # duplicating our parent object.
            print("Found a one-to-many field: {}".format(field.name))

            # 'field' is a ManyToOneRel which is not iterable, we need to get the object attribute itself
            related_object_manager = getattr(self, field.name)
            related_objects = list(related_object_manager.all())
            if related_objects:
                print(" - {len(related_objects)} related objects to copy")
                related_objects_to_copy += related_objects

        elif field.many_to_one:
            # In testing so far, these relationships are preserved when the parent object is copied,
            # so they don't need to be copied separately.
            print("Found a many-to-one field: {}".format(field.name))

        elif field.many_to_many:
            # Many to many fields are relationships where many parent objects can be related to many
            # child objects. Because of this the child objects don't need to be copied when we copy
            # the parent, we just need to re-create the relationship to them on the copied parent.
            print("Found a many-to-many field: {}".format(field.name))
            related_object_manager = getattr(self, field.name)
            relations = list(related_object_manager.all())
            if relations:
                print(" - {} relations to set".format(len(relations)))
                relations_to_set[field.name] = relations

    # Duplicate the parent object
    self.pk = None
    self.lodgement_number = ""
    self.save()
    print("Copied parent object {}".format(str(self)))

    # Copy the one-to-many child objects and relate them to the copied parent
    for related_object in related_objects_to_copy:
        # Iterate through the fields in the related object to find the one that relates to the
        # parent model (I feel like there might be an easier way to get at this).
        for related_object_field in related_object._meta.fields:
            if related_object_field.related_model == self.__class__:
                # If the related_model on this field matches the parent object's class, perform the
                # copy of the child object and set this field to the parent object, creating the
                # new child -> parent relationship.
                related_object.pk = None
                # if related_object_field.name=='approvals':
                #    related_object.lodgement_number = None
                ##if isinstance(related_object, Approval):
                ##    related_object.lodgement_number = ''

                setattr(related_object, related_object_field.name, self)
                print(related_object_field)
                try:
                    related_object.save()
                except Exception as e:
                    logger.warn(e)

                text = str(related_object)
                text = (text[:40] + "..") if len(text) > 40 else text
                print("|- Copied child object {}".format(text))

    # Set the many-to-many relations on the copied parent
    for field_name, relations in relations_to_set.items():
        # Get the field by name and set the relations, creating the new relationships
        field = getattr(self, field_name)
        field.set(relations)
        text_relations = []
        for relation in relations:
            text_relations.append(str(relation))
        print(
            "|- Set {} many-to-many relations on {} {}".format(
                len(relations), field_name, text_relations
            )
        )

    return self


def searchKeyWords(
    searchWords, searchProposal, searchApproval, searchCompliance, is_internal=True
):
    from licensing_template.utils import search, search_approval, search_compliance
    from licensing_template.components.approvals.models import Approval
    from licensing_template.components.compliances.models import Compliance

    qs = []
    application_types = [
        ApplicationType.TCLASS,
        ApplicationType.EVENT,
        ApplicationType.FILMING,
    ]
    if is_internal:
        # proposal_list = Proposal.objects.filter(application_type__name='T Class').exclude(processing_status__in=['discarded','draft'])
        proposal_list = Proposal.objects.filter(
            application_type__name__in=application_types
        ).exclude(processing_status__in=["discarded", "draft"])
        approval_list = (
            Approval.objects.all()
            .order_by("lodgement_number", "-issue_date")
            .distinct("lodgement_number")
        )
        compliance_list = Compliance.objects.all()
    if searchWords:
        if searchProposal:
            for p in proposal_list:
                # if p.data:
                if p.search_data:
                    try:
                        # results = search(p.data[0], searchWords)
                        results = search(p.search_data, searchWords)
                        final_results = {}
                        if results:
                            for r in results:
                                for key, value in r.items():
                                    final_results.update({"key": key, "value": value})
                            res = {
                                "number": p.lodgement_number,
                                "id": p.id,
                                "type": "Proposal",
                                "applicant": p.applicant,
                                "text": final_results,
                            }
                            qs.append(res)
                    except:
                        raise
        if searchApproval:
            for a in approval_list:
                try:
                    results = search_approval(a, searchWords)
                    qs.extend(results)
                except:
                    raise
        if searchCompliance:
            for c in compliance_list:
                try:
                    results = search_compliance(c, searchWords)
                    qs.extend(results)
                except:
                    raise
    return qs


def search_reference(reference_number):
    from licensing_template.components.approvals.models import Approval
    from licensing_template.components.compliances.models import Compliance

    proposal_list = Proposal.objects.all().exclude(processing_status__in=["discarded"])
    approval_list = (
        Approval.objects.all()
        .order_by("lodgement_number", "-issue_date")
        .distinct("lodgement_number")
    )
    compliance_list = Compliance.objects.all().exclude(processing_status__in=["future"])
    record = {}
    try:
        result = proposal_list.get(lodgement_number=reference_number)
        record = {"id": result.id, "type": "proposal"}
    except Proposal.DoesNotExist:
        try:
            result = approval_list.get(lodgement_number=reference_number)
            record = {"id": result.id, "type": "approval"}
        except Approval.DoesNotExist:
            try:
                for c in compliance_list:
                    if c.reference == reference_number:
                        record = {"id": c.id, "type": "compliance"}
            except:
                raise ValidationError(
                    "Record with provided reference number does not exist"
                )
    if record:
        return record
    else:
        raise ValidationError("Record with provided reference number does not exist")


from ckeditor.fields import RichTextField


class HelpPage(models.Model):
    HELP_TEXT_EXTERNAL = 1
    HELP_TEXT_INTERNAL = 2
    HELP_TYPE_CHOICES = (
        (HELP_TEXT_EXTERNAL, "External"),
        (HELP_TEXT_INTERNAL, "Internal"),
    )

    application_type = models.ForeignKey(
        ApplicationType, null=True, on_delete=models.SET_NULL
    )
    content = RichTextField()
    description = models.CharField(max_length=256, blank=True, null=True)
    help_type = models.SmallIntegerField(
        "Help Type", choices=HELP_TYPE_CHOICES, default=HELP_TEXT_EXTERNAL
    )
    version = models.SmallIntegerField(default=1, blank=False, null=False)

    class Meta:
        app_label = "licensing_template"
        unique_together = ("application_type", "help_type", "version")
