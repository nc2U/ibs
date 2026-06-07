import { h, resolveComponent } from 'vue'

const workProject = {
  path: 'work',
  name: '업 무 관 리',
  redirect: '/work/project/list',
  component: {
    render() {
      return h(resolveComponent('router-view'))
    },
  },
  meta: { title: '업 무 관 리', auth: true, affix: true },
  children: [
    {
      path: 'project',
      name: '프로젝트',
      redirect: '/work/project/list',
      component: () => import('@/views/_Work/Manages/Projects/Index.vue'),
      children: [
        {
          path: 'list',
          name: '프로젝트 - 리스트',
          component: () => import('@/views/_Work/Manages/Projects/components/ProjectList.vue'),
        },
        {
          path: 'create',
          name: '프로젝트 - 추가',
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
              path: ':meetingId',
              name: '(회의) - 보기',
            },
            {
              path: ':meetingId/update',
              name: '(회의) - 수정',
            },
          ],
        },
        {
          path: ':projId/activity',
          name: '(실행기록)',
          component: () => import('@/views/_Work/Manages/Projects/components/Activity/Index.vue'),
        },
        {
          path: ':projId/roadmap',
          name: '(추진현황)',
          component: () => import('@/views/_Work/Manages/Projects/components/Roadmap/Index.vue'),
          children: [
            {
              path: ':verId',
              name: '(추진현황) - 보기',
            },
            {
              path: 'create',
              name: '(추진현황) - 추가',
            },
            {
              path: ':verId/update',
              name: '(추진현황) - 수정',
            },
            // {
            //   path: ':verId/delete',
            //   name: '(추진현황) - 삭제',
            // },
          ],
        },
        {
          path: ':projId/issue',
          name: '(업무)',
          component: () => import('@/views/_Work/Manages/Projects/components/Issues/Index.vue'),
          children: [
            {
              path: ':issueId',
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
        // {
        //   path: ':projId/time_entry',
        //   name: '(소요시간)',
        //   component: () => import('@/views/_Work/Manages/Projects/components/SpentTime/Index.vue'),
        //   children: [
        //     {
        //       path: 'create',
        //       name: '(소요시간) - 추가',
        //     },
        //     {
        //       path: ':timeId/update',
        //       name: '(소요시간) - 편집',
        //     },
        //     // {
        //     //   path: ':timeId/delete',
        //     //   name: '(소요시간) - 삭제',
        //     // },
        //   ],
        // },
        {
          path: ':projId/calendar',
          name: '(달력)',
          component: () => import('@/views/_Work/Manages/Projects/components/Calendar/Index.vue'),
        },
        {
          path: ':projId/news',
          name: '(공지)',
          component: () => import('@/views/_Work/Manages/Projects/components/News/Index.vue'),
          children: [
            {
              path: ':newsId',
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
              path: 'create',
              name: '(문서) - 추가',
            },
            {
              path: ':docId',
              name: '(문서) - 보기',
            },
            {
              path: ':docId/update',
              name: '(문서) - 편집',
            },
          ],
        },
        {
          path: ':projId/forum',
          name: '(게시판)',
          component: () => import('@/views/_Work/Manages/Projects/components/Forum/Index.vue'),
          children: [
            {
              path: ':forumId',
              name: '(게시판) - 보기',
              children: [
                {
                  path: 'create',
                  name: '(게시판) - 게시물 작성',
                },
                {
                  path: ':postId',
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
              path: 'category/:cateId/update',
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
      children: [
        {
          path: 'create',
          name: '회의 - 추가',
        },
        {
          path: ':meetingId',
          name: '회의 - 보기',
        },
        {
          path: ':meetingId/update',
          name: '회의 - 수정',
        },
      ],
    },
    {
      path: 'activity',
      name: '실행기록',
      component: () => import('@/views/_Work/Manages/Activity/Index.vue'),
    },
    {
      path: 'issue',
      name: '업무',
      component: () => import('@/views/_Work/Manages/Issues/Index.vue'),
      children: [
        {
          path: 'create',
          name: '업무 - 추가',
        },
      ],
    },
    // {
    //   path: 'time_entry',
    //   name: '소요시간',
    //   component: () => import('@/views/_Work/Manages/SpentTime/Index.vue'),
    //   children: [
    //     {
    //       path: 'create',
    //       name: '소요시간 - 추가',
    //     },
    //     {
    //       path: ':timeId/update',
    //       name: '소요시간 - 편집',
    //     },
    //     // {
    //     //   path: ':timeId/delete',
    //     //   name: '소요시간 - 삭제',
    //     // },
    //   ],
    // },
    {
      path: 'calendar',
      name: '달력',
      component: () => import('@/views/_Work/Manages/Calendar/Index.vue'),
    },
    {
      path: 'news',
      name: '공지',
      component: () => import('@/views/_Work/Manages/News/Index.vue'),
    },
    {
      path: 'search',
      name: '전체검색',
      component: () => import('@/views/_Work/components/SearchBody/Index.vue'),
    },
  ],
}

export default workProject
