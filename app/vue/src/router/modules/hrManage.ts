import { h, resolveComponent } from 'vue'

const hrManage = {
  path: 'hr-manage',
  name: '인사 조직 관리',
  redirect: '/hr-manage/org-chart',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'department',
      name: '부서 관리',
      component: () => import('@/views/hrManage/Organization/Department/Index.vue'),
      meta: {
        title: '부서 관리',
        auth: true,
      },
    },
    {
      path: 'grade',
      name: '직급 관리',
      component: () => import('@/views/hrManage/Organization/Grade/Index.vue'),
      meta: {
        title: '직급 관리',
        auth: true,
      },
    },
    {
      path: 'position',
      name: '직위 관리',
      component: () => import('@/views/hrManage/Organization/Position/Index.vue'),
      meta: {
        title: '직위 관리',
        auth: true,
      },
    },
    {
      path: 'duty',
      name: '직책 관리',
      component: () => import('@/views/hrManage/Organization/Duty/Index.vue'),
      meta: {
        title: '직책 관리',
        auth: true,
      },
    },
    {
      path: 'org-chart',
      name: '조 직 도',
      component: () => import('@/views/hrManage/Organization/OrgChart/Index.vue'),
      meta: {
        title: '조 직 도',
        auth: true,
      },
    },
    {
      path: 'staff',
      name: '직원 정보',
      component: () => import('@/views/hrManage/HRManage/Staff/Index.vue'),
      meta: {
        title: '직원 정보',
        auth: true,
      },
    },
    {
      path: 'attendance',
      name: '근태 현황',
      component: () => import('@/views/hrManage/HRManage/Attendance/Index.vue'),
      meta: {
        title: '근태 현황',
        auth: true,
      },
    },
    {
      path: 'leave',
      name: '휴가 연차',
      component: () => import('@/views/hrManage/HRManage/Leave/Index.vue'),
      meta: {
        title: '휴가 연차',
        auth: true,
      },
    },
    {
      path: 'appointments',
      name: '인사 발령',
      component: () => import('@/views/hrManage/HRManage/Appointment/Index.vue'),
      meta: {
        title: '인사 발령',
        auth: true,
      },
    },
    {
      path: 'records',
      name: '인사 기록',
      component: () => import('@/views/hrManage/HRManage/Record/Index.vue'),
      meta: {
        title: '인사 기록',
        auth: true,
      },
    },
    {
      path: 'other-settings',
      name: '기타 설정',
      component: () => import('@/views/hrManage/Settings/Index.vue'),
      meta: {
        title: '기타 설정',
        auth: true,
      },
    },
  ],
}

export default hrManage
