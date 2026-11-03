import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { createVuetify } from 'vuetify'
import { createTestingPinia } from '@pinia/testing'

const mockRouter = {
  push: vi.fn(),
}

// Mock Vue Router composables
vi.mock('vue-router', async importOriginal => {
  const actual = (await importOriginal()) as Record<string, any>
  return {
    ...actual,
    useRoute: () => ({
      name: 'some-title',
      meta: { title: 'some-title' },
      query: {},
    }),
    useRouter: () => mockRouter,
  }
})

import CoreuiVue from '@coreui/vue'
import ContentHeader from '../ContentHeader/Index.vue'
import HeaderNav from '../ContentHeader/components/HeaderNav.vue'
import CompanySelect from '../ContentHeader/components/CompanySelect.vue'
import ProjectSelect from '../ContentHeader/components/ProjectSelect.vue'

const vuetify = createVuetify()

const mockRoute = {
  name: 'some-title',
  meta: {
    title: 'some-title',
  },
  query: {},
}

describe('ContentHeader Test', () => {
  it('Header Nav test', async () => {
    mockRouter.push.mockClear()
    const wrapper = mount(HeaderNav, {
      props: {
        menus: ['1st Menu', '2nd Menu'],
        query: { project: '1', page: '2', highlight_id: '788', contractor: '10' },
      },
      global: {
        plugins: [CoreuiVue],
      },
    })

    expect(wrapper.html()).toContain('1st Menu')
    expect(wrapper.html()).toContain('2nd Menu')

    // Click 2nd Menu nav link
    const links = wrapper.findAll('.nav-link')
    await links[1].trigger('click')

    // Transient queries (page, highlight_id, contractor) must be filtered out,
    // only persistent context query (project) should be preserved
    expect(mockRouter.push).toHaveBeenCalledWith({
      name: '2nd Menu',
      query: { project: '1' },
    })
  })

  it('company select test', () => {
    const wrapper = mount(CompanySelect, {
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: ['Multiselect'],
      },
    })
    wrapper.find('multiselect-stub').trigger('select')

    expect(wrapper.emitted()).toHaveProperty('com-select')
  })

  it('project select test', () => {
    const wrapper = mount(ProjectSelect, {
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: ['Multiselect'],
      },
    })

    wrapper.find('multiselect-stub').trigger('select')

    expect(wrapper.emitted()).toHaveProperty('proj-select')
  })
})
