import { createRouter, createWebHashHistory } from 'vue-router'
import Cookies from 'js-cookie'
import routes from '@/router/routes'

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.name !== 'Login') Cookies.set('redirectPath', to.path)
  next()
})

export default router
