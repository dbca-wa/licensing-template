<template lang="html">
    <div>
    <div v-if="debug">components/form_lease_licence.vue</div>
    <FormSection label="Tourism Proposal Details" Index="tourism_proposal_details" v-if="proposal">
        <slot name="slot_proposal_details_checklist_questions"></slot>
        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="profit_and_loss_text" class="control-label pull-left">Provide five-year integrated profit and loss, balance sheet and cash flow projections (preferably by month).  State clearly the underlying assumptions made in respect to design, construction, rental, operations and target markets</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.profit_and_loss_text"
                    ref="profit_and_loss_text"
                    id="profit_and_loss_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="profit_and_loss_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="profit_and_loss_documents"
                        name="profit_and_loss_documents"
                        id="profit_and_loss_documents"
                        :isRepeatable="true"
                        :documentActionUrl="profitAndLossDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="cash_flow_text" class="control-label pull-left">Provide cash flow projections to demonstrate time to amortize the capital investment</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.cash_flow_text"
                ref="cash_flow_text"
                id="cash_flow_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="cash_flow_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="cash_flow_documents"
                    name="cash_flow_documents"
                    id="cash_flow_documents"
                    :isRepeatable="true"
                    :documentActionUrl="cashFlowDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="capital_investment_text" class="control-label pull-left">Include proposed capital investment showing costing against each component of the built development and start-up costs</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.capital_investment_text"
                ref="capital_investment_text"
                id="capital_investment_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="capital_investment_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="capital_investment_documents"
                    name="capital_investment_documents"
                    id="capital_investment_documents"
                    :isRepeatable="true"
                    :documentActionUrl="capitalInvestmentDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="financial_capacity_text" class="control-label pull-left">Demonstrate that you and/or the nominated operator have the financial capacity to build and operate the proposal.  Information/evidence from banks/financiers/accountants would assist in demonstrating this, for example, audited financial statements for the last 3 years or letter from a financier confirming access to the required finance</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.financial_capacity_text"
                ref="financial_capacity_text"
                id="financial_capacity_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="financial_capacity_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="financial_capacity_documents"
                    name="financial_capacity_documents"
                    id="financial_capacity_documents"
                    :isRepeatable="true"
                    :documentActionUrl="financialCapacityDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="available_activities_text" class="control-label pull-left">Specify the full range of recreational, educational, cultural and other activities that will be available to visitors through your proposal and what will be required/developed to undertake them.  Articulate the timeline for the introduction of each activity over a five-year period</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.available_activities_text"
                ref="available_activities_text"
                id="available_activities_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="available_activities_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="available_activities_documents"
                    name="available_activities_documents"
                    id="available_activities_documents"
                    :isRepeatable="true"
                    :documentActionUrl="availableActivitiesDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="market_analysis_text" class="control-label pull-left">Outline a market analysis that identifies the target markets for the operation and how these will be accommodated as well as a competitor analysis.  (Note the market analysis should inform the integrated profit and loss and cash flow projections with realistic assumptions and estimations)</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.market_analysis_text"
                ref="market_analysis_text"
                id="market_analysis_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="market_analysis_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="market_analysis_documents"
                    name="market_analysis_documents"
                    id="market_analysis_documents"
                    :isRepeatable="true"
                    :documentActionUrl="marketAnalysisDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="staffing_text" class="control-label pull-left">Provide details of staffing, workforce management. (Note the market analysis should inform the integrated profit and loss and cash flow projections with realistic assumptions and estimations)</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.staffing_text"
                ref="staffing_text"
                id="staffing_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="staffing_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="staffing_documents"
                    name="staffing_documents"
                    id="staffing_documents"
                    :isRepeatable="true"
                    :documentActionUrl="staffingDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>


    </FormSection>
    <FormSection label="General Proposal Details" Index="general_proposal_details" v-if="proposal">
        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="key_personnel_text" class="control-label pull-left">Provide details of the key personnel and their qualifications and experience that is appropriate to developing and operating the venture under the proposed tourism lease.  Include bios of the proposed board and management team demonstrating capability in delivering and maintaining the proposal</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.key_personnel_text"
                ref="key_personnel_text"
                id="key_personnel_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="key_personnel_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="key_personnel_documents"
                    name="key_personnel_documents"
                    id="key_personnel_documents"
                    :isRepeatable="true"
                    :documentActionUrl="keyPersonnelDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>
        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="key_milestones_text" class="control-label pull-left">Provide details regarding key milestones</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.key_milestones_text"
                ref="key_milestones_text"
                id="key_milestones_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="key_milestones_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="key_milestones_documents"
                    name="key_milestones_documents"
                    id="key_milestones_documents"
                    :isRepeatable="true"
                    :documentActionUrl="keyMilestonesDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="risk_factors_text" class="control-label pull-left">Identify specific risk factors and likely impacts to allow consideration of options.  Include how key risks will be avoided, reduced, managed or mitigated.  (Note the management of risk should inform the integrated profit and loss and cash flow projections).</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.risk_factors_text"
                ref="risk_factors_text"
                id="risk_factors_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="risk_factors_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="risk_factors_documents"
                    name="risk_factors_documents"
                    id="risk_factors_documents"
                    :isRepeatable="true"
                    :documentActionUrl="riskFactorsDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>
        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="legislative_requirements_text" class="control-label pull-left">If legislative or regulatory requirements apply to thie proposal, please provide details and upload any approvals already received</label>
            </div>
            <div class="col-sm-8">
                <RichText
                :proposalData="proposal.legislative_requirements_text"
                ref="legislative_requirements_text"
                id="legislative_requirements_text"
                :readonly="readonly" 
                :can_view_richtext_src=true
                v-bind:key="proposal.id"
                />
            </div>
            </div>
            <div class="row question-row">
            <div class="col-sm-3">
                <label for="legislative_requirements_documents">Attach any supporting documents</label>
            </div>
            <div class="col-sm-9">
                <FileField 
                    :readonly="readonly"
                    ref="legislative_requirements_documents"
                    name="legislative_requirements_documents"
                    id="legislative_requirements_documents"
                    :isRepeatable="true"
                    :documentActionUrl="legislativeRequirementsDocumentsUrl"
                    :replace_button_by_text="true"
                />
            </div>
            </div>
        </div>

    </FormSection>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue'
import RichText from '@/components/forms/richtext.vue'
import FileField from '@/components/forms/filefield_immediate.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

    export default {
        name: 'LeaseLicenceForm',
        props:{
            proposal:{
                type: Object,
                required:true
            },
            readonly:{
                type: Boolean,
                default: true,
            },
        },
        data:function () {
            return{
            }
        },
        components: {
            FormSection,
            RichText,
            FileField,
        },
        computed:{
            debug: function(){
                if (this.$route.query.debug){
                    return this.$route.query.debug === 'true'
                }
                return false
            },
            proposalId: function() {
                return this.proposal ? this.proposal.id : null;
            },
            profitAndLossDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_profit_and_loss_document/'
                    )
            },
            cashFlowDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_cash_flow_document/'
                    )
            },
            capitalInvestmentDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_capital_investment_document/'
                    )
            },
            financialCapacityDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_financial_capacity_document/'
                    )
            },
            availableActivitiesDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_available_activities_document/'
                    )
            },
            marketAnalysisDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_market_analysis_document/'
                    )
            },
            staffingDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_staffing_document/'
                    )
            },
            keyPersonnelDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_key_personnel_document/'
                    )
            },
            keyMilestonesDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_key_milestones_document/'
                    )
            },
            riskFactorsDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_risk_factors_document/'
                    )
            },
            legislativeRequirementsDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_legislative_requirements_document/'
                    )
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
                    this.proposal.id + '/process_supporting_document/'
                    )
            },
            exclusiveUseDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_exclusive_use_document/'
                    )
            },
            longTermUseDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_long_term_use_document/'
                    )
            },
            consistentPurposeDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_consistent_purpose_document/'
                    )
            },
            consistentPlanDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_consistent_plan_document/'
                    )
            },
            clearingVegetationDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_clearing_vegetation_document/'
                    )
            },
            groundDisturbingWorksDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_ground_disturbing_works_document/'
                    )
            },
            heritageSiteDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_heritage_site_document/'
                    )
            },
            environmentallySensitiveDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_environmentally_sensitive_document/'
                    )
            },
            wetlandsImpactDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_wetlands_impact_document/'
                    )
            },
            buildingRequiredDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_building_required_document/'
                    )
            },
            significantChangeDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_significant_change_document/'
                    )
            },
            aboriginalSiteDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_aboriginal_site_document/'
                    )
            },
            nativeTitleConsultationDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_native_title_consultation_document/'
                    )
            },
            miningTenementDocumentsUrl: function() {
                return helpers.add_endpoint_join(
                    api_endpoints.proposal,
                    this.proposal.id + '/process_mining_tenement_document/'
                    )
            },
        },
        methods:{
        },
        mounted: function() {
        }
 
    }
</script>

<style lang="css" scoped>
    .inline-details-text{
        margin-bottom: 20px;
    }
    .question-row{
        margin-bottom: 10px;
        padding-left: 15px;
    }
    .details-text{
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
</style>

