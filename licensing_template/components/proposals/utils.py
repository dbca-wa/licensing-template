import re
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
import traceback
import os
from copy import deepcopy
from datetime import datetime
import time
import json
from django.contrib.gis.geos import (
    GEOSGeometry,
    GeometryCollection,
    Polygon,
    MultiPolygon,
    LinearRing,
)
from django.contrib.gis.gdal import SpatialReference
from licensing_template.components.main.utils import get_dbca_lands_and_waters_geos

# from preserialize.serialize import serialize
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Invoice  # , Document
from licensing_template.components.proposals.models import (
    ProposalUserAction,
    Proposal
)
from licensing_template.components.proposals import email as proposal_email


from licensing_template.components.proposals.email import (
    send_submit_email_notification,
    send_external_submit_email_notification,
)


import logging

from licensing_template.helpers import is_assessor

logger = logging.getLogger(__name__)


def save_proponent_data(instance, request, viewset, parks=None, trails=None):
    pass

