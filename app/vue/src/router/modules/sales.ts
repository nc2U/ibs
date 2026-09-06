import { h, resolveComponent } from 'vue'

const sales = {
  path: 'sales',
  name: '분양 대행 관리',
  redirect: '/sales/performance',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'performance',
      name: '계약 실적 관리',
      component: () => import('@/views/sales/Performance/Index.vue'),
      meta: {
        title: '계약 실적 관리',
        auth: true,
      },
    },
    {
      path: 'settlement',
      name: '수수료 정산 관리',
      component: () => import('@/views/sales/Settlement/Index.vue'),
      meta: {
        title: '수수료 정산 관리',
        auth: true,
      },
    },
    {
      path: 'payout',
      name: '수수료 지급 관리',
      component: () => import('@/views/sales/Payout/Index.vue'),
      meta: {
        title: '수수료 지급 관리',
        auth: true,
      },
    },
    {
      path: 'organization',
      name: '영업 조직 관리',
      component: () => import('@/views/sales/Organization/Index.vue'),
      meta: {
        title: '영업 조직 관리',
        auth: true,
      },
    },
    {
      path: 'policy',
      name: '수수료 정책 관리',
      component: () => import('@/views/sales/Policy/Index.vue'),
      meta: {
        title: '수수료 정책 관리',
        auth: true,
      },
    },
  ],
}

export default sales
