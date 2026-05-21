import { h, resolveComponent } from 'vue'

const proDocs = {
  path: 'project-docs',
  name: '문서 소송 관리',
  redirect: '/project-docs/general/docs',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  children: [
    {
      path: 'general/docs',
      name: '일반 문서 관리',
      component: () => import('@/views/proDocs/GeneralDocs/Index.vue'),
      meta: {
        title: '일반 문서 관리',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: '일반 문서 관리 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: '일반 문서 관리 - 수정',
        },
        {
          path: 'create',
          name: '일반 문서 관리 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/docs',
      name: '소송 문서 관리',
      component: () => import('@/views/proDocs/LawsuitDocs/Index.vue'),
      meta: {
        title: '소송 문서 관리',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':docsId(\\d+)',
          name: '소송 문서 관리 - 보기',
        },
        {
          path: ':docsId(\\d+)/update',
          name: '소송 문서 관리 - 수정',
        },
        {
          path: 'create',
          name: '소송 문서 관리 - 작성',
        },
      ],
    },
    {
      path: 'lawsuit/case',
      name: '소송 사건 관리',
      component: () => import('@/views/proDocs/LawsuitCase/Index.vue'),
      meta: {
        title: '소송 사건 관리',
        auth: true,
        requiresProjectDocsAuth: true,
      },
      children: [
        {
          path: ':caseId(\\d+)',
          name: '소송 사건 관리 - 보기',
        },
        {
          path: ':caseId(\\d+)/update',
          name: '소송 사건 관리 - 수정',
        },
        {
          path: 'create',
          name: '소송 사건 관리 - 작성',
        },
      ],
    },
  ],
}

export default proDocs
