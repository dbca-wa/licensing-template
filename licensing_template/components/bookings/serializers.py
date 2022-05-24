from django.conf import settings
from django.utils import timezone
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address, Invoice
from licensing_template.components.proposals.serializers import (
    ProposalSerializer,
    InternalProposalSerializer,
    ProposalParkSerializer,
)
from licensing_template.components.main.serializers import ApplicationTypeSerializer
from licensing_template.components.bookings.models import (
    Booking,
    BookingInvoice,
)
from licensing_template.components.proposals.serializers import ProposalSerializer
from rest_framework import serializers


class BookingInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingInvoice
        fields = "invoice_reference"


class BookingSerializer(serializers.ModelSerializer):
    # park_bookings = ParkBookingSerializer(many=True, read_only=True)
    application_fee_invoice = serializers.SerializerMethodField(read_only=True)
    approval_number = serializers.SerializerMethodField(read_only=True)
    applicant = serializers.SerializerMethodField(read_only=True)
    org_applicant = serializers.SerializerMethodField(read_only=True)
    trading_name = serializers.SerializerMethodField(read_only=True)
    proxy_applicant = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    payment_method = serializers.SerializerMethodField(read_only=True)
    invoice_reference = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "admission_number",
            "application_fee_invoice",
            "approval_number",
            "applicant",
            "org_applicant",
            "trading_name",
            "proxy_applicant",
            "payment_status",
            "payment_method",
            "invoice_reference",
            #'park_bookings',
        )
        datatables_always_serialize = (
            "id",
            "admission_number",
            "application_fee_invoice",
            "approval_number",
            "applicant",
            "org_applicant",
            "trading_name",
            "proxy_applicant",
            "payment_status",
            "payment_method",
            "invoice_reference",
            #'park_bookings',
        )

    def get_application_fee_invoice(self, obj):
        return obj.proposal.fee_invoice_reference

    def get_approval_number(self, obj):
        try:
            return obj.proposal.approval.lodgement_number
        except:
            return ""

    def get_applicant(self, obj):
        try:
            return obj.proposal.approval.applicant
        except:
            return ""

    def get_org_applicant(self, obj):
        try:
            return obj.proposal.approval.org_applicant.name
        except:
            return ""

    def get_trading_name(self, obj):
        try:
            return obj.proposal.approval.org_applicant.organisation.trading_name
        except:
            return ""

    def get_proxy_applicant(self, obj):
        try:
            return obj.proposal.approval.proxy_applicant
        except:
            return ""

    def get_invoice_reference(self, obj):
        if obj and obj.invoices.last():
            return obj.invoices.last().invoice_reference
        return None

    def get_overdue(self, obj):
        if obj and obj.invoices.last():
            bi = obj.invoices.last()
            return bi.overdue
        return None

    def get_payment_status(self, obj):
        try:
            return obj.invoices.last().payment_status
        except:
            return "Unpaid"

    def get_payment_method(self, obj):
        if obj and obj.invoices.last():
            inv = obj.invoices.last()
            return Invoice.objects.get(
                reference=inv.invoice_reference
            ).get_payment_method_display()
        else:
            # if no invoice exists, likely this is booking is for monthly_invoicing
            return obj.get_booking_type_display()


class OverdueBookingInvoiceSerializer(serializers.ModelSerializer):
    invoice_reference = serializers.SerializerMethodField(read_only=True)
    overdue = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BookingInvoice
        fields = (
            "id",
            "invoice_reference",
            "overdue",
        )

    def get_invoice_reference(self, obj):
        if obj and obj.booking.invoices.last():
            return obj.booking.invoices.last().invoice_reference
        return None

    def get_overdue(self, obj):
        if obj and obj.booking.invoices.last():
            bi = obj.booking.invoices.last()
            return bi.overdue
        return None


class DTBookingSerializer(serializers.ModelSerializer):
    # park_bookings = ParkBookingSerializer(many=True, read_only=True)
    application_fee_invoice = serializers.SerializerMethodField(read_only=True)
    approval_number = serializers.SerializerMethodField(read_only=True)
    applicant = serializers.SerializerMethodField(read_only=True)
    org_applicant = serializers.SerializerMethodField(read_only=True)
    trading_name = serializers.SerializerMethodField(read_only=True)
    proxy_applicant = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    payment_method = serializers.SerializerMethodField(read_only=True)
    invoice_reference = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "admission_number",
            "application_fee_invoice",
            "approval_number",
            "applicant",
            "org_applicant",
            "trading_name",
            "proxy_applicant",
            "payment_status",
            "payment_method",
            "invoice_reference",
        )
        datatables_always_serialize = (
            "id",
            "admission_number",
            "application_fee_invoice",
            "approval_number",
            "applicant",
            "org_applicant",
            "trading_name",
            "proxy_applicant",
            "payment_status",
            "payment_method",
            "invoice_reference",
        )

    def get_application_fee_invoice(self, obj):
        return obj.proposal.fee_invoice_reference

    def get_approval_number(self, obj):
        try:
            return obj.proposal.approval.lodgement_number
        except:
            return ""

    def get_applicant(self, obj):
        try:
            return obj.proposal.approval.applicant
        except:
            return ""

    def get_org_applicant(self, obj):
        try:
            return obj.proposal.approval.org_applicant.name
        except:
            return ""

    def get_trading_name(self, obj):
        try:
            return obj.proposal.approval.org_applicant.organisation.trading_name
        except:
            return ""

    def get_proxy_applicant(self, obj):
        try:
            return obj.proposal.approval.proxy_applicant
        except:
            return ""

    def get_invoice_reference(self, obj):
        if obj and obj.invoices.last():
            return obj.invoices.last().invoice_reference
        return None

    def get_overdue(self, obj):
        if obj and obj.invoices.last():
            bi = obj.invoices.last()
            return bi.overdue
        return None

    def get_payment_status(self, obj):
        try:
            return obj.invoices.last().payment_status
        except:
            return "Unpaid"

    def get_payment_method(self, obj):
        if obj and obj.invoices.last():
            inv = obj.invoices.last()
            return Invoice.objects.get(
                reference=inv.invoice_reference
            ).get_payment_method_display()
        else:
            # if no invoice exists, likely this is booking is for monthly_invoicing
            return obj.get_booking_type_display()
