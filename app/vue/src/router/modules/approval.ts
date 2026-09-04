import { h, resolveComponent } from 'vue'

const approval = {
  path: 'approval',
  name: '전자 결재 관리',
  redirect: '/approval/pending',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'pending',
      name: '결재 대기함',
      component: () => import('@/views/approval/Index.vue'),
      meta: { title: '결재 대기함', auth: true },
      children: [
        {
          path: ':docId(\\d+)',
          name: '결재 대기함 - 보기',
          component: () => import('@/views/approval/Index.vue'),
        },
      ],
    },
    {
      path: 'drafted',
      name: '기안 문서함',
      component: () => import('@/views/approval/Index.vue'),
      meta: { title: '기안 문서함', auth: true },
      children: [
        {
          path: ':docId(\\d+)',
          name: '기안 문서함 - 보기',
          component: () => import('@/views/approval/Index.vue'),
        },
        {
          path: 'create',
          name: '기안 문서함 - 작성',
          component: () => import('@/views/approval/Index.vue'),
        },
        {
          path: ':docId(\\d+)/edit',
          name: '기안 문서함 - 수정',
          component: () => import('@/views/approval/Index.vue'),
        },
      ],
    },
    {
      path: 'approved',
      name: '결재 문서함',
      component: () => import('@/views/approval/Index.vue'),
      meta: { title: '결재 문서함', auth: true },
      children: [
        {
          path: ':docId(\\d+)',
          name: '결재 문서함 - 보기',
          component: () => import('@/views/approval/Index.vue'),
        },
      ],
    },
    {
      path: 'all',
      name: '전체 문서함',
      component: () => import('@/views/approval/Index.vue'),
      meta: { title: '전체 문서함', auth: true },
      children: [
        {
          path: ':docId(\\d+)',
          name: '전체 문서함 - 보기',
          component: () => import('@/views/approval/Index.vue'),
        },
      ],
    },
    {
      path: 'official-letters',
      name: '공문 발송 대장',
      component: () => import('@/views/approval/OfficialLetter/Index.vue'),
      meta: { title: '공문 발송 대장', auth: true },
      children: [
        {
          path: ':letterId(\\d+)',
          name: '공문 발송 대장 - 보기',
        },
        {
          path: 'create',
          name: '공문 발송 대장 - 작성',
        },
        {
          path: ':letterId(\\d+)/edit',
          name: '공문 발송 대장 - 수정',
        },
      ],
    },
    {
      path: 'delegation',
      name: '결재 위임 관리',
      component: () => import('@/views/approval/Index.vue'),
      meta: { title: '결재 위임 관리', auth: true },
    },
  ],
}

export default approval
