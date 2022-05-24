<template lang="html">
    <div id="proposalRequirementDetail">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="Requirement" large>
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="requirementForm">
                        <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <label class="radio-inline control-label"><input type="radio" name="requirementType" :value="true" v-model="requirement.standard">Standard Requirement</label>
                                <label class="radio-inline"><input type="radio" name="requirementType" :value="false" v-model="requirement.standard">Free Text Requirement</label>
                            </div>
                        </div>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left"  for="Name">Requirement</label>
                                    </div>
                                    <div class="col-sm-9" v-if="requirement.standard">
                                        <div>
                                            <select class="form-control" ref="standard_req" name="standard_requirement" v-model="requirement.standard_requirement" style="width:70%">
                                                <!--option v-for="r in requirements" :value="r.id" v-model="requirement.standard_requirement">{{r.code}} {{r.text}}</option-->
                                                <option v-for="r in requirements" :value="r.id">{{r.code}} {{r.text}}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-sm-9" v-else>
                                        <textarea style="width: 70%;" class="form-control" name="free_requirement" v-model="requirement.free_requirement"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left"  for="Name">Due Date</label>
                                    </div>
                                    <div class="col-sm-4">
                                        <input type="date" id="due_date" ref="due_date" v-model="requirement.due_date" class="form-control">
                                    </div>
                                </div>
                            </div>
                            <template v-if="validDate">
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-sm-3">
                                            <label class="control-label pull-left"  for="Name">Recurrence</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <label class="checkbox-inline"><input type="checkbox" v-model="requirement.recurrence"></label>
                                        </div>
                                    </div>
                                </div>
                                <template v-if="requirement.recurrence">
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label class="control-label pull-left"  for="Name">Recurrence pattern</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <label class="radio-inline control-label"><input type="radio" name="recurrenceSchedule" value="1" v-model="requirement.recurrence_pattern">Weekly</label>
                                                <label class="radio-inline control-label"><input type="radio" name="recurrenceSchedule" value="2" v-model="requirement.recurrence_pattern">Monthly</label>
                                                <label class="radio-inline control-label"><input type="radio" name="recurrenceSchedule" value="3" v-model="requirement.recurrence_pattern">Yearly</label>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-12">
                                                <label class="control-label"  for="Name">
                                                    <strong class="pull-left">Recur every</strong> 
                                                    <input class="pull-left" style="width:10%; margin-left:10px;" type="number" name="schedule" v-model="requirement.recurrence_schedule"/> 
                                                    <strong v-if="requirement.recurrence_pattern == '1'" class="pull-left" style="margin-left:10px;">week(s)</strong>
                                                    <strong v-else-if="requirement.recurrence_pattern == '2'" class="pull-left" style="margin-left:10px;">month(s)</strong>
                                                    <strong v-else-if="requirement.recurrence_pattern == '3'" class="pull-left" style="margin-left:10px;">year(s)</strong>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                            </template>
                        </div>
                    </form>
                </div>
            </div>
            <div slot="footer">
                <template v-if="requirement.id">
                    <button type="button" v-if="updatingRequirement" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinnner fa-spin"></i> Updating</button>
                    <button type="button" v-else class="btn btn-default" @click="ok">Update</button>
                </template>
                <template v-else>
                    <button type="button" v-if="addingRequirement" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                    <button type="button" v-else class="btn btn-default" @click="ok">Add</button>
                </template>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
//import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import {helpers,api_endpoints} from "@/utils/hooks.js"
export default {
    name:'Requirement-Detail',
    components:{
        modal,
        alert
    },
    props:{
            proposal_id:{
                type:Number,
                required: true
            },
            requirements: {
                type: Array,
                required: true
            },
    },
    data:function () {
        let vm = this;
        return {
            isModalOpen:false,
            form:null,
            requirement: {
                due_date: '',
                standard: true,
                recurrence: false,
                recurrence_pattern: '1',
                proposal: vm.proposal_id,
            },
            addingRequirement: false,
            updatingRequirement: false,
            validation_form: null,
            type: '1',
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            validDate: false
        }
    },
    computed: {
        showError: function() {
            return this.errors;
        },
    },
    watch: {
    },
    methods:{
        ok:function () {
            this.sendData();
        },
        cancel:function () {
            this.close()
        },
        close:function () {
            this.isModalOpen = false;
        },
        fetchContact: function(id){
            let vm = this;
            vm.$http.get(api_endpoints.contact(id)).then((response) => {
                vm.contact = response.body; vm.isModalOpen = true;
            },(error) => {
                console.log(error);
            } );
        },
        sendData:function(){
            this.errors = false;
            if (this.requirement.standard){
                this.requirement.free_requirement = '';
            }
            else{
                this.requirement.standard_requirement = '';
                $(this.$refs.standard_req).val(null).trigger('change');
            }
            if (!this.requirement.due_date){
                this.requirement.due_date = null;
                this.requirement.recurrence = false;
                delete this.requirement.recurrence_pattern;
                this.requirement.recurrence_schedule ? delete this.requirement.recurrence_schedule : '';
            }
            if (this.requirement.id){
                this.updatingRequirement = true;
                this.$http.put(helpers.add_endpoint_json(api_endpoints.proposal_requirements,requirement.id),this.requirement,{
                    }).then((response)=>{
                        this.updatingRequirement = false;
                        this.$parent.updatedRequirements();
                        this.close();
                    },(error)=>{
                        this.errors = true;
                        this.errorString = helpers.apiVueResourceError(error);
                        this.updatingRequirement = false;
                    });
            } else {
                this.addingRequirement = true;
                this.$http.post(api_endpoints.proposal_requirements,this.requirement,{
                    }).then((response)=>{
                        this.addingRequirement = false;
                        this.close();
                        this.$emit("updateRequirements");
                    },(error)=>{
                        this.errors = true;
                        this.addingRequirement = false;
                        this.errorString = helpers.apiVueResourceError(error);
                    });
            }
        },

       eventListeners:function () {
            let vm = this;
       }
   },
   mounted:function () {
        let vm =this;
        vm.form = document.forms.requirementForm;
        this.$nextTick(()=>{
            vm.eventListeners();
        });
   }
}
</script>

<style lang="css">
</style>
