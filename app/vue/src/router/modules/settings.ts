import { h, resolveComponent } from 'vue'

const settings = {
  path: 'settings',
  name: '환 경 설 정',
  redirect: '/settings/company',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'company',
      name: '회사 정보 관리',
      component: () => import('@/views/settings/Company/Index.vue'),
      meta: {
        title: '회사 정보 관리',
        auth: true,
        requiresCompanySettingsAuth: true,
      },
    },
    {
      path: 'authorization',
      name: '권한 설정 관리',
      component: () => import('@/views/settings/Authorization/Index.vue'),
      meta: {
        title: '권한 설정 관리',
        auth: true,
        requiresAuthManageAuth: true,
      },
    },
  ],
}

export default settings
