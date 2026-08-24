import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import AppHeader from '@/layouts/containers/AppHeader.vue'

const vuetify = createVuetify()

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: { template: '<div>Home</div>' },
    },
    {
      path: '/login',
      name: 'Login',
      component: { template: '<div>Login</div>' },
    },
  ],
})

describe('AppHeader Component Test', () => {
  it('Header components check', async () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue, router],
        stubs: ['CIcon', 'c-header-brand', 'app-header-dropdown-accnt', 'tags-view'],
      },
    })

    const buttons = wrapper.findAll('button')

    expect(buttons[0].find('.mdi-format-indent-decrease').exists()).toBeTruthy()
    expect(wrapper.find('nav[aria-label=breadcrumb]').exists()).toBeTruthy()
    expect(wrapper.find('nav>ol').classes()).toContain('breadcrumb')
    expect(buttons[1].find('.mdi-fullscreen').exists()).toBeTruthy()
    expect(buttons[2].exists()).toBeTruthy()
    expect(wrapper.find('app-header-dropdown-accnt-stub').exists()).toBeFalsy()
    expect(wrapper.find('.mdi-apps').exists()).toBeTruthy()
    expect(wrapper.find('tags-view-stub').exists()).toBeTruthy()
  })
})
