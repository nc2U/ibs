import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createVuetify } from 'vuetify'
import { vMaska } from 'maska/vue'
import CoreuiVue from '@coreui/vue'

import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import type { Company } from '@/store/types/settings'
import type { IssueProject } from '@/store/types/work_project'
import { PERM } from '@/store/constants/permissions'

import SettingsCompanyGuard from '@/components/AuthGuard/SettingsCompanyGuard.vue'
import CompanyIndex from '../Index.vue'
import CompanyDetail from '../components/CompanyDetail.vue'
import CompanyForm from '../components/CompanyForm.vue'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/utils/helper', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/helper')>()
  return {
    ...actual,
    message: vi.fn(),
    errorHandle: vi.fn(),
  }
})

const mockedApi = vi.mocked(api)
const vuetify = createVuetify()

const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  template:
    '<input class="datepicker-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
})

const ConfirmModalStub = defineComponent({
  name: 'ConfirmModal',
  data: () => ({ isOpen: false }),
  methods: {
    callModal() {
      this.isOpen = true
    },
    close() {
      this.isOpen = false
    },
  },
  template: '<div v-if="isOpen" class="confirm-modal-stub"><slot /><slot name="footer" /></div>',
})

const AlertModalStub = defineComponent({
  name: 'AlertModal',
  data: () => ({ isOpen: false }),
  methods: {
    callModal() {
      this.isOpen = true
    },
    close() {
      this.isOpen = false
    },
  },
  template: '<div v-if="isOpen" class="alert-modal-stub"><slot /></div>',
})

const ContentHeaderStub = defineComponent({
  name: 'ContentHeader',
  props: {
    pageTitle: { type: String, default: '' },
    navMenu: { type: Array, default: () => [] },
    selectable: { type: Boolean, default: true },
  },
  template:
    '<div class="content-header-stub" :data-selectable="String(selectable)">{{ pageTitle }} {{ navMenu.join(",") }}</div>',
})

const makeCompany = (overrides: Partial<Company> = {}): Company => ({
  pk: 1,
  name: '코리아 주식회사',
  en_name: 'Korea Inc.',
  short_name: '코리아',
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
  phone: '02-111-2222',
  fax: '02-111-2223',
  email: 'info@korea.co.kr',
  is_default: true,
  ...overrides,
})

const createTestRouter = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Home', component: { template: '<div />' } },
      {
        path: '/settings/company',
        name: '회사 정보 관리',
        component: { template: '<div />' },
        meta: { title: '회사 정보 관리' },
      },
      {
        path: '/settings/authorization',
        name: '권한 설정 관리',
        component: { template: '<div />' },
        meta: { title: '권한 설정 관리' },
      },
    ],
  })
  await router.push('/settings/company')
  await router.isReady()
  return router
}

describe('settings Company module', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
    mockedApi.get.mockResolvedValue({ data: { results: [] } } as never)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('aligns SettingsCompanyGuard with canGlobal OR semantics and restricts writes to superuser', async () => {
    const accStore = useAccount()
    const workStore = useWork()

    // 본사 스태프 + PROJECT_UPDATE 전역 보유(OR), 현재 열린 워크스페이스는 닫힘 상태(currentProject)여도 진입 허용
    accStore.userInfo = {
      pk: 10,
      email: 'staff@test.com',
      username: 'staff_mgr',
      is_active: true,
      is_superuser: false,
      is_staff: false,
      is_hq_staff: true,
      work_manager: false,
      date_joined: '2026-01-01',
      profile: null,
      last_login: null,
    }
    workStore.myProjects = [
      {
        pk: 1,
        name: 'HQ',
        slug: 'hq',
        type: '1',
        status: '1',
        my_perms: [PERM.PROJECT_UPDATE],
      } as unknown as IssueProject,
    ]
    workStore.currentProject = {
      pk: 99,
      name: 'Closed Workspace',
      slug: 'closed-ws',
      type: '2',
      status: '2',
      my_perms: [],
    } as unknown as IssueProject

    const wGuardAllowed = mount(SettingsCompanyGuard, {
      slots: { default: '<div class="allowed">허용</div>' },
      global: { plugins: [vuetify, CoreuiVue] },
    })
    expect(wGuardAllowed.find('.allowed').exists()).toBe(true)

    // 비슈퍼유저 스태프는 CompanyDetail에서 수정/등록 버튼이 숨겨짐 (백엔드 IsSuperUserOrReadOnly 일치)
    const wDetailNonSuper = mount(CompanyDetail, {
      props: { company: makeCompany() },
      global: { plugins: [vuetify, CoreuiVue] },
    })
    expect(wDetailNonSuper.text()).toContain('Korea Inc.')
    expect(wDetailNonSuper.text()).toContain('메인 회사')
    expect(wDetailNonSuper.text()).not.toContain('수정하기')
    expect(wDetailNonSuper.text()).not.toContain('등록하기')

    // 프로젝트 권한 없는 일반 스태프는 NoAuth 표시
    workStore.myProjects = []
    const router = await createTestRouter()
    const wGuardDenied = mount(SettingsCompanyGuard, {
      slots: { default: '<div class="allowed">허용</div>' },
      global: { plugins: [vuetify, CoreuiVue, router] },
    })
    expect(wGuardDenied.find('.allowed').exists()).toBe(false)
    expect(wGuardDenied.text()).toContain('Authorization not granted!')
  })

  it('renders Company header menu and extended detail fields', async () => {
    const router = await createTestRouter()
    const accStore = useAccount()
    const comStore = useCompany()
    accStore.userInfo = {
      pk: 1,
      email: 'admin@test.com',
      username: 'admin',
      is_active: true,
      is_superuser: true,
      is_staff: true,
      work_manager: true,
      date_joined: '2026-01-01',
      profile: null,
      last_login: null,
    }
    comStore.company = makeCompany()

    const wrapper = mount(CompanyIndex, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CompanySelect: { template: '<div />' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('환경 설정')
    expect(wrapper.text()).toContain('회사 정보 관리')
    expect(wrapper.text()).toContain('권한 설정 관리')
    expect(wrapper.text()).toContain('Korea Inc.')
    expect(wrapper.text()).toContain('02-111-2222')
    expect(wrapper.text()).toContain('info@korea.co.kr')
    expect(wrapper.text()).toContain('수정하기')
    expect(wrapper.text()).toContain('등록하기')
  })

  it('CompanyForm preserves extended fields, normalizes null dates, and keeps form open when update fails', async () => {
    const router = await createTestRouter()
    const accStore = useAccount()
    const comStore = useCompany()
    accStore.userInfo = {
      pk: 1,
      email: 'admin@test.com',
      username: 'admin',
      is_active: true,
      is_superuser: true,
      is_staff: true,
      work_manager: true,
      date_joined: '2026-01-01',
      profile: null,
      last_login: null,
    }
    const baseCompany = makeCompany({ es_date: null, op_date: '2020-01-02' })
    comStore.company = baseCompany

    const wrapper = mount(CompanyIndex, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        directives: { maska: vMaska },
        stubs: {
          ContentHeader: ContentHeaderStub,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
          AlertModal: AlertModalStub,
          DaumPostcode: { template: '<div />' },
        },
      },
    })
    await flushPromises()

    // 수정 모드 진입 시 CompanySelect selectable=false
    const editBtn = wrapper.findAll('button').find(b => b.text().includes('수정하기'))
    await editBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.content-header-stub').attributes('data-selectable')).toBe('false')
    const formComp = wrapper.findComponent(CompanyForm)
    expect(formComp.exists()).toBe(true)

    // Label for <-> input id 정합성
    expect(wrapper.find('label[for="name"]').exists()).toBe(true)
    expect(wrapper.find('#name').exists()).toBe(true)
    expect(wrapper.find('label[for="tax_number"]').exists()).toBe(true)
    expect(wrapper.find('#tax_number').exists()).toBe(true)

    // 미수정 상태에서는 저장 비활성화 (es_date가 null이어도 ''와 동등 취급)
    const saveBtn = wrapper.find('button[type="submit"]')
    expect(saveBtn.attributes('disabled')).toBeDefined()

    // 값 변경 후 저장 활성화
    await wrapper.find('#name').setValue('코리아홀딩스(주)')
    await wrapper.find('#en_name').setValue('Korea Holdings Co.')
    expect(saveBtn.attributes('disabled')).toBeUndefined()

    // 1) PATCH 실패 시 상세로 돌아가지 않고 수정 폼 유지
    mockedApi.patch.mockRejectedValueOnce(new Error('server error'))
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    const confirmSave = wrapper
      .findAll('.confirm-modal-stub button')
      .find(b => b.text().includes('저장'))
    await confirmSave!.trigger('click')
    await flushPromises()

    expect(mockedApi.patch).toHaveBeenCalledWith(
      '/company/1/',
      expect.objectContaining({
        name: '코리아홀딩스(주)',
        en_name: 'Korea Holdings Co.',
        es_date: null,
        op_date: '2020-01-02',
      }),
    )
    expect(wrapper.findComponent(CompanyForm).exists()).toBe(true)

    // 2) PATCH 성공 시 목록과 단건 재조회 후 상세 화면으로 복귀
    const updatedCompany = makeCompany({ name: '코리아홀딩스(주)', en_name: 'Korea Holdings Co.' })
    mockedApi.patch.mockResolvedValueOnce({ data: updatedCompany } as never)
    mockedApi.get.mockImplementation((url: string) => {
      if (url === '/company/') return Promise.resolve({ data: { results: [updatedCompany] } } as never)
      if (url === '/company/1/') return Promise.resolve({ data: updatedCompany } as never)
      return Promise.resolve({ data: { results: [] } } as never)
    })

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    const confirmSave2 = wrapper
      .findAll('.confirm-modal-stub button')
      .find(b => b.text().includes('저장'))
    await confirmSave2!.trigger('click')
    await flushPromises()

    expect(wrapper.findComponent(CompanyForm).exists()).toBe(false)
    expect(wrapper.findComponent(CompanyDetail).exists()).toBe(true)
    expect(wrapper.text()).toContain('코리아홀딩스(주)')
    expect(comStore.companyList).toHaveLength(1)
  })

  it('deleteCompany clears current company and localStorage when last company is deleted', async () => {
    const comStore = useCompany()
    comStore.company = makeCompany({ pk: 1 })
    localStorage.setItem('curr-company', '1')

    mockedApi.delete.mockResolvedValueOnce({} as never)
    mockedApi.get.mockResolvedValueOnce({ data: { results: [] } } as never)

    const ok = await comStore.deleteCompany(1)
    expect(ok).toBe(true)
    expect(comStore.company).toBeNull()
    expect(localStorage.getItem('curr-company')).toBeNull()
  })
})
