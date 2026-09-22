import { describe, expect, it } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'

import QuillEditor from '../QuillEditor/index.vue'

describe('QuillEditor Component Test', () => {
  it('Quild editor test', async () => {
    const wrapper = mount(QuillEditor, {
      global: {
        plugins: [createTestingPinia()],
      },
    })
    await flushPromises()

    expect(wrapper.find('.ql-container').exists()).toBeTruthy()
    expect(wrapper.find('.ql-editor').exists()).toBeTruthy()
    expect(wrapper.find('.ql-tooltip').exists()).toBeTruthy()
    expect(wrapper.find('a.ql-preview').exists()).toBeTruthy()
    expect(wrapper.find('input[type=text]').exists()).toBeTruthy()
    expect(wrapper.find('a.ql-remove').exists()).toBeTruthy()
  })
})
