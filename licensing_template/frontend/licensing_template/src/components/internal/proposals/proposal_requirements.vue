<template id="proposal_requirements">
    <div>
        <FormSection :formCollapse="false" label="Conditions" Index="conditions">
            <form class="form-horizontal" action="index.html" method="post">
                <div class="col-sm-12">
                    <button v-if="hasAssessorMode" @click.prevent="addRequirement()" style="margin-bottom:10px;" class="btn btn-primary pull-right">Add Condition</button>
                </div>
                <datatable ref="requirements_datatable" :id="datatableId" :dtOptions="requirement_options" :dtHeaders="requirement_headers"/>
            </form>

            <RequirementDetail
                ref="requirement_detail"
                :proposal_id="proposal.id"
                :requirements="requirements"
                @updateRequirements="updatedRequirements"
                :key="uuid"
            />
        </FormSection>
    </div>
</template>
<script>
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import RequirementDetail from '@/components/internal/proposals/proposal_add_requirement.vue'
import FormSection from "@/components/forms/section_toggle.vue"

export default {
    name: 'InternalProposalRequirements',
    props: {
        proposal: Object
    },
    data: function() {
        let vm = this;
        return {
            uuid: 0,
            panelBody: "proposal-requirements-"+vm._uid,
            requirements: [],
            requirement_headers:["Requirement","Due Date","Recurrence","Action","Order"],
            requirement_options:{
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.proposal, vm.proposal.id+'/requirements'),
                    "dataSrc": ''
                },
                order: [],
                dom: 'lBfrtip',
                buttons:[
                'excel', 'csv', ], //'copy'
                columns: [
                    {
                        data: "requirement",
                        //orderable: false,
                        //'render': function (value) {
                        mRender:function (data,type,full) {
                            var ellipsis = '...',
                                truncated = _.truncate(data, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' '
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template('<a tabindex="0" ' +
                                    'role="button" ' +
                                    'data-bs-toggle="popover" ' +
                                    //'data-bs-container="body" ' +
                                    'data-bs-trigger="focus" ' +
                                    'data-bs-placement="top"' +
                                    //'data-bs-html="true" ' +
                                    'data-bs-content="<%= text %>" ' +
                                    '>more</button>');
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: data
                                });
                            }

                            return result;
                        },
                        //'createdCell': helpers.dtPopoverCellFn,
                    },
                    {
                        data: "due_date",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY'): '';
                        },
                        orderable: false
                    },
                    {
                        data: "recurrence",
                        mRender:function (data,type,full) {
                            if (full.recurrence){
                                switch(full.recurrence_pattern){
                                    case 1:
                                        return `Once per ${full.recurrence_schedule} week(s)`;
                                    case 2:
                                        return `Once per ${full.recurrence_schedule} month(s)`;
                                    case 3:
                                        return `Once per ${full.recurrence_schedule} year(s)`;
                                    default:
                                        return '';
                                }
                            }
                            return '';
                        },
                        orderable: false
                    },
                    {
                        data: "id",
                        mRender:function (data,type,full) {
                            let links = '';
                            if (vm.proposal.assessor_mode.has_assessor_mode){
                                if(full.copied_from==null)
                                {
                                    links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                }
                                //links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                links +=  `<a href='#' class="deleteRequirement" data-id="${full.id}">Delete</a><br/>`;
                            }
                            return links;
                        },
                        orderable: false
                    },
                    {
                        data: "id",
                        mRender:function (data,type,full) {
                            let links = '';
                            // TODO check permission to change the order
                            if (vm.proposal.assessor_mode.has_assessor_mode){
                                /*
                                links +=  `<i data-id="${full.id}" class="dtMoveUp fa fa-angle-up fa-2x"></i><br/>`;
                                links +=  `<i data-id="${full.id}" class="dtMoveDown fa fa-angle-down fa-2x"></i><br/>`;
                                */
                                links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up fa-2x"></i></a><br/>`;
                                links +=  `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down fa-2x"></i></a><br/>`;
                                /*
                                links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="down-chevron-close"></i></a><br/>`;
                                //links +=  `<i class="bi fw-bold down-chevron-close chevron-toggle" :data-bs-target="'#' +section_body_id"></i>`;
                                */
                            }
                            return links;
                        },
                        orderable: false
                    }
                ],
                processing: true,
                /*
                rowCallback: function ( row, data, index) {
                    console.log("rowCallback")
                    if (data.copied_for_renewal && data.require_due_date && !data.due_date) {
                        $('td', row).css('background-color', 'Red');
                        vm.setApplicationWorkflowState(false)
                        //vm.$emit('refreshRequirements',false);
                    }
                },
                drawCallback: function (settings) {
                    console.log("drawCallback")
                    $(vm.$refs.requirements_datatable.table).find('tr:last .dtMoveDown').remove();
                    $(vm.$refs.requirements_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();

                    // Remove previous binding before adding it
                    $('.dtMoveUp').unbind('click');
                    $('.dtMoveDown').unbind('click');

                    // Bind clicks to functions
                    $('.dtMoveUp').click(vm.moveUp);
                    $('.dtMoveDown').click(vm.moveDown);
                },
                 preDrawCallback: function (settings) {
                    console.log("preDrawCallback")
                    vm.setApplicationWorkflowState(true)
                    //vm.$emit('refreshRequirements',true);
                },
                */
                initComplete: function() {
                    vm.enablePopovers();
                    //console.log($('#' + vm.datatableId).DataTable());
                    vm.addTableListeners();
                },
            }
        }
    },
    watch:{
        hasAssessorMode(){
            // reload the table
            this.updatedRequirements();
        }
    },
    components:{
        datatable,
        RequirementDetail,
        FormSection,
    },
    computed:{
        datatableId: function() {
            return 'requirements-datatable-' + this._uid;
        },
        hasAssessorMode(){
            return this.proposal.assessor_mode.has_assessor_mode;
        }
    },
    methods:{
        addRequirement(){
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.requirement_detail.isModalOpen = true;
            });
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
                fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id+'/discard'))
                .then((response) => {
                    vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
                }, (error) => {
                    console.log(error);
                });

            },(error) => {
            });
        },
        fetchRequirements(){
            let vm = this;
            let url = api_endpoints.proposal_standard_requirements
            fetch(url, {params: {'application_type_code': vm.proposal.application_type_code}}).then((response) => {
                vm.requirements = response.body
            },(error) => {
                console.log(error);
            })
        },
        editRequirement(_id){
            let vm = this;
            fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id)).then((response) => {
                this.$refs.requirement_detail.requirement = response.body;
                this.$refs.requirement_detail.requirement.due_date =  response.body.due_date != null && response.body.due_date != undefined ? moment(response.body.due_date).format('DD/MM/YYYY'): '';
                response.body.standard ? $(this.$refs.requirement_detail.$refs.standard_req).val(response.body.standard_requirement).trigger('change'): '';
                this.addRequirement();
            },(error) => {
                console.log(error);
            })
        },
        updatedRequirements(){
            this.$refs.requirements_datatable.vmDataTable.ajax.reload();
        },
        eventListeners(){
            let vm = this;
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.deleteRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.removeRequirement(id);
            });
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.editRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.editRequirement(id);
            });
        },
        addTableListeners: function() {
            let vm = this;
            $(vm.$refs.requirements_datatable.table).find('tr:last .dtMoveDown').remove();
            $(vm.$refs.requirements_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();
            // Remove previous binding before adding it
            $('.dtMoveUp').off('click');
            $('.dtMoveDown').off('click');

            // Bind clicks to functions
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.dtMoveUp', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveUp(id);
            });
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.dtMoveDown', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveDown(id);
            });
        },
        async sendDirection(req,direction){
            let vm = this;
            let movement = direction == 'down'? 'move_down': 'move_up';
            try {
                const res = await fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,req+'/'+movement))
                this.$parent.uuid++;
                //await this.$refs.requirements_datatable.vmDataTable.ajax.reload();
                //this.$refs.requirements_datatable.vmDataTable.page(0).draw(false);
                //this.$refs.requirements_datatable.vmDataTable.draw();
            } catch(error) {
                console.log(error);
            }
        },
        moveUp(id) {
            this.sendDirection(id,'up');
        },
        moveDown(id) {
            this.sendDirection(id,'down');
        },
        enablePopovers: function() {
            var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
            var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
                let popover = new bootstrap.Popover(popoverTriggerEl)
            })
        },
    },
    mounted: function(){
        let vm = this;
        this.fetchRequirements();
        vm.$nextTick(() => {
            this.eventListeners();
        });
    },
}
</script>
<style scoped>
.dataTables_wrapper .dt-buttons{
    float: right;
}
</style>
