import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'

import DatePicker from '../DatePicker/DatePicker.vue'

const vuetify = createVuetify()

describe('DatePicker Component Test', () => {
  it('VueDatePicker elements test', () => {
    const wrapper = mount(DatePicker, {
      global: {
        plugins: [createTestingPinia(), vuetify],
      },
    })

    expect(wrapper.find('.dp__input_wrap').find('input').exists()).toBeTruthy()
    expect(wrapper.find('.dp__input_wrap').html()).toContain('data-maska="####-##-##"')
    expect(wrapper.find('.dp__input_icon').find('i').exists()).toBeTruthy()
    // expect(wrapper.find('transition-stub[name=dp-menu-appear-bottom]').exists()).toBeTruthy()
  })
})
