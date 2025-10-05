import { h, resolveComponent } from 'vue'

const notices = {
  path: 'notices',
  name: '고객 고지 관리',
  redirect: '/notices/bill',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'bill',
      name: '수납 고지서 출력',
      component: () => import('@/views/notices/Bill/Index.vue'),
      meta: {
        title: '수납 고지서 출력',
        auth: true,
        requiresNoticeAuth: true,
      },
    },
    {
      path: 'sms',
      name: 'SMS 발송 관리',
      component: () => import('@/views/notices/Sms/Index.vue'),
      meta: {
        title: 'SMS 발송 관리',
        auth: true,
        requiresNoticeAuth: true,
      },
    },
    {
      path: 'mailing',
      name: 'MAIL 발송 관리',
      component: () => import('@/views/notices/Mailing/Index.vue'),
      meta: {
        title: 'MAIL 발송 관리',
        auth: true,
        requiresNoticeAuth: true,
      },
    },
    {
      path: 'post-label',
      name: '우편 라벨 관리',
      component: () => import('@/views/notices/Label/Index.vue'),
      meta: {
        title: '우편 라벨 관리',
        auth: true,
        requiresNoticeAuth: true,
      },
    },
    {
      path: 'log',
      name: '발송 기록 관리',
      component: () => import('@/views/notices/Log/Index.vue'),
      meta: {
        title: '발송 기록 관리',
        auth: true,
        requiresNoticeAuth: true,
      },
    },
  ],
}

export default notices
