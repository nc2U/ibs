import { h, resolveComponent } from 'vue'

const hrManage = {
  path: 'hr-manage',
  name: '인사 조직 관리',
  redirect: '/hr-manage/department',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'department',
      name: '부서 정보 관리',
      component: () => import('@/views/hrManage/Organization/Department/Index.vue'),
      meta: {
        title: '부서 정보 관리',
        auth: true,
      },
    },
    {
      path: 'grade',
      name: '직급 정보 관리',
      component: () => import('@/views/hrManage/Organization/Grade/Index.vue'),
      meta: {
        title: '직급 정보 관리',
        auth: true,
      },
    },
    {
      path: 'position',
      name: '직위 정보 관리',
      component: () => import('@/views/hrManage/Organization/Position/Index.vue'),
      meta: {
        title: '직위 정보 관리',
        auth: true,
      },
    },
    {
      path: 'duty',
      name: '직책 정보 관리',
      component: () => import('@/views/hrManage/Organization/Duty/Index.vue'),
      meta: {
        title: '직책 정보 관리',
        auth: true,
      },
    },
    {
      path: 'executive-rank',
      name: '임원 직위 관리',
      component: () => import('@/views/hrManage/Organization/ExecutiveRank/Index.vue'),
      meta: {
        title: '임원 직위 관리',
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
      name: '직원 정보 관리',
      component: () => import('@/views/hrManage/HRManage/Staff/Index.vue'),
      meta: {
        title: '직원 정보 관리',
        auth: true,
      },
    },
    {
      path: 'executives',
      name: '임원 재임 관리',
      component: () => import('@/views/hrManage/HRManage/Appointment/Index.vue'),
      meta: {
        title: '임원 재임 관리',
        auth: true,
      },
    },
    {
      path: 'appointments',
      name: '인사 발령 관리',
      component: () => import('@/views/hrManage/HRManage/Appointment/Index.vue'),
      meta: {
        title: '인사 발령 관리',
        auth: true,
      },
    },
    {
      path: 'records',
      name: '인사 이력 관리',
      component: () => import('@/views/hrManage/HRManage/Record/Index.vue'),
      meta: {
        title: '인사 이력 관리',
        auth: true,
      },
    },
    {
      path: 'leave-quota',
      name: '연차 부여 관리',
      component: () => import('@/views/hrManage/Attendance/LeaveQuota/Index.vue'),
      meta: {
        title: '연차 부여 관리',
        auth: true,
      },
    },
    {
      path: 'leave-usage',
      name: '휴가 사용 내역',
      component: () => import('@/views/hrManage/Attendance/LeaveUsage/Index.vue'),
      meta: {
        title: '휴가 사용 내역',
        auth: true,
      },
    },
    {
      path: 'attendance',
      name: '근태 현황 관리',
      component: () => import('@/views/hrManage/Attendance/Status/Index.vue'),
      meta: {
        title: '근태 현황 관리',
        auth: true,
      },
    },
    {
      path: 'evaluations',
      name: '인사 업적 평가',
      component: () => import('@/views/hrManage/Promotion/Evaluation/Index.vue'),
      meta: {
        title: '인사 업적 평가',
        auth: true,
      },
    },
    {
      path: 'promotions',
      name: '승진 심사 대상',
      component: () => import('@/views/hrManage/Promotion/Candidates/Index.vue'),
      meta: {
        title: '승진 심사 대상',
        auth: true,
      },
    },
    {
      path: 'promotion-policy',
      name: '승급 정책 설정',
      component: () => import('@/views/hrManage/Promotion/Policy/Index.vue'),
      meta: {
        title: '승급 정책 설정',
        auth: true,
      },
    },
  ],
}

export default hrManage
