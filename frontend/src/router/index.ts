import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import List from '../views/List.vue'
import Detail from '../views/Detail.vue'
import Dashboard from '../views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: List },
    { path: '/applications/:id', component: Detail },
    { path: '/dashboard', component: Dashboard },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!localStorage.getItem('token')) return '/login'
  return true
})

export default router
