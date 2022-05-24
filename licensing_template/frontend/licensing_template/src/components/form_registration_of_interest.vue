<template lang="html">
    <div>
    <div v-if="debug">components/form_registration_of_interest.vue</div>
    <FormSection label="Proposal Details" Index="application_details" v-if="proposal">
        <slot name="slot_proposal_details_checklist_questions"></slot>
        <div class="col-sm-12 inline-details-text">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="details_text" class="control-label pull-left">Provide a description of your proposal</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    id="details_text"
                    :proposalData="proposal.details_text"
                    ref="details_text"
                    label="Rich text in here" 
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="supporting_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="supporting_documents"
                        name="supporting_documents"
                        id="supporting_documents"
                        :isRepeatable="true"
                        :documentActionUrl="supportingDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>
        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal require exclusive use of or non-exclusive access to a site?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.exclusive_use" type="radio" name="exclusive_use_yes" id="exclusive_use_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="exclusive_use_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.exclusive_use" type="radio" name="exclusive_use_no" id="exclusive_use_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="exclusive_use_no">No</label>
                    </li>
                </ul>
            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.exclusive_use">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.exclusive_use_text"
                    ref="exclusive_use_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="exclusive_use_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="exclusive_use_documents"
                        name="exclusive_use_documents"
                        id="exclusive_use_documents"
                        :isRepeatable="true"
                        :documentActionUrl="exclusiveUseDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal require long-term use of or access to a site?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.long_term_use" type="radio" name="long_term_use_yes" id="long_term_use_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="long_term_use_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.long_term_use" type="radio" name="long_term_use_no" id="long_term_use_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="long_term_use_no">No</label>
                    </li>
                </ul>
            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.long_term_use">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="long_term_use_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.long_term_use_text"
                    ref="long_term_use_text"
                    id="long_term_use_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="long_term_use_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="long_term_use_documents"
                        name="long_term_use_documents"
                        id="long_term_use_documents"
                        :isRepeatable="true"
                        :documentActionUrl="longTermUseDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Is the proposal consistent with the purpose of the park or reserve?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.consistent_purpose" type="radio" name="consistent_purpose_yes" id="consistent_purpose_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="consistent_purpose_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.consistent_purpose" type="radio" name="consistent_purpose_no" id="consistent_purpose_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="consistent_purpose_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.consistent_purpose" type="radio" name="consistent_purpose_null" id="consistent_purpose_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="consistent_purpose_null">Unsure</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.consistent_purpose">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="consistent_purpose_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.consistent_purpose_text"
                    ref="consistent_purpose_text"
                    id="consistent_purpose_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="consistent_purpose_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="consistent_purpose_documents"
                        name="consistent_purpose_documents"
                        id="consistent_purpose_documents"
                        :isRepeatable="true"
                        :documentActionUrl="consistentPurposeDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Is the proposal consistent with the <a href="http://www.google.com" target="_blank">park or reserve management plan</a>?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.consistent_plan" type="radio" name="consistent_plan_yes" id="consistent_plan_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="consistent_plan_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.consistent_plan" type="radio" name="consistent_plan_no" id="consistent_plan_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="consistent_plan_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.consistent_plan" type="radio" name="consistent_plan_null" id="consistent_plan_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="consistent_plan_null">Unsure</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.consistent_plan">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="consistent_plan_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.consistent_plan_text"
                    ref="consistent_plan_text"
                    id="consistent_plan_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="consistent_plan_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="consistent_plan_documents"
                        name="consistent_plan_documents"
                        id="consistent_plan_documents"
                        :isRepeatable="true"
                        :documentActionUrl="consistentPlanDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

    </FormSection>
    <FormSection label="Proposal Impact" Index="proposal_impact" v-if="proposal">
        <slot name="slot_proposal_impact_checklist_questions"></slot>
        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal involve clearing of native vegetation?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.clearing_vegetation" type="radio" name="clearing_vegetation_yes" id="clearing_vegetation_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="clearing_vegetation_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.clearing_vegetation" type="radio" name="clearing_vegetation_no" id="clearing_vegetation_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="clearing_vegetation_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.clearing_vegetation" type="radio" name="clearing_vegetation_null" id="clearing_vegetation_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="clearing_vegetation_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.clearing_vegetation">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="clearing_vegetation_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.clearing_vegetation_text"
                    ref="clearing_vegetation_text"
                    id="clearing_vegetation_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="clearing_vegetation_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="clearing_vegetation_documents"
                        name="clearing_vegetation_documents"
                        id="clearing_vegetation_documents"
                        :isRepeatable="true"
                        :documentActionUrl="clearingVegetationDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal involve ground-disturbing works?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.ground_disturbing_works" type="radio" name="ground_disturbing_works_yes" id="ground_disturbing_works_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="ground_disturbing_works_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.ground_disturbing_works" type="radio" name="ground_disturbing_works_no" id="ground_disturbing_works_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="ground_disturbing_works_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.ground_disturbing_works" type="radio" name="ground_disturbing_works_null" id="ground_disturbing_works_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="ground_disturbing_works_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.ground_disturbing_works">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="ground_disturbing_works_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.ground_disturbing_works_text"
                    ref="ground_disturbing_works_text"
                    id="ground_disturbing_works_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="ground_disturbing_works_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="ground_disturbing_works_documents"
                        name="ground_disturbing_works_documents"
                        id="ground_disturbing_works_documents"
                        :isRepeatable="true"
                        :documentActionUrl="groundDisturbingWorksDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal impact on a World or National Heritage area?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.heritage_site" type="radio" name="heritage_site_yes" id="heritage_site_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="heritage_site_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.heritage_site" type="radio" name="heritage_site_no" id="heritage_site_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="heritage_site_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.heritage_site" type="radio" name="heritage_site_null" id="heritage_site_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="heritage_site_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.heritage_site">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="heritage_site_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.heritage_site_text"
                    ref="heritage_site_text"
                    id="heritage_site_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="heritage_site_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="heritage_site_documents"
                        name="heritage_site_documents"
                        id="heritage_site_documents"
                        :isRepeatable="true"
                        :documentActionUrl="heritageSiteDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Is the proposal located in a environmentally sensitive area or habitat for significant flora and fauna?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.environmentally_sensitive" type="radio" name="environmentally_sensitive_yes" id="environmentally_sensitive_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="environmentally_sensitive_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.environmentally_sensitive" type="radio" name="environmentally_sensitive_no" id="environmentally_sensitive_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="environmentally_sensitive_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.environmentally_sensitive" type="radio" name="environmentally_sensitive_null" id="environmentally_sensitive_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="environmentally_sensitive_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.environmentally_sensitive">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="environmentally_sensitive_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.environmentally_sensitive_text"
                    ref="environmentally_sensitive_text"
                    id="environmentally_sensitive_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="environmentally_sensitive_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="environmentally_sensitive_documents"
                        name="environmentally_sensitive_documents"
                        id="environmentally_sensitive_documents"
                        :isRepeatable="true"
                        :documentActionUrl="environmentallySensitiveDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal impact on wetlands or water courses?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.wetlands_impact" type="radio" name="wetlands_impact_yes" id="wetlands_impact_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="wetlands_impact_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.wetlands_impact" type="radio" name="wetlands_impact_no" id="wetlands_impact_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="wetlands_impact_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.wetlands_impact" type="radio" name="wetlands_impact_null" id="wetlands_impact_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="wetlands_impact_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.wetlands_impact">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="wetlands_impact_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.wetlands_impact_text"
                    ref="wetlands_impact_text"
                    id="wetlands_impact_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="wetlands_impact_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="wetlands_impact_documents"
                        name="wetlands_impact_documents"
                        id="wetlands_impact_documents"
                        :isRepeatable="true"
                        :documentActionUrl="wetlandsImpactDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal involve building a structure or building?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.building_required" type="radio" name="building_required_yes" id="building_required_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="building_required_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.building_required" type="radio" name="building_required_no" id="building_required_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="building_required_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.building_required" type="radio" name="building_required_null" id="building_required_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="building_required_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.building_required">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="building_required_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.building_required_text"
                    ref="building_required_text"
                    id="building_required_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="building_required_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="building_required_documents"
                        name="building_required_documents"
                        id="building_required_documents"
                        :isRepeatable="true"
                        :documentActionUrl="buildingRequiredDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal create a significant change to or visual impact on the proposed site?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.significant_change" type="radio" name="significant_change_yes" id="significant_change_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="significant_change_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.significant_change" type="radio" name="significant_change_no" id="significant_change_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="significant_change_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.significant_change" type="radio" name="significant_change_null" id="significant_change_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="significant_change_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.significant_change">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="significant_change_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.significant_change_text"
                    ref="significant_change_text"
                    id="significant_change_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="significant_change_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="significant_change_documents"
                        name="significant_change_documents"
                        id="significant_change_documents"
                        :isRepeatable="true"
                        :documentActionUrl="significantChangeDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal impact on a <a target="_blank" href="http://www.google.com">registered Aboriginal site</a>?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.aboriginal_site" type="radio" name="aboriginal_site_yes" id="aboriginal_site_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="aboriginal_site_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.aboriginal_site" type="radio" name="aboriginal_site_no" id="aboriginal_site_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="aboriginal_site_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.aboriginal_site" type="radio" name="aboriginal_site_null" id="aboriginal_site_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="aboriginal_site_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.aboriginal_site">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="aboriginal_site_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.aboriginal_site_text"
                    ref="aboriginal_site_text"
                    id="aboriginal_site_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="aboriginal_site_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="aboriginal_site_documents"
                        name="aboriginal_site_documents"
                        id="aboriginal_site_documents"
                        :isRepeatable="true"
                        :documentActionUrl="aboriginalSiteDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Has any consultation occurred with the relevant Aboriginal native title party?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.native_title_consultation" type="radio" name="native_title_consultation_yes" id="native_title_consultation_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="native_title_consultation_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.native_title_consultation" type="radio" name="native_title_consultation_no" id="native_title_consultation_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="native_title_consultation_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.native_title_consultation" type="radio" name="native_title_consultation_null" id="native_title_consultation_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="native_title_consultation_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.native_title_consultation">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="native_title_consultation_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.native_title_consultation_text"
                    ref="native_title_consultation_text"
                    id="native_title_consultation_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="native_title_consultation_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="native_title_consultation_documents"
                        name="native_title_consultation_documents"
                        id="native_title_consultation_documents"
                        :isRepeatable="true"
                        :documentActionUrl="nativeTitleConsultationDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </div>

        <!--div class="col-sm-12"-->
        <div class="row question-row">
            <div class="col-sm-3">
                <label class="control-label pull-left">Will the proposal impact on a <a target="_blank" href="http://google.com">mining tenement</a>?</label>
            </div>
            <div class="col-sm-9">
                <ul  class="list-inline col-sm-9">
                    <li class="list-inline-item">
                        <input class="form-check-input" v-model="proposal.mining_tenement" type="radio" name="mining_tenement_yes" id="mining_tenement_yes" :value="true" data-parsley-required :disabled="readonly"/>
                        <label for="mining_tenement_yes">Yes</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.mining_tenement" type="radio" name="mining_tenement_no" id="mining_tenement_no" :value="false" data-parsley-required :disabled="readonly"/> 
                        <label for="mining_tenement_no">No</label>
                    </li>
                    <li class="list-inline-item">
                        <input  class="form-check-input" v-model="proposal.mining_tenement" type="radio" name="mining_tenement_null" id="mining_tenement_null" :value="null" data-parsley-required :disabled="readonly"/> 
                        <label for="mining_tenement_null">Unknown at this stage</label>
                    </li>
                </ul>

            </div>
        </div>
        <div class="col-sm-12 inline-details-text" v-show="proposal.mining_tenement">
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="mining_tenement_text" class="control-label pull-left">Provide details</label>
                </div>
                <div class="col-sm-8">
                    <RichText
                    :proposalData="proposal.mining_tenement_text"
                    ref="mining_tenement_text"
                    id="mining_tenement_text"
                    :readonly="readonly" 
                    :can_view_richtext_src=true
                    v-bind:key="proposal.id"
                    />
                </div>
            </div>
            <div class="row question-row">
                <div class="col-sm-3">
                    <label for="mining_tenement_documents">Attach any supporting documents</label>
                </div>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="mining_tenement_documents"
                        name="mining_tenement_documents"
                        id="mining_tenement_documents"
                        :isRepeatable="true"
                        :documentActionUrl="miningTenementDocumentsUrl"
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
        name: 'RegistrationOfInterestForm',
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
    .details-text{
        padding-left: 15px;
    }
    .question-row{
        margin-bottom: 10px;
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

