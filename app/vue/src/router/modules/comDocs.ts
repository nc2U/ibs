import { h, resolveComponent } from 'vue'

const comDocs = {
  path: 'docs',
  name: '본사 문서 관리',
  redirect: '/docs/general/docs',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'general/docs',
      name: '본사 일반 문서',
      component: () => import('@/views/comDocs/GeneralDocs/Index.vue'),
      meta: {
        title: '본사 일반 문서',
        auth: true,
        requiresCompanyDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: '본사 일반 문서 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: '본사 일반 문서 - 수정',
        },
        {
          path: 'create',
          name: '본사 일반 문서 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/docs',
      name: '본사 소송 문서',
      component: () => import('@/views/comDocs/LawsuitDocs/Index.vue'),
      meta: {
        title: '본사 소송 문서',
        auth: true,
        requiresCompanyDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: '본사 소송 문서 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: '본사 소송 문서 - 수정',
        },
        {
          path: 'create',
          name: '본사 소송 문서 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/case',
      name: '본사 소송 사건',
      component: () => import('@/views/comDocs/LawsuitCase/Index.vue'),
      meta: {
        title: '본사 소송 사건',
        auth: true,
        requiresCompanyDocsAuth: true,
      },
      children: [
        {
          path: ':caseId(\\d+)',
          name: '본사 소송 사건 - 보기',
        },
        {
          path: ':caseId(\\d+)/update',
          name: '본사 소송 사건 - 수정',
        },
        {
          path: 'create',
          name: '본사 소송 사건 - 작성',
        },
      ],
    },
    {
      path: 'official/letters',
      name: '본사 공문 발송',
      component: () => import('@/views/comDocs/OfficialLetter/Index.vue'),
      meta: {
        title: '본사 공문 발송',
        auth: true,
        requiresCompanyDocsAuth: true,
      },
      children: [
        {
          path: ':letterId(\\d+)',
          name: '본사 공문 발송 - 보기',
        },
        {
          path: ':letterId(\\d+)/update',
          name: '본사 공문 발송 - 수정',
        },
        {
          path: 'create',
          name: '본사 공문 발송 - 작성',
        },
      ],
    },
  ],
}

export default comDocs
