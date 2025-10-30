import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'

import TableTitleRow from '../TableTitleRow.vue'

const vuetify = createVuetify()

describe('TableTitleRow Component Test', () => {
  it('TableTitleRow comp test', async () => {
    const wrapper = mount(TableTitleRow, {
      global: {
        plugins: [vuetify],
      },
      props: {
        title: '',
        excel: true,
        pdf: false,
        url: 'abc.com/1',
        disabled: false,
      },
    })

    expect(wrapper.find('.v-row').exists()).toBeTruthy()
    expect(wrapper.find('.v-col').exists()).toBeTruthy()
    expect(wrapper.find('h6').exists()).toBeTruthy()
    expect(wrapper.findComponent({ name: 'ExcelExport' }).props('url')).toBe('abc.com/1')
    expect(wrapper.find('.v-btn').classes()).not.toContain('v-btn--disabled')
    expect(wrapper.find('.v-btn').text()).toContain('Excel Export')

    await wrapper.setProps({ title: '1st title', excel: false, pdf: true, disabled: true })

    expect(wrapper.find('h6').text()).toBe('1st title')
    expect(wrapper.find('.v-btn').classes()).toContain('v-btn--disabled')
    expect(wrapper.find('.v-btn').text()).toContain('Pdf Export')
  })
})
