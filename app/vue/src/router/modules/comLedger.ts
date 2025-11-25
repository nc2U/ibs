import { h, resolveComponent } from 'vue'

const comLedger = {
  path: 'ledger',
  name: '본사 회계 관리',
  redirect: '/ledger/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: '본사 자금 현황1',
      component: () => import('@/views/comLedger/Status/Index.vue'),
      meta: {
        title: '본사 자금 현황1',
        auth: true,
        requiresCompanyCashAuth: true,
      },
    },
    {
      path: 'index',
      name: '본사 출납 내역1',
      component: () => import('@/views/comLedger/CashManage/Index.vue'),
      meta: {
        title: '본사 출납 내역1',
        auth: true,
        requiresCompanyCashAuth: true,
      },
    },
  ],
}

export default comLedger
