import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import AppHeader from '@/layouts/containers/AppHeader.vue'

const vuetify = createVuetify()

describe('AppHeader Component Test', () => {
  it('Header components check', async () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
        stubs: ['CIcon', 'c-header-brand', 'app-header-dropdown-accnt', 'router-link', 'tags-view'],
      },
    })

    const buttons = wrapper.findAll('button')

    expect(buttons[0].find('.mdi-format-indent-decrease').exists()).toBeTruthy()
    expect(wrapper.find('nav[aria-label=breadcrumb]').exists()).toBeTruthy()
    expect(wrapper.find('nav>ol').classes()).toContain('breadcrumb')
    expect(buttons[1].find('.mdi-fullscreen').exists()).toBeTruthy()
    expect(wrapper.find('button.dropdown-toggle').exists() || wrapper.find('.dropdown').exists()).toBeTruthy()
    expect(wrapper.find('app-header-dropdown-accnt-stub').exists()).toBeFalsy()
    expect(wrapper.find('router-link-stub').exists()).toBeTruthy()
    expect(buttons[2].find('.mdi-apps').exists()).toBeTruthy()
    expect(wrapper.find('tags-view-stub').exists()).toBeTruthy()
  })
})
