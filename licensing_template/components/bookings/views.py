from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.views.generic.base import View, TemplateView
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.exceptions import PermissionDenied

from datetime import datetime, timedelta, date
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from licensing_template.components.proposals.models import Proposal
from licensing_template.components.compliances.models import Compliance
from licensing_template.components.main.models import ApplicationType
from licensing_template.components.organisations.models import Organisation
from licensing_template.components.bookings.context_processors import (
    licensing_template_url,
    template_context,
)
from licensing_template.components.bookings.invoice_pdf import create_invoice_pdf_bytes
from licensing_template.components.bookings.invoice_compliance_pdf import (
    create_invoice_compliance_pdf_bytes,
)
from licensing_template.components.bookings.confirmation_pdf import (
    create_confirmation_pdf_bytes,
)
from licensing_template.components.bookings.monthly_confirmation_pdf import (
    create_monthly_confirmation_pdf_bytes,
)
from licensing_template.components.bookings.awaiting_payment_invoice_pdf import (
    create_awaiting_payment_invoice_pdf_bytes,
)
from licensing_template.components.bookings.email import (
    send_invoice_tclass_email_notification,
    send_confirmation_tclass_email_notification,
    send_application_fee_invoice_tclass_email_notification,
    send_application_fee_confirmation_tclass_email_notification,
    send_compliance_fee_invoice_events_email_notification,
    send_application_invoice_filming_email_notification,
)
from licensing_template.components.bookings.utils import (
    create_booking,
    get_session_booking,
    set_session_booking,
    delete_session_booking,
    create_lines,
    checkout,
    checkout_existing_invoice,
    create_fee_lines,
    create_compliance_fee_lines,
    get_session_application_invoice,
    set_session_application_invoice,
    delete_session_application_invoice,
    get_session_compliance_invoice,
    set_session_compliance_invoice,
    delete_session_compliance_invoice,
    get_session_filming_invoice,
    set_session_filming_invoice,
    delete_session_filming_invoice,
    calc_payment_due_date,
    create_bpay_invoice,
    create_other_invoice,
    create_monthly_confirmation,
    get_basket,
    redirect_to_zero_payment_view,
)
from licensing_template.components.bookings.models import (
    Booking,
    BookingInvoice,
    ApplicationFee,
    ApplicationFeeInvoice,
    ComplianceFee,
    ComplianceFeeInvoice,
)
from licensing_template.components.proposals.serializers import ProposalSerializer

# from ledger_api_client.utils import create_basket_session, create_checkout_session, place_order_submission, get_cookie_basket, createCustomBasket
from ledger_api_client.utils import (
    create_basket_session,
    create_checkout_session,
    oracle_parser,
)

# from ledger.payments.utils import oracle_parser_on_invoice,update_payments
# from ledger.payments.invoice.utils import CreateInvoiceBasket
import json
from decimal import Decimal
from collections import OrderedDict

from ledger_api_client.ledger_models import Invoice
from ledger_api_client.order import Order

# from ledger.basket.models import Basket
# from ledger.payments.mixins import InvoiceOwnerMixin
# from oscar.apps.order.models import Order
from licensing_template.helpers import (
    is_internal,
    is_licensing_template_admin,
    is_in_organisation_contacts,
)

# from ledger.payments.helpers import is_payment_admin

import logging

logger = logging.getLogger("payment_checkout")


class ApplicationFeeView(TemplateView):
    # template_name = 'licensing_template/booking/preview.html'
    template_name = ""  #'licensing_template/booking/preview_deferred.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs["proposal_pk"])

    def post(self, request, *args, **kwargs):

        try:
            proposal = self.get_object()
            application_fee = ApplicationFee.objects.create(
                proposal=proposal,
                created_by=request.user,
                payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY,
            )

            with transaction.atomic():
                lines = create_fee_lines(proposal)

                set_session_application_invoice(request.session, application_fee)
                checkout_response = checkout(
                    request,
                    proposal,
                    lines,
                    return_url_ns="fee_success",
                    return_preload_url_ns="fee_success",
                    invoice_text="Application Fee",
                )

                if proposal.allow_full_discount:
                    return redirect_to_zero_payment_view(request, proposal, lines)

                logger.info(
                    "{} built payment line item {} for Application Fee and handing over to payment gateway".format(
                        "User {} with id {}".format(
                            proposal.submitter.get_full_name(), proposal.submitter.id
                        ),
                        proposal.id,
                    )
                )
                return checkout_response

        except Exception as e:
            logger.error("Error Creating Application Fee: {}".format(e))
            if application_fee:
                application_fee.delete()
            raise


class ComplianceFeeView(TemplateView):
    template_name = "licensing_template/booking/success.html"

    def get_object(self):
        return get_object_or_404(Compliance, id=self.kwargs["compliance_pk"])

    def post(self, request, *args, **kwargs):

        compliance = self.get_object()
        compliance_fee = ComplianceFee.objects.create(
            compliance=compliance,
            created_by=request.user,
            payment_type=ComplianceFee.PAYMENT_TYPE_TEMPORARY,
        )

        try:
            with transaction.atomic():
                set_session_compliance_invoice(request.session, compliance_fee)
                lines = create_compliance_fee_lines(compliance)
                checkout_response = checkout(
                    request,
                    compliance.proposal,
                    lines,
                    return_url_ns="compliance_fee_success",
                    return_preload_url_ns="compliance_fee_success",
                    # invoice_text='Compliance Fee ({} - {})'.format(compliance.proposal.event_activity.commencement_date, compliance.proposal.event_activity.completion_date)
                    invoice_text="Per participant licence charge",
                )

                logger.info(
                    "{} built payment line item {} for Compliance Fee and handing over to payment gateway".format(
                        "User {} with id {}".format(
                            compliance.proposal.submitter.get_full_name(),
                            compliance.proposal.submitter.id,
                        ),
                        compliance.id,
                    )
                )
                return checkout_response

        except Exception as e:
            logger.error("Error Creating Compliance Fee: {}".format(e))
            if compliance_fee:
                compliance_fee.delete()
            raise


class FilmingFeeView(TemplateView):
    template_name = "licensing_template/booking/success.html"

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs["proposal_pk"])

    def get(self, request, *args, **kwargs):

        proposal = self.get_object()
        # filming_fee = FilmingFee.objects.create(proposal=proposal, created_by=request.user, payment_type=FilmingFee.PAYMENT_TYPE_TEMPORARY)
        filming_fee = proposal.filming_fees.order_by("-id").first()
        inv_ref = (
            filming_fee.filming_fee_invoices.order_by("-id").first().invoice_reference
        )

        try:
            with transaction.atomic():
                set_session_filming_invoice(request.session, filming_fee)
                # lines = create_filming_fee_lines(proposal)
                lines = filming_fee.lines
                invoice = Invoice.objects.get(reference=inv_ref)

                film_types = "/".join(
                    [
                        w.capitalize().replace("_", " ")
                        for w in proposal.filming_activity.film_type
                    ]
                )
                # invoice_text = 'Payment Invoice: {} - {}'.format(film_types, self.filming_activity.activity_title)
                invoice_text = "Payment Invoice: {}".format(film_types)

                checkout_response = checkout_existing_invoice(
                    request,
                    invoice,
                    lines,
                    return_url_ns="filming_fee_success",
                    return_preload_url_ns="filming_fee_success",
                    invoice_text=invoice_text,
                )

                logger.info(
                    "{} built payment line item {} for Proposal Fee and handing over to payment gateway".format(
                        "User {} with id {}".format(
                            proposal.submitter.get_full_name(), proposal.submitter.id
                        ),
                        proposal.id,
                    )
                )
                return checkout_response

        except Exception as e:
            logger.error("Error Creating Proposal Fee: {}".format(e))
            if filming_fee:
                filming_fee.delete()
            raise


class DeferredInvoicingPreviewView(TemplateView):
    template_name = "licensing_template/booking/preview_deferred.html"

    def post(self, request, *args, **kwargs):

        payment_method = self.request.GET.get("method")
        context = template_context(self.request)
        proposal_id = int(kwargs["proposal_pk"])
        proposal = Proposal.objects.get(id=proposal_id)
        try:
            recipient = proposal.applicant.email
            submitter = proposal.applicant
        except:
            recipient = proposal.submitter.email
            submitter = proposal.submitter

        # if isinstance(proposal.org_applicant, Organisation) and (proposal.org_applicant.monthly_invoicing_allowed or proposal.org_applicant.bpay_allowed or proposal.org_applicant.other_allowed):
        if isinstance(proposal.org_applicant, Organisation) and (
            proposal.org_applicant.monthly_invoicing_allowed
            or proposal.org_applicant.bpay_allowed
            or (settings.OTHER_PAYMENT_ALLOWED and is_payment_admin(request.user))
        ):
            try:
                lines = create_lines(request)
                logger.info(
                    "{} Show Park Bookings Preview for BPAY/Other/monthly invoicing".format(
                        "User {} with id {}".format(
                            proposal.submitter.get_full_name(), proposal.submitter.id
                        ),
                        proposal.id,
                    )
                )
                context.update(
                    {
                        "lines": lines,
                        "line_details": request.POST["payment"],
                        "proposal_id": proposal_id,
                        "submitter": submitter,
                        "payment_method": payment_method,
                    }
                )
                return render(request, self.template_name, context)

            except Exception as e:
                logger.error("Error creating booking preview: {}".format(e))
        else:
            logger.error("Error creating booking preview: {}".format(e))
            raise


class DeferredInvoicingView(TemplateView):
    template_name = "licensing_template/booking/success.html"

    def post(self, request, *args, **kwargs):

        payment_method = self.request.POST.get("method")
        context = template_context(self.request)
        proposal_id = int(kwargs["proposal_pk"])
        proposal = Proposal.objects.get(id=proposal_id)
        try:
            recipient = proposal.applicant.email
            submitter = proposal.applicant
        except:
            recipient = proposal.submitter.email
            submitter = proposal.submitter

        if isinstance(proposal.org_applicant, Organisation):
            try:
                if proposal.org_applicant.bpay_allowed and payment_method == "bpay":
                    booking_type = Booking.BOOKING_TYPE_INTERNET
                elif (
                    proposal.org_applicant.monthly_invoicing_allowed
                    and payment_method == "monthly_invoicing"
                ):
                    booking_type = Booking.BOOKING_TYPE_MONTHLY_INVOICING
                # elif proposal.org_applicant.other_allowed and payment_method=='other':
                else:
                    booking_type = Booking.BOOKING_TYPE_RECEPTION

                booking = create_booking(request, proposal, booking_type=booking_type)
                invoice_reference = None
                if booking and payment_method == "bpay":
                    # BPAY/OTHER invoice are created immediately. Monthly invoices are created later by Cron
                    ret = create_bpay_invoice(submitter, booking)
                    invoice_reference = booking.invoice.reference

                if booking and payment_method == "other":
                    # BPAY/Other invoice are created immediately. Monthly invoices are created later by Cron
                    ret = create_other_invoice(submitter, booking)
                    invoice_reference = booking.invoice.reference

                if booking and payment_method == "monthly_invoicing":
                    # For monthly_invoicing, invoice is created later by Cron. Now we only create a confirmation
                    ret = create_monthly_confirmation(submitter, booking)

                logger.info(
                    "{} Created Park Bookings with payment method {} for Proposal ID {}".format(
                        "User {} with id {}".format(
                            proposal.submitter.get_full_name(), proposal.submitter.id
                        ),
                        payment_method,
                        proposal.id,
                    )
                )
                # send_monthly_invoicing_confirmation_tclass_email_notification(request, booking, invoice, recipients=[recipient])
                context.update(
                    {
                        "booking": booking,
                        "booking_id": booking.id,
                        "submitter": submitter,
                        "monthly_invoicing": True
                        if payment_method == "monthly_invoicing"
                        else False,
                        "invoice_reference": invoice_reference,
                    }
                )
                if payment_method == "other":
                    if is_payment_admin(request.user):
                        #                        if proposal.processing_status == Proposal.PROCESSING_STATUS_AWAITING_PAYMENT:
                        #                            return HttpResponseRedirect(reverse('/'))
                        #                        else:
                        #                            return HttpResponseRedirect(reverse('payments:invoice-payment') + '?invoice={}'.format(invoice_reference))
                        return HttpResponseRedirect(
                            reverse("payments:invoice-payment")
                            + "?invoice={}".format(invoice_reference)
                        )
                    else:
                        raise PermissionDenied
                else:
                    return render(request, self.template_name, context)

            except Exception as e:
                logger.error("Error Creating booking: {}".format(e))
                if booking:
                    booking.delete()
                raise
        else:
            logger.error("Error Creating booking: {}".format(e))
            raise


class MakePaymentView(TemplateView):
    # template_name = 'mooring/booking/make_booking.html'
    template_name = "licensing_template/booking/success.html"

    def post(self, request, *args, **kwargs):

        proposal_id = int(kwargs["proposal_pk"])
        proposal = Proposal.objects.get(id=proposal_id)

        try:
            booking = create_booking(
                request, proposal, booking_type=Booking.BOOKING_TYPE_TEMPORARY
            )
            with transaction.atomic():
                set_session_booking(request.session, booking)
                # lines = create_lines(request)
                checkout_response = checkout(
                    request,
                    proposal,
                    # lines,
                    booking.as_line_items,
                    return_url_ns="public_booking_success",
                    return_preload_url_ns="public_booking_success",
                    invoice_text="Payment Invoice",
                )

                logger.info(
                    "{} built payment line items {} for Park Bookings and handing over to payment gateway".format(
                        "User {} with id {}".format(
                            proposal.submitter.get_full_name(), proposal.submitter.id
                        ),
                        proposal.id,
                    )
                )
                return checkout_response

        except Exception as e:
            logger.error("Error Creating booking: {}".format(e))
            if booking:
                booking.delete()
            raise


class ComplianceFeeSuccessView(TemplateView):
    template_name = "licensing_template/booking/success_compliance_fee.html"

    def get(self, request, *args, **kwargs):
        print(" COMPLIANCE FEE SUCCESS ")

        proposal = None
        compliance = None
        submitter = None
        invoice = None
        try:
            context = template_context(self.request)
            basket = None
            compliance_fee = get_session_compliance_invoice(request.session)
            compliance = compliance_fee.compliance
            proposal = compliance.proposal

            try:
                recipient = proposal.applicant.email
                submitter = proposal.applicant
            except:
                recipient = proposal.submitter.email
                submitter = proposal.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(
                    status="Submitted", owner=request.user
                ).order_by("-id")[:1]
            else:
                basket = Basket.objects.filter(
                    status="Submitted", owner=proposal.submitter
                ).order_by("-id")[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference
            fee_inv, created = ComplianceFeeInvoice.objects.get_or_create(
                compliance_fee=compliance_fee, invoice_reference=invoice_ref
            )

            if compliance_fee.payment_type == ComplianceFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error(
                        "{} tried paying an compliance fee with an incorrect invoice".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user"
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))
                if inv.system not in ["0557"]:
                    logger.error(
                        "{} tried paying an compliance fee with an invoice from another system with reference number {}".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user",
                            inv.reference,
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))

                if fee_inv:
                    # application_fee.payment_type = 1  # internet booking
                    compliance_fee.payment_type = ComplianceFee.PAYMENT_TYPE_INTERNET
                    compliance_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if proposal and (
                        invoice.payment_status == "paid"
                        or invoice.payment_status == "over_paid"
                    ):
                        compliance.submit(request)
                        compliance.fee_invoice_reference = invoice_ref
                        compliance.save()
                    else:
                        logger.error(
                            "Invoice payment status is {}".format(
                                invoice.payment_status
                            )
                        )
                        raise

                    compliance_fee.save()
                    request.session["cols_last_comp_invoice"] = compliance_fee.id
                    delete_session_compliance_invoice(request.session)

                    send_compliance_fee_invoice_events_email_notification(
                        request, compliance, invoice, recipients=[recipient]
                    )

                    context = {
                        "compliance": compliance,
                        "submitter": submitter,
                        "fee_invoice": invoice,
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            if (
                "cols_last_comp_invoice" in request.session
            ) and ComplianceFee.objects.filter(
                id=request.session["cols_last_comp_invoice"]
            ).exists():
                compliance_fee = ComplianceFee.objects.get(
                    id=request.session["cols_last_comp_invoice"]
                )
                compliance = compliance_fee.compliance
                proposal = compliance.proposal

                try:
                    recipient = proposal.applicant.email
                    submitter = proposal.applicant
                except:
                    recipient = proposal.submitter.email
                    submitter = proposal.submitter

                if (
                    ComplianceFeeInvoice.objects.filter(
                        compliance_fee=compliance_fee
                    ).count()
                    > 0
                ):
                    cfi = ComplianceFeeInvoice.objects.filter(
                        compliance_fee=compliance_fee
                    )
                    invoice = cfi[0]
            else:
                return redirect("home")

        context = {
            "compliance": compliance,
            "submitter": submitter,
            "fee_invoice": invoice,
        }
        return render(request, self.template_name, context)


class FilmingFeeSuccessView(TemplateView):
    template_name = "licensing_template/booking/success_fee.html"

    def get(self, request, *args, **kwargs):
        print(" FILMING FEE SUCCESS ")

        proposal = None
        submitter = None
        inv = None
        try:
            context = template_context(self.request)
            basket = None
            filming_fee = get_session_filming_invoice(request.session)
            fee_inv = filming_fee.filming_fee_invoices.order_by("-id").first()
            invoice_ref = fee_inv.invoice_reference
            proposal = filming_fee.proposal

            try:
                recipient = proposal.applicant.email
                submitter = proposal.applicant
            except:
                recipient = proposal.submitter.email
                submitter = proposal.submitter

            inv = Invoice.objects.get(reference=invoice_ref)
            if filming_fee.payment_type == FilmingFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    # inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error(
                        "{} tried paying an filming fee with an incorrect invoice".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user"
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))
                if inv.system not in ["0557"]:
                    logger.error(
                        "{} tried paying an filming fee with an invoice from another system with reference number {}".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user",
                            inv.reference,
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))

                if fee_inv:
                    filming_fee.payment_type = FilmingFee.PAYMENT_TYPE_INTERNET
                    filming_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if proposal and (
                        inv.payment_status == "paid"
                        or inv.payment_status == "over_paid"
                    ):
                        proposal.fee_invoice_reference = invoice_ref
                        proposal.save()
                        proposal.final_approval(request, None)
                        proposal.reset_application_discount(request.user)
                    else:
                        logger.error(
                            "Invoice payment status is {}".format(inv.payment_status)
                        )
                        raise

                    filming_fee.save()
                    request.session["cols_last_filming_invoice"] = filming_fee.id
                    delete_session_filming_invoice(request.session)

                    # NOTE: the confirmation invoice is sent from ../proposal/models/final_approval()
                    # send_application_invoice_filming_email_notification(request, proposal, invoice, recipients=[recipient])

                    context = {
                        "proposal": proposal,
                        "submitter": submitter,
                        #'fee_invoice': invoice
                        "fee_invoice": fee_inv,
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            if (
                "cols_last_filming_invoice" in request.session
            ) and FilmingFee.objects.filter(
                id=request.session["cols_last_filming_invoice"]
            ).exists():
                filming_fee = FilmingFee.objects.get(
                    id=request.session["cols_last_filming_invoice"]
                )
                proposal = filming_fee.proposal

                try:
                    recipient = proposal.applicant.email
                    submitter = proposal.applicant
                except:
                    recipient = proposal.submitter.email
                    submitter = proposal.submitter

                if (
                    FilmingFeeInvoice.objects.filter(filming_fee=filming_fee).count()
                    > 0
                ):
                    ffi = FilmingFeeInvoice.objects.filter(filming_fee=filming_fee)
                    inv = ffi[0]
            else:
                return redirect("home")

        context = {"proposal": proposal, "submitter": submitter, "fee_invoice": inv}
        return render(request, self.template_name, context)


class ZeroApplicationFeeView(TemplateView):
    template_name = "licensing_template/booking/success_fee.html"

    def post(self, request, *args, **kwargs):
        try:
            context_processor = template_context(request)
            application_fee = (
                ApplicationFee.objects.get(pk=request.session["cols_app_invoice"])
                if "cols_app_invoice" in request.session
                else None
            )
            proposal = application_fee.proposal

            try:
                recipient = proposal.applicant.email
                submitter = proposal.applicant
            except:
                recipient = proposal.submitter.email
                submitter = proposal.submitter

            if (
                request.user.is_staff
                or request.user.is_superuser
                or ApplicationFee.objects.filter(pk=application_fee.id).count() == 1
            ):
                invoice = None
                # basket = get_basket(request)
                basket = request.basket

                # here we are manually creating an order and invoice from the basket - by-passing credit card payment screen.
                ## commenting below lines and using CreateInvoiceBasket because basket created in previous view
                # order_response = place_order_submission(request)
                # order = Order.objects.get(basket=basket, user=submitter)

                order = CreateInvoiceBasket(
                    payment_method="other", system=settings.PAYMENT_SYSTEM_PREFIX
                ).create_invoice_and_order(
                    basket,
                    0,
                    None,
                    None,
                    user=request.user,
                    invoice_text="Application Fee",
                )
                invoice = Invoice.objects.get(order_number=order.number)
                fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(
                    application_fee=application_fee, invoice_reference=invoice.reference
                )

                if fee_inv:
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_ZERO
                    application_fee.expiry_time = None

                    proposal = proposal_submit(proposal, request)
                    if proposal and (
                        invoice.payment_status == "paid"
                        or invoice.payment_status == "over_paid"
                    ):
                        proposal.fee_invoice_reference = invoice.reference
                        proposal.save()
                        proposal.reset_application_discount(request.user)
                    else:
                        logger.error(
                            "Invoice payment status is {}".format(
                                invoice.payment_status
                            )
                        )
                        raise

                    application_fee.save()
                    request.session["cols_last_app_invoice"] = application_fee.id
                    delete_session_application_invoice(request.session)

                    send_application_fee_invoice_tclass_email_notification(
                        request, proposal, invoice, recipients=[recipient]
                    )

                context = {
                    "proposal": proposal,
                    "submitter": submitter,
                    "fee_invoice": fee_inv,
                    "basket": basket,
                    "lines": request.basket.lines.all(),
                    "line_details": "N/A",  # request.POST['payment'],
                    "proposal_id": proposal.id,
                    "payment_method": "N/A",
                }

                return render(request, self.template_name, context)
            else:
                return HttpResponseRedirect(reverse("home"))

        except Exception as e:
            return redirect("home")


from licensing_template.components.proposals.utils import proposal_submit


class ApplicationFeeSuccessView(TemplateView):
    template_name = "licensing_template/booking/success_fee.html"

    def get(self, request, *args, **kwargs):
        print(" APPLICATION FEE SUCCESS ")
        #        for ss in request.session.keys():
        #            print (ss)
        #            print (request.session[ss])

        proposal = None
        submitter = None
        invoice = None
        try:
            context = template_context(self.request)
            basket = None
            application_fee = get_session_application_invoice(request.session)
            proposal = application_fee.proposal

            try:
                recipient = proposal.applicant.email
                submitter = proposal.applicant
            except:
                recipient = proposal.submitter.email
                submitter = proposal.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(
                    status="Submitted", owner=request.user
                ).order_by("-id")[:1]
            else:
                basket = Basket.objects.filter(
                    status="Submitted", owner=booking.proposal.submitter
                ).order_by("-id")[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference
            fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(
                application_fee=application_fee, invoice_reference=invoice_ref
            )

            if application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                except Invoice.DoesNotExist:
                    logger.error(
                        "{} tried paying an application fee with an incorrect invoice".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user"
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))
                if inv.system not in ["0557"]:
                    logger.error(
                        "{} tried paying an application fee with an invoice from another system with reference number {}".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user",
                            inv.reference,
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))

                if fee_inv:
                    # application_fee.payment_type = 1  # internet booking
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                    application_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if (
                        proposal.processing_status
                        == Proposal.PROCESSING_STATUS_AWAITING_PAYMENT
                        and proposal.application_type.name == ApplicationType.FILMING
                    ):
                        proposal.final_approval(request, None)
                    else:
                        proposal = proposal_submit(proposal, request)

                    if proposal and (
                        invoice.payment_status == "paid"
                        or invoice.payment_status == "over_paid"
                    ):
                        proposal.fee_invoice_reference = invoice_ref
                        proposal.save()
                        proposal.reset_application_discount(request.user)
                    else:
                        logger.error(
                            "Invoice payment status is {}".format(
                                invoice.payment_status
                            )
                        )
                        raise

                    application_fee.save()

                    request.session["cols_last_app_invoice"] = application_fee.id
                    delete_session_application_invoice(request.session)

                    send_application_fee_invoice_tclass_email_notification(
                        request, proposal, invoice, recipients=[recipient]
                    )
                    # send_application_fee_confirmation_tclass_email_notification(request, application_fee, invoice, recipients=[recipient])

                    context = {
                        "proposal": proposal,
                        "submitter": submitter,
                        #'fee_invoice': invoice
                        "fee_invoice": fee_inv,
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            if (
                "cols_last_app_invoice" in request.session
            ) and ApplicationFee.objects.filter(
                id=request.session["cols_last_app_invoice"]
            ).exists():
                application_fee = ApplicationFee.objects.get(
                    id=request.session["cols_last_app_invoice"]
                )
                proposal = application_fee.proposal

                try:
                    recipient = proposal.applicant.email
                    submitter = proposal.applicant
                except:
                    recipient = proposal.submitter.email
                    submitter = proposal.submitter

                if (
                    ApplicationFeeInvoice.objects.filter(
                        application_fee=application_fee
                    ).count()
                    > 0
                ):
                    afi = ApplicationFeeInvoice.objects.filter(
                        application_fee=application_fee
                    )
                    invoice = afi[0]
            else:
                return redirect("home")

        context = {"proposal": proposal, "submitter": submitter, "fee_invoice": invoice}
        return render(request, self.template_name, context)


class BookingSuccessView(TemplateView):
    template_name = "licensing_template/booking/success.html"

    def get(self, request, *args, **kwargs):
        print(" BOOKING SUCCESS ")

        booking = None
        submitter = None
        invoice = None
        try:
            context = template_context(self.request)
            basket = None
            booking = get_session_booking(request.session)
            proposal = booking.proposal
            recipients = [request.user.email]

            try:
                recipients.append(proposal.applicant.email)
                submitter = proposal.applicant
            except:
                recipients.append(proposal.submitter.email)
                submitter = proposal.submitter

            try:
                # add org_applicant email, if exists
                recipients.append(proposal.org_applicant.email)
            except:
                pass

            # make distinct
            recipients = list(set(recipients))

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(
                    status="Submitted", owner=request.user
                ).order_by("-id")[:1]
            else:
                basket = Basket.objects.filter(
                    status="Submitted", owner=booking.proposal.submitter
                ).order_by("-id")[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference
            book_inv, created = BookingInvoice.objects.get_or_create(
                booking=booking,
                invoice_reference=invoice_ref,
                payment_method=invoice.payment_method,
            )

            if booking.booking_type == Booking.BOOKING_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    # if (inv.payment_method == Invoice.PAYMENT_METHOD_BPAY):
                    #    # will return 1st of the next month + monthly_payment_due_period (days) e.g 20th of next month
                    #    now = timezone.now().date()
                    #    dt = date(now.year, now.month, 1) + relativedelta(months=1)
                    #    inv.settlement_date = calc_payment_due_date(booking, dt) - relativedelta(days=1)
                    #    inv.save()

                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error(
                        "{} tried paying an admission fee with an incorrect invoice".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user"
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))
                if inv.system not in ["0557"]:
                    logger.error(
                        "{} tried paying an admission fee with an invoice from another system with reference number {}".format(
                            "User {} with id {}".format(
                                proposal.submitter.get_full_name(),
                                proposal.submitter.id,
                            )
                            if proposal.submitter
                            else "An anonymous user",
                            inv.reference,
                        )
                    )
                    return redirect("external-proposal-detail", args=(proposal.id,))

                if book_inv:
                    booking.booking_type = Booking.BOOKING_TYPE_INTERNET
                    booking.expiry_time = None
                    # booking.set_admission_number()
                    update_payments(invoice_ref)

                    if (
                        not (
                            invoice.payment_status == "paid"
                            or invoice.payment_status == "over_paid"
                        )
                        and invoice.payment_method == Invoice.PAYMENT_METHOD_CC
                    ):
                        logger.error(
                            "Payment Method={} - Admission Fee Invoice payment status is {}".format(
                                invoice.get_payment_method_display(),
                                invoice.payment_status,
                            )
                        )
                        raise

                    booking.save()
                    request.session["cols_last_booking"] = booking.id
                    delete_session_booking(request.session)

                    send_invoice_tclass_email_notification(
                        request.user, booking, invoice, recipients=recipients
                    )
                    send_confirmation_tclass_email_notification(
                        request.user, booking, invoice, recipients=recipients
                    )

                    context.update(
                        {
                            "booking_id": booking.id,
                            "submitter": submitter,
                            "payer": request.user,
                            "invoice_reference": invoice.reference,
                        }
                    )
                    return render(request, self.template_name, context)

        except Exception as e:
            # logger.error('{}'.format(e))
            if ("cols_last_booking" in request.session) and Booking.objects.filter(
                id=request.session["cols_last_booking"]
            ).exists():
                booking = Booking.objects.get(id=request.session["cols_last_booking"])
                proposal = booking.proposal
                recipients = [request.user.email]

                try:
                    recipients.append(proposal.applicant.email)
                    submitter = proposal.applicant
                except:
                    recipients.append(proposal.submitter.email)
                    submitter = proposal.submitter

                try:
                    # add org_applicant email, if exists
                    recipients.append(proposal.org_applicant.email)
                except:
                    pass

                # make distinct
                recipients = list(set(recipients))

                if BookingInvoice.objects.filter(booking=booking).count() > 0:
                    bi = BookingInvoice.objects.filter(booking=booking)
                    invoice = bi[0]
            else:
                return redirect("home")

        context.update(
            {
                "booking_id": booking.id,
                "submitter": submitter,
                "payer": request.user,
                "invoice_reference": invoice.invoice_reference,
            }
        )
        return render(request, self.template_name, context)


# class InvoicePDFView(InvoiceOwnerMixin,View):
class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs["reference"])
        bi = BookingInvoice.objects.filter(invoice_reference=invoice.reference).last()

        if bi:
            proposal = bi.booking.proposal
        else:
            proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)

        organisation = proposal.org_applicant.organisation.organisation_set.all()[0]
        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(create_invoice_pdf_bytes("invoice.pdf", invoice, proposal))
            return response
        raise PermissionDenied

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs["reference"])

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


class InvoiceFilmingFeePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs["reference"])
        proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)

        organisation = proposal.org_applicant.organisation.organisation_set.all()[0]
        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_invoice_filmingfee_pdf_bytes("invoice.pdf", invoice, proposal)
            )
            return response
        raise PermissionDenied

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs["reference"])

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


class InvoiceCompliancePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs["reference"])
        cfi = ComplianceFeeInvoice.objects.filter(
            invoice_reference=invoice.reference
        ).last()

        compliance = cfi.compliance_fee.compliance

        organisation = (
            compliance.proposal.org_applicant.organisation.organisation_set.all()[0]
        )
        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_invoice_compliance_pdf_bytes("invoice.pdf", invoice, compliance)
            )
            return response
        raise PermissionDenied

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs["reference"])

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


# class ConfirmationPDFView(InvoiceOwnerMixin,View):
class ConfirmationPDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs["reference"])
        bi = BookingInvoice.objects.filter(invoice_reference=invoice.reference).last()
        organisation = (
            bi.booking.proposal.org_applicant.organisation.organisation_set.all()[0]
        )

        if self.check_owner(organisation):
            # GST ignored here because GST amount is not included on the confirmation PDF
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_confirmation_pdf_bytes("confirmation.pdf", invoice, bi.booking)
            )
            return response
        raise PermissionDenied

    def get_object(self):
        invoice = get_object_or_404(Invoice, reference=self.kwargs["reference"])
        return invoice

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


class MonthlyConfirmationPDFBookingView(View):
    """for the Visitor Admissions Payment Dashboard - View by Booking (payments_dashboard.vue)"""

    def get(self, request, *args, **kwargs):
        booking = get_object_or_404(Booking, id=self.kwargs["id"])
        organisation = (
            booking.proposal.org_applicant.organisation.organisation_set.all()[0]
        )

        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_monthly_confirmation_pdf_bytes(
                    "monthly_confirmation.pdf", booking
                )
            )
            return response
        raise PermissionDenied

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


class MonthlyConfirmationPDFParkBookingView(View):
    """for the Visitor Admissions Payment Dashboard - View by ParkBooking (parkbookings_dashboard.vue)"""

    def get(self, request, *args, **kwargs):
        park_booking = get_object_or_404(ParkBooking, id=self.kwargs["id"])
        booking = park_booking.booking
        organisation = (
            booking.proposal.org_applicant.organisation.organisation_set.all()[0]
        )

        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_monthly_confirmation_pdf_bytes(
                    "monthly_confirmation.pdf", booking
                )
            )
            return response
        raise PermissionDenied

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )


class AwaitingPaymentInvoicePDFView(View):
    """ """

    def get(self, request, *args, **kwargs):
        proposal = get_object_or_404(Proposal, id=self.kwargs["id"])
        organisation = proposal.org_applicant.organisation.organisation_set.all()[0]

        if self.check_owner(organisation):
            response = HttpResponse(content_type="application/pdf")
            response.write(
                create_awaiting_payment_invoice_pdf_bytes(
                    "awaiting_payment_invoice.pdf", proposal
                )
            )
            return response
        raise PermissionDenied

    def check_owner(self, organisation):
        return (
            is_in_organisation_contacts(self.request, organisation)
            or is_internal(self.request)
            or self.request.user.is_superuser
        )
