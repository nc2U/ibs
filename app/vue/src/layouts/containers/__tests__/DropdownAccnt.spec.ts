import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import AppHeaderDropdown from '@/layouts/containers/AppHeaderDropdown.vue'

const vuetify = createVuetify()

describe('AppHeaderDropdownAccnt Component Test', () => {
  it('should ', async () => {
    vi.mock('vue-router', async () => {
      const actual = await vi.importActual('vue-router')
      return {
        ...(actual as object),
        useRouter: vi.fn(() => ({
          push: () => {},
        })),
      }
    })

    const wrapper = mount(AppHeaderDropdown, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
        mocks: {},
        provide: {},
        components: {},
        directives: {},
        stubs: ['CIcon'],
      },
      attrs: {},
      props: {
        userInfo: {
          pk: 1,
          email: 'admin@mail.com',
          username: 'admin',
          is_active: false,
          is_superuser: false,
          is_staff: false,
          work_manager: false,
          date_joined: '2022-01-30T19:16:53+09:00',
          staffauth: null,
          profile: null,
          assigned_projects: [],
          last_login: '2023-01-30T19:16:53+09:00',
        },
        profile: null,
      },
      slots: {},
    })

    expect(wrapper.find('.dropdown-header').text()).toBe('admin님')

    await wrapper.setProps({
      profile: {
        pk: 1,
        user: 1,
        name: '운영자',
        birth_date: '',
        cell_phone: '',
        image: null,
      },
    })

    expect(wrapper.find('.dropdown-header').text()).toBe('운영자님')
    expect(wrapper.find('.dropdown-menu').html()).toContain('할일 관리')
    expect(wrapper.find('.dropdown-menu').html()).toContain('마이페이지')
    expect(wrapper.find('.dropdown-menu').html()).not.toContain('관리자 페이지')
    expect(wrapper.find('.dropdown-menu').html()).not.toContain('사용자 매뉴얼')

    await wrapper.setProps({
      userInfo: {
        pk: 1,
        email: 'admin@mail.com',
        username: 'admin',
        is_active: true,
        is_superuser: true,
        is_staff: false,
        work_manager: false,
        date_joined: '2022-01-30T19:16:53+09:00',
        staffauth: null,
        profile: null,
        assigned_projects: [],
        last_login: '2023-01-30T19:16:53+09:00',
      },
    })

    expect(wrapper.find('.dropdown-menu').html()).toContain('사용자 매뉴얼')
    expect(wrapper.find('.dropdown-menu').html()).toContain('관리자 페이지')
    expect(wrapper.find('.dropdown-menu').html()).toContain('로그아웃')
  })
})
