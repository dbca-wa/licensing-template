
import { RouterView } from 'vue-router'
import InternalDashboard from '@/components/internal/dashboard.vue'
import OrgAccessTable from '@/components/internal/organisations/dashboard.vue'
import OrgAccess from '@/components/internal/organisations/access.vue'
import Organisation from '@/components/internal/organisations/manage.vue'
import Proposal from '@/components/internal/proposals/proposal.vue'
import ApprovalDash from '@/components/internal/approvals/dashboard.vue'
import ComplianceDash from '@/components/internal/compliances/dashboard.vue'
import Search from '@/components/internal/search/dashboard.vue'
import PersonDetail from '@/components/internal/person/person_detail.vue'
import Compliance from '../compliances/access.vue'
import Reports from '@/components/reports/reports.vue'
import Approval from '@/components/internal/approvals/approval.vue'

export default
{
    path: '/internal',
    component: RouterView,
    children: [
        {
            path: '/internal',
            component: InternalDashboard
        },
        {
            path: 'approvals',
            component: ApprovalDash,
            name:"internal-approvals-dash"
        },
        {
            path: 'approval/:approval_id',
            component: Approval,
            name: 'internal-approval-detail',
        },
        {
            path: 'compliances',
            component: ComplianceDash,
            name: "internal-compliances-dash"
        },
        {
            path: 'compliance/:compliance_id',
            component: Compliance,

        },
        {
            path: 'search',
            component: Search,
            name:"internal-search"
        },
        {
            path:'reports',
            name:'reports',
            component:Reports
        },
        {
            path: 'organisations',
            component: RouterView,
            children: [
                {
                    path: 'access',
                    component: OrgAccessTable,
                    name:"org-access-dash"
                },
                {
                    path: 'access',
                    component: OrgAccessTable,
                    name:"org-access-dash"
                },
                {
                    path: 'access/:access_id',
                    component: OrgAccess,
                    name:"org-access"
                },
                {
                    path: ':org_id',
                    component: Organisation,
                    name:"internal-org-detail"
                },

            ]
        },
        {
            path: 'proposal/:proposal_id',
            component: Proposal,
            name: 'internal-proposal',
        },
    ]
}
