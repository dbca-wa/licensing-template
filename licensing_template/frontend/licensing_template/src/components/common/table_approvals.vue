<template>
    <div>
        <CollapsibleFilters component_title="Filters" ref="collapsible_filters" @created="collapsible_component_mounted" class="mb-2">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Type</label>
                    <select class="form-control" v-model="filterApprovalType">
                        <option value="all">All</option>
                        <option v-for="type in approval_types" :value="type.code">{{ type.description }}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterApprovalStatus">
                        <option value="all">All</option>
                        <option v-for="status in approval_statuses" :value="status.code">{{ status.description }}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Expiry Date From</label>
                    <div class="input-group date" ref="approvalDateFromPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterApprovalExpiryDateFrom">
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Expiry Date To</label>
                    <div class="input-group date" ref="approvalDateToPicker">
                        <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterApprovalExpiryDateTo">
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    ref="approvals_datatable"
                    :id="datatable_id"
                    :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers"
                />
            </div>
        </div>
        <ApprovalCancellation ref="approval_cancellation"  @refreshFromResponse="refreshFromResponseApprovalModify"></ApprovalCancellation>
        <ApprovalSuspension ref="approval_suspension"  @refreshFromResponse="refreshFromResponseApprovalModify"></ApprovalSuspension>
        <ApprovalSurrender ref="approval_surrender"  @refreshFromResponse="refreshFromResponseApprovalModify"></ApprovalSurrender>
        <div v-if="approvalHistoryId">
            <ApprovalHistory
                ref="approval_history"
                :key="approvalHistoryId"
                :approvalId="approvalHistoryId"
            />
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import OfferMooringLicence from '@/components/internal/approvals/offer_mooring_licence.vue'
import ApprovalCancellation from '../internal/approvals/approval_cancellation.vue'
import ApprovalSuspension from '../internal/approvals/approval_suspension.vue'
import ApprovalSurrender from '../internal/approvals/approval_surrender.vue'
import ApprovalHistory from '../internal/approvals/approval_history.vue'
import { api_endpoints, helpers }from '@/utils/hooks'
import CollapsibleFilters from '@/components/forms/collapsible_component.vue'
import { v4 as uuid } from 'uuid';

export default {
    name: 'TableApprovals',
    props: {
        /*
        approvalTypeFilter: {
            type: Array,
            required: true,
        },
        */
        level:{
            type: String,
            required: true,
            validator: function(val) {
                let options = ['internal', 'referral', 'external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
        target_email_user_id: {
            type: Number,
            required: false,
            default: 0,
        }
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'approvals-datatable-' + uuid(),
            //approvalTypesToDisplay: ['wla'],
            show_expired_surrendered: false,
            selectedWaitingListAllocationId: null,
            approvalHistoryId: null,
            uuid: 0,
            mooringBayId: null,
            statusValues: [],
            filterApprovalType: null,
            //approvalTypes: [],
            holderList: [],
            profile: {},

            // selected values for filtering
            filterApprovalType: sessionStorage.getItem('filterApprovalType') ? sessionStorage.getItem('filterApprovalType') : 'all',
            filterApprovalStatus: sessionStorage.getItem('filterApprovalStatus') ? sessionStorage.getItem('filterApprovalStatus') : 'all',
            filterApprovalExpiryDateFrom: sessionStorage.getItem('filterApprovalExpiryDateFrom') ? sessionStorage.getItem('filterApprovalExpiryDateFrom') : '',
            filterApprovalExpiryDateTo: sessionStorage.getItem('filterApprovalExpiryDateTo') ? sessionStorage.getItem('filterApprovalExpiryDateTo') : '',

            // filtering options
            approval_types: [],
            approval_statuses: [],

            // Filters toggle
            filters_expanded: false,

            dateFormat: 'DD/MM/YYYY',
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
        }
    },
    components:{
        datatable,
        OfferMooringLicence,
        ApprovalCancellation,
        ApprovalSuspension,
        ApprovalSurrender,
        ApprovalHistory,
        CollapsibleFilters,
    },
    watch: {
        show_expired_surrendered: function(value){
            console.log(value)
            this.$refs.approvals_datatable.vmDataTable.ajax.reload()
        },
        filterApprovalStatus: function() {
            this.$refs.approvals_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem('filterApprovalStatus', this.filterApprovalStatus);
        },
        filterApprovalType: function() {
            this.$refs.approvals_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem('filterApprovalType', this.filterApprovalType);
        },
        filterApprovalExpiryDateFrom: function() {
            this.$refs.approvals_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem('filterApprovalExpiryDateFrom', this.filterApprovalExpiryDateFrom);
        },
        filterApprovalExpiryDateTo: function() {
            this.$refs.approvals_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem('filterApprovalExpiryDateTo', this.filterApprovalExpiryDateTo);
        },
        filterApplied: function(){
            if (this.$refs.collapsible_filters){
                // Collapsible component exists
                this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
            }
        }
    },
    computed: {
        filterApplied: function(){
            let filter_applied = true
            if(this.filterApprovalStatus.toLowerCase() === 'all' && this.filterApprovalType.toLowerCase() === 'all' &&
                this.filterApprovalExpiryDateFrom.toLowerCase() === '' && this.filterApprovalExpiryDateTo.toLowerCase() === ''){
                filter_applied = false
            }
            return filter_applied
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        debug: function(){
            if (this.$route.query.debug){
                return this.$route.query.debug === 'Tru3'
            }
            return false
        },
        is_external: function() {
            return this.level == 'external'
        },
        is_internal: function() {
            return this.level == 'internal'
        },
        // Datatable settings
        datatable_headers: function() {
            if (this.is_external) {
                return [
                    'Id',
                    'Number',
                    'Type',
                    'Site',
                    'Holder',
                    'Status',
                    'Expiry Date',
                    'Document',
                    'Action',
                ]
            } else if (this.is_internal) {
                return [
                    'Id',
                    'Number',
                    'Type',
                    'Holder',
                    'Application',
                    'Status',
                    'Expiry Date',
                    'Document',
                    'Action',
                ]
            }
        },
        columnId: function() {
            return {
                        // 1. ID
                        data: "id",
                        orderable: false,
                        searchable: false,
                        visible: false,
                        'render': function(row, type, full){
                            console.log('---full---')
                            console.log(full)
                            return full.id
                        }
                    }
        },
        columnLodgementNumber: function() {
            return {
                        // 2. Lodgement Number
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            if (full.migrated){
                                return full.lodgement_number + ' (M)'
                            } else {
                                return full.lodgement_number
                            }
                        }
                    }
        },
        columnType: function() {
            return {
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return '(todo)'
                }
            }
        },
        columnSite: function() {
            return {
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return '(todo)'
                }
            }
        },
        columnHolder: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            //return full.holder;
                            return 'holder?';
                        }
                    }
        },
        columnStatus: function() {
            return {
                        // 5. Status
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.status
                        }
                    }
        },
        columnExpiryDate: function() {
            return {
                        // 9. Expiry Date
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.expiry_date;
                        }
                    }
        },
        columnDocument: function() {
            return {
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return '(todo)'
                }
            }
        },
        columnAction: function() {
            let vm = this;
            return {
                        // 10. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            let links = '';
                            if(vm.debug){
                                links +=  `<a href='#${full.id}' data-request-new-sticker='${full.id}'>Request New Sticker</a><br/>`;
                            }
                            /*
                            if (vm.is_internal && vm.wlaDash) {
                                links += full.offer_link;
                            } else
                            */
                            if (vm.is_external && full.can_reissue) {
                                if(full.can_action || vm.debug){
                                    if(full.amend_or_renew === 'amend' || vm.debug){
                                       links +=  `<a href='#${full.id}' data-amend-approval='${full.current_proposal_id}'>Amend</a><br/>`;
                                    } else if(full.amend_or_renew === 'renew' || vm.debug){
                                        links +=  `<a href='#${full.id}' data-renew-approval='${full.current_proposal_id}'>Renew</a><br/>`;
                                    }
                                    links +=  `<a href='#${full.id}' data-surrender-approval='${full.id}'>Surrender</a><br/>`;
                                }


                            } else if (!vm.is_external){
                                links +=  `<a href='/internal/approval/${full.id}'>View</a><br/>`;
                                links +=  `<a href='#${full.id}' data-history-approval='${full.id}'>History</a><br/>`;
                                if(full.can_reissue && full.current_proposal_id && full.is_approver && full.current_proposal_approved){
                                        links +=  `<a href='#${full.id}' data-reissue-approval='${full.current_proposal_id}'>Reissue</a><br/>`;
                                }
                                if (vm.is_internal && vm.wlaDash) {
                                    links += full.offer_link;
                                }
                                //if(vm.check_assessor(full)){
                                //if (full.allowed_assessors.includes(vm.profile.id)) {
                                if (full.allowed_assessors_user) {
                                //if (true) {
                                    if(full.can_reissue && full.can_action){
                                        links +=  `<a href='#${full.id}' data-cancel-approval='${full.id}'>Cancel</a><br/>`;
                                        links +=  `<a href='#${full.id}' data-surrender-approval='${full.id}'>Surrender</a><br/>`;
                                    }
                                    if(full.status == 'Current' && full.can_action){
                                        links +=  `<a href='#${full.id}' data-suspend-approval='${full.id}'>Suspend</a><br/>`;
                                    }
                                    if(full.can_reinstate)
                                    {
                                        links +=  `<a href='#${full.id}' data-reinstate-approval='${full.id}'>Reinstate</a><br/>`;
                                    }
                                }
                                if(full.renewal_document && full.renewal_sent){
                                  links +=  `<a href='${full.renewal_document}' target='_blank'>Renewal Notice</a><br/>`;
                                }
                            }

                            return links;
                        }
                    }
        },
        datatable_options: function() {
            let vm = this;
            let selectedColumns = [];
            if (this.is_external) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnType,
                    vm.columnSite,
                    vm.columnHolder,
                    vm.columnStatus,
                    vm.columnExpiryDate,
                    vm.columnDocument,
                    vm.columnAction,
                ]
            } else if (vm.is_internal) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnType,
                    vm.columnHolder,
                    vm.columnApplication,
                    vm.columnStatus,
                    vm.columnExpiryDate,
                    vm.columnDocument,
                    vm.columnAction,
                ]
            }
            let buttons = []
            if (vm.is_internal){
                buttons = [
                    {
                        extend: 'excel',
                        text: '<i class="fa-solid fa-download"></i> Excel',
                        className: 'btn btn-primary ml-2',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'csv',
                        text: '<i class="fa-solid fa-download"></i> CSV',
                        className: 'btn btn-primary',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                ]
            }

            return {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                //searching: false,
                searching: true,
                ajax: {
                    "url": api_endpoints.approvals_paginated_list + '?format=datatables&target_email_user_id=' + vm.target_email_user_id,
                    //"url": api_endpoints.approvals,
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_type = vm.filterApprovalType
                        d.filter_approval_status = vm.filterApprovalStatus
                        d.filter_approval_expiry_date_from = vm.filterApprovalExpiryDateFrom
                        d.filter_approval_expiry_date_to = vm.filterApprovalExpiryDateTo
                        d.level = vm.level
                    }
                },
                //dom: 'frt', //'lBfrtip',
                //dom: 'lBfrtip',
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                columns: selectedColumns,
                processing: true,
                initComplete: function() {
                    console.log('in initComplete')
                },
            }
        },
    },
    methods: {
        adjust_table_width: function(){
            this.$refs.approvals_datatable.vmDataTable.columns.adjust()
            this.$refs.approvals_datatable.vmDataTable.responsive.recalc()
        },
        collapsible_component_mounted: function(){
            this.$refs.collapsible_filters.show_warning_icon(this.filterApplied)
        },
        sendData: function(params){
            let vm = this
            fetch(helpers.add_endpoint_json(api_endpoints.approvals, params.approval_id + '/request_new_stickers'), {body: params, method: 'POST', }).then(
                res => {
                    helpers.post_and_redirect('/sticker_replacement_fee/', {'csrfmiddlewaretoken' : vm.csrf_token, 'data': JSON.stringify(res.body)});
                },
                err => {
                    console.log(err)
                }
            )
        },
        fetchProfile: function(){
            let vm = this;
            fetch(api_endpoints.profile).then((response) => {
                vm.profile = response.body

            },(error) => {
                console.log(error);

            })
        },
        refreshFromResponseApprovalModify: function(){
            this.$refs.approvals_datatable.vmDataTable.ajax.reload();
        },
        refreshFromResponse: async function(lodgementNumber){
            console.log("refreshFromResponse");
            await swal({
                title: "Saved",
                text: 'Mooring Licence Application ' + lodgementNumber + ' has been created',
                type:'success'
            });
            await this.$refs.approvals_datatable.vmDataTable.ajax.reload();
        },
        addEventListeners: function(){
            let vm = this;
            /*
            // update to bs5
            // Lodged From
            $(vm.$refs.approvalDateFromPicker).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.approvalDateFromPicker).on('dp.change',function (e) {
                if ($(vm.$refs.approvalDateFromPicker).data('DateTimePicker').date()) {
                    // DateFrom has been picked
                    vm.filterApprovalExpiryDateFrom = e.date.format('DD/MM/YYYY');
                    $(vm.$refs.approvalDateToPicker).data("DateTimePicker").minDate(e.date);
                }
                else if ($(vm.$refs.approvalDateFromPicker).data('date') === "") {
                    vm.filterApprovalExpiryDateFrom = "";
                    $(vm.$refs.approvalDateToPicker).data("DateTimePicker").minDate(false);
                }
            });

            // Lodged To
            $(vm.$refs.approvalDateToPicker).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.approvalDateToPicker).on('dp.change',function (e) {
                if ($(vm.$refs.approvalDateToPicker).data('DateTimePicker').date()) {
                    // DateTo has been picked
                    vm.filterApprovalExpiryDateTo = e.date.format('DD/MM/YYYY');
                    $(vm.$refs.approvalDateFromPicker).data("DateTimePicker").maxDate(e.date);
                }
                else if ($(vm.$refs.approvalDateToPicker).data('date') === "") {
                    vm.filterApprovalExpiryDateTo = "";
                    $(vm.$refs.approvalDateFromPicker).data("DateTimePicker").maxDate(false);
                }
            });
            */

            //Internal Action shortcut listeners
            let table = vm.$refs.approvals_datatable.vmDataTable
            table.on('processing.dt', function(e) {
            })
            table.on('click', 'a[data-offer]', async function(e) {
                e.preventDefault();
                var id = $(this).attr('data-offer');
                vm.mooringBayId = parseInt($(this).attr('data-mooring-bay'));
                await vm.offerMooringLicence(id);
            }).on('responsive-display.dt', function () {
                var tablePopover = $(this).find('[data-toggle="popover"]');
                if (tablePopover.length > 0) {
                    tablePopover.popover();
                    // the next line prevents from scrolling up to the top after clicking on the popover.
                    $(tablePopover).on('click', function (e) {
                        e.preventDefault();
                        return true;
                    });
                }
            }).on('draw.dt', function () {
                var tablePopover = $(this).find('[data-toggle="popover"]');
                if (tablePopover.length > 0) {
                    tablePopover.popover();
                    // the next line prevents from scrolling up to the top after clicking on the popover.
                    $(tablePopover).on('click', function (e) {
                        e.preventDefault();
                        return true;
                    });
                }
            });
            // Internal Reissue listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-reissue-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-reissue-approval');
                vm.reissueApproval(id);
            });

            //Internal Cancel listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-cancel-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-cancel-approval');
                vm.cancelApproval(id);
            });

            //Internal Suspend listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-suspend-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-suspend-approval');
                vm.suspendApproval(id);
            });

            // Internal Reinstate listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-reinstate-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-reinstate-approval');
                vm.reinstateApproval(id);
            });

            //Internal/ External Surrender listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-surrender-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-surrender-approval');
                vm.surrenderApproval(id);
            });

            //External Request New Sticker listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-request-new-sticker]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-request-new-sticker');
                vm.requestNewSticker(id);
            });

            // External renewal listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-renew-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-renew-approval');
                vm.renewApproval(id);
            });

            // External amend listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-amend-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-amend-approval');
                vm.amendApproval(id);
            });

            // Internal history listener
            vm.$refs.approvals_datatable.vmDataTable.on('click', 'a[data-history-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-history-approval');
                vm.approvalHistory(id);
            });

        },
        fetchFilterLists: async function(){
            // Status values
            const statusRes = await fetch(api_endpoints.approval_statuses_dict);
            const statusData = await statusRes.json()
            for (let s of statusData) {
                if (this.wlaDash && !(['extended', 'awaiting_payment', 'approved'].includes(s.code))) {
                    this.statusValues.push(s);
                //} else if (!(['extended', 'awaiting_payment', 'offered', 'approved'].includes(s.code))) {
                } else if (!(['extended', 'awaiting_payment', 'offered', 'approved'].includes(s.code))) {
                    this.statusValues.push(s);
                }
            }
        },
        reissueApproval:async function (proposal_id) {
            let vm = this;
            let status= 'with_approver'
            let data = {'status': status}
            await swal.fire({
                title: "Reissue Approval",
                text: "Are you sure you want to reissue this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Reissue approval',
                //confirmButtonColor:'#d9534f'
            })
            try {
                const response = await fetch(helpers.add_endpoint_json(api_endpoints.proposal,(proposal_id+'/reissue_approval')),
                    { 
                        body: JSON.stringify(data),
                        method: 'POST',
                    })

                vm.$router.push({
                name:"internal-proposal",
                params:{proposal_id:proposal_id}
                });
            } catch (error) {
                    console.log(error);
                    swal.fire({
                    title: "Reissue Approval",
                    text: error.body,
                    icon: "error",
                    })
            }
        },

        reinstateApproval:async function (approval_id) {
            let vm = this;
            let status= 'with_approver'
            //let data = {'status': status}
            await swal.fire({
                title: "Reinstate Approval",
                text: "Are you sure you want to reinstate this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Reinstate approval',
                //confirmButtonColor:'#d9534f'
            })
            try {
                const response = fetch(helpers.add_endpoint_json(api_endpoints.approvals,(approval_id+'/approval_reinstate')),
                    {
                    method: 'POST',
                    })
                    await swal(
                        'Reinstate',
                        'Your approval has been reinstated',
                        'success'
                    )
                    vm.$refs.approvals_datatable.vmDataTable.ajax.reload();
                } catch (error) {
                    console.log(error);
                    swal.fire({
                    title: "Reinstate Approval",
                    text: error.body,
                    type: "error",
                    })
                }
        },
        cancelApproval: function(approval_id){
            this.$refs.approval_cancellation.approval_id = approval_id;
            this.$refs.approval_cancellation.isModalOpen = true;
        },

        suspendApproval: function(approval_id){
            this.$refs.approval_suspension.approval = {};
            this.$refs.approval_suspension.approval_id = approval_id;
            this.$refs.approval_suspension.isModalOpen = true;
        },

        surrenderApproval: function(approval_id){
            this.$refs.approval_surrender.approval_id = approval_id;
            this.$refs.approval_surrender.isModalOpen = true;
        },
        requestNewSticker: function(approval_id){
            this.$refs.request_new_sticker_modal.approval_id = approval_id
            this.$refs.request_new_sticker_modal.isModalOpen = true
        },
        approvalHistory: function(id){
            this.approvalHistoryId = parseInt(id);
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.approval_history.isModalOpen = true;
            });
        },

        renewApproval:async function (proposal_id) {
            let vm = this;
            let status= 'with_approver'
            swal({
                title: "Renew Approval",
                text: "Are you sure you want to renew this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Renew approval',
            })
            try {
                const response = fetch(helpers.add_endpoint_json(api_endpoints.proposal,(proposal_id+'/renew_amend_approval_wrapper')) + '?debug=' + vm.debug + '&type=renew',
                    {
                    method: 'POST',
                    })
                vm.$router.push({
                    name:"draft_proposal",
                    params:{proposal_id: proposal.id}
                });
            } catch (error) {
                    console.log(error);
                    swal.fire({
                    title: "Renew Approval",
                    text: error.body,
                    icon: "error",
                    })
            }
        },

        amendApproval:async function (proposal_id) {
            let vm = this;
            swal.fire({
                title: "Amend Approval",
                text: "Are you sure you want to amend this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Amend approval',
            })
            try {
                const response = fetch(helpers.add_endpoint_json(api_endpoints.proposal,(proposal_id+'/renew_amend_approval_wrapper')) + '?debug=' + vm.debug + '&type=amend', 
                {
                    method: 'POST',
                })
                vm.$router.push({
                    name:"draft_proposal",
                    params:{proposal_id: proposal.id}
                });
            } catch (error) {
                    console.log(error);
                    swal.fire({
                    title: "Amend Approval",
                    text: error.body,
                    icon: "error",
                    })
            }
        },


    },
    created: async function(){
        await this.fetchFilterLists();
        await this.fetchProfile();
    },
    mounted: function(){
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>

<style scoped>
</style>
