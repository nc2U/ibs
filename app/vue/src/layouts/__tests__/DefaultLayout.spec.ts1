import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'

import DefaultLayout from '@/layouts/DefaultLayout.vue'

describe('DefaultLayout', () => {
  it('DefaultLayout check', () => {
    const wrapper = shallowMount(DefaultLayout, {
      global: {
        plugins: [createTestingPinia()],
        stubs: ['router-view'],
      },
    })

    const div1 = wrapper.findAll('div')[0]
    const div2 = wrapper.findAll('div')[1]

    expect(wrapper.html()).toContain('app-sidebar-stub')
    expect(div1.attributes('class')).toContain('wrapper d-flex')
    expect(div1.html()).toContain('app-header-stub')
    expect(div2.attributes('class')).toContain('body d-flex flex-column flex-grow-1')
    expect(div2.html()).toContain('c-container-stub')
    expect(wrapper.html()).toContain('app-footer-stub')
    expect(wrapper.html()).toContain('back-to-top-stub')
  })
})
