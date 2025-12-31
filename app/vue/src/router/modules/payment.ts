import { h, resolveComponent } from 'vue'

const payments = {
  path: 'payments',
  name: '분양 수납 관리',
  redirect: '/payments/index',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'index',
      name: '전체 납부 내역',
      component: () => import('@/views/payments/List/Index.vue'),
      meta: {
        title: '전체 납부 내역',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'manage',
      name: '건별 수납 관리',
      component: () => import('@/views/payments/Register/Index.vue'),
      meta: {
        title: '건별 수납 관리',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'manage/:contractId(\\d+)',
      name: '건별 수납 내역',
      component: () => import('@/views/payments/Register/Index.vue'),
      meta: {
        title: '건별 수납 관리',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'status',
      name: '수납 현황 집계',
      component: () => import('@/views/payments/Status/Index.vue'),
      meta: {
        title: '수납 현황 집계',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
  ],
}

export default payments
