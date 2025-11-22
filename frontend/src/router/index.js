import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/rules',
    name: 'AllRules',
    component: () => import('../views/AllRules.vue'),
  },
  {
    path: '/rules/:id',
    name: 'RuleDetail',
    component: () => import('../views/RuleDetail.vue'),
  },
  {
    path: '/requests',
    name: 'Requests',
    component: () => import('../views/RequestsList.vue'),
  },
  {
    path: '/requests/new',
    name: 'RequestNew',
    component: () => import('../views/RequestNew.vue'),
  },
  {
    path: '/requests/:id',
    name: 'RequestDetail',
    component: () => import('../views/RequestDetail.vue'),
  },
  {
    path: '/requests/:requestId/rules/:ruleId',
    name: 'RequestRuleDetail',
    component: () => import('../views/RuleDetail.vue'),
  },
  {
    path: '/assets',
    name: 'Assets',
    component: () => import('../views/AssetsList.vue'),
  },
  {
    path: '/assets/upload',
    name: 'AssetUpload',
    component: () => import('../views/AssetUpload.vue'),
  },
  {
    path: '/assets/:id',
    name: 'AssetDetail',
    component: () => import('../views/AssetDetail.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

