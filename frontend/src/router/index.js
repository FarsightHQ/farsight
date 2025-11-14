import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
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
    path: '/requests/:id/rules',
    name: 'RulesList',
    component: () => import('../views/RulesList.vue'),
  },
  {
    path: '/rules/:id',
    name: 'RuleDetail',
    component: () => import('../views/RuleDetail.vue'),
  },
  {
    path: '/assets',
    name: 'AssetsList',
    component: () => import('../views/AssetsList.vue'),
  },
  {
    path: '/assets/upload',
    name: 'AssetUpload',
    component: () => import('../views/AssetUpload.vue'),
  },
  {
    path: '/assets/:ip_address',
    name: 'AssetDetail',
    component: () => import('../views/AssetDetail.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

