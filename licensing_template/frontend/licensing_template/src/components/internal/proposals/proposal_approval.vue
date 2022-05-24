<template id="proposal_approval">
    <div>
        <div v-if="displayApprovedMsg" class="col-md-12 alert alert-success">
            <!--p>The {{ applicationTypeNameDisplay }} was approved to proceed to a full application on date by {{ proposal.assigned_approver.email }}</p-->
            <p>The {{ applicationTypeNameDisplay }} was approved to proceed to a full application on {{ approvalIssueDate }} by { insert approver name here }</p>
            <!--p>Expiry date: {{ approvalExpiryDate }}</p>
            <p>Permit: <a target="_blank" :href="proposal.permit">approval.pdf</a></p-->
        </div>
        <div v-if="displayDeclinedMsg" class="col-md-12 alert alert-warning">
            <p>The proposal was declined. The decision was emailed to {{ proposal.submitter.email }}</p>
        </div>

        <div class="card card-default">
            <div class="card-header">
                <h3 v-if="!isFinalised" class="card-title">Proposed Decision
                    <a class="panelClicker" :href="'#'+proposedDecision" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="proposedDecision">
                        <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                    </a>
                </h3>
                <h3 v-else class="card-title">Decision
                    <a class="panelClicker" :href="'#'+proposedDecision" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="proposedDecision">
                        <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                    </a>
                </h3>
            </div>
            <div class="card-body" :id="proposedDecision">
                <div class="row">
                    <div class="col-sm-12">
                        <template v-if="!proposal.proposed_decline_status">
                            <template v-if="isFinalised">
                                <p><strong>Decision: Issue</strong></p>
                                <p><strong>Start date: {{proposal.proposed_issuance_approval.start_date}}</strong></p>
                                <p><strong>Expiry date: {{proposal.proposed_issuance_approval.expiry_date}}</strong></p>
                                <p><strong>CC emails: {{proposal.proposed_issuance_approval.cc_email}}</strong></p>
                            </template>
                            <template v-else>
                                <p><strong>Proposed decision: Issue</strong></p>
                                <p><strong>Proposed cc emails: {{proposal.proposed_issuance_approval.cc_email}}</strong></p>
                            </template>
                        </template>
                        <template v-else>
                            <strong v-if="!isFinalised">Proposed decision: Decline</strong>
                            <strong v-else>Decision: Decline</strong>
                        </template>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import RequirementDetail from './proposal_add_requirement.vue'
//import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import uuid from 'uuid'
import { constants } from '@/utils/hooks'

export default {
    name: 'InternalProposalApproval',
    props: {
        proposal: Object
    },
    data: function() {
        let vm = this;
        return {
            proposedDecision: "proposal-decision-"+vm._uid,
            proposedLevel: "proposal-level-"+vm._uid,
            uploadedFile: null,
            component_site_selection_key: '',
        }
    },
    watch:{
    },
    components:{
        FormSection,
        //ComponentSiteSelection,
    },
    computed:{
        approvalIssueDate: function() {
            if (this.proposal) {
                return this.proposal.approval_issue_date;
            }
        },
        applicationTypeNameDisplay: function() {
            if (this.proposal) {
                return this.proposal.application_type.name_display;
            }
        },
        displayAwaitingPaymentMsg: function(){
            let display = false
            console.log(this.proposal.processing_status)
            if (this.proposal.processing_status === constants.AWAITING_PAYMENT){
                display = true
            }
            return display
        },
        displayApprovedMsg: function(){
            let display = false
            if (this.proposal.processing_status === constants.APPROVED){
                display = true
            }
            return display
        },
        displayDeclinedMsg: function(){
            let display = false
            if (this.proposal.processing_status === constants.DECLINED){
                display = true
            }
            return display
        },
        approvalExpiryDate: function() {
            let returnDate = null;
            if (this.proposal && this.proposal.end_date) {
                returnDate = moment(this.proposal.end_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            return returnDate;
        },
        hasAssessorMode(){
            return this.proposal.assessor_mode.has_assessor_mode;
        },
        isFinalised: function(){
            return this.proposal.processing_status == 'Approved' || this.proposal.processing_status == 'Declined';
        },
        isApprovalLevel:function(){
            return this.proposal.approval_level != null ? true : false;
        },

    },
    methods:{
        readFile: function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedFile)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedFile = _file;
            vm.save()
        },
        removeFile: function(){
            let vm = this;
            vm.uploadedFile = null;
            vm.save()
        },
        save: function(){
            let vm = this;
                let data = new FormData(vm.form);
                data.append('approval_level_document', vm.uploadedFile)
                if (vm.proposal.approval_level_document) {
                    data.append('approval_level_document_name', vm.proposal.approval_level_document[0])
                }
                vm.$http.post(helpers.add_endpoint_json(api_endpoints.proposals,vm.proposal.id+'/approval_level_document'),data,{
                emulateJSON:true
            }).then(res=>{
                vm.proposal = res.body;
                vm.$emit('refreshFromResponse',res);

                },err=>{
                swal(
                    'Submit Error',
                    helpers.apiVueResourceError(err),
                    'error'
                )
            });


        },
        uploadedFileName: function() {
            return this.uploadedFile != null ? this.uploadedFile.name: '';
        },
        addRequirement(){
            this.$refs.requirement_detail.isModalOpen = true;
        },
        removeRequirement(_id){
            let vm = this;
            swal({
                title: "Remove Requirement",
                text: "Are you sure you want to remove this requirement?",
                type: "warning",
                showCancelButton: true,
                confirmButtonText: 'Remove Requirement',
                confirmButtonColor:'#d9534f'
            }).then(() => {
                vm.$http.delete(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id))
                .then((response) => {
                    vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
                }, (error) => {
                    console.log(error);
                });
            },(error) => {
            });
        },
    },
    mounted: function(){
        let vm = this;
    }
}
</script>
<style scoped>
</style>
