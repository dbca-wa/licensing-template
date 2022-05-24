from django.conf import settings
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from licensing_template.components.proposals.serializers import (
    ProposalSerializer,
    InternalProposalSerializer,
    ProposalParkSerializer,
)
from licensing_template.components.main.serializers import ApplicationTypeSerializer
from licensing_template.components.approvals.models import (
    Approval,
    ApprovalLogEntry,
    ApprovalUserAction,
)
from licensing_template.components.organisations.models import Organisation
from licensing_template.components.main.serializers import CommunicationLogEntrySerializer
from licensing_template.components.proposals.serializers import ProposalSerializer
from rest_framework import serializers


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = ("id", "email", "first_name", "last_name", "title", "organisation")


class ApprovalPaymentSerializer(serializers.ModelSerializer):
    # proposal = serializers.SerializerMethodField(read_only=True)
    org_applicant = serializers.SerializerMethodField(read_only=True)
    bpay_allowed = serializers.SerializerMethodField(read_only=True)
    monthly_invoicing_allowed = serializers.SerializerMethodField(read_only=True)
    other_allowed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            "lodgement_number",
            "current_proposal",
            "expiry_date",
            "org_applicant",
            "bpay_allowed",
            "monthly_invoicing_allowed",
            "other_allowed",
        )
        read_only_fields = (
            "lodgement_number",
            "current_proposal",
            "expiry_date",
            "org_applicant",
            "bpay_allowed",
            "monthly_invoicing_allowed",
            "other_allowed",
        )

    def get_org_applicant(self, obj):
        return obj.org_applicant.name if obj.org_applicant else None

    def get_bpay_allowed(self, obj):
        return obj.bpay_allowed

    def get_monthly_invoicing_allowed(self, obj):
        return obj.monthly_invoicing_allowed

    def get_other_allowed(self, obj):
        return settings.OTHER_PAYMENT_ALLOWED

    # def get_monthly_invoicing_period(self,obj):
    #    return obj.monthly_invoicing_period

    # def get_monthly_payment_due_period(self,obj):
    #    return obj.monthly_payment_due_period

    # def get_proposal_id(self,obj):
    #    return obj.current_proposal_id


class _ApprovalPaymentSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField(read_only=True)
    applicant_type = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display")
    title = serializers.CharField(source="current_proposal.title")
    application_type = serializers.SerializerMethodField(read_only=True)
    land_parks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Approval
        fields = (
            "id",
            "lodgement_number",
            "current_proposal",
            "title",
            "issue_date",
            "start_date",
            "expiry_date",
            "applicant",
            "applicant_type",
            "applicant_id",
            "status",
            "cancellation_date",
            "application_type",
            "land_parks",
        )

    def get_application_type(self, obj):
        if obj.current_proposal.application_type:
            return obj.current_proposal.application_type.name
        return None

    def get_applicant(self, obj):
        return (
            obj.applicant.name
            if isinstance(obj.applicant, Organisation)
            else obj.applicant
        )

    def get_applicant_type(self, obj):
        return obj.applicant_type

    def get_applicant_id(self, obj):
        return obj.applicant_id

    def get_land_parks(self, obj):
        return None  # obj.current_proposal.land_parks
        # return AuthorSerializer(obj.author).data
        # if obj.current_proposal.land_parks:
        #    return ProposalParkSerializer(obj.current_proposal.land_parks).data
        # return None


class ApprovalSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField(read_only=True)
    applicant_type = serializers.SerializerMethodField(read_only=True)
    applicant_id = serializers.SerializerMethodField(read_only=True)
    # licence_document = serializers.CharField(source='licence_document._file.url')
    # renewal_document = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display")
    # allowed_assessors = EmailUserSerializer(many=True)
    # title = serializers.CharField(source='current_proposal.title')
    application_type = serializers.SerializerMethodField(read_only=True)
    linked_applications = serializers.SerializerMethodField(read_only=True)
    can_renew = serializers.SerializerMethodField()
    can_extend = serializers.SerializerMethodField()
    is_assessor = serializers.SerializerMethodField()
    is_approver = serializers.SerializerMethodField()
    requirement_docs = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = (
            "id",
            "lodgement_number",
            "linked_applications",
            # 'licence_document',
            "replaced_by",
            "current_proposal",
            "tenure",
            # 'title',
            # 'renewal_document',
            "renewal_sent",
            "issue_date",
            "original_issue_date",
            "start_date",
            "expiry_date",
            "surrender_details",
            "suspension_details",
            "applicant",
            "applicant_type",
            "applicant_id",
            "extracted_fields",
            "status",
            "reference",
            "can_reissue",
            # 'allowed_assessors',
            "cancellation_date",
            "cancellation_details",
            "can_action",
            "set_to_cancel",
            "set_to_surrender",
            "set_to_suspend",
            "can_renew",
            "can_extend",
            "can_amend",
            "can_reinstate",
            "application_type",
            "migrated",
            "is_assessor",
            "is_approver",
            "requirement_docs",
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            "id",
            # 'title',
            "status",
            "reference",
            "lodgement_number",
            "linked_applications",
            # 'licence_document',
            "start_date",
            "expiry_date",
            "applicant",
            "can_reissue",
            "can_action",
            "can_reinstate",
            "can_amend",
            "can_renew",
            "can_extend",
            "set_to_cancel",
            "set_to_suspend",
            "set_to_surrender",
            "current_proposal",
            # 'renewal_document',
            "renewal_sent",
            # 'allowed_assessors',
            "application_type",
            "migrated",
            "is_assessor",
            "is_approver",
            "requirement_docs",
        )

    def get_linked_applications(self, obj):
        return obj.linked_applications

    def get_renewal_document(self, obj):
        if obj.renewal_document and obj.renewal_document._file:
            return obj.renewal_document._file.url
        return None

    def get_application_type(self, obj):
        if obj.current_proposal:
            if obj.current_proposal.application_type:
                return obj.current_proposal.application_type.name
        return None

    def get_applicant(self, obj):
        try:
            return (
                obj.applicant.name
                if isinstance(obj.applicant, Organisation)
                else obj.applicant
            )
        except:
            return None

    def get_applicant_type(self, obj):
        try:
            return obj.applicant_type
        except:
            return None

    def get_applicant_id(self, obj):
        try:
            return obj.applicant_id
        except:
            return None

    def get_can_renew(self, obj):
        return obj.can_renew

    def get_can_extend(self, obj):
        return obj.can_extend

    def get_is_assessor(self, obj):
        request = self.context["request"]
        user = request.user
        return obj.is_assessor(user)

    def get_is_approver(self, obj):
        request = self.context["request"]
        user = request.user
        return obj.is_approver(user)

    def get_requirement_docs(self, obj):
        if obj.requirement_docs:
            return [[d.name, d._file.url] for d in obj.requirement_docs]
        return None


class ApprovalExtendSerializer(serializers.Serializer):
    extend_details = serializers.CharField()


class ApprovalCancellationSerializer(serializers.Serializer):
    cancellation_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    cancellation_details = serializers.CharField()


class ApprovalSuspensionSerializer(serializers.Serializer):
    from_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    to_date = serializers.DateField(
        input_formats=["%d/%m/%Y"], required=False, allow_null=True
    )
    suspension_details = serializers.CharField()


class ApprovalSurrenderSerializer(serializers.Serializer):
    surrender_date = serializers.DateField(input_formats=["%d/%m/%Y"])
    surrender_details = serializers.CharField()


class ApprovalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source="who.get_full_name")

    class Meta:
        model = ApprovalUserAction
        fields = "__all__"


class ApprovalLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]
