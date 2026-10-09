import { describe, expect, it } from 'vitest'
import { computed } from 'vue'
import { shallowMount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import { createRouter, createWebHistory } from 'vue-router'

import AppAside from '@/layouts/containers/AppAside.vue'

const vuetify = createVuetify()
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div></div>' } }],
})

describe('AppAside Component Test', () => {
  it('sidebar exsists check', () => {
    const wrapper = shallowMount(AppAside, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue, router],
        stubs: ['CIcon'],
        provide: {
          company: computed(() => ({ name: 'Test Company' })),
        },
      },
      props: {
        position: 'fixed',
      },
    })

    expect(wrapper.html()).toContain('c-sidebar-stub')
  })
})
