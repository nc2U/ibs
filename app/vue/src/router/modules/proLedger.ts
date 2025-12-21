import { h, resolveComponent } from 'vue'

const proLedger = {
  path: 'project-ledger',
  name: 'PR 회계 관리',
  redirect: '/project-ledger/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: 'PR 정산 현황',
      component: () => import('@/views/proLedger/Status/Index.vue'),
      meta: {
        title: 'PR 정산 현황',
        auth: true,
        requiresProjectCashAuth: true,
      },
    },
    {
      path: 'index',
      name: 'PR 거래 내역',
      component: () => import('@/views/proLedger/Manage/Index.vue'),
      meta: {
        title: 'PR 거래 내역',
        auth: true,
        requiresProjectCashAuth: true,
      },
      children: [
        {
          path: 'create',
          name: 'PR 거래 내역 - 생성',
          meta: {
            title: 'PR 거래 내역',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
        {
          path: ':transId(\\d+)/update',
          name: 'PR 거래 내역 - 수정',
          meta: {
            title: 'PR 거래 내역',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
      ],
    },
    {
      path: 'imprest',
      name: '운영비 내역',
      component: () => import('@/views/proLedger/Imprest/Index.vue'),
      meta: {
        title: '운영비 내역',
        auth: true,
        requiresProjectCashAuth: true,
      },
      children: [
        {
          path: 'create',
          name: '운영비 내역 - 생성',
          meta: {
            title: '운영비 내역',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
        {
          path: ':transId(\\d+)/update',
          name: '운영비 내역 - 수정',
          meta: {
            title: '운영비 내역',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
      ],
    },
  ],
}

export default proLedger
