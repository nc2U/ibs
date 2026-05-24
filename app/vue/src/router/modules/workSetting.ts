import { h, resolveComponent } from 'vue'

const workSetting = {
  path: 'manage',
  name: '설 정 관 리',
  redirect: '/manage/user',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  meta: { title: '설 정 관 리', auth: true },
  children: [
    {
      path: 'user',
      name: '사용자',
      component: () => import('@/views/_Work/Settings/Users/Index.vue'),
      children: [
        {
          path: ':userId',
          name: '사용자 - 보기',
        },
        {
          path: 'create',
          name: '사용자 - 생성',
        },
        {
          path: ':userId/update',
          name: '사용자 - 수정',
        },
      ],
    },
    {
      path: 'role',
      name: '역할 및 권한',
      component: () => import('@/views/_Work/Settings/Roles_Perms/Index.vue'),
    },
  ],
}

export default workSetting
