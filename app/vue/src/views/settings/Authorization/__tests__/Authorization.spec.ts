import { describe, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import Authorization from '../Index.vue'

const vuetify = createVuetify()

describe('Authorization Component Test', () => {
  it('should ', () => {
    const wrapper = mount(Authorization, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
        mocks: {},
        provide: {},
        components: {},
        directives: {},
        stubs: ['CIcon'],
      },
      attrs: {},
      props: {},
      slots: {},
      shallow: true,
    })

    console.log(wrapper.html(), '---')
  })
})
