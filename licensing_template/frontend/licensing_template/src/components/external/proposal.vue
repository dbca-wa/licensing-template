<template lang="html">
    <div class="container" >
        <div v-if="!proposal_readonly">
          <div v-if="hasAmendmentRequest" class="row" style="color:red;">
              <div class="col-lg-12 pull-right">
                <div class="card card-default">
                  <div class="card-header">
                    <h3 class="card-title" style="color:red;">An amendment has been requested for this Application
                      <a class="panelClicker" :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                      </a>
                    </h3>
                  </div>
                  <div class="card-body collapse in" :id="pBody">
                    <div v-for="a in amendment_request">
                      <p>Reason: {{a.reason}}</p>
                      <p>Details: <p v-for="t in splitText(a.text)">{{t}}</p></p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div id="error" v-if="missing_fields.length > 0" style="margin: 10px; padding: 5px; color: red; border:1px solid red;">
            <b>Please answer the following mandatory question(s):</b>
            <ul>
                <li v-for="error in missing_fields">
                    {{ error.label }}
                </li>
            </ul>
        </div>
        <ApplicationForm
        v-if="proposal"
        :proposal="proposal"
        :is_external="true"
        ref="application_form"
        :readonly="readonly"
        :submitterId="submitterId"
        @updateSubmitText="updateSubmitText"
        :registrationOfInterest="registrationOfInterest"
        :leaseLicence="leaseLicence"
        />

        <div>
            <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
            <input type='hidden' name="schema" :value="JSON.stringify(proposal)" />
            <input type='hidden' name="proposal_id" :value="1" />

            <div class="navbar fixed-bottom" style="background-color: #f5f5f5;">
                <div v-if="proposal && !proposal.readonly" class="container">
                    <div class="col-md-12 text-end">
                        <button v-if="saveExitProposal" type="button" class="btn btn-primary" disabled>
                            Save and Exit&nbsp;<i v-show="terms_and_conditions_checked" class="fa fa-circle-o-notch fa-spin fa-fw"></i>
                        </button>
                        <input v-else type="button" @click.prevent="save_exit" class="btn btn-primary" value="Save and Exit" :disabled="savingProposal || paySubmitting"/>

                        <button v-if="savingProposal" type="button" class="btn btn-primary" disabled>
                            Save and Continue&nbsp;<i v-show="terms_and_conditions_checked" class="fa fa-circle-o-notch fa-spin fa-fw"></i>
                        </button>
                        <input v-else type="button" @click.prevent="save" class="btn btn-primary" value="Save and Continue" :disabled="saveExitProposal || paySubmitting"/>

                        <button v-if="paySubmitting" type="button" class="btn btn-primary" disabled>
                            {{ submitText }}&nbsp; <i v-show="terms_and_conditions_checked" class="fa fa-circle-o-notch fa-spin fa-fw"></i>
                        </button>

                        <input v-else
                            type="button"
                            @click.prevent="submit"
                            class="btn btn-primary"
                            :value="submitText"
                            :disabled="saveExitProposal || savingProposal || disableSubmit"
                            id="submitButton"
                            :title="disabledSubmitText"
                        />

                        <input id="save_and_continue_btn" type="hidden" @click.prevent="save_wo_confirm" class="btn btn-primary" value="Save Without Confirmation"/>
                    </div>
                </div>
                <div v-else>
                    <div class="container-fluid">
                        <router-link class="btn btn-primary" :to="{name: 'external-dashboard'}">Back to Dashboard</router-link>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import ApplicationForm from '../form.vue';
import { api_endpoints, helpers } from '@/utils/hooks'

export default {
  name: 'ExternalProposal',
  data: function() {
    return {
      "proposal": null,
      "loading": [],
      amendment_request: [],
      //isDataSaved: false,
      proposal_readonly: true,
      hasAmendmentRequest: false,
      submitting: false,
      saveExitProposal: false,
      savingProposal:false,
      paySubmitting:false,
      newText: "",
      pBody: 'pBody',
      missing_fields: [],
      proposal_parks:null,
      terms_and_conditions_checked: false,
      vesselChanged: false,
      // AUA
      mooringOptionsChanged: false,
      // WLA
      mooringPreferenceChanged: false,
      submitText: "Submit",
    }
  },
  components: {
      ApplicationForm,
  },
  computed: {
        registrationOfInterest: function(){
            let retVal = false;
            if (this.proposal && this.proposal.application_type.name === 'registration_of_interest') {
                retVal = true;
            }
            return retVal;
        },
        leaseLicence: function(){
            let retVal = false;
            if (this.proposal && this.proposal.application_type.name === 'lease_licence') {
                retVal = true;
            }
            return retVal;
        },

      disableSubmit: function() {
          let disable = false;
          if (this.proposal.proposal_type.code ==='amendment') {
              if (['aaa', 'mla'].includes(this.proposal.application_type_code) && !this.vesselChanged) {
                  disable = true;
              } else if (this.proposal.application_type_code === 'wla' && !this.vesselChanged && !this.mooringPreferenceChanged) {
                  disable = true;
              } else if (this.proposal.application_type_code === 'aua' && !this.vesselChanged && !this.mooringOptionsChanged) {
                  disable = true;
              }
          }
          return disable;
      },
      disabledSubmitText: function() {
          let text = "";
          if (this.disableSubmit) {
              text = "No relevant details have been detected in this amendment application";
          }
          return text;
      },
      autoRenew: function() {
          let renew = false;
          if (!this.vesselChanged && !this.mooringOptionsChanged && this.proposal.proposal_type.code ==='renewal' && ['mla', 'aua'].includes(this.proposal.application_type_code)) {
              renew = true;
          }
          return renew;
      },
      submitterId: function() {
          let submitter = null;
          if (this.proposal && this.proposal.submitter && this.proposal.submitter.id) {
              submitter = this.proposal.submitter.id;
          }
          return submitter;
      },
      readonly: function() {
          let returnVal = true;
          if (this.proposal.processing_status === 'Draft') {
              returnVal = false;
          }
          return returnVal;
      },
      isLoading: function() {
        return this.loading.length > 0
      },
      csrf_token: function() {
        return helpers.getCookie('csrftoken')
      },
      proposal_form_url: function() {
        return (this.proposal) ? `/api/proposal/${this.proposal.id}/draft.json` : '';
          // revert to above
        //return (this.proposal) ? `/api/proposal/${this.proposal.id}/submit.json` : '';
      },
      application_fee_url: function() {
          return (this.proposal) ? `/application_fee/${this.proposal.id}/` : '';
      },
      confirmation_url: function() {
          // For authorised user application and mooring licence application
          return (this.proposal) ? `/confirmation/${this.proposal.id}/` : '';
      },
      proposal_submit_url: function() {
        return (this.proposal) ? `/api/proposal/${this.proposal.id}/submit.json` : '';
        //return this.submit();
      },
      canEditActivities: function(){
        return this.proposal ? this.proposal.can_user_edit: 'false';
      },
      canEditPeriod: function(){
        return this.proposal ? this.proposal.can_user_edit: 'false';
      },
      /*
      application_type_tclass: function(){
        return api_endpoints.t_class;
      },
      application_type_filming: function(){
        return api_endpoints.filming;
      },
      application_type_event: function(){
        return api_endpoints.event;
      },
      */
      trainingCompleted: function(){
        if(this.proposal.application_type== 'Event')
          {
            return this.proposal.applicant_training_completed;
          }
        return this.proposal.training_completed;
      },
      showElectoralRoll: function() {
          let show = false;
          if (this.proposal && ['wla', 'mla'].includes(this.proposal.application_type_code)) {
              show = true;
          }
          return show;
      },
      applicationTypeCode: function() {
          if (this.proposal) {
              return this.proposal.application_type_code;
          }
      },
      amendmentOrRenewal: function(){
          let amendRenew=false;
          //if (this.proposal && ['amendment', 'renewal'].includes(this.proposal.proposal_type.code))
          if(this.proposal && this.proposal.proposal_type && this.proposal.proposal_type.code !== 'new'){
              amendRenew=true;
          }
          return amendRenew;
      },
      /*
      annualAdmissionApplication: function() {
          let retVal = false;
          if (this.proposal && this.proposal.application_type_code === 'aaa') {
              retVal = true;
          }
          return retVal;
      },
      */

  },
  methods: {
      /*
    addEventListeners: function() {
        const submitButton = document.getElementById("submitButton");
        console.log(submitButton);
        submitButton.addEventListener("mouseenter", function(e) {
            e.target.title = "mouse over"
        }, false);
    },
    */
    updateMooringAuth: function(changed) {
        this.mooringOptionsChanged = changed;
    },
    updateVesselChanged: function(vesselChanged) {
        this.vesselChanged = vesselChanged;
    },
    updateMooringPreference: function(preferenceChanged) {
        this.mooringPreferenceChanged = preferenceChanged;
    },
    proposal_refs:function(){
      if(this.applicationTypeCode == 'wla') {
          return this.$refs.waiting_list_application;
      } else if (this.applicationTypeCode == 'aaa') {
          return this.$refs.annual_admission_application;
      } else if (this.applicationTypeCode == 'aua') {
          return this.$refs.authorised_user_application;
      } else if (this.applicationTypeCode == 'mla') {
          return this.$refs.mooring_licence_application;
      } /*else if(vm.proposal.application_type == vm.application_type_filming) {
          return vm.$refs.proposal_filming;
      } else if(vm.proposal.application_type == vm.application_type_event) {
          return vm.$refs.proposal_event;
      }
      */
    },
    updateSubmitText: function(submitText) {
        this.submitText = submitText;
    },
      /*
    set_submit_text: function() {
        //let submitText = 'Submit';
        if(['wla', 'aaa'].includes(this.proposal.application_type_code)) {
            if (this.proposal.fee_paid){
                this.submitText = 'Submit';
            } else {
                this.submitText = 'Pay / Submit';
            }
        }
        //return submitText;
    },
    */
    save_applicant_data:function(){
      if(this.proposal.applicant_type == 'SUB')
      {
        this.proposal_refs().$refs.profile.updatePersonal();
        this.proposal_refs().$refs.profile.updateAddress();
        this.proposal_refs().$refs.profile.updateContact();
      }
        /*
      if(vm.proposal.applicant_type == 'ORG'){
        vm.proposal_refs().$refs.organisation.updateDetails();
        vm.proposal_refs().$refs.organisation.updateAddress();
      }
      */
    },

    save: async function(withConfirm=true, url=this.proposal_form_url) {
        let vm = this;
        vm.savingProposal=true;
        //vm.save_applicant_data();
        let payload = {
            proposal: {}
        }

        if (this.registrationOfInterest) {
            payload.proposal = {
                    'exclusive_use': this.proposal.exclusive_use,
                    'long_term_use': this.proposal.long_term_use,
                    'consistent_purpose': this.proposal.consistent_purpose,
                    'consistent_plan': this.proposal.consistent_plan,
                    'clearing_vegetation': this.proposal.clearing_vegetation,
                    'ground_disturbing_works': this.proposal.ground_disturbing_works,
                    'heritage_site': this.proposal.heritage_site,
                    'environmentally_sensitive': this.proposal.environmentally_sensitive,
                    'wetlands_impact': this.proposal.wetlands_impact,
                    'building_required': this.proposal.building_required,
                    'significant_change': this.proposal.significant_change,
                    'aboriginal_site': this.proposal.aboriginal_site,
                    'native_title_consultation': this.proposal.native_title_consultation,
                    'mining_tenement': this.proposal.mining_tenement,
                }
            payload.proposal.details_text = this.$refs.application_form.$refs.registration_of_interest.$refs.details_text.detailsText;
            payload.proposal.exclusive_use_text = this.$refs.application_form.$refs.registration_of_interest.$refs.exclusive_use_text.detailsText;
            payload.proposal.long_term_use_text = this.$refs.application_form.$refs.registration_of_interest.$refs.long_term_use_text.detailsText;
            payload.proposal.consistent_purpose_text = this.$refs.application_form.$refs.registration_of_interest.$refs.consistent_purpose_text.detailsText;
            payload.proposal.consistent_plan_text = this.$refs.application_form.$refs.registration_of_interest.$refs.consistent_plan_text.detailsText;
            payload.proposal.clearing_vegetation_text = this.$refs.application_form.$refs.registration_of_interest.$refs.clearing_vegetation_text.detailsText;
            payload.proposal.ground_disturbing_works_text = this.$refs.application_form.$refs.registration_of_interest.$refs.ground_disturbing_works_text.detailsText;
            payload.proposal.heritage_site_text = this.$refs.application_form.$refs.registration_of_interest.$refs.heritage_site_text.detailsText;
            payload.proposal.environmentally_sensitive_text = this.$refs.application_form.$refs.registration_of_interest.$refs.environmentally_sensitive_text.detailsText;
            payload.proposal.wetlands_impact_text = this.$refs.application_form.$refs.registration_of_interest.$refs.wetlands_impact_text.detailsText;
            payload.proposal.building_required_text = this.$refs.application_form.$refs.registration_of_interest.$refs.building_required_text.detailsText;
            payload.proposal.significant_change_text = this.$refs.application_form.$refs.registration_of_interest.$refs.significant_change_text.detailsText;
            payload.proposal.aboriginal_site_text = this.$refs.application_form.$refs.registration_of_interest.$refs.aboriginal_site_text.detailsText;
            payload.proposal.native_title_consultation_text = this.$refs.application_form.$refs.registration_of_interest.$refs.native_title_consultation_text.detailsText;
            payload.proposal.mining_tenement_text = this.$refs.application_form.$refs.registration_of_interest.$refs.mining_tenement_text.detailsText;
        } else if (this.leaseLicence) {
            payload.proposal.profit_and_loss_text = this.$refs.application_form.$refs.lease_licence.$refs.profit_and_loss_text.detailsText;
            payload.proposal.cash_flow_text = this.$refs.application_form.$refs.lease_licence.$refs.cash_flow_text.detailsText;
            payload.proposal.capital_investment_text = this.$refs.application_form.$refs.lease_licence.$refs.capital_investment_text.detailsText;
            payload.proposal.financial_capacity_text = this.$refs.application_form.$refs.lease_licence.$refs.financial_capacity_text.detailsText;
            payload.proposal.available_activities_text = this.$refs.application_form.$refs.lease_licence.$refs.available_activities_text.detailsText;
            payload.proposal.market_analysis_text = this.$refs.application_form.$refs.lease_licence.$refs.market_analysis_text.detailsText;
            payload.proposal.staffing_text = this.$refs.application_form.$refs.lease_licence.$refs.staffing_text.detailsText;
            payload.proposal.key_personnel_text = this.$refs.application_form.$refs.lease_licence.$refs.key_personnel_text.detailsText;
            payload.proposal.key_milestones_text = this.$refs.application_form.$refs.lease_licence.$refs.key_milestones_text.detailsText;
            payload.proposal.risk_factors_text = this.$refs.application_form.$refs.lease_licence.$refs.risk_factors_text.detailsText;
            payload.proposal.legislative_requirements_text = this.$refs.application_form.$refs.lease_licence.$refs.legislative_requirements_text.detailsText;
        }
        if (this.$refs.application_form.componentMapOn) {
            payload.proposal_geometry = this.$refs.application_form.$refs.component_map.getJSONFeatures();
        }
        const res = await fetch(url, { body: JSON.stringify(payload), method: 'POST' });
        if (res.ok) {
            if (withConfirm) {
                swal(
                    'Saved',
                    'Your application has been saved',
                    'success'
                );
            };
            vm.savingProposal=false;
            //this.$refs.application_form.incrementComponentMapKey();
            const resData = await res.json()
            this.proposal = resData;
            this.$nextTick(async () => {
                this.$refs.application_form.incrementComponentMapKey();
            });
            return resData;
        } else {
            const err = await res.json()
            swal.fire({
                title: "Please fix following errors before saving",
                //text: err.bodyText,
                text: JSON.stringify(err),
                icon:'error'
            });
            vm.savingProposal=false;
        }
    },
    save_exit: function() {
      let vm = this;
      this.submitting = true;
      this.saveExitProposal=true;
      this.save();
      this.saveExitProposal=false;
      // redirect back to dashboard
      vm.$router.push({
        name: 'external-dashboard'
      });
    },

    save_wo_confirm: function() {
      this.save(false);
    },
    setdata: function(readonly){
      this.proposal_readonly = readonly;
    },

    setAmendmentData: function(amendment_request){
      this.amendment_request = amendment_request;

      if (amendment_request.length > 0)
        this.hasAmendmentRequest = true;

    },

    splitText: function(aText){
      let newText = '';
      newText = aText.split("\n");
      return newText;

    },

    leaving: function(e) {
      let vm = this;
      var dialogText = 'You have some unsaved changes.';
      if (!vm.proposal_readonly && !vm.submitting){
        e.returnValue = dialogText;
        return dialogText;
      }
      else{
        return null;
      }
    },

    highlight_missing_fields: function(){
        let vm = this;
        for (var missing_field of vm.missing_fields) {
            $("#" + missing_field.id).css("color", 'red');
        }
    },
    can_submit: function(){
      let vm=this;
      let blank_fields=[]

      if (vm.proposal.application_type==vm.application_type_tclass) {
          if (vm.$refs.proposal_tclass.$refs.other_details.selected_accreditations.length==0 ){
            blank_fields.push(' Level of Accreditation is required')
          }
          else{
            for(var i=0; i<vm.proposal.other_details.accreditations.length; i++){
              if(!vm.proposal.other_details.accreditations[i].is_deleted && vm.proposal.other_details.accreditations[i].accreditation_type!='no'){
                if(vm.proposal.other_details.accreditations[i].accreditation_expiry==null || vm.proposal.other_details.accreditations[i].accreditation_expiry==''){
                  blank_fields.push('Expiry date for accreditation type '+vm.proposal.other_details.accreditations[i].accreditation_type_value+' is required')
                }
                // var acc_doc_ref='accreditation_file'+vm.proposal.other_details.accreditations[i].accreditation_type;
                var acc_ref= vm.proposal.other_details.accreditations[i].accreditation_type;
                // console.log(acc_doc_ref, acc_ref);
                if(vm.$refs.proposal_tclass.$refs.other_details.$refs[acc_ref][0].$refs.accreditation_file.documents.length==0){
                  blank_fields.push('Accreditation Certificate for accreditation type '+vm.proposal.other_details.accreditations[i].accreditation_type_value+' is required')
                }

              }
            }
          }

          if (vm.proposal.other_details.preferred_licence_period=='' || vm.proposal.other_details.preferred_licence_period==null ){
            blank_fields.push(' Preferred Licence Period is required')
          }
          if (vm.proposal.other_details.nominated_start_date=='' || vm.proposal.other_details.nominated_start_date==null ){
            blank_fields.push(' Licence Nominated Start Date is required')
          }

          if(vm.$refs.proposal_tclass.$refs.other_details.$refs.deed_poll_doc.documents.length==0){
            blank_fields.push(' Deed poll document is missing')
          }

          if(vm.$refs.proposal_tclass.$refs.other_details.$refs.currency_doc.documents.length==0){
            blank_fields.push(' Certificate of currency document is missing')
          }
          if(vm.proposal.other_details.insurance_expiry=='' || vm.proposal.other_details.insurance_expiry==null){
            blank_fields.push(' Certificate of currency expiry date is missing')
          }

      } else if (vm.proposal.application_type==vm.application_type_filming) {
          blank_fields=vm.can_submit_filming()

      } else if (vm.proposal.application_type==vm.application_type_event) {
          blank_fields=vm.can_submit_event();

      }

      if(blank_fields.length==0){
        return true;
      }
      else{
        return blank_fields;
      }

    },
    submit: async function(){
        console.log('in submit()')
        //let vm = this;

        // remove the confirm prompt when navigating away from window (on button 'Submit' click)
        this.submitting = true;
        this.paySubmitting=true;

        try {
            await swal.fire({
                title: this.submitText + " Application",
                text: "Are you sure you want to " + this.submitText.toLowerCase()+ " this application?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: this.submitText
            })
        } catch (cancel) {
            this.submitting = false;
            this.paySubmitting=false;
            return;
        }
        try {
            const res = await this.save(false, this.proposal_submit_url);
            if (res.ok) {
                // change this to confirmation page
                this.$router.push({
                    name: 'submit-proposal',
                    params: {proposal: this.proposal},
                });
            }
        } catch(err) {
            console.log(err)
            await swal.fire({
                title: 'Submit Error',
                html: helpers.apiVueResourceError(err),
                icon: 'error',
            })
            this.savingProposal = false;
            this.paySubmitting = false;
        }
        /*
        if (!this.proposal.fee_paid) {
            this.$nextTick(async () => {
                await this.save_and_pay();
            });
        } else {
            await this.save_without_pay();
        }
        */
    },

  },

  mounted: function() {
  },


  beforeRouteEnter: function(to, from, next) {
      console.log(to)
      console.log(from)
      //console.log(next)
    if (to.params.proposal_id) {
      let vm = this;
      fetch(`/api/proposal/${to.params.proposal_id}.json`).then(res => {
          next(async (vm) => {
              console.log(vm)
              const proposalData = await res.json()
              console.log(proposalData)
              vm.proposal = proposalData;
              });
          },
        err => {
          console.log(err);
        });
    }
  }
}
</script>

<style lang="css" scoped>
.btn-primary {
    margin: 2px;
}
</style>
