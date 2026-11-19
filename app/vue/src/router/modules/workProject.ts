const workProject = {
  path: 'work',
  name: '업 무 관 리',
  redirect: '/work/project/list',
  component: () => import('@/views/_Work/Manages/Layout.vue'),
  meta: { title: '업 무 관 리', auth: true, affix: true },
  children: [
    {
      path: 'project',
      name: '워크스페이스',
      redirect: '/work/project/list',
      component: () => import('@/views/_Work/Manages/Projects/Index.vue'),
      children: [
        {
          path: 'list',
          name: '워크스페이스 - 리스트',
          component: () => import('@/views/_Work/Manages/Projects/components/ProjectList.vue'),
        },
        {
          path: 'create',
          name: '워크스페이스 - 추가',
          component: () => import('@/views/_Work/Manages/Projects/components/ProjectCreate.vue'),
        },
        {
          path: ':projId',
          name: '(개요)',
          component: () => import('@/views/_Work/Manages/Projects/components/Overview/Index.vue'),
        },
        {
          path: ':projId/meeting',
          name: '(회의)',
          component: () => import('@/views/_Work/Manages/Projects/components/Meetings/Index.vue'),
          children: [
            {
              path: 'create',
              name: '(회의) - 추가',
            },
            {
              path: ':meetingId(\\d+)',
              name: '(회의) - 보기',
            },
            {
              path: ':meetingId(\\d+)/update',
              name: '(회의) - 수정',
            },
          ],
        },
        {
          path: ':projId/activity',
          name: '(업무실행내역)',
          component: () => import('@/views/_Work/Manages/Projects/components/Activity/Index.vue'),
        },
        {
          path: ':projId/roadmap',
          name: '(로드맵)',
          component: () => import('@/views/_Work/Manages/Projects/components/Roadmap/Index.vue'),
          children: [
            {
              path: ':verId(\\d+)',
              name: '(로드맵) - 보기',
            },
            {
              path: 'create',
              name: '(로드맵) - 추가',
            },
            {
              path: ':verId(\\d+)/update',
              name: '(로드맵) - 수정',
            },
          ],
        },
        {
          path: ':projId/issue',
          name: '(업무)',
          component: () => import('@/views/_Work/Manages/Projects/components/Issues/Index.vue'),
          children: [
            {
              path: ':issueId(\\d+)',
              name: '(업무) - 보기',
            },
            {
              path: 'create',
              name: '(업무) - 추가',
            },
            {
              path: 'report',
              name: '(업무) - 보고서',
            },
          ],
        },
        {
          path: ':projId/calendar',
          name: '(캘린더)',
          component: () => import('@/views/_Work/Manages/Projects/components/Calendar/Index.vue'),
        },
        {
          path: ':projId/news',
          name: '(공지)',
          component: () => import('@/views/_Work/Manages/Projects/components/News/Index.vue'),
          children: [
            {
              path: ':newsId(\\d+)',
              name: '(공지) - 보기',
            },
          ],
        },
        {
          path: ':projId/document',
          name: '(문서)',
          component: () => import('@/views/_Work/Manages/Projects/components/Documents/Index.vue'),
          children: [
            {
              path: ':docId(\\d+)',
              name: '(문서) - 보기',
            },
            {
              path: 'case',
              name: '(문서 사건)',
            },
            {
              path: 'case/:caseId(\\d+)',
              name: '(문서 사건) - 보기',
            },
            {
              path: 'case/create',
              name: '(문서 사건) - 작성',
            },
            {
              path: 'case/:caseId(\\d+)/update',
              name: '(문서 사건) - 수정',
            },
          ],
        },
        {
          path: ':projId/forum',
          name: '(게시판)',
          component: () => import('@/views/_Work/Manages/Projects/components/Forum/Index.vue'),
          children: [
            {
              path: ':forumId(\\d+)',
              name: '(게시판) - 보기',
              children: [
                {
                  path: 'create',
                  name: '(게시판) - 게시물 작성',
                },
                {
                  path: ':postId(\\d+)',
                  name: '(게시판) - 게시물 보기',
                  children: [
                    {
                      path: 'edit',
                      name: '(게시판) - 게시물 수정',
                    },
                  ],
                },
              ],
            },
          ],
        },
        {
          path: ':projId/setting',
          name: '(설정)',
          component: () => import('@/views/_Work/Manages/Projects/components/Settings/Index.vue'),
          children: [
            {
              path: 'category/create',
              name: '(설정) - 범주추가',
            },
            {
              path: 'category/:cateId(\\d+)/update',
              name: '(설정) - 범주수정',
            },
          ],
        },
      ],
    },
    {
      path: 'meeting',
      name: '회의',
      component: () => import('@/views/_Work/Manages/Meetings/Index.vue'),
    },
    {
      path: 'activity',
      name: '업무실행내역',
      component: () => import('@/views/_Work/Manages/Activity/Index.vue'),
    },
    {
      path: 'issue',
      name: '업무',
      component: () => import('@/views/_Work/Manages/Issues/Index.vue'),
    },
    {
      path: 'calendar',
      name: '캘린더',
      component: () => import('@/views/_Work/Manages/Calendar/Index.vue'),
    },
    {
      path: 'news',
      name: '공지',
      component: () => import('@/views/_Work/Manages/News/Index.vue'),
    },
    {
      path: 'document',
      name: '문서',
      component: () => import('@/views/_Work/Manages/Documents/Index.vue'),
      children: [
        {
          path: 'case',
          name: '문서 사건',
        },
        {
          path: 'case/:caseId(\\d+)',
          name: '문서 사건 - 보기',
        },
        {
          path: 'case/create',
          name: '문서 사건 - 작성',
        },
        {
          path: 'case/:caseId(\\d+)/update',
          name: '문서 사건 - 수정',
        },
      ],
    },
    {
      path: 'search',
      name: '전체검색',
      component: () => import('@/views/_Work/components/SearchBody/Index.vue'),
    },
  ],
}

export default workProject
