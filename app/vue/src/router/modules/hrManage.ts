import { h, resolveComponent } from 'vue'

const hrManage = {
  path: 'hr-manage',
  name: '인사 조직 관리',
  redirect: '/hr-manage/staff',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'staff',
      name: '직원 정보',
      component: () => import('@/views/hrManage/Staff/Index.vue'),
      meta: {
        title: '직원 정보',
        auth: true,
        requiresHrAuth: true,
      },
    },
    {
      path: 'department',
      name: '부서 관리',
      component: () => import('@/views/hrManage/Department/Index.vue'),
      meta: {
        title: '부서 관리',
        auth: true,
        requiresHrAuth: true,
      },
    },
    {
      path: 'position',
      name: '직위 관리',
      component: () => import('@/views/hrManage/Position/Index.vue'),
      meta: {
        title: '직위 관리',
        auth: true,
        requiresHrAuth: true,
      },
    },
    {
      path: 'duty',
      name: '직책 관리',
      component: () => import('@/views/hrManage/Duty/Index.vue'),
      meta: {
        title: '직책 관리',
        auth: true,
        requiresHrAuth: true,
      },
    },
    {
      path: 'grade',
      name: '직급 관리',
      component: () => import('@/views/hrManage/Grade/Index.vue'),
      meta: {
        title: '직급 관리',
        auth: true,
        requiresHrAuth: true,
      },
    },
  ],
}

export default hrManage
