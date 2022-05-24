import traceback
import os
import datetime
import base64
import geojson
from six.moves.urllib.parse import urlparse
from wsgiref.util import FileWrapper
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics, views
from rest_framework.decorators import action as detail_route, renderer_classes
from rest_framework.decorators import action as list_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAdminUser,
    BasePermission,
)
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from collections import OrderedDict
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from ledger_api_client.country_models import Country
from datetime import datetime, timedelta, date
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from licensing_template.components.proposals.models import Proposal, ApplicationType
from licensing_template.components.bookings.models import (
    Booking,
    BookingInvoice,
)
from licensing_template.components.bookings.serializers import (
    BookingSerializer,
    OverdueBookingInvoiceSerializer,
    #    BookingSerializer2,
    #    ParkBookingSerializer2,
)
from licensing_template.helpers import is_customer, is_internal
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from licensing_template.components.proposals.api import (
    ProposalFilterBackend,
    ProposalRenderer,
)


class BookingPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (ProposalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ProposalRenderer,)
    page_size = 10
    queryset = Booking.objects.none()
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Booking.objects.all().exclude(
                booking_type=Booking.BOOKING_TYPE_TEMPORARY
            )
        elif is_customer(self.request):
            user_orgs = [org.id for org in user.licensing_template_organisations.all()]
            return Booking.objects.filter(
                Q(proposal__org_applicant_id__in=user_orgs)
                | Q(proposal__submitter=user)
            ).exclude(booking_type=Booking.BOOKING_TYPE_TEMPORARY)
        return Booking.objects.none()

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def bookings_external(self, request, *args, **kwargs):
        """
        Paginated serializer for datatables - used by the internal and external dashboard (filtered by the get_queryset method)

        To test:
            http://localhost:8000/api/booking_paginated/bookings_external/?format=datatables&draw=1&length=2
        """

        qs = self.get_queryset()
        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = BookingSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.none()
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return Booking.objects.all().exclude(
                booking_type=Booking.BOOKING_TYPE_TEMPORARY
            )
        elif is_customer(self.request):
            user_orgs = [org.id for org in user.licensing_template_organisations.all()]
            return Booking.objects.filter(
                Q(proposal__org_applicant_id__in=user_orgs)
                | Q(proposal__submitter=user)
            ).exclude(booking_type=Booking.BOOKING_TYPE_TEMPORARY)
        return Booking.objects.none()


class OverdueBookingInvoiceViewSet(viewsets.ModelViewSet):
    queryset = BookingInvoice.objects.none()
    serializer_class = OverdueBookingInvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            bi = BookingInvoice.objects.all().exclude(
                booking__booking_type=Booking.BOOKING_TYPE_TEMPORARY
            )
            return [inv for inv in bi if inv.overdue]
        elif is_customer(self.request):
            user_orgs = [org.id for org in user.licensing_template_organisations.all()]
            bi = BookingInvoice.objects.filter(
                Q(booking__proposal__org_applicant_id__in=user_orgs)
                | Q(booking__proposal__submitter=user)
            ).exclude(booking__booking_type=Booking.BOOKING_TYPE_TEMPORARY)
            return [inv for inv in bi if inv.overdue]
        return BookingInvoice.objects.none()
