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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

