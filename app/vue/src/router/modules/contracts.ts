import { h, resolveComponent } from 'vue'

const contract = {
  path: 'contracts',
  name: '공급 계약 관리',
  redirect: '/contracts/index',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'index',
      name: '계약 내역 조회',
      component: () => import('@/views/contracts/List/Index.vue'),
      meta: {
        title: '계약 내역 조회',
        auth: true,
        requiresContractAuth: true,
      },
    },
    {
      path: 'register',
      name: '계약 상세 관리',
      component: () => import('@/views/contracts/Manage/Index.vue'),
      meta: {
        title: '계약 상세 관리',
        auth: true,
        requiresContractAuth: true,
      },
    },
    {
      path: 'succession',
      name: '권리 의무 승계',
      component: () => import('@/views/contracts/Succession/Index.vue'),
      meta: {
        title: '권리 의무 승계',
        auth: true,
        requiresContractAuth: true,
      },
    },
    {
      path: 'release',
      name: '계약 해지 관리',
      component: () => import('@/views/contracts/Release/Index.vue'),
      meta: {
        title: '계약 해지 관리',
        auth: true,
        requiresContractAuth: true,
      },
    },
    {
      path: 'status',
      name: '동호 배치 현황',
      component: () => import('@/views/contracts/Status/Index.vue'),
      meta: {
        title: '동호 배치 현황',
        auth: true,
        requiresContractAuth: true,
      },
    },
  ],
}

export default contract
