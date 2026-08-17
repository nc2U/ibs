import { h, resolveComponent } from 'vue'

const approval = {
  path: 'approval',
  name: '전자결재',
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
      component: () => import('@/views/approval/PendingList.vue'),
      meta: { title: '결재 대기함', auth: true },
    },
    {
      path: 'drafted',
      name: '기안함',
      component: () => import('@/views/approval/DraftedList.vue'),
      meta: { title: '기안함', auth: true },
    },
    {
      path: 'create',
      name: '결재문서 작성',
      component: () => import('@/views/approval/DocumentForm.vue'),
      meta: { title: '결재문서 작성', auth: true },
    },
    {
      path: ':docId(\\d+)',
      name: '결재문서 상세',
      component: () => import('@/views/approval/DocumentDetail.vue'),
      meta: { title: '결재문서 상세', auth: true },
    },
    {
      path: ':docId(\\d+)/edit',
      name: '결재문서 수정',
      component: () => import('@/views/approval/DocumentForm.vue'),
      meta: { title: '결재문서 수정', auth: true },
    },
  ],
}

export default approval
