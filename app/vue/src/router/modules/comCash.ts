import { h, resolveComponent } from 'vue'

const comCash = {
  path: 'cashes',
  name: '본사 자금 관리',
  redirect: '/cashes/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: '본사 자금 현황',
      component: () => import('@/views/comCash/Status/Index.vue'),
      meta: {
        title: '본사 자금 현황',
        auth: true,
        requiresCompanyCashAuth: true,
      },
    },
    {
      path: 'index',
      name: '본사 출납 내역',
      component: () => import('@/views/comCash/CashManage/Index.vue'),
      meta: {
        title: '본사 출납 내역',
        auth: true,
        requiresCompanyCashAuth: true,
      },
    },
  ],
}

export default comCash
