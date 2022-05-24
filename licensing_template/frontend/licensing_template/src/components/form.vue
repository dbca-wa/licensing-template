<template lang="html">
    <div class="">
        <div v-if="debug">components/form.vue</div>
        <div v-if="proposal && show_application_title" id="scrollspy-heading" class="" >
            <h4>{{applicationTypeText}} Application: {{proposal.lodgement_number}}</h4>
        </div>

        <div class="">
            <ul class="nav nav-pills" id="pills-tab" role="tablist">
                <li class="nav-item mr-1" role="presentation">
                    <!--a class="nav-link active" id="pills-applicant-tab" data-toggle="pill" href="#pills-applicant" role="tab" aria-controls="pills-applicant" aria-selected="true"-->
                    <button class="nav-link active" id="pills-applicant-tab" data-bs-toggle="pill" data-bs-target="#pills-applicant" role="tab" aria-controls="pills-applicant" aria-selected="true">
                      Applicant
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="pills-map-tab" data-bs-toggle="pill" data-bs-target="#pills-map" role="tab" aria-controls="pills-map" aria-selected="false" @click="toggleComponentMapOn">
                      Map
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="pills-details-tab" data-bs-toggle="pill" data-bs-target="#pills-details" role="tab" aria-controls="pills-details" aria-selected="false">
                      Details
                    </button>
                </li>
                <template v-if="show_related_items_tab">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="pills-related-items-tab" data-bs-toggle="pill" data-bs-target="#pills-related-items" role="tab" aria-controls="pills-related-items" aria-selected="false">
                          Related Items
                        </button>
                    </li>
                </template>
            </ul>
            <div class="tab-content" id="pills-tabContent">
              <div class="tab-pane fade show active" id="pills-applicant" role="tabpanel" aria-labelledby="pills-applicant-tab">
                  <div v-if="is_external">
                      <Profile
                      :isApplication="true"
                      v-if="applicantType == 'SUB'"
                      ref="profile"
                      @profile-fetched="populateProfile"
                      :proposalId="proposal.id"
                      :readonly="readonly"
                      :submitterId="submitterId"
                      />
                  </div>
                  <div v-else>
                    <!-- Applicant
                        :email_user="proposal.submitter"
                        :applicantType="proposal.applicant_type"
                        id="proposalStartApplicant"
                        :readonly="readonly"
                        :showElectoralRoll="showElectoralRoll"
                        :storedSilentElector="silentElector"
                        :proposalId="proposal.id"
                    / -->
                      <Applicant
                          :email_user="email_user_applicant"
                          :applicantType="proposal.applicant_type"
                          id="proposalStartApplicant"
                          :readonly="readonly"
                          :proposalId="proposal.id"
                      />
                  </div>
              </div>
              <div class="tab-pane fade" id="pills-map" role="tabpanel" aria-labelledby="pills-map-tab">
                  <FormSection :formCollapse="false" label="Map" Index="proposal_geometry">
                      <slot name="slot_map_checklist_questions"></slot>
                      <ComponentMap
                          ref="component_map"
                          :is_internal="is_internal"
                          :is_external="is_external"
                          :key="componentMapKey"
                          v-if="componentMapOn"
                          @featuresDisplayed="updateTableByFeatures"
                          :can_modify="can_modify"
                          :display_at_time_of_submitted="show_col_status_when_submitted"
                          @featureGeometryUpdated="featureGeometryUpdated"
                          @popupClosed="popupClosed"
                          :proposal="proposal"
                          :readonly="readonly"
                      />

                  </FormSection>
              </div>
              <div class="tab-pane fade" id="pills-details" role="tabpanel" aria-labelledby="pills-details-tab">
                  <RegistrationOfInterest
                  :proposal="proposal"
                  :readonly="readonly"
                  ref="registration_of_interest"
                  v-if="registrationOfInterest"
                  >
                      <template v-slot:slot_proposal_details_checklist_questions>
                          <slot name="slot_proposal_details_checklist_questions"></slot>
                      </template>

                      <template v-slot:slot_proposal_impact_checklist_questions>
                          <slot name="slot_proposal_impact_checklist_questions"></slot>
                      </template>

                  </RegistrationOfInterest>

                  <LeaseLicence
                  :proposal="proposal"
                  :readonly="readonly"
                  ref="lease_licence"
                  v-if="leaseLicence"
                  >
                  </LeaseLicence>

                  <FormSection label="Other" Index="other_section">
                      <slot name="slot_other_checklist_questions"></slot>
                  </FormSection>

                  <FormSection label="Deed Poll" Index="deed_poll">
                      <slot name="slot_deed_poll_checklist_questions"></slot>
                      <div class="col-sm-12 section-style">
                          <p>
                              <strong>It is a requirement of all lease and licence holders to sign a deed poll to release and indemnify the State of Western Australia.
                              Please note: electronic or digital signatures cannot be accepted.
                              <p></p>
                              The deed poll must be signed and have a witness signature and be dated.  Once signed and dated, please scan and attach the deed poll below.
                              </strong>
                          </p>

                          <label for="deed_poll_document">Deed poll:</label>
                          <FileField
                              :readonly="readonly"
                              ref="deed_poll_document"
                              name="deed_poll_document"
                              id="deed_poll_document"
                              :isRepeatable="true"
                              :documentActionUrl="deedPollDocumentUrl"
                              :replace_button_by_text="true"
                          />
                      </div>
                  </FormSection>

                  <template v-if="show_additional_documents_tab">
                      <FormSection label="Additional Documents" Index="additional_documents">
                          <slot name="slot_additional_documents_checklist_questions"></slot>
                      </FormSection>
                  </template>
              </div>

              <!-- Related Items tab is shown on the internal proposal page -->
              <template v-if="show_related_items_tab">
                  <div class="tab-pane fade" id="pills-related-items" role="tabpanel" aria-labelledby="pills-related-items-tab">
                      <slot name="slot_section_related_items"></slot>
                  </div>
              </template>
            </div>
        </div>
    </div>
</template>

<script>
import Profile from '@/components/user/profile.vue'
import Applicant from '@/components/common/applicant.vue'
import FormSection from '@/components/forms/section_toggle.vue'
import RichText from '@/components/forms/richtext.vue'
import FileField from '@/components/forms/filefield_immediate.vue'
import ComponentMap from '@/components/common/component_map.vue'
import RegistrationOfInterest from './form_registration_of_interest.vue'
import LeaseLicence from './form_lease_licence.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
/*
import Confirmation from '@/components/common/confirmation.vue'
*/
    export default {
        name: 'ApplicationForm',
        props:{
            show_related_items_tab: {
                type: Boolean,
                default: false,
            },
            show_additional_documents_tab: {
                type: Boolean,
                default: false,
            },
            proposal:{
                type: Object,
                required:true
            },
            show_application_title: {
                type: Boolean,
                default: true,
            },
            submitterId: {
                type: Number,
            },
            canEditActivities:{
              type: Boolean,
              default: true
            },
            is_external:{
              type: Boolean,
              default: false
            },
            is_internal:{
              type: Boolean,
              default: false
            },
            is_referral:{
              type: Boolean,
              default: false
            },
            hasReferralMode:{
                type:Boolean,
                default: false
            },
            hasAssessorMode:{
                type:Boolean,
                default: false
            },
            referral:{
                type: Object,
                required:false
            },
            readonly:{
                type: Boolean,
                default: true,
            },
            registrationOfInterest:{
                type: Boolean,
                default: true,
            },
            leaseLicence:{
                type: Boolean,
                default: true,
            },
        },
        data:function () {
            return{
                can_modify: true,
                show_col_status_when_submitted: true,
                //component_map_key: '',
                componentMapKey: 0,
                componentMapOn: false,
                values:null,
                profile: {},
                uuid: 0,
                keep_current_vessel: true,
                //vesselLength: null,
                showPaymentTab: false,
                detailsText: null,
            }
        },
        components: {
            RegistrationOfInterest,
            LeaseLicence,
            Applicant,
            Profile,
            FormSection,
            RichText,
            FileField,
            ComponentMap,
        },
        computed:{
            email_user_applicant: function(){
                return this.proposal.applicant_obj
            },
            debug: function(){
                if (this.$route.query.debug){
                    return this.$route.query.debug === 'true'
                }
                return false
            },
            proposalId: function() {
                return this.proposal ? this.proposal.id : null;
            },
            deedPollDocumentUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_deed_poll_document/'
                    )
            },
            supportingDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_deed_poll_document/'
                    )
            },

            profileVar: function() {
                if (this.is_external) {
                    return this.profile;
                } else if (this.proposal) {
                    return this.proposal.submitter;
                }
            },
            applicantType: function(){
                if (this.proposal) {
                    return this.proposal.applicant_type;
                }
            },
            applicationTypeText: function(){
                let text = '';
                if (this.proposal) {
                    text = this.proposal.application_type.name_display;
                }
                return text;
            },

        },
        methods:{
            incrementComponentMapKey: function() {
                this.componentMapKey++;
            },
            toggleComponentMapOn: function() {
                this.incrementComponentMapKey()
                this.componentMapOn = true;
                /*
                this.$nextTick(() => {
                    this.$refs.component_map.forceMapRefresh();
                });
                */
            },
            updateTableByFeatures: function() {
            },
            featureGeometryUpdated: function() {
            },
            popupClosed: function() {
            },
            populateProfile: function(profile) {
                this.profile = Object.assign({}, profile);
            },
        },
        mounted: function() {
            this.$emit('formMounted')
        }

    }
</script>

<style lang="css" scoped>
    .question-title{
        padding-left: 15px;
    }
    .section-style{
        padding-left: 15px;
        margin-bottom: 20px;
    }
    .list-inline-item{
        padding-right: 15px;
    }
    .section{
        text-transform: capitalize;
    }
    .list-group{
        margin-bottom: 0;
    }
    .fixed-top{
        position: fixed;
        top:56px;
    }

    .nav-item {
        margin-bottom: 2px;
    }

    .nav-item>li>a {
        background-color: yellow !important;
        color: #fff;
    }

    .nav-item>li.active>a, .nav-item>li.active>a:hover, .nav-item>li.active>a:focus {
      color: white;
      background-color: blue;
      border: 1px solid #888888;
    }

	.admin > div {
	  display: inline-block;
	  vertical-align: top;
	  margin-right: 1em;
	}
    .nav-pills .nav-link {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
        border-top-left-radius: 0.5em;
        border-top-right-radius: 0.5em;
        margin-right: 0.25em;
    }
    .nav-pills .nav-link {
        background: lightgray;
    }
    .nav-pills .nav-link.active {
        background: gray;
    }
</style>

