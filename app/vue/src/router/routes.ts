import { useStore } from '@/store'
import { hashCode } from '@/utils/helper'
import { type RouteRecordRaw } from 'vue-router'

/* Layout Containers */
import DefaultLayout from '@/layouts/DefaultLayout.vue'

/* Router Modules */
import workProject from '@/router/modules/workProject'
import workSetting from '@/router/modules/workSetting'
import contracts from '@/router/modules/contracts'
import payments from '@/router/modules/payments'
import notices from '@/router/modules/notices'
import proCash from '@/router/modules/proCash'
import proDocs from '@/router/modules/proDocs'
import projects from '@/router/modules/projects'
import comCash from '@/router/modules/comCash'
import comDocs from '@/router/modules/comDocs'
import hrManage from '@/router/modules/hrManage'
import settings from '@/router/modules/settings'
import myPage from '@/router/modules/mypage'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: DefaultLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: '대 시 보 드',
        // route level code-splitting
        // this generates a separate chunk (dashboard.[hash].js) for this route
        // which is lazy-loaded when the route is visited.
        component: () => import(/* webpackChunkName: "dashboard" */ '@/views/_Dashboard/Index.vue'),
        meta: { title: '대 시 보 드', auth: true, affix: true },
      },
      // {
      //   path: 'dashboard/notices',
      //   name: '공지 게시판',
      //   component: () => import('@/views/_Dashboard/components/NoticeApp/Index.vue'),
      //   meta: { title: '대 시 보 드', auth: true, affix: true },
      //   children: [
      //     {
      //       path: ':postId(\\d+)',
      //       name: '공지 게시판 - 보기',
      //       component: () => import('@/views/_Dashboard/components/NoticeApp/Index.vue'),
      //     },
      //     {
      //       path: 'create',
      //       name: '공지 게시판 - 작성',
      //       component: () => import('@/views/_Dashboard/components/NoticeApp/Index.vue'),
      //     },
      //     {
      //       path: ':postId(\\d+)/update',
      //       name: '공지 게시판 - 수정',
      //       component: () => import('@/views/_Dashboard/components/NoticeApp/Index.vue'),
      //     },
      //   ],
      // },
      workProject as RouteRecordRaw,
      workSetting as RouteRecordRaw,
      contracts,
      payments,
      notices,
      proCash,
      proDocs,
      projects,
      comCash,
      comDocs,
      hrManage,
      settings,
      myPage,
      {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/components/NotFound.vue'),
        meta: { title: 'Not-Found', except: true },
      },
    ],
  },
  {
    path: '/accounts/login',
    name: 'Login',
    component: () => import('@/views/_Accounts/Login.vue'),
    meta: { title: '로그인', except: true },
  },
  {
    path: '/accounts/register',
    name: 'Register',
    component: () => import('@/views/_Accounts/Register.vue'),
    meta: { title: '회원가입', except: true },
    beforeEnter: (to, from, next) => {
      const store = useStore()
      if (from.name === 'RegisterCode' && to.query.id == hashCode(store.registerCode).toString()) {
        next()
      } else {
        next({
          name: 'RegisterCode',
        })
      }
    },
  },
  {
    path: '/accounts/register-code',
    name: 'RegisterCode',
    component: () => import('@/views/_Accounts/RegisterCode.vue'),
    meta: { title: '코드입력', except: true },
  },
  {
    path: '/accounts/pass-reset',
    name: 'pass-reset',
    component: () => import('@/views/_Accounts/PasswordReset.vue'),
    meta: { title: '비밀번호 재설정', except: true },
  },
]

export default routes
