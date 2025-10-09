import { h, resolveComponent } from 'vue'

const proDocs = {
  path: 'project-docs',
  name: 'PR 문서 관리',
  redirect: '/project-docs/general/docs',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'general/docs',
      name: 'PR 일반 문서',
      component: () => import('@/views/proDocs/GeneralDocs/Index.vue'),
      meta: {
        title: 'PR 일반 문서',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: 'PR 일반 문서 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: 'PR 일반 문서 - 수정',
        },
        {
          path: 'create',
          name: 'PR 일반 문서 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/docs',
      name: 'PR 소송 문서',
      component: () => import('@/views/proDocs/LawsuitDocs/Index.vue'),
      meta: {
        title: 'PR 소송 문서',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: 'PR 소송 문서 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: 'PR 소송 문서 - 수정',
        },
        {
          path: 'create',
          name: 'PR 소송 문서 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/case',
      name: 'PR 소송 사건',
      component: () => import('@/views/proDocs/LawsuitCase/Index.vue'),
      meta: {
        title: 'PR 소송 사건',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':caseId(\\d+)',
          name: 'PR 소송 사건 - 보기',
        },
        {
          path: ':caseId(\\d+)/update',
          name: 'PR 소송 사건 - 수정',
        },
        {
          path: 'create',
          name: 'PR 소송 사건 - 작성',
        },
      ],
    },
  ],
}

export default proDocs
