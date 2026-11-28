import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'

import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import type { User } from '@/store/types/accounts'
import type { IssueProject, Member, Role } from '@/store/types/work_project'
import { PERM } from '@/store/constants/permissions'

import SettingsAuthGuard from '@/components/AuthGuard/SettingsAuthGuard.vue'
import AuthorizationIndex from '../Index.vue'
import AddUserFormModal from '../components/AddUserFormModal.vue'
import SideBarManageAuth from '../components/SideBarManageAuth.vue'
import UserSelect from '../components/UserSelect.vue'

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

const FormModalStub = defineComponent({
  name: 'FormModal',
  emits: ['close'],
  data: () => ({ isOpen: false }),
  methods: {
    callModal() {
      this.isOpen = true
    },
    close() {
      this.isOpen = false
      this.$emit('close')
    },
  },
  template: '<div v-if="isOpen" class="form-modal-stub"><slot name="header" /><slot /></div>',
})

const ConfirmModalStub = defineComponent({
  name: 'ConfirmModal',
  data: () => ({ isOpen: false, header: '', body: '' }),
  methods: {
    callModal(h = '', b = '') {
      this.header = h
      this.body = b
      this.isOpen = true
    },
    close() {
      this.isOpen = false
    },
  },
  template:
    '<div v-if="isOpen" class="confirm-modal-stub"><div class="confirm-body">{{ body }}</div><slot name="footer" /></div>',
})

const AlertModalStub = defineComponent({
  name: 'AlertModal',
  data: () => ({ isOpen: false, head: '', body: '' }),
  methods: {
    callModal(h = '', b = '') {
      this.head = h
      this.body = b
      this.isOpen = true
    },
    close() {
      this.isOpen = false
    },
  },
  template: '<div v-if="isOpen" class="alert-modal-stub">{{ body }}</div>',
})

const makeUser = (overrides: Partial<User> = {}): User => ({
  pk: 1,
  email: 'user@test.com',
  username: 'user1',
  is_active: true,
  is_superuser: false,
  is_staff: false,
  is_hq_staff: true,
  work_manager: false,
  date_joined: '2026-01-01',
  profile: null,
  last_login: null,
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
  await router.push('/settings/authorization')
  await router.isReady()
  return router
}

describe('settings Authorization module', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
    mockedApi.get.mockResolvedValue({ data: { results: [] } } as never)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('SettingsAuthGuard allows global PROJECT_MEMBER and workManager even when currentProject lacks perms', async () => {
    const accStore = useAccount()
    const workStore = useWork()
    const router = await createTestRouter()

    // 일반 HQ 스태프가 특정 프로젝트에서 project.member 권한 보유 (currentProject는 미보유 프로젝트)
    accStore.userInfo = makeUser({ pk: 2, work_manager: false, is_hq_staff: true })
    workStore.myProjects = [
      {
        pk: 1,
        name: 'Proj A',
        slug: 'proj-a',
        type: '2',
        status: '1',
        my_perms: [PERM.PROJECT_MEMBER],
      } as unknown as IssueProject,
    ]
    workStore.currentProject = {
      pk: 99,
      name: 'Other',
      slug: 'other',
      type: '2',
      status: '2',
      my_perms: [],
    } as unknown as IssueProject

    const wGuardAllowed = mount(SettingsAuthGuard, {
      slots: { default: '<div class="allowed">OK</div>' },
      global: { plugins: [vuetify, CoreuiVue, router] },
    })
    expect(wGuardAllowed.find('.allowed').exists()).toBe(true)

    // 권한 없는 사용자는 차단
    workStore.myProjects = []
    const wGuardDenied = mount(SettingsAuthGuard, {
      slots: { default: '<div class="allowed">OK</div>' },
      global: { plugins: [vuetify, CoreuiVue, router] },
    })
    expect(wGuardDenied.find('.allowed').exists()).toBe(false)
    expect(wGuardDenied.text()).toContain('Authorization not granted!')

    // workManager는 isStaff 여부와 무관하게 허용
    accStore.userInfo = makeUser({ pk: 3, work_manager: true, is_hq_staff: false })
    const wGuardWm = mount(SettingsAuthGuard, {
      slots: { default: '<div class="allowed">OK</div>' },
      global: { plugins: [vuetify, CoreuiVue, router] },
    })
    expect(wGuardWm.find('.allowed').exists()).toBe(true)
  })

  it('Authorization loads pending users for workManager, exposes them in UserSelect, and approves via AdminManageUserView', async () => {
    const accStore = useAccount()
    const router = await createTestRouter()

    const wmUser = makeUser({
      pk: 5,
      username: 'wm_manager',
      email: 'wm@test.com',
      work_manager: true,
      is_superuser: false,
    })
    const pendingUser = makeUser({
      pk: 12,
      username: 'new_applicant',
      email: 'applicant@test.com',
      is_active: false,
      work_manager: false,
    })
    const approvedUser = { ...pendingUser, is_active: true }

    accStore.userInfo = wmUser
    mockedApi.get.mockImplementation((url: string, config?: Parameters<typeof api.get>[1]) => {
      const params = config?.params as Record<string, unknown> | undefined
      if (url === '/user/' && params?.is_active === 'all') {
        return Promise.resolve({ data: { results: [wmUser, pendingUser] } } as never)
      }
      if (url === `/user/${wmUser.pk}/`) {
        return Promise.resolve({ data: wmUser } as never)
      }
      if (url === `/user/${pendingUser.pk}/`) {
        return Promise.resolve({ data: pendingUser } as never)
      }
      return Promise.resolve({ data: { results: [] } } as never)
    })
    mockedApi.put.mockResolvedValueOnce({ data: { detail: '승인 완료' } } as never)

    const wrapper = mount(AuthorizationIndex, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          Loading: { template: '<div />' },
          CompanySelect: { template: '<div />' },
          SideBarManageAuth: { template: '<div />' },
          AddUserFormModal: FormModalStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('환경 설정')
    expect(wrapper.text()).toContain('권한 설정 관리')
    expect(mockedApi.get).toHaveBeenCalledWith('/user/', {
      params: { limit: 500, is_active: 'all' },
    })

    // 비슈퍼유저 workManager에게도 승인 대기 사용자를 포함해 모든 조회된 사용자 옵션 노출
    const userSelectComp = wrapper.findComponent(UserSelect)
    expect(userSelectComp.text()).toContain('new_applicant [승인대기]')

    // 미승인 사용자 선택 시 승인 대기 안내 및 가입 승인 버튼 노출
    userSelectComp.vm.$emit('select-user', pendingUser.pk)
    await flushPromises()

    expect(wrapper.text()).toContain('승인 대기 (비활성)')
    expect(wrapper.text()).toContain('가입 승인 (활성화)')

    // 가입 승인 클릭 -> 확인 -> PUT /admin-create-user/
    const approveBtn = wrapper
      .findAll('button')
      .find(b => b.text().includes('가입 승인 (활성화)'))
    await approveBtn!.trigger('click')
    await flushPromises()

    mockedApi.get.mockImplementation((url: string) => {
      if (url === `/user/${pendingUser.pk}/`) {
        return Promise.resolve({ data: approvedUser } as never)
      }
      if (url === '/user/') {
        return Promise.resolve({ data: { results: [wmUser, approvedUser] } } as never)
      }
      return Promise.resolve({ data: { results: [] } } as never)
    })

    const confirmBtn = wrapper
      .findAll('.confirm-modal-stub button')
      .find(b => b.text().includes('확인'))
    await confirmBtn!.trigger('click')
    await flushPromises()

    expect(mockedApi.put).toHaveBeenCalledWith('/admin-create-user/', {
      email: 'applicant@test.com',
      is_active: true,
    })
    expect(wrapper.text()).toContain('활성 계정')
  })

  it('SideBarManageAuth scopes dev projects to company, checks per-project permissions and allowed_roles, and passes userPk to deleteMember', async () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()

    accStore.userInfo = makeUser({ pk: 7, username: 'proj_admin', is_superuser: false, work_manager: false })
    comStore.company = { pk: 1, name: '(주)일번회사' } as never

    const projAllowed = {
      pk: 101,
      company: '(주)일번회사',
      type: '2',
      status: '1',
      name: '1번회사 분양현장A',
      slug: 'site-a',
      is_public: false,
      allowed_roles: [{ pk: 10, name: '분양관리자' }],
      my_perms: [PERM.PROJECT_MEMBER],
    } as unknown as IssueProject

    const projNoPerm = {
      pk: 102,
      company: '(주)일번회사',
      type: '2',
      status: '1',
      name: '권한없는 현장B',
      slug: 'site-b',
      is_public: true,
      allowed_roles: [],
      my_perms: [],
    } as unknown as IssueProject

    const projOtherCompany = {
      pk: 103,
      company: '(주)타회사',
      type: '2',
      status: '1',
      name: '타회사 프로젝트',
      slug: 'other-site',
      is_public: true,
      allowed_roles: [],
      my_perms: [PERM.PROJECT_MEMBER],
    } as unknown as IssueProject

    workStore.myProjects = [projAllowed]
    workStore.allReadableProjects = [projAllowed, projNoPerm, projOtherCompany]
    workStore.roleList = [
      { pk: 10, name: '분양관리자', category: 'ibs_pr_manage', is_confidential: false } as Role,
      { pk: 11, name: '정산담당자', category: 'ibs_pr_manage', is_confidential: false } as Role,
      { pk: 12, name: '보안역할', category: 'ibs_pr_manage', is_confidential: true } as Role,
    ]

    const existingMember: Member = {
      pk: 500,
      user: { pk: 7, username: 'proj_admin' },
      project: {
        pk: 101,
        type: '2',
        name: '1번회사 분양현장A',
        slug: 'site-a',
        visible: true,
        status: '1',
      },
      roles: [{ pk: 10, name: '분양관리자' }],
      created: '2026-01-01',
    }

    mockedApi.get.mockImplementation((url: string, config?: Parameters<typeof api.get>[1]) => {
      const params = config?.params as Record<string, unknown> | undefined
      if (url === '/member/' && params?.user === 7) {
        return Promise.resolve({ data: { results: [existingMember] } } as never)
      }
      if (url === '/issue-project/my_projects/') {
        return Promise.resolve({ data: [projAllowed] } as never)
      }
      if (url === '/issue-project/') {
        return Promise.resolve({ data: { results: [projAllowed, projNoPerm, projOtherCompany] } } as never)
      }
      if (url === '/role/') {
        return Promise.resolve({ data: { results: workStore.roleList } } as never)
      }
      return Promise.resolve({ data: { results: [] } } as never)
    })
    mockedApi.delete.mockResolvedValueOnce({} as never)

    const wrapper = mount(SideBarManageAuth, {
      props: { user: accStore.userInfo },
      global: { plugins: [vuetify, CoreuiVue] },
    })
    await flushPromises()

    // 선택 회사('(주)일번회사') 개발 프로젝트만 노출
    expect(wrapper.text()).toContain('1번회사 분양현장A')
    expect(wrapper.text()).toContain('권한없는 현장B')
    expect(wrapper.text()).not.toContain('타회사 프로젝트')
    expect(wrapper.text()).toContain('할당 권한 없음')

    // 비슈퍼유저에게는 is_confidential 역할 숨김, allowed_roles 외 역할은 비활성 + (미허용) 표시
    expect(wrapper.text()).not.toContain('보안역할')
    expect(wrapper.find('#member-role-101-11').attributes('disabled')).toBeDefined()
    expect(wrapper.find('#member-role-102-10').attributes('disabled')).toBeDefined()
    expect(wrapper.find('#member-role-101-10').attributes('disabled')).toBeUndefined()

    // 본인(pk=7)의 마지막 역할 해제 -> deleteMember(500, 7) 호출 + my_projects 동기화
    await wrapper.find('#member-role-101-10').trigger('change')
    await flushPromises()

    expect(mockedApi.delete).toHaveBeenCalledWith('/member/500/')
    expect(mockedApi.get).toHaveBeenCalledWith('/member/', { params: { limit: 500, user: 7 } })
    expect(mockedApi.get).toHaveBeenCalledWith('/issue-project/my_projects/')
  })

  it('AddUserFormModal validates inputs, disables expired on send_option=2, and keeps modal open on API failure', async () => {
    const wrapper = mount(AddUserFormModal, {
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { FormModal: FormModalStub, AlertModal: AlertModalStub },
      },
    })
    ;(wrapper.vm as unknown as { callModal: () => void }).callModal()
    await flushPromises()

    // option 내부 invalid <span> 없이 '01' ~ '24' 텍스트 렌더링
    const options = wrapper.findAll('select option')
    expect(options[0].text()).toBe('01')
    expect(options[0].find('span').exists()).toBe(false)

    // send_option='2' 선택 시 expired select 비활성화
    await wrapper.find('#content-option2').setValue(true)
    expect(wrapper.find('select').attributes('disabled')).toBeDefined()

    // 비밀번호 불일치 시 AlertModal 호출 & POST 미발생
    await wrapper.find('#username').setValue('newstaff')
    await wrapper.find('#email').setValue('newstaff@test.com')
    await wrapper.find('#password').setValue('Secret1234!')
    await wrapper.find('#pass_conf').setValue('Different!')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.find('.alert-modal-stub').text()).toContain('비밀번호가 일치하지 않습니다.')
    expect(mockedApi.post).not.toHaveBeenCalled()

    // API 실패 시 모달이 닫히거나 폼이 초기화되지 않음
    await wrapper.find('#pass_conf').setValue('Secret1234!')
    mockedApi.post.mockRejectedValueOnce(new Error('duplicate email'))
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(mockedApi.post).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.form-modal-stub').exists()).toBe(true)
    expect((wrapper.find('#username').element as HTMLInputElement).value).toBe('newstaff')
    expect(wrapper.emitted('on-created')).toBeUndefined()

    // API 성공 시 pass_conf 미포함 전송 후 모달 닫힘 + on-created emit
    mockedApi.post.mockResolvedValueOnce({ data: { pk: 88 } } as never)
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(mockedApi.post).toHaveBeenLastCalledWith(
      '/admin-create-user/',
      expect.not.objectContaining({ pass_conf: expect.anything() }),
    )
    expect(wrapper.find('.form-modal-stub').exists()).toBe(false)
    expect(wrapper.emitted('on-created')).toEqual([[88]])
  })
})
