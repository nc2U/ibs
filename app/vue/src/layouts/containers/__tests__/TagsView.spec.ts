import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'

import TagsView from '@/layouts/containers/TagsView.vue'

const vuetify = createVuetify()

vi.stubGlobal(
  'ResizeObserver',
  class {
    observe = vi.fn()
    unobserve = vi.fn()
    disconnect = vi.fn()
  },
)

vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({
    path: '/dashboard',
    meta: {
      title: '대 시 보 드',
    },
  })),
  useRouter: vi.fn(() => ({
    push: () => {},
    getRoutes: vi.fn(() => []),
  })),
}))

describe('TagsView Component Test', () => {
  it('TagsView test', () => {
    const wrapper = mount(TagsView, {
      global: {
        plugins: [createTestingPinia(), vuetify],
      },
    })

    expect(wrapper.find('.v-sheet').exists()).toBeTruthy()
    expect(wrapper.find('.v-slide-group').exists()).toBeTruthy()
    expect(wrapper.find('.v-slide-group__container').exists()).toBeTruthy()
    expect(wrapper.find('.v-slide-group__content').exists()).toBeTruthy()
  })
})
