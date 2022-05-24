<template>
    <div class="">
        <div class="card card-default">
            <div class="card-header">
               Submission
            </div>
            <div class="card-body card-collapse">
                <div class="row">
                    <div class="col-sm-12">
                        <strong>Submitted by</strong><br/>
                        {{ submitter_first_name }}
                        {{ submitter_last_name }}
                    </div>
                    <div class="col-sm-12 top-buffer-s">
                        <strong>Lodged on</strong><br/>
                        {{ lodgement_date | formatDate}}
                    </div>
                    <div class="col-sm-12 top-buffer-s">
                        <table class="table small-table">
                            <tr>
                                <th>Lodgement</th>
                                <th>Date</th>
                                <th>Action</th>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'Submission',
    data: function() {
        let vm = this;
        return {

        }
    },
    props: {
        submitter_first_name: {
            type: String,
            default: '',
        },
        submitter_last_name: {
            type: String,
            default: '',
        },
        lodgement_date: {
            type: String,
            default: null,
        },
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
}
</script>
