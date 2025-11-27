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
      name: '본사 정산 현황',
      component: () => import('@/views/comLedger/Status/Index.vue'),
      meta: {
        title: '본사 정산 현황',
        auth: true,
        requiresCompanyCashAuth: true,
      },
    },
    {
      path: 'index',
      name: '본사 거래 내역',
      component: () => import('@/views/comLedger/CashManage/Index.vue'),
      meta: {
        title: '본사 거래 내역',
        auth: true,
        requiresCompanyCashAuth: true,
      },
      children: [
        {
          path: ':transId(\\d+)/update',
          name: '본사 거래 내역 - 수정',
          meta: {
            title: '본사 거래 내역',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
      ],
    },
  ],
}

export default comLedger
