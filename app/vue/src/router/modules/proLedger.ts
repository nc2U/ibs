import { h, resolveComponent } from 'vue'

const proLedger = {
  path: 'project-ledger',
  name: '회계 자금 관리',
  redirect: '/project-ledger/status',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'status',
      name: '정산 현황 관리',
      component: () => import('@/views/proLedger/Status/Index.vue'),
      meta: {
        title: '정산 현황 관리',
        auth: true,
        requiresProjectCashAuth: true,
      },
    },
    {
      path: 'manage',
      name: '거래 내역 관리',
      component: () => import('@/views/proLedger/Manage/Index.vue'),
      meta: {
        title: '거래 내역 관리',
        auth: true,
        requiresProjectCashAuth: true,
      },
      children: [
        {
          path: 'create',
          name: '거래 내역 관리 - 생성',
          meta: {
            title: '거래 내역 관리',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
        {
          path: ':transId(\\d+)/update',
          name: '거래 내역 관리 - 수정',
          meta: {
            title: '거래 내역 관리',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
      ],
    },
    {
      path: 'imprest',
      name: '운영비 내역 관리',
      component: () => import('@/views/proLedger/Imprest/Index.vue'),
      meta: {
        title: '운영비 내역 관리',
        auth: true,
        requiresProjectCashAuth: true,
      },
      children: [
        {
          path: 'create',
          name: '운영비 내역 관리 - 생성',
          meta: {
            title: '운영비 내역 관리',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
        {
          path: ':transId(\\d+)/update',
          name: '운영비 내역 관리 - 수정',
          meta: {
            title: '운영비 내역 관리',
            auth: true,
            requiresCompanyCashAuth: true,
          },
        },
      ],
    },
  ],
}

export default proLedger
