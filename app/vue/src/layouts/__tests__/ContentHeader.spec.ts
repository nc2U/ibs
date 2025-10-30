import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { createVuetify } from 'vuetify'
import { createTestingPinia } from '@pinia/testing'

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
    useRouter: () => ({
      push: vi.fn(),
    }),
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

const mockRouter = {
  push: vi.fn(),
}

describe('ContentHeader Test', () => {
  it('header main select test', async () => {
    const wrapper = mount(ContentHeader, {
      props: {
        pateTitle: 'Page Title',
        navMenu: ['1st Menu', '2nd Menu'],
        selector: 'CompanySelect',
      },
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
        stubs: ['Multiselect'],
      },
    })

    expect(wrapper.html()).toContain('Page Title')
    expect(wrapper.html()).toContain('1st Menu')
    expect(wrapper.html()).toContain('2nd Menu')
    expect(wrapper.html()).toContain('회사명')

    await wrapper.setProps({ selector: 'ProjectSelect' })

    expect(wrapper.html()).toContain('프로젝트')
  })

  it('Header Nav test', () => {
    const wrapper = mount(HeaderNav, {
      props: {
        menus: ['1st Menu', '2nd Menu'],
      },
      global: {
        plugins: [CoreuiVue],
      },
    })

    expect(wrapper.html()).toContain('1st Menu')
    expect(wrapper.html()).toContain('2nd Menu')
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
