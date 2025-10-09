import { h, resolveComponent } from 'vue'

const proCash = {
  path: 'project-cash',
  name: 'PR 자금 관리',
  redirect: '/project-cash/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: 'PR 자금 현황',
      component: () => import('@/views/proCash/Status/Index.vue'),
      meta: {
        title: 'PR 자금 현황',
        auth: true,
        requiresProjectCashAuth: true,
      },
    },
    {
      path: 'index',
      name: 'PR 출납 내역',
      component: () => import('@/views/proCash/Manage/Index.vue'),
      meta: {
        title: 'PR 출납 내역',
        auth: true,
        requiresProjectCashAuth: true,
      },
    },
    {
      path: 'imprest',
      name: '운영 비용 내역',
      component: () => import('@/views/proCash/Imprest/Index.vue'),
      meta: {
        title: '운영 비용 내역',
        auth: true,
        requiresProjectCashAuth: true,
      },
    },
  ],
}

export default proCash
