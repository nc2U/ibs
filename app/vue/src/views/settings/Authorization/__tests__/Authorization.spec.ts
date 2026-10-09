import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import { createRouter, createWebHistory } from 'vue-router'

import Authorization from '../Index.vue'

const vuetify = createVuetify()

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: { template: '<div>Home</div>' },
    },
  ],
})

describe('Authorization Component Test', () => {
  it('Authorization header title and menu check', async () => {
    const wrapper = mount(Authorization, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue, router],
        stubs: {
          Loading: {
            template: '<div><slot /></div>',
          },
          SettingsAuthGuard: {
            template: '<div><slot /></div>',
          },
          UserSelect: {
            template: '<div class="user-select-stub">UserSelect</div>',
          },
          SideBarManageAuth: {
            template: '<div class="sidebar-manage-auth-stub">SideBarManageAuth</div>',
          },
          AddUserFormModal: {
            template: '<div>AddUserFormModal</div>',
          },
        },
      },
    })

    await router.isReady()
    await flushPromises()

    expect(wrapper.html()).toContain('환경 설정')
    expect(wrapper.html()).toContain('회사 정보 관리')
    expect(wrapper.html()).toContain('권한 설정 관리')
  })
})
