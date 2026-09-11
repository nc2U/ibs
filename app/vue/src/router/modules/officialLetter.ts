import { h, resolveComponent } from 'vue'

const officialLetter = {
  path: 'official-letter',
  name: '대외 공문 관리',
  redirect: '/official-letter/outbound',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'outbound',
      name: '발송 공문 관리',
      component: () => import('@/views/letters/Outbound/Index.vue'),
      meta: { title: '발송 공문 관리', auth: true },
      children: [
        {
          path: ':letterId(\\d+)',
          name: '발송 공문 관리 - 보기',
        },
        {
          path: 'create',
          name: '발송 공문 관리 - 작성',
        },
        {
          path: ':letterId(\\d+)/edit',
          name: '발송 공문 관리 - 수정',
        },
      ],
    },
    {
      path: 'inbound',
      name: '수신 공문 관리',
      component: () => import('@/views/letters/Inbound/Index.vue'),
      meta: { title: '수신 공문 관리', auth: true },
    },
  ],
}

export default officialLetter
