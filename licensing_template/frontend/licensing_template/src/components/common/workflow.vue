<template>
    <div class="">
        <div class="card card-default">
            <div class="card-header">
                Workflow
            </div>
            <div class="card-body card-collapse">
                <div class="row">
                    <div class="col-sm-12">
                        <strong>Status</strong><br/>
                        {{ proposal.processing_status }}
                    </div>
                    <div class="col-sm-12">
                        <div class="separator"></div>
                    </div>
                    <div v-if="!isFinalised" class="col-sm-12">
                        <strong>Currently assigned to</strong><br/>
                        <div class="form-group">
                            <template v-if="proposal.processing_status_id == 'with_approver'">
                                <select
                                    ref="assigned_officer"
                                    :disabled="!canAction"
                                    class="form-control"
                                    v-model="proposal.assigned_approver"
                                    @change="assignTo()">
                                    <option v-for="member in proposal.allowed_assessors" :value="member.id">{{ member.first_name }} {{ member.last_name }}</option>
                                </select>
                                <div class="text-end">
                                    <a v-if="canAssess && proposal.assigned_approver != proposal.current_assessor.id" @click.prevent="assignRequestUser()" class="actionBtn pull-right">Assign to me</a>
                                </div>
                            </template>
                            <template v-else>
                                <select
                                    ref="assigned_officer"
                                    :disabled="!canAction"
                                    class="form-control"
                                    v-model="proposal.assigned_officer"
                                    @change="assignTo()">
                                    <option v-for="member in proposal.allowed_assessors" :value="member.id">{{ member.first_name }} {{ member.last_name }}</option>
                                </select>
                                <div class="text-end">
                                    <a v-if="canAssess && proposal.assigned_officer != proposal.current_assessor.id" @click.prevent="assignRequestUser()" class="actionBtn pull-right">Assign to me</a>
                                </div>
                            </template>
                        </div>
                    </div>

                    <template v-if="show_toggle_proposal">
                        <div class="col-sm-12">
                            <strong>Proposal</strong><br/>
                            <a class="actionBtn" v-if="!showingProposal" @click.prevent="toggleProposal()">Show Application</a>
                            <a class="actionBtn" v-else @click.prevent="toggleProposal()">Hide Application</a>
                        </div>
                        <div class="col-sm-12">
                            <div class="separator"></div>
                        </div>
                    </template>
                    <template v-if="show_toggle_requirements">
                        <div class="col-sm-12">
                            <strong>Conditions</strong><br/>
                            <a class="actionBtn" v-if="!showingRequirements" @click.prevent="toggleRequirements()">Show Conditions</a>
                            <a class="actionBtn" v-else @click.prevent="toggleRequirements()">Hide Conditions</a>
                        </div>
                        <div class="col-sm-12">
                            <div class="separator"></div>
                        </div>
                    </template>

                    <div class="col-sm-12">
                        <div class="separator"></div>
                    </div>
                            <template v-if="proposal.processing_status == 'With Assessor' || proposal.processing_status == 'With Referral'">
                                <div class="col-sm-12">
                                    <strong>Referrals</strong><br/>
                                    <div class="form-group">
                                        <select :disabled="!canLimitedAction" ref="department_users" class="form-control">
                                            <option value="null"></option>
                                            <option v-for="user in department_users" :value="user.email">{{user.name}}</option>
                                        </select>
                                        <template v-if='!sendingReferral'>
                                            <template v-if="selected_referral">
                                                <label class="control-label pull-left"  for="Name">Comments</label>
                                                <textarea class="form-control comments_to_referral" name="name" v-model="referral_text"></textarea>
                                                <div class="text-end">
                                                    <a v-if="canLimitedAction" @click.prevent="sendReferral()" class="actionBtn">Send</a>
                                                </div>
                                            </template>
                                        </template>
                                        <template v-else>
                                            <span v-if="canLimitedAction" @click.prevent="sendReferral()" disabled class="actionBtn text-primary pull-right">
                                                Sending Referral&nbsp;
                                                <i class="fa fa-circle-o-notch fa-spin fa-fw"></i>
                                            </span>
                                        </template>
                                    </div>
                                    <table class="table small-table">
                                        <tr>
                                            <th>Referral</th>
                                            <th>Status/Action</th>
                                        </tr>
                                        <tr v-for="r in proposal.latest_referrals">
                                            <td>
                                                <small><strong>{{r.referral_obj.first_name}} {{ r.referral_obj.last_name }}</strong></small><br/>
                                                <small><strong>{{r.lodged_on | formatDate}}</strong></small>
                                            </td>
                                            <td>
                                                <small><strong>{{r.processing_status}}</strong></small><br/>
                                                <template v-if="r.processing_status == 'Awaiting'">
                                                    <small v-if="canLimitedAction"><a @click.prevent="remindReferral(r)" href="#">Remind</a> / <a @click.prevent="recallReferral(r)" href="#">Recall</a></small>
                                                </template>
                                                <template v-else>
                                                    <small v-if="canLimitedAction"><a @click.prevent="resendReferral(r)" href="#">Resend</a></small>
                                                </template>
                                            </td>
                                        </tr>
                                    </table>

                                    <MoreReferrals 
                                        @refreshFromResponse="refreshFromResponse" 
                                        :proposal="proposal" 
                                        :canAction="canLimitedAction" 
                                        :isFinalised="isFinalised" 
                                        :referral_url="referralListURL"
                                    />
                                </div>
                                <div class="col-sm-12">
                                    <div class="separator"></div>
                                </div>
                            </template>


                    <div v-if="display_actions">
                        <div>
                            <strong>Action</strong>
                        </div>

                        <div class="" v-if="display_action_enter_conditions">
                            <button
                                class="btn btn-primary w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="switchStatus('with_assessor_conditions')"
                            >Enter Conditions</button>
                        </div>

                        <div class="" v-if="display_action_complete_referral">
                            <button
                                class="btn btn-primary w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="completeReferral()"
                            >Complete Referral</button>
                        </div>

                        <div class="" v-if="display_action_request_amendment">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="amendmentRequest()"
                            >Request Amendment</button>
                        </div>

                        <div class="" v-if="display_action_propose_decline">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="proposedDecline()"
                            >Propose Decline</button>
                        </div>

                        <div class="" v-if="display_action_require_das">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="requireDas()"
                            >Require DAS</button>
                        </div>

                        <div class="" v-if="display_action_complete_editing">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="completeEditing()"
                            >Complete Editing</button>
                        </div>

                        <div class="" v-if="display_action_back_to_application">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="switchStatus('with_assessor')"
                            >Back To Application</button>
                        </div>

                        <div class="" v-if="display_action_propose_approve">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="proposedApproval()"
                            >Propose Approve</button>
                        </div>

                        <div class="" v-if="display_action_back_to_assessor">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                :disabled="can_user_edit"
                                @click.prevent="switchStatus('with_assessor')"
                            >Back To Assessor</button>
                        </div>

                        <div class="" v-if="display_action_approve">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                @click.prevent="issueProposal()"
                            >Approve</button>
                        </div>

                        <div class="" v-if="display_action_decline">
                            <button
                                class="btn btn-primary  w-75 my-1"
                                @click.prevent="declineProposal()"
                            >Decline</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints, helpers, constants } from '@/utils/hooks'
import MoreReferrals from '@common-utils/more_referrals.vue'

export default {
    name: 'Workflow',
    data: function() {
        let vm = this;

        let PS = constants.PROPOSAL_STATUS
        let ROLES = constants.ROLES
        let conf_buttons = [ // List the statuses for which the button is to be displayed
            {
                'enter_conditions': {
                    'registration_of_interest': [],  // No conditions for registration_of_interest
                    'lease_licence': [PS.WITH_ASSESSOR, PS.WITH_REFERRAL,],
                    'roles_allowed': [ROLES.ASSESSOR, ROLES.REFERRAL,]
                },
                'complete_referral': {
                    'registration_of_interest': [PS.WITH_REFERRAL,],
                    'lease_licence': [PS.WITH_REFERRAL,],
                    'roles_allowed': [ROLES.REFERRAL,],
                },
                'request_amendment': {
                    'registration_of_interest': [PS.WITH_ASSESSOR,],
                    'lease_licence': [PS.WITH_ASSESSOR,],
                    'roles_allowed': [ROLES.ASSESSOR,]
                },
                'propose_decline': {
                    'registration_of_interest': [PS.WITH_ASSESSOR, PS.WITH_ASSESSOR_CONDITIONS,], // There should not be with_assessor_conditions status for registration_of_interest
                    'lease_licence': [PS.WITH_ASSESSOR,],
                    'roles_allowed': [ROLES.ASSESSOR,]
                },
                'back_to_application': {
                    'registration_of_interest': [],  // No conditions for the registration_of_interest
                    'lease_licence': [PS.WITH_ASSESSOR_CONDITIONS,],
                    'roles_allowed': [ROLES.ASSESSOR, ROLES.REFERRAL,]
                },
                'propose_approve': {
                    'registration_of_interest': [PS.WITH_ASSESSOR, PS.WITH_ASSESSOR_CONDITIONS,], // There should not be with_assessor_conditions status for registration_of_interest
                    'lease_licence': [PS.WITH_ASSESSOR_CONDITIONS,],
                    'roles_allowed': [ROLES.ASSESSOR,]
                },
                'back_to_assessor': {
                    'registration_of_interest': [PS.WITH_APPROVER,],
                    'lease_licence': [PS.WITH_APPROVER,],
                    'roles_allowed': [ROLES.APPROVER,]
                },
                'approve': {
                    'registration_of_interest': [PS.WITH_APPROVER,],
                    'lease_licence': [PS.WITH_APPROVER,],
                    'roles_allowed': [ROLES.APPROVER,]
                },
                'decline': {
                    'registration_of_interest': [PS.WITH_APPROVER],
                    'lease_licence': [PS.WITH_APPROVER,],
                    'roles_allowed': [ROLES.APPROVER,]
                },
                'require_das': {
                    'registration_of_interest': [],
                    'lease_licence': [PS.WITH_ASSESSOR],
                    'roles_allowed': [ROLES.ASSESSOR,]
                },
                'complete_editing': {
                    'registration_of_interest': [],
                    'lease_licence': [PS.APPROVED_EDITING_INVOICING,],
                    'roles_allowed': [ROLES.ASSESSOR,]
                },
            },
        ]

        class Button{
            constructor(id, condition){
                this._id = id
                this._condition = condition
            }

            get_allowed_ids(key_name){
                let me = this

                let displayable_status_ids = me._condition[key_name].map(a_status => {
                    if (a_status.hasOwnProperty('ID'))
                        return a_status.ID
                    else if (a_status.hasOwnProperty('id'))
                        return a_status.id
                    else if (a_status.hasOwnProperty('Id'))
                        return a_status.Id
                    else
                        return a_status
                })

                return displayable_status_ids
            }

            absorb_type_difference(processing_status_id){
                let ret_value = ''

                if(processing_status_id.hasOwnProperty('ID'))
                    ret_value = processing_status_id.ID
                else if(processing_status_id.hasOwnProperty('id'))
                    ret_value = processing_status_id.id
                else if(processing_status_id.hasOwnProperty('Id'))
                    ret_value = processing_status_id.Id
                else
                    ret_value = processing_status_id.toLowerCase()

                return ret_value
            }

            displayable(application_type, processing_status_id, accessing_user_roles){
                let me = this
                if (vm.debug)
                    return true

                let displayable_status_ids = me.get_allowed_ids(application_type)
                let displayable_role_ids = me.get_allowed_ids('roles_allowed')
                let my_processing_status_id = me.absorb_type_difference(processing_status_id)

                /*
                console.log('---------' + me._id + '--------------')
                console.log(displayable_status_ids)
                console.log(displayable_role_ids)
                console.log(my_processing_status_id)
                */

                let status_allowed = displayable_status_ids.includes(my_processing_status_id)
                let intersection = displayable_role_ids.filter(x => accessing_user_roles.includes(x));

                return status_allowed && intersection.length > 0
            }
        }

        return {
            showingProposal: false,
            showingRequirements: false,

            "loading": [],

            department_users : [],
            selected_referral: [],
            referral_text: '',
            sendingReferral: false,
            buttons: (function(){
                let button_array = {}
                conf_buttons.forEach(dict => {
                    for (let [key, value] of Object.entries(dict)) {
                        button_array[key] = new Button(key, value)
                    }
                })
                return button_array
            })()
        }
    },
    props: {
        proposal: {
            type: Object,
            default: null,
        },
        isFinalised: {
            type: Boolean,
            default: false,
        },
        canAction: {
            type: Boolean,
            default: false,
        },
        canAssess: {
            type: Boolean,
            default: false,
        },
        can_user_edit: {
            type: Boolean,
            default: false,
        },
        //proposed_decline_status: {
        //    type: Boolean,
        //    default: false,
        //},
    },
    components: {
        MoreReferrals,
    },
    computed: {
        proposal_form_url: function() {
            return (this.proposal) ? `/api/proposal/${this.proposal.id}/assessor_save.json` : '';
        },
        referralListURL: function(){
            return this.proposal!= null ? helpers.add_endpoint_json(api_endpoints.referrals,'datatable_list')+'?proposal='+this.proposal.id : '';
        },
        canLimitedAction:function(){
            // TOOD: refer to proposal_apiary.vue
            return true
        },
        show_toggle_proposal: function(){
            if(this.proposal.processing_status == constants.WITH_ASSESSOR_CONDITIONS || this.proposal.processing_status == constants.WITH_APPROVER || this.isFinalised){
                return true
            } else {
                return false
            }
        },
        show_toggle_requirements: function(){
            if(this.proposal.processing_status == constants.WITH_APPROVER || this.isFinalised){
                return true
            } else {
                return false
            }
        },
        debug: function(){
            return (this.$route.query.debug && this.$route.query.debug == 'true') ? true : false
        },
        display_referrals: function(){
            return true
        },
        display_actions: function(){
            if (this.debug) return true

            return !this.isFinalised && this.canAction
        },
        display_action_complete_referral: function(){
            return this.buttons['complete_referral'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_request_amendment: function(){
            return this.buttons['request_amendment'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_enter_conditions: function(){
            return this.buttons['enter_conditions'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_propose_decline: function(){
            return this.buttons['propose_decline'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_back_to_application: function(){
            return this.buttons['back_to_application'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_propose_approve: function(){
            return this.buttons['propose_approve'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_require_das: function(){
            return this.buttons['require_das'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_complete_editing: function(){
            return this.buttons['complete_editing'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_back_to_assessor: function(){
            return this.buttons['back_to_assessor'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_approve: function(){
            return this.buttons['approve'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
        display_action_decline: function(){
            return this.buttons['decline'].displayable(this.proposal.application_type.name, this.proposal.processing_status_id, this.proposal.accessing_user_roles)
        },
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
    methods: {
        completeEditing: function(){
        },
        requireDas: function(){
        },
        checkAssessorData: function(){
            //check assessor boxes and clear value of hidden assessor boxes so it won't get printed on approval pdf.

            //select all fields including hidden fields
            var all_fields = $('input[type=text]:required, textarea:required, input[type=checkbox]:required, input[type=radio]:required, input[type=file]:required, select:required')

            all_fields.each(function() {
                var ele=null;
                //check the fields which has assessor boxes.
                ele = $("[name="+this.name+"-Assessor]");
                if(ele.length>0){
                    var visiblity=$("[name="+this.name+"-Assessor]").is(':visible')
                    if(!visiblity){
                        if(ele[0].value!=''){
                            ele[0].value=''
                        }
                    }
                }
            });
        },
        initialiseSelects: function(){
            let vm = this;
            $(vm.$refs.department_users).select2({
                "theme": "bootstrap-5",
                allowClear: true,
                placeholder:"Select Referral"
            }).
            on("select2:select",function (e) {
                var selected = $(e.currentTarget);
                vm.selected_referral = selected.val();
            }).
            on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                vm.selected_referral = ''
            });
            vm.initialiseAssignedOfficerSelect();
        },
        initialiseAssignedOfficerSelect:function(reinit=false){
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_officer).data('select2') ? $(vm.$refs.assigned_officer).select2('destroy'): '';
            }
            // Assigned officer select
            $(vm.$refs.assigned_officer).select2({
                "theme": "bootstrap-5",
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
        updateAssignedOfficerSelect:function(selected_user){
            let vm = this;
            //if (vm.proposal.processing_status == 'With Approver'){
                //$(vm.$refs.assigned_officer).val(vm.proposal.assigned_approver);
                $(vm.$refs.assigned_officer).val(selected_user)
                $(vm.$refs.assigned_officer).trigger('change')
            //}
            //else{
            //    $(vm.$refs.assigned_officer).val(vm.proposal.assigned_officer);
            //    $(vm.$refs.assigned_officer).trigger('change');
            //}
        },
        refreshFromResponse:function(response){
            let vm = this;
            vm.proposal = helpers.copyObject(response.body);
            vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
            vm.$nextTick(() => {
                vm.initialiseAssignedOfficerSelect(true);
                vm.updateAssignedOfficerSelect();
            });
        },
        fetchDeparmentUsers: async function(){
            this.loading.push('Loading Department Users');
            try {
                const response  = await fetch(api_endpoints.department_users)
                const resData = response.json()
                this.department_users = Object.assign(resData)
                this.loading.splice('Loading Department Users',1);
            } catch(error) {
                console.log(error);
                this.loading.splice('Loading Department Users',1);
            }
        },
        sendReferral: async function(){
            this.checkAssessorData();
            let formData = new FormData(vm.form);
            this.sendingReferral = true;
            try {
                const res = await fetch(this.proposal_form_url, { body: {'proposal': this.proposal}, method: 'POST' })
                const resData = await res.json()
                let data = {'email':this.selected_referral, 'text': this.referral_text}
                this.sendingReferral = true;
                const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposals, (this.proposal.id + '/assesor_send_referral')), 
                { 
                    body: JSON.stringify(data),
                    method: 'POST',
                })
                this.sendingReferral = false;
                    //this.proposal = response.body;  // <== Mutating props... Is this fine??? // 20220509 - no, it is not
                    /* 
                    // Don't use this endpoint
                    $(vm.$refs.department_users).val(null).trigger("change");  // Unselect referral
                    vm.selected_referral = '';
                    vm.referral_text = '';
                    },
                    error => {
                        $(vm.$refs.department_users).val(null).trigger("change");  // Unselect referral
                        vm.sendingReferral = false;
                    }
                    */
            } catch (error) {
                swal(
                    'Referral Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        remindReferral: async function(r){
            try {
                fetch(helpers.add_endpoint_json(api_endpoints.referrals,r.id+'/remind'))
                //this.proposal = response.body;
                //vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
                swal.fire(
                    'Referral Reminder',
                    'A reminder has been sent to '+r.referral,
                    'success'
                )
            } catch (error) {
                swal.fire(
                    'Proposal Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        resendReferral:async function(r){
            try {
                await fetch(helpers.add_endpoint_json(api_endpoints.referrals,r.id+'/resend'))
                //vm.proposal = response.body;
                //vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
                swal.fire(
                    'Referral Resent',
                    'The referral has been resent to '+r.referral,
                    'success'
                )
            } catch (error) {
                swal.fire(
                    'Proposal Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        recallReferral:async function(r){
            swal.fire({
                    title: "Loading...",
                    //text: "Loading...",
                    allowOutsideClick: false,
                    allowEscapeKey:false,
                    onOpen: () =>{
                        swal.showLoading()
                    }
            })
            try {
                await fetch(helpers.add_endpoint_json(api_endpoints.referrals,r.id+'/recall'))
                swal.hideLoading();
                swal.close();
                /*
                vm.proposal = response.body;
                vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
                */
                await swal.fire(
                    'Referral Recall',
                    'The referall has been recalled from '+r.referral,
                    'success'
                )
            } catch (error) {
                swal.fire(
                    'Proposal Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            }
        },
        assignRequestUser: function(){
            this.$emit('assignRequestUser')
        },
        assignTo: function(){
            this.$emit('assignTo')
        },
        toggleProposal:function(){
            this.showingProposal = !this.showingProposal;
            this.$emit('toggleProposal', this.showingProposal)
        },
        toggleRequirements:function(){
            this.showingRequirements = !this.showingRequirements;
            this.$emit('toggleRequirements', this.showingRequirements)
        },
        switchStatus: function(value){
            this.$emit('switchStatus', value)
        },
        amendmentRequest: function(){
            this.$emit('amendmentRequest')
        },
        completeReferral: function(){
            this.$emit('completeReferral')
        },
        proposedDecline: function(){
            this.$emit('proposedDecline')
        },
        proposedApproval: function(){
            this.$emit('proposedApproval')
        },
        issueProposal: function(){
            this.$emit('issueProposal')
        },
        declineProposal: function(){
            this.$emit('declineProposal')
        },
    },
    created: function(){
        this.fetchDeparmentUsers()
    },
    mounted: function(){
        let vm = this
        this.$nextTick(() => {
            vm.initialiseSelects();
        })
    },
}
</script>

<style scoped>
.actionBtn {
    cursor: pointer;
}
.separator {
    border: 1px solid;
    margin-top: 15px;
    margin-bottom: 10px;
    width: 100%;
}
.referral_comment_textarea {
    resize: vertical;
}
.comments_to_referral {
    resize: vertical;
}
</style>
