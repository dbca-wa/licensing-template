//import Vue from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Profile from '@/components/user/profile.vue'
import external_routes from '@/components/external/routes'
import internal_routes from '@/components/internal/routes'

//Vue.use(Router)
var NotFoundComponent = null

//console.log(process.env.BASE_URL)
const router = createRouter({
    //history: createWebHistory(process.env.BASE_URL),
    history: createWebHistory(),
    //strict: true,
    routes: [
        {
            path: '/:pathMatch(.*)', 
            component: NotFoundComponent
        },
        {
          path: '/firsttime',
          name: 'first-time',
          component: Profile
        },
        {
          path: '/account',
          name: 'account',
          component: Profile
        },
        external_routes,
        internal_routes,
    ]
})

export default router;
