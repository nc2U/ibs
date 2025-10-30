import { useStore } from '@/store'
import { hashCode } from '@/utils/helper'
import { type RouteRecordRaw } from 'vue-router'

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
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: '대 시 보 드',
        component: () =>
          import(
            /* webpackChunkName: "dashboard" */
            /* webpackPreload: true */
            '@/views/_Dashboard/Index.vue'
          ),
        meta: { title: '대 시 보 드', auth: true, affix: true },
      },
      workProject as RouteRecordRaw,
      workSetting as RouteRecordRaw,
      contracts,
      payments,
      notices,
      proCash,
      proDocs as unknown as RouteRecordRaw,
      projects,
      comCash,
      comDocs as unknown as RouteRecordRaw,
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
