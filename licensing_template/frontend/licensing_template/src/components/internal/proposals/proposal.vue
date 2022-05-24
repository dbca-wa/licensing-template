<template lang="html">
    <div v-if="proposal" class="container" id="internalProposal">
        <div v-if="debug">internal/proposals/proposal.vue</div>
        <div class="row">
            <h3 v-if="proposal.migrated">Application: {{ proposal.lodgement_number }} (Migrated)</h3>
            <h3 v-else>Application: {{ proposal.lodgement_number }}</h3>
            <h4>Application Type: {{ proposal.proposal_type.description }}</h4>

            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />

                <Submission v-if="canSeeSubmission"
                    :submitter_first_name="submitter_first_name"
                    :submitter_last_name="submitter_last_name"
                    :lodgement_date="proposal.lodgement_date"
                    class="mt-2"
                />

                <Workflow
                    ref='workflow'
                    :proposal="proposal"
                    :isFinalised="isFinalised"
                    :canAction="canAction"
                    :canAssess="canAssess"
                    :can_user_edit="proposal.can_user_edit"
                    @toggleProposal="toggleProposal"
                    @toggleRequirements="toggleRequirements"
                    @switchStatus="switchStatus"
                    @completeReferral="completeReferral"
                    @amendmentRequest="amendmentRequest"
                    @proposedDecline="proposedDecline"
                    @proposedApproval="proposedApproval"
                    @issueProposal="issueProposal"
                    @declineProposal="declineProposal"
                    @assignRequestUser="assignRequestUser"
                    @assignTo="assignTo"
                    class="mt-2"
                />
            </div>

            <div class="col-md-9">
                <!-- Main contents -->
                <template v-if="display_approval_screen">
                    <ApprovalScreen
                        :proposal="proposal"
                        @refreshFromResponse="refreshFromResponse"
                    />
                </template>

                <template v-if="display_requirements">
                    <Requirements
                        :proposal="proposal"
                        :key="requirementsKey"
                    />
                </template>

                <template v-if="canSeeSubmission || (!canSeeSubmission && showingProposal)">
                    <ApplicationForm
                        v-if="proposal"
                        :proposal="proposal"
                        :show_application_title="false"
                        :is_external="false"
                        :is_internal="true"
                        ref="application_form"
                        :readonly="readonly"
                        :submitterId="submitter_id"
                        :key="computedProposalId"
                        :show_related_items_tab="true"
                        :show_additional_documents_tab="true"
                        :registrationOfInterest="isRegistrationOfInterest"
                        :leaseLicence="isLeaseLicence"
                        @formMounted="applicationFormMounted"
                    >
                        <!-- Inserted into the slot on the form.vue: Collapsible Assessor Questions -->
                        <template v-slot:slot_map_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_map_checklist_questions" @created="collapsible_map_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_map.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_map">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_map"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>
                        </template>

                        <template v-slot:slot_proposal_details_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_proposal_details_checklist_questions" @created="collapsible_proposal_details_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_proposal_details.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_proposal_details">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_proposal_details"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>
                        </template>

                        <template v-slot:slot_proposal_impact_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_proposal_impact_checklist_questions" @created="collapsible_proposal_impact_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_proposal_impact.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_proposal_impact">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_proposal_impact"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>
                        </template>

                        <template v-slot:slot_other_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_other_checklist_questions" @created="collapsible_other_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_other.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_other">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_other"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>
                        </template>

                        <template v-slot:slot_deed_poll_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_deed_poll_checklist_questions" @created="collapsible_deed_poll_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_deed_poll.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_deed_poll">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_deed_poll"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>
                        </template>

                        <template v-slot:slot_additional_documents_checklist_questions>
                            <CollapsibleQuestions component_title="Checklist Questions" ref="collapsible_additional_documents_checklist_questions" @created="collapsible_additional_documents_checklist_questions_component_mounted" class="mb-2">
                                <template v-if="assessment_for_assessor_additional_documents.length > 0">
                                    <div class="assessment_title">Assessor</div>
                                </template>
                                <template v-for="question in assessment_for_assessor_additional_documents">  <!-- There is only one assessor assessment -->
                                    <ChecklistQuestion :question="question" />
                                </template>

                                <template v-for="assessment in assessments_for_referrals_additional_documents"> <!-- There can be multiple referral assessments -->
                                    <div class="assessment_title">Referral: {{ assessment.referral_fullname }}</div>
                                    <template v-for="question in assessment.answers"> <!-- per question -->
                                        <ChecklistQuestion :question="question" />
                                    </template>
                                </template>
                            </CollapsibleQuestions>

                            <strong>Select one or more documents that need to be provided by the applicant:</strong>
                            <template v-show="select2AppliedToAdditionalDocumentTypes">
                                <select class="form-select" ref="select_additional_document_types"></select>
                            </template>
                        </template>

                        <!-- Inserted into the slot on the form.vue: Related Items -->
                        <template v-slot:slot_section_related_items>
                            <FormSection :formCollapse="false" label="Related Items" Index="related_items">
                                Related Items table here
                            </FormSection>
                        </template>

                    </ApplicationForm>
                </template>

            </div>
        </div>

        <ProposedApproval
            v-if="proposal"
            :proposal="proposal"
            ref="proposed_approval"
            :processing_status="proposal.processing_status"
            :proposal_id="proposal.id"
            :proposal_type='proposal.proposal_type.code'
            :isApprovalLevelDocument="isApprovalLevelDocument"
            :submitter_email="submitter_email"
            :applicant_email="applicant_email"
            @refreshFromResponse="refreshFromResponse"
            :key="proposedApprovalKey"
            :proposedApprovalKey="proposedApprovalKey"
        />
        <ProposedDecline
            ref="proposed_decline"
            :processing_status="proposal.processing_status"
            :proposal="proposal"
            @refreshFromResponse="refreshFromResponse"
            :proposedApprovalKey="proposedApprovalKey"
        />
        <AmendmentRequest
            ref="amendment_request"
            :proposal="proposal"
            @refreshFromResponse="refreshFromResponse"
        />
        <!--
        <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
        <input type='hidden' name="schema" :value="JSON.stringify(proposal)" />
        <input type='hidden' name="proposal_id" :value="1" />
        -->
        <div v-if="displaySaveBtns" class="navbar fixed-bottom" style="background-color: #f5f5f5;">
            <div class="container">
                <div class="col-md-12 text-end">
                    <button class="btn btn-primary" @click.prevent="save_and_continue()" :disabled="disableSaveAndContinueBtn">Save and Continue</button>
                    <button class="btn btn-primary" @click.prevent="save_and_exit()" :disabled="disableSaveAndExitBtn">Save and Exit</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
//import ProposalDisturbance from '../../form.vue'
//import ProposalApiary from '@/components/form_apiary.vue'
//import NewApply from '../../external/proposal_apply_new.vue'
import ProposedDecline from '@/components/internal/proposals/proposal_proposed_decline.vue'
import AmendmentRequest from '@/components/internal/proposals/amendment_request.vue'
import datatable from '@vue-utils/datatable.vue'
import Requirements from '@/components/internal/proposals/proposal_requirements.vue'
import ProposedApproval from '@/components/internal/proposals/proposed_issuance.vue'
import ApprovalScreen from '@/components/internal/proposals/proposal_approval.vue'
import CommsLogs from '@common-utils/comms_logs.vue'
import Submission from '@common-utils/submission.vue'
import Workflow from '@common-utils/workflow.vue'
import { api_endpoints, helpers, constants } from '@/utils/hooks'
import ApplicationForm from '@/components/form.vue';
import FormSection from "@/components/forms/section_toggle.vue"
import CollapsibleQuestions from '@/components/forms/collapsible_component.vue'
import ChecklistQuestion from '@/components/common/component_checklist_question.vue'
require("select2/dist/css/select2.min.css");

export default {
    name: 'InternalProposal',
    data: function() {
        let vm = this;
        return {
            detailsBody: 'detailsBody'+vm._uid,
            addressBody: 'addressBody'+vm._uid,
            contactsBody: 'contactsBody'+vm._uid,
            siteLocations: 'siteLocations'+vm._uid,
            defaultKey: "aho",
            "proposal": null,
            "loading": [],
            //selected_referral: '',
            //referral_text: '',
            approver_comment: '',
            form: null,
            members: [],
            //department_users : [],
            contacts_table_initialised: false,
            initialisedSelects: false,
            showingProposal:false,
            showingRequirements:false,
            hasAmendmentRequest: false,
            //requirementsComplete:true,
            state_options: ['requirements','processing'],
            contacts_table_id: vm._uid+'contacts-table',
            contacts_options:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": vm.contactsURL,
                    "dataSrc": ''
                },
                columns: [
                    {
                        title: 'Name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {
                        title: 'Phone',
                        data:'phone_number'
                    },
                    {
                        title: 'Mobile',
                        data:'mobile_number'
                    },
                    {
                        title: 'Fax',
                        data:'fax_number'
                    },
                    {
                        title: 'Email',
                        data:'email'
                    },
                  ],
                  processing: true
            },
            contacts_table: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            //comms_url: helpers.add_endpoint_json(api_endpoints.proposals, vm.$route.params.proposal_id + '/comms_log'),
            //comms_add_url: helpers.add_endpoint_json(api_endpoints.proposals, vm.$route.params.proposal_id + '/add_comms_log'),
            //logs_url: helpers.add_endpoint_json(api_endpoints.proposals, vm.$route.params.proposal_id + '/action_log'),
            comms_url: helpers.add_endpoint_json(api_endpoints.proposal, vm.$route.params.proposal_id + '/comms_log'),
            comms_add_url: helpers.add_endpoint_json(api_endpoints.proposal, vm.$route.params.proposal_id + '/add_comms_log'),
            logs_url: helpers.add_endpoint_json(api_endpoints.proposal, vm.$route.params.proposal_id + '/action_log'),
            panelClickersInitialised: false,
            //sendingReferral: false,
            uuid: 0,
            //additional_document_types: [],
            additionalDocumentTypesSelected: [],
            select2AppliedToAdditionalDocumentTypes: false,
        }
    },
    components: {
        //ProposalDisturbance,
        //ProposalApiary,
        datatable,
        ProposedDecline,
        AmendmentRequest,
        Requirements,
        ProposedApproval,
        ApprovalScreen,
        CommsLogs,
        Submission,
        Workflow,
        //MoreReferrals,
        //NewApply,
        //MapLocations,
        ApplicationForm,
        FormSection,
        CollapsibleQuestions,
        ChecklistQuestion,
    },
    props: {
        proposalId: {
            type: Number,
        },
    },
    watch: {

    },
    computed: {
        requirementsKey: function() {
            const req = "proposal_requirements_" + this.uuid;
            return req;
        },
        displaySaveBtns: function(){
            let display = false
            if ([constants.WITH_ASSESSOR, constants.WITH_ASSESSOR_CONDITIONS].includes(this.proposal.processing_status)){
                if (this.proposal.accessing_user_roles.includes(constants.ROLES.ASSESSOR.ID)){
                    display = true
                }
            }
            if ([constants.WITH_REFERRAL, constants.WITH_REFERRAL_CONDITIONS].includes(this.proposal.processing_status)){
                if (this.proposal.accessing_user_roles.includes(constants.ROLES.REFERRAL.ID)){
                    display = true
                }
            }
            return display
        },
        disableSaveAndContinueBtn: function(){
            let enabled = false
            if ([constants.WITH_ASSESSOR, constants.WITH_ASSESSOR_CONDITIONS].includes(this.proposal.processing_status)){
                if (this.proposal.accessing_user_roles.includes(constants.ROLES.ASSESSOR.ID)){
                    enabled = true
                }
            }
            if ([constants.WITH_REFERRAL, constants.WITH_REFERRAL_CONDITIONS].includes(this.proposal.processing_status)){
                if (this.proposal.accessing_user_roles.includes(constants.ROLES.REFERRAL.ID)){
                    enabled = true
                }
            }
            return !enabled
        },
        disableSaveAndExitBtn: function(){
            return this.disableSaveAndContinueBtn
        },
        submitter_first_name: function(){
            if (this.proposal.submitter){
                return this.proposal.submitter.first_name
            } else {
                return ''
            }
        },
        submitter_last_name: function(){
            if (this.proposal.submitter){
                return this.proposal.submitter.last_name
            } else {
                return ''
            }
        },
        submitter_id: function(){
            if (this.proposal.submitter){
                return this.proposal.submitter.id
            } else {
                return this.proposal.applicant_obj.id
            }
        },
        submitter_email: function(){
            if (this.proposal.submitter){
                return this.proposal.submitter.email
            } else {
                return this.proposal.applicant_obj.email
            }
        },
        proposal_form_url: function() {
            if ([constants.WITH_ASSESSOR, constants.WITH_ASSESSOR_CONDITIONS].includes(this.proposal.processing_status)){
                return `/api/proposal/${this.proposal.id}/assessor_save.json`
            } else if ([constants.WITH_REFERRAL, constants.WITH_REFERRAL_CONDITIONS].includes(this.proposal.processing_status)){
                return `/api/proposal/${this.proposal.id}/referral_save.json`
            } else {
                // Should not reach here
                return ''
            }
        },
        complete_referral_url: function(){
            return `/api/proposal/${this.proposal.id}/complete_referral.json`
        },
        isRegistrationOfInterest: function(){
            return this.proposal.application_type.name === constants.APPLICATION_TYPE.REGISTRATION_OF_INTEREST ? true : false
        },
        isLeaseLicence: function(){
            return this.proposal.application_type.name === constants.APPLICATION_TYPE.LEASE_LICENCE ? true : false
        },
        assessment_for_assessor_map: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.map // This may return undefined
                return answers ? answers : []  // Check if it's undefined
            } catch (err) {
                return []
            }
        },
        assessment_for_assessor_proposal_details: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.proposal_details
                return answers ? answers : []
            } catch (err) {
                return []
            }
        },
        assessment_for_assessor_proposal_impact: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.proposal_impact
                return answers ? answers : []
            } catch (err) {
                return []
            }
        },
        assessment_for_assessor_other: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.other
                return answers ? answers : []
            } catch (err) {
                return []
            }
        },
        assessment_for_assessor_deed_poll: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.deed_poll
                return answers ? answers : []
            } catch (err) {
                return []
            }
        },
        assessment_for_assessor_additional_documents: function(){
            try {
                let answers = this.proposal.assessor_assessment.section_answers.additional_documents
                return answers ? answers : []
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_map: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if (assessment.section_answers.map){  // Check if this is undefined
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.map
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_proposal_details: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if(assessment.section_answers.proposal_details){
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.proposal_details
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_proposal_impact: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if(assessment.section_answers.proposal_impact){
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.proposal_impact
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_other: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if(assessment.section_answers.other){
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.other
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_deed_poll: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if(assessment.section_answers.deed_poll){
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.deed_poll
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        assessments_for_referrals_additional_documents: function(){
            try {
                let assessments = []
                for (let assessment of this.proposal.referral_assessments){
                    if(assessment.section_answers.additional_documents){
                        let my_assessment = {
                            'referral_fullname': assessment.referral.referral.fullname,
                            'answers': assessment.section_answers.additional_documents
                        }
                        assessments.push(my_assessment)
                    }
                }
                return assessments
            } catch (err) {
                return []
            }
        },
        debug: function(){
            if (this.$route.query.debug){
                return this.$route.query.debug == 'true'
            }
            return false
        },
        proposedApprovalKey: function() {
            return "proposed_approval_" + this.uuid;
        },
        computedProposalId: function(){
            if (this.proposal) {
                return this.proposal.id;
            }
        },
        display_approval_screen: function(){
            let ret_val =
                this.proposal.processing_status == constants.WITH_APPROVER ||
                this.proposal.processing_status == constants.AWAITING_STICKER ||
                this.proposal.processing_status == constants.AWAITING_PAYMENT ||
                this.isFinalised
            return ret_val
        },
        display_requirements: function(){
            let ret_val =
                this.proposal.processing_status == constants.WITH_ASSESSOR_CONDITIONS ||
                ((this.proposal.processing_status == constants.WITH_APPROVER || this.isFinalised) && this.showingRequirements)
            return ret_val
        },
        /*
        showElectoralRoll: function(){
            // TODO: implement
            return true
        },
        */
        showElectoralRoll: function() {
            let show = false;
            if (this.proposal && ['wla', 'mla'].includes(this.proposal.application_type_code)) {
                show = true;
            }
            return show;
        },
        readonly: function() {
            return true
        },
        contactsURL: function(){
            return this.proposal!= null ? helpers.add_endpoint_json(api_endpoints.organisations, this.proposal.applicant.id + '/contacts') : '';
        },
        isLoading: function() {
          return this.loading.length > 0
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        isFinalised: function(){
            return this.proposal.processing_status == 'Declined' || this.proposal.processing_status == 'Approved';
        },
        canAssess: function(){
            return true  // TODO: Implement correctly.  May not be needed though

            //return this.proposal && this.proposal.assessor_mode.assessor_can_assess ? true : false;
        },
        hasAssessorMode:function(){
            return this.proposal && this.proposal.assessor_mode.has_assessor_mode ? true : false;
        },
        canAction: function(){

            return true  // TODO: implement this.  This is just temporary solution

            if (this.proposal.processing_status == 'With Approver'){
                return this.proposal && (this.proposal.processing_status == 'With Approver' || this.proposal.processing_status == 'With Assessor' || this.proposal.processing_status == 'With Assessor (Requirements)') && !this.isFinalised && !this.proposal.can_user_edit && (this.proposal.current_assessor.id == this.proposal.assigned_approver || this.proposal.assigned_approver == null ) && this.proposal.assessor_mode.assessor_can_assess? true : false;
            }
            else{
                return this.proposal && (this.proposal.processing_status == 'With Approver' || this.proposal.processing_status == 'With Assessor' || this.proposal.processing_status == 'With Assessor (Requirements)') && !this.isFinalised && !this.proposal.can_user_edit && (this.proposal.current_assessor.id == this.proposal.assigned_officer || this.proposal.assigned_officer == null ) && this.proposal.assessor_mode.assessor_can_assess? true : false;
            }
        },
        canLimitedAction: function(){

            //return false  // TODO: implement this.  This is just temporary solution

            if (this.proposal.processing_status == 'With Approver'){
                return
                    this.proposal
                    && (
                        this.proposal.processing_status == 'With Assessor' ||
                        //this.proposal.processing_status == 'With Referral' ||
                        this.proposal.processing_status == 'With Assessor (Requirements)'
                    )
                    && !this.isFinalised && !this.proposal.can_user_edit
                    && (
                        this.proposal.current_assessor.id == this.proposal.assigned_approver ||
                        this.proposal.assigned_approver == null
                    ) && this.proposal.assessor_mode.assessor_can_assess? true : false;
            }
            else{
                return
                    this.proposal
                    && (
                        this.proposal.processing_status == 'With Assessor' ||
                        //this.proposal.processing_status == 'With Referral' ||
                        this.proposal.processing_status == 'With Assessor (Requirements)'
                    ) && !this.isFinalised && !this.proposal.can_user_edit
                    && (
                        this.proposal.current_assessor.id == this.proposal.assigned_officer ||
                        this.proposal.assigned_officer == null
                    ) && this.proposal.assessor_mode.assessor_can_assess? true : false;
            }
        },
        canSeeSubmission: function(){
            return this.proposal && (this.proposal.processing_status != 'With Assessor (Requirements)' && this.proposal.processing_status != 'With Approver' && !this.isFinalised)
        },
        isApprovalLevelDocument: function(){
            return this.proposal && this.proposal.processing_status == 'With Approver' && this.proposal.approval_level != null && this.proposal.approval_level_document == null ? true : false;
        },
        applicant_email:function(){
            return this.proposal && this.proposal.applicant.email ? this.proposal.applicant.email : '';
        },
    },
    methods: {
        applicationFormMounted: function(){
            this.fetchAdditionalDocumentTypesDict()  // <select> element for the additional document type exists in the ApplicationForm component, which is a child component of this component.
                                                     // Therefore to apply select2 to the element inside child component, we have to make sure the childcomponent has been mounted.  Then select2 can be applied.
        },
        applySelect2ToAdditionalDocumentTypes: function(option_data){
            let vm = this

            console.log('in applySelect2ToAdditionalDocumentTypes')
            console.log(this.$refs.select_additional_document_types)

            if (!vm.select2AppliedToAdditionalDocumentTypes){
                $(vm.$refs.select_additional_document_types).select2({
                    "theme": "bootstrap-5",
                    allowClear: false,
                    placeholder:"Select Type",
                    multiple:true,
                    data: option_data,
                }).
                on('select2:select', function(e){
                    //vm.updateApplicationTypeFilterCache()
                    //vm.main_manager.show_me()
                }).
                on('select2:unselect', function(e){
                    //vm.updateApplicationTypeFilterCache()
                    //vm.main_manager.show_me()
                })
                vm.select2AppliedToAdditionalDocumentTypes = true
            }

            // Set default selections
            //$(vm.$refs.select_additional_document_types).val(vm.additionalDocumentTypesSelected).trigger('change')
        },
        addEventListeners: function(){
        },
        /*
        applySelect2ToAdditionalDocumentType: function(option_data){
            let vm = this
            vm.additional_document_types = option_data

            // TODO: Make select2 work...  Somehow the code below doesn't work...

            $(vm.$refs.selectAdditionalDocumentTypes).select2({
                "theme": "bootstrap-5",
                allowClear: true,
                placeholder: "Select Document Type(s)",
                multiple: true,
                minimumResultsForSearch: -1,  // This hide the search box below selections
            //    data: option_data,
            })
            vm.select2AppliedToAdditionalDocumentTypes = true
        },
        */
        collapsible_map_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_map_checklist_questions.show_warning_icon(false)
        },
        collapsible_other_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_other_checklist_questions.show_warning_icon(false)
        },
        collapsible_deed_poll_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_deed_poll_checklist_questions.show_warning_icon(false)
        },
        collapsible_additional_documents_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_additional_documents_checklist_questions.show_warning_icon(false)
        },
        collapsible_proposal_details_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_proposal_details_checklist_questions.show_warning_icon(false)
        },
        collapsible_proposal_impact_checklist_questions_component_mounted: function(){
            this.$refs.collapsible_proposal_impact_checklist_questions.show_warning_icon(false)
        },
        locationUpdated: function(){
            console.log('in locationUpdated()');
        },
        save_and_continue: function(){
            this.save()
        },
        save_and_exit: async function(){
            await this.save()
            this.$router.push({ name: 'internal-dashboard' })
        },
        completeReferral: async function(){
            let vm = this;
            vm.checkAssessorData();
            try {
                const swal_result = await swal({
                    title: "Complete Referral",
                    text: "Are you sure you want to complete this referral?",
                    type: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Submit'
                })
                const res_save_data = await fetch(vm.complete_referral_url, { body: {'proposal': JSON.stringify(this.proposal)}, method: 'POST', })
                this.$router.push({ name: 'internal-dashboard' })
            } catch (err) {
                swal(
                    'Referral Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        save: async function() {
            let vm = this;
            vm.checkAssessorData();
            try {
                let payload = {'proposal': this.proposal}
                if (this.$refs.application_form.componentMapOn) {
                    //this.proposal.proposal_geometry = this.$refs.application_form.$refs.component_map.getJSONFeatures();
                    payload['proposal_geometry'] = this.$refs.application_form.$refs.component_map.getJSONFeatures();
                }
                const res = await fetch(vm.proposal_form_url, { body: JSON.stringify(payload), method: 'POST' })
                console.log('aho4')

                if(res.ok){
                    swal({
                        title: 'Saved',
                        text: 'Your proposal has been saved',
                        type: 'success',
                    })
                } else {
                    swal({
                        title: "Please fix following errors before saving",
                        text: err.bodyText,
                        type:'error',
                    })
                }
            } catch (err){
                console.error(err)
            }
        },
        checkAssessorData: function(){
            //check assessor boxes and clear value of hidden assessor boxes so it won't get printed on approval pdf.

            //select all fields including hidden fields
            //console.log("here");
            var all_fields = $('input[type=text]:required, textarea:required, input[type=checkbox]:required, input[type=radio]:required, input[type=file]:required, select:required')

            all_fields.each(function() {
                var ele=null;
                //check the fields which has assessor boxes.
                ele = $("[name="+this.name+"-Assessor]");
                if(ele.length>0){
                    var visiblity=$("[name="+this.name+"-Assessor]").is(':visible')
                    if(!visiblity){
                        if(ele[0].value!=''){
                            //console.log(visiblity, ele[0].name, ele[0].value)
                            ele[0].value=''
                        }
                    }
                }
            });
        },
        initialiseOrgContactTable: function(){
            let vm = this;
            if (vm.proposal && !vm.contacts_table_initialised){
                vm.contacts_options.ajax.url = helpers.add_endpoint_json(api_endpoints.organisations,vm.proposal.applicant.id+'/contacts');
                vm.contacts_table = $('#'+vm.contacts_table_id).DataTable(vm.contacts_options);
                vm.contacts_table_initialised = true;
            }
        },
        commaToNewline(s){
            return s.replace(/[,;]/g, '\n');
        },
        proposedDecline: function(){
            console.log('in proposedDecline')
            this.uuid++;
            //this.$refs.proposed_decline.decline = this.proposal.proposaldeclineddetails != null ? Object.assign({}, this.proposal.proposaldeclineddetails): {};
            this.$nextTick(() => {
                this.$refs.proposed_decline.isModalOpen = true;
            });
        },
        proposedApproval: function(){
            this.uuid++;
            this.$nextTick(() => {
                //this.$refs.proposed_approval.approval = this.proposal.proposed_issuance_approval != null ? Object.assign({}, this.proposal.proposed_issuance_approval) : {};
                this.$refs.proposed_approval.isModalOpen = true;
            });
        },
        issueProposal:function(){
            console.log('in issueProposal')
            //this.$refs.proposed_approval.approval = helpers.copyObject(this.proposal.proposed_issuance_approval);

            //save approval level comment before opening 'issue approval' modal
            if(this.proposal && this.proposal.processing_status == 'With Approver' && this.proposal.approval_level != null && this.proposal.approval_level_document == null){
                if (this.proposal.approval_level_comment!=''){
                    let vm = this;
                    let data = new FormData();
                    data.append('approval_level_comment', vm.proposal.approval_level_comment)
                    fetch(helpers.add_endpoint_json(api_endpoints.proposal,vm.proposal.id+'/approval_level_comment'), { body: JSON.stringify(data), method: 'POST' }).then(
                        res => {
                            vm.proposal = res.body;
                            vm.refreshFromResponse(res);
                        }, err => {
                            console.log(err);
                        }
                    );
                }
            }
            if(this.isApprovalLevelDocument && this.proposal.approval_level_comment==''){
                swal(
                    'Error',
                    'Please add Approval document or comments before final approval',
                    'error'
                )
            } else {
                this.uuid++;
                this.$nextTick(() => {
                    this.$refs.proposed_approval.approval = this.proposal.proposed_issuance_approval != null ? helpers.copyObject(this.proposal.proposed_issuance_approval) : {};
                    this.$refs.proposed_approval.state = 'final_approval';
                    this.$refs.proposed_approval.isApprovalLevelDocument = this.isApprovalLevelDocument;
                    this.$refs.proposed_approval.isModalOpen = true;
                });
            }

        },
        declineProposal:function(){
            console.log('in declineProposal')
            this.$refs.proposed_decline.decline = this.proposal.proposaldeclineddetails != null ? helpers.copyObject(this.proposal.proposaldeclineddetails): {};
            this.$refs.proposed_decline.isModalOpen = true;
        },
        amendmentRequest: function(){
            let values = '';
            $('.deficiency').each((i,d) => {
                values +=  $(d).val() != '' ? `Question - ${$(d).data('question')}\nDeficiency - ${$(d).val()}\n\n`: '';
            });
            //this.deficientFields();
            this.$refs.amendment_request.amendment.text = values;

            this.$refs.amendment_request.isModalOpen = true;
        },
        highlight_deficient_fields: function(deficient_fields){
            let vm = this;
            for (var deficient_field of deficient_fields) {
                $("#" + "id_"+deficient_field).css("color", 'red');
            }
        },
        deficientFields(){
            let vm=this;
            let deficient_fields=[]
            $('.deficiency').each((i,d) => {
                if($(d).val() != ''){
                    var name=$(d)[0].name
                    var tmp=name.replace("-comment-field","")
                    deficient_fields.push(tmp);
                    //console.log('data', $("#"+"id_" + tmp))
                }
            });
            //console.log('deficient fields', deficient_fields);
            vm.highlight_deficient_fields(deficient_fields);
        },
        toggleProposal:function(value){
            this.showingProposal = value
        },
        toggleRequirements:function(value){
            this.showingRequirements = value
        },
        updateAssignedOfficerSelect:function(){
            console.log('updateAssignedOfficerSelect')
            let vm = this;
            if (vm.proposal.processing_status == 'With Approver'){
                //$(vm.$refs.assigned_officer).val(vm.proposal.assigned_approver);
                //$(vm.$refs.assigned_officer).trigger('change');
                vm.$refs.workflow.updateAssignedOfficerSelect(vm.proposal.assigned_approver)
            }
            else{
                //$(vm.$refs.assigned_officer).val(vm.proposal.assigned_officer);
                //$(vm.$refs.assigned_officer).trigger('change');
                vm.$refs.workflow.updateAssignedOfficerSelect(vm.proposal.assigned_officer)
            }
        },
        assignRequestUser: async function(){
            console.log('in assignRequestUser')
            try {
                const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id + '/assign_request_user')))
                const resData = await response.json();
                this.proposal = Object.assign({}, resData);
                this.updateAssignedOfficerSelect();
            } catch (error) {
                this.updateAssignedOfficerSelect();
                swal.fire(
                    'Proposal Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        refreshFromResponse:function(response){
            this.proposal = helpers.copyObject(response.body);
            this.$nextTick(() => {
                this.initialiseAssignedOfficerSelect(true);
                this.updateAssignedOfficerSelect();
            });
        },
        assignTo: async function(){
            console.log('in assignTo')
            let unassign = true;
            let data = {};
            if (this.processing_status == 'With Approver'){
                unassign = this.proposal.assigned_approver != null && this.proposal.assigned_approver != 'undefined' ? false: true;
                data = {'assessor_id': this.proposal.assigned_approver};
            }
            else{
                unassign = this.proposal.assigned_officer != null && this.proposal.assigned_officer != 'undefined' ? false: true;
                data = {'assessor_id': this.proposal.assigned_officer};
            }
            if (!unassign){
                try {
                    const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id+'/assign_to')),
                    {
                        body: JSON.stringify(data),
                        method: 'POST',
                    })
                    const resData = await response.json()
                    this.proposal = Object.assign({}, resData);
                    this.updateAssignedOfficerSelect();
                } catch (error) {
                    this.updateAssignedOfficerSelect();
                    swal.fire(
                        'Proposal Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                }
            }
            else{
                try {
                    const response = fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id+'/unassign')))
                    const responseData = await response.json()
                    this.proposal = Object.assign({}, responseData);
                    this.updateAssignedOfficerSelect();
                } catch (error) {
                    this.updateAssignedOfficerSelect();
                    swal.fire(
                        'Proposal Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                }
            }
        },
        switchStatus:async function(new_status){
            if(this.proposal.processing_status == 'With Assessor' && new_status == 'with_assessor_requirements'){
                this.checkAssessorData();
                let formData = new FormData(vm.form);
                let data = {'status': new_status, 'approver_comment': vm.approver_comment}
                try {
                    const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id + '/switch_status')), 
                    {
                        body: JSON.stringify(data),
                        method: 'POST',
                    })
                    const responseData = await response.json()
                    this.proposal = responseData;
                    this.approver_comment='';
                    this.$nextTick(() => {
                        this.initialiseAssignedOfficerSelect(true);
                        this.updateAssignedOfficerSelect();
                    });
                } catch (error) {
                    swal.fire(
                        'Proposal Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                }
            }

            //if approver is pushing back proposal to Assessor then navigate the approver back to dashboard page
            else if(this.proposal.processing_status == 'With Approver' && (new_status == 'with_assessor_requirements' || new_status=='with_assessor')) {
                let data = {'status': new_status, 'approver_comment': this.approver_comment}
                try {
                    const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id + '/switch_status')),
                    {
                        body: JSON.stringify(data),
                        method: 'POST',
                    })
                    const responseData = await response.json()
                    this.proposal = Object.assign({}, responseData);
                    this.approver_comment='';
                    this.$nextTick(() => {
                        this.initialiseAssignedOfficerSelect(true);
                        this.updateAssignedOfficerSelect();
                    });
                    this.$router.push({ path: '/internal' });
                } catch (error) {
                    swal.fire(
                        'Proposal Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                }
            } else {
                let data = {'status': new_status, 'approver_comment': vm.approver_comment}
                try {
                    const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal, (vm.proposal.id + '/switch_status')), 
                    {
                        body: JSON.stringify(data),
                        method: 'POST',
                    })
                    const resData = await response.json()
                    this.proposal = Object.assign({}, resData);
                    this.approver_comment='';
                    this.$nextTick(() => {
                        this.initialiseAssignedOfficerSelect(true);
                        this.updateAssignedOfficerSelect();
                    });
                } catch (error) {
                    swal.fire(
                        'Proposal Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                }
            }
        },
        initialiseAssignedOfficerSelect:function(reinit=false){
            console.log('initialiseAssignedOfficerSelect')
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_officer).data('select2') ? $(vm.$refs.assigned_officer).select2('destroy'): '';
            }
            // Assigned officer select
            /*
            console.log('Elem: ')
            console.log(vm.$refs.assigned_officer)
            */
            $(vm.$refs.assigned_officer).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Officer"
            }).
            on("select2:select",function (e) {
                var selected = $(e.currentTarget);
                if (vm.proposal.processing_status == 'With Approver'){
                    vm.proposal.assigned_approver = selected.val();
                }
                else{
                    vm.proposal.assigned_officer = selected.val();
                }
                vm.assignTo();
            }).on("select2:unselecting", function(e) {
                var self = $(this);
                setTimeout(() => {
                    self.select2('close');
                }, 0);
            }).on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                if (vm.proposal.processing_status == 'With Approver'){
                    vm.proposal.assigned_approver = null;
                }
                else{
                    vm.proposal.assigned_officer = null;
                }
                vm.assignTo();
            });
        },
        initialiseSelects: function(){
            let vm = this;
            if (!vm.initialisedSelects){
                /*
                $(vm.$refs.department_users).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    //placeholder:"Select Referral"
                }).
                on("select2:select",function (e) {
                    var selected = $(e.currentTarget);
                    //vm.selected_referral = selected.val();
                }).
                on("select2:unselect",function (e) {
                    var selected = $(e.currentTarget);
                    //vm.selected_referral = ''
                });
                */
                vm.initialiseAssignedOfficerSelect();
                vm.initialisedSelects = true;
            }
        },
        fetchAdditionalDocumentTypesDict: async function(){
            const response = await fetch('/api/additional_document_types_dict')
            console.log(response)
            const resData = await response.json()
            this.applySelect2ToAdditionalDocumentTypes(resData)
        },
    },
    mounted: function() {
        console.log('in mounted')
        let vm = this
        this.$nextTick(() => {
            vm.addEventListeners()
        })
    },
    updated: function(){
        let vm = this;
        if (!vm.panelClickersInitialised){
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                },100);
            });
            vm.panelClickersInitialised = true;
        }
        this.$nextTick(() => {
            vm.initialiseOrgContactTable();
            vm.initialiseSelects();
            vm.form = document.forms.new_proposal;
            if(vm.hasAmendmentRequest){
                vm.deficientFields();
            }
        });
    },
    created: async function() {
        console.log('in created')
        try {
        const res = await fetch(`/api/proposal/${this.$route.params.proposal_id}/internal_proposal.json`);
        const resData = await res.json();
        this.proposal = Object.assign({}, resData);
        this.hasAmendmentRequest=this.proposal.hasAmendmentRequest;
        } catch (err) {
          console.log(err);
        }
    },
}
</script>
<style scoped>
.horizontal_rule {
    margin: 15px 0 10px 0;
    border-top: 2px solid #888;
}
.assessment_title {
    margin: 20px 0 10px 0;
    border-bottom: 1px solid #888;
    font-weight: bold;
    font-size: 1.3em;
}
</style>
