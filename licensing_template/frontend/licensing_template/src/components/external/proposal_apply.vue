<template lang="html">
    <div class="container" >
        <!--button type="button" @click="createML">Mooring Licence Application</button-->
        <div class="row" v-if="applicationsLoading">
            <div class="col-sm-3">
                <i class='fa fa-5x fa-spinner fa-spin pull-right'></i>
            </div>
        </div>
        <div v-else class="row">
            <div class="col-sm-12">
                <form class="form-horizontal" name="personal_form" method="post">
                    <FormSection label="Apply on behalf of">
                        <label style="margin-left:20px">Apply on behalf of</label>
                        <div class="col-sm-12" style="margin-left:20px">
                            <div class="form-group">
                            </div>
                        </div>
                    </FormSection>

                    <FormSection label="Apply for">
                        <label style="margin-left:20px">Apply for</label>
                        <div class="col-sm-12" style="margin-left:20px">
                            <div class="form-group">
                                <div v-for="(application_type, index) in application_types">
                                    <input 
                                    type="radio" 
                                    name="applicationType" 
                                    :id="application_type.code + '_' + index" 
                                    :value="application_type" 
                                    v-model="selectedApplication"
                                    />
                                    <label :for="application_type.code + '_' + index" style="font-weight:normal">{{ application_type.description }}</label>
                                </div>
                            </div>
                        </div>
                    </FormSection>
                    <div class="col-sm-12">
                        <button v-if="!creatingProposal" :disabled="isDisabled" @click.prevent="submit()" class="btn btn-primary pull-right">Continue</button>
                        <button v-else disabled class="pull-right btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Creating</button>
                    </div>
                  </form>
            </div>
        </div>
    </div>
</template>
<script>
import Vue from 'vue'
import FormSection from '@/components/forms/section_toggle.vue'
//require('bootstrap/dist/css/bootstrap.css')
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import utils from './utils'
export default {
  data: function() {
    let vm = this;
    return {
        applicationsLoading: false,
        "proposal": null,
        profile: {
        },
        "loading": [],
        form: null,
        selectedApplication: {},
        selectedCurrentProposal: null,
        //selected_application_name: '',
        application_types: [],
        creatingProposal: false,
        //site_url: (api_endpoints.site_url.endsWith("/")) ? (api_endpoints.site_url): (api_endpoints.site_url + "/"),
    }
  },
  components: {
      FormSection
  },
  computed: {
    isLoading: function() {
      return this.loading.length > 0
    },
    isDisabled: function() {
        let disabled = true;
        if (this.selectedApplication && this.selectedApplication.code) {
            disabled = false;
        }
        return disabled;
    },
    alertText: function() {
        let text = '';
        if (this.selectedApplication && this.selectedApplication.description) {
            text = this.selectedApplication.description;
        }
		if (this.selectedApplication.code == 'wla') {
            text = "a " + text;
		} else {
        	//return "a Filming";
            text = "an "+ text;
        }
        return text
	},

  },
  methods: {
      /*
    selectApplication(applicationType) {
        this.selectedCurrentProposal = null;
        this.selectedApplication = Object.assign({}, applicationType)
        if (this.selectedApplication.current_proposal_id) {
            this.selectedCurrentProposal = this.selectedApplication.current_proposal_id;
        }
    },
    */
    submit: function() {
        //let vm = this;
        swal.fire({
            title: "Create " + this.selectedApplication.description,
            text: "Are you sure you want to create " + this.alertText + "?",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then(() => {
            this.createProposal();
            /*
            if (!vm.has_active_proposals()) {
         	    vm.createProposal();
            }
            */
        },(error) => {
        });
    },
    createProposal: async function () {
        this.$nextTick(async () => {
            let res = null;
            try {
                this.creatingProposal = true;
                const payload = {
                    "application_type": this.selectedApplication,
                }
                res = await fetch(api_endpoints.proposal, { body: JSON.stringify(payload), method: 'POST' });
                const resData = await res.json()
                const proposal = Object.assign({}, resData);
                this.$router.push({
                    name:"draft_proposal",
                    params:{proposal_id:proposal.id}
                });
                this.creatingProposal = false;
            } catch(error) {
                console.log(error)
                await swal.fire({
                //title: "Renew/Amend Approval",
                title: "Create Proposal",
                text: error.body,
                icon: "error",
                });
                this.$router.go();
            }
        });
    },
	searchList: function(id, search_list){
        /* Searches for dictionary in list */
        for (var i = 0; i < search_list.length; i++) {
            if (search_list[i].value == id) {
                return search_list[i];
            }
        }
        return [];
    },
    fetchApplicationTypes: async function(){
        //const response = await this.$http.get(api_endpoints.application_types_dict+'?apply_page=True');
        const response = await fetch(api_endpoints.application_types_dict);
        const resData = await response.json()
        for (let app_type of resData) {
            this.application_types.push(app_type)
        }
    },
      /*
    fetchExistingLicences: async function(){
        const response = await this.$http.get(api_endpoints.existing_licences);
        for (let l of response.body) {
            this.application_types.push(l)
        }
    },
    */
  },
  mounted: async function() {
    this.applicationsLoading = true;
    await this.fetchApplicationTypes();
    //await this.fetchExistingLicences();
    this.form = document.forms.new_proposal;
    this.applicationsLoading = false;
  },
  beforeRouteEnter: function(to, from, next) {
    let initialisers = [
        utils.fetchProfile(),
        //utils.fetchProposal(to.params.proposal_id)
    ]
    next(vm => {
        vm.loading.push('fetching profile')
        Promise.all(initialisers).then(data => {
            vm.profile = data[0];
            //vm.proposal = data[1];
            vm.loading.splice('fetching profile', 1)
        })
    })
    
  }
}
</script>

<style lang="css">
input[type=text], select{
    width:40%;
    box-sizing:border-box;

    min-height: 34px;
    padding: 0;
    height: auto;
}

.group-box {
	border-style: solid;
	border-width: thin;
	border-color: #FFFFFF;
}
.radio-buttons {
    padding: 5px;
}
</style>
