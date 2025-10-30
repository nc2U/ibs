import { describe, it, expect, vi } from 'vitest'
import { shallowMount, mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createVuetify } from 'vuetify'
import { vMaska } from 'maska/vue'
import CoreuiVue from '@coreui/vue'
import { createRouter, createWebHistory } from 'vue-router'

import Company from '../Index.vue'
import CompanyDetail from '../components/CompanyDetail.vue'
import CompanyForm from '../components/CompanyForm.vue'

const vuetify = createVuetify()

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: { template: '<div>Home</div>' },
    },
  ],
})

describe('Company app test', () => {
  it('Company header title check', async () => {
    const wrapper = mount(Company, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue, router],
        stubs: {
          CompanySettingsAuthGuard: {
            template: '<div><slot /></div>',
          },
        },
      },
    })

    await router.isReady()
    await flushPromises()

    expect(wrapper.html()).toContain('환경 설정')
    expect(wrapper.html()).toContain('회사 정보 관리')
    expect(wrapper.html()).toContain('권한 설정 관리')
  })

  const company = {
    pk: 1,
    name: '코리아 주식회사',
    ceo: '홍길동',
    tax_number: '333-11-12345',
    org_number: '567890-1234567',
    business_cond: 'abc',
    business_even: 'def',
    es_date: '2020-01-01',
    op_date: '2020-01-02',
    zipcode: '12345',
    address1: '주소1',
    address2: '주소2',
    address3: '주소3',
  }

  it('Company Detail company date check...', async () => {
    const wrapper = mount(CompanyDetail, {
      global: {
        plugins: [createTestingPinia(), vuetify, CoreuiVue],
      },
      props: {
        company,
      },
    })

    expect(wrapper.html()).toContain('코리아 주식회사')
    expect(wrapper.html()).toContain('홍길동')
    expect(wrapper.html()).toContain('주소1')
    expect(wrapper.html()).toContain('주소2')
    expect(wrapper.html()).toContain('주소3')
  })

  it('Company Form check', async () => {
    const wrapper = mount(CompanyForm, {
      global: {
        plugins: [vuetify, CoreuiVue],
        directives: {
          maska: vMaska,
        },
      },
      props: {
        company,
      },
    })

    await flushPromises()

    const inputs = wrapper.findAll('input')

    expect(inputs[0].element.value).toBe('코리아 주식회사')
    expect(inputs[1].element.value).toBe('홍길동')
    expect(inputs[2].element.value).toBe('333-11-12345')
    expect(inputs[3].element.value).toBe('567890-1234567')
    expect(inputs[4].element.value).toBe('abc')
    expect(inputs[5].element.value).toBe('def')
    expect(inputs[6].element.value).toBe('2020-01-01')
    expect(inputs[7].element.value).toBe('2020-01-02')
    expect(inputs[8].element.value).toBe('12345')
    expect(inputs[9].element.value).toBe('주소1')
    expect(inputs[10].element.value).toBe('주소2')
    expect(inputs[11].element.value).toBe('주소3')

    await inputs[0].setValue('korea inc.')
    await inputs[1].setValue('James')
    await inputs[2].setValue('123-12-12345')
    await inputs[3].setValue('123123-1231234')
    await inputs[4].setValue('trade')
    await inputs[5].setValue('trade, deal')
    await inputs[6].setValue('2020-12-12')
    await inputs[7].setValue('2020-12-13')
    await inputs[8].setValue('12345')
    await inputs[9].setValue('Incheun')
    await inputs[10].setValue('Yeonsu')
    await inputs[11].setValue('Convensia daero')

    expect(inputs[0].element.value).toBe('korea inc.')
    expect(inputs[1].element.value).toBe('James')
    expect(inputs[2].element.value).toBe('123-12-12345')
    expect(inputs[3].element.value).toBe('123123-1231234')
    expect(inputs[4].element.value).toBe('trade')
    expect(inputs[5].element.value).toBe('trade, deal')
    expect(inputs[6].element.value).toBe('2020-12-12')
    expect(inputs[7].element.value).toBe('2020-12-13')
    expect(inputs[8].element.value).toBe('12345')
    expect(inputs[9].element.value).toBe('Incheun')
    expect(inputs[10].element.value).toBe('Yeonsu')
    expect(inputs[11].element.value).toBe('Convensia daero')
  })
})
