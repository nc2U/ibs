import { beforeEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'

import CoreuiVue from '@coreui/vue'
import ContentBody from '../ContentBody/Index.vue'

const vuetify = createVuetify()

const mockRoute = {
  name: 'some-title',
  meta: {
    title: null as string | null,
  },
}

describe('Content Body Testing', () => {
  let wrapper: VueWrapper
  beforeEach(() => {
    wrapper = mount(ContentBody, {
      global: {
        plugins: [vuetify, CoreuiVue],
        mocks: {
          route: mockRoute,
        },
      },
      slots: {
        default: `Hello default slot`,
      },
    })
  })

  it('header title check', () => {
    expect(wrapper.html()).toContain('some-title')
  })

  it('default slot Test', () => {
    expect(wrapper.html()).toContain('Hello default slot')
  })
})
