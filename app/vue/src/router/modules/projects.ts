import { h, resolveComponent } from 'vue'

const projects = {
  path: 'project',
  name: 'PR 등록 관리',
  redirect: '/project/manage/index',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'manage/index',
      name: '신규 PR 등록',
      component: () => import('@/views/projects/List/Index.vue'),
      meta: {
        title: '신규 PR 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'site/index',
      name: '지번 목록 관리',
      component: () => import('@/views/projects/SiteList/Index.vue'),
      meta: {
        title: '지번 목록 관리',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'site/owner',
      name: '소유자 별 관리',
      component: () => import('@/views/projects/SiteOwner/Index.vue'),
      meta: {
        title: '소유자 별 관리',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'site/contract',
      name: '매입 계약 관리',
      component: () => import('@/views/projects/SiteContract/Index.vue'),
      meta: {
        title: '매입 계약 관리',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'manage/inc-budget',
      name: '수입 예산 등록',
      component: () => import('@/views/projects/IncBudget/Index.vue'),
      meta: {
        title: '수입 예산 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'manage/out-budget',
      name: '지출 예산 등록',
      component: () => import('@/views/projects/OutBudget/Index.vue'),
      meta: {
        title: '지출 예산 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'manage/order',
      name: '차수 분류 등록',
      component: () => import('@/views/projects/OrderGroup/Index.vue'),
      meta: {
        title: '차수 분류 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'manage/type',
      name: '타입 정보 등록',
      component: () => import('@/views/projects/Type/Index.vue'),
      meta: {
        title: '타입 정보 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/floor',
      name: '층별 조건 등록',
      component: () => import('@/views/projects/Floor/Index.vue'),
      meta: {
        title: '층별 조건 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/bldg',
      name: '동(건물) 등록',
      component: () => import('@/views/projects/Building/Index.vue'),
      meta: {
        title: '동(건물) 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/unit',
      name: '호(유닛) 등록',
      component: () => import('@/views/projects/Unit/Index.vue'),
      meta: {
        title: '호(유닛) 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/payment-order',
      name: '납부 회차 등록',
      component: () => import('@/views/projects/PayOrder/Index.vue'),
      meta: {
        title: '납부 회차 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/down-payment',
      name: '계약 금액 등록',
      component: () => import('@/views/projects/DownPay/Index.vue'),
      meta: {
        title: '계약 금액 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/price',
      name: '공급 가격 등록',
      component: () => import('@/views/projects/Price/Index.vue'),
      meta: {
        title: '공급 가격 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/required',
      name: '구비 서류 등록',
      component: () => import('@/views/projects/Required/Index.vue'),
      meta: {
        title: '구비 서류 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
    {
      path: 'settings/options',
      name: '옵션 품목 등록',
      component: () => import('@/views/projects/PaidOption/Index.vue'),
      meta: {
        title: '옵션 품목 등록',
        auth: true,
        requiresProjectAuth: true,
      },
    },
  ],
}

export default projects
