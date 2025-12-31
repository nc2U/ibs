import { h, resolveComponent } from 'vue'

const payment = {
  path: 'payment',
  name: '계약 납부 관리',
  redirect: '/payment/index',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'index',
      name: '전체 납부 내역',
      component: () => import('@/views/payment/List/Index.vue'),
      meta: {
        title: '전체 납부 내역',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'manage',
      name: '건별 납부 관리',
      component: () => import('@/views/payment/Register/Index.vue'),
      meta: {
        title: '건별 납부 관리',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'manage/:contractId(\\d+)',
      name: '건별 납부 관리 - 상세',
      component: () => import('@/views/payment/Register/Index.vue'),
      meta: {
        title: '건별 납부 관리',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
    {
      path: 'status',
      name: '납부 현황 집계',
      component: () => import('@/views/payment/Status/Index.vue'),
      meta: {
        title: '납부 현황 집계',
        auth: true,
        requiresPaymentAuth: true,
      },
    },
  ],
}

export default payment
