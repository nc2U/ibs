import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { shallowMount } from '@vue/test-utils'
import api from '@/api'
import nav from '@/layouts/_nav'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import type { User } from '@/store/types/accounts'
import type { IssueProject } from '@/store/types/work_project'
import { navMenu as attendanceNavMenu } from '../_menu/headermixin3'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/utils/helper', () => ({
  errorHandle: vi.fn(),
  getErrorData: vi.fn(),
  message: vi.fn(),
  isValidate: vi.fn(() => false),
}))

const mockApi = api as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const makeUser = (overrides: Partial<User> = {}): User => ({
  pk: 1,
  email: 'staff@example.com',
  username: 'staff',
  is_active: true,
  is_superuser: false,
  is_staff: false,
  work_manager: false,
  date_joined: '2026-01-01',
  profile: null,
  last_login: null,
  is_hq_staff: true,
  has_staff: true,
  ...overrides,
})

const makeIssueProject = (perms: string[]): IssueProject => ({
  pk: 10,
  company: 1,
  project: null,
  type: '1',
  name: '본사',
  slug: 'hq',
  description: '',
  is_public: false,
  parent: null,
  parent_name: null,
  allowed_roles: [],
  status: '1',
  status_display: '사용중',
  chat_channel_enabled: false,
  slack_notifications_enabled: false,
  sub_projects: [],
  depth: 0,
  my_perms: perms,
  all_members: [],
  parent_visible: false,
  homepage: null,
  is_inherit_members: false,
  default_version: null,
  trackers: [],
  ancestors: [],
  members: [],
  versions: [],
  categories: [],
  forums: [],
})

describe('hrManage regression fixes', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockApi.get.mockResolvedValue({ data: { results: [], count: 0 } })
  })

  it('fetches paginated staff with limit=10, omits status when sts="" and encodes search', async () => {
    const comStore = useCompany()

    await comStore.fetchStaffList({ com: 2, page: 3, sts: '', q: '홍길동&테스트' })
    expect(mockApi.get).toHaveBeenCalledWith(
      '/staff/?limit=10&page=3&company=2&search=%ED%99%8D%EA%B8%B8%EB%8F%99%26%ED%85%8C%EC%8A%A4%ED%8A%B8',
    )

    await comStore.fetchAllStaffList(2, '')
    expect(mockApi.get).toHaveBeenLastCalledWith('/staff/?company=2&limit=500')

    await comStore.fetchAllStaffList(2)
    expect(mockApi.get).toHaveBeenLastCalledWith('/staff/?company=2&limit=500&status=1')
  })

  it('returns boolean from HR mutations and preserves active filters on refresh', async () => {
    const comStore = useCompany()

    mockApi.post.mockResolvedValueOnce({ data: { pk: 11 } })
    const created = await comStore.createDepartment(
      {
        upper_depart: null,
        level: 1,
        name: '개발팀',
        manager: null,
        task: '',
      },
      2,
      2,
      { com: 2, upp: '5', q: '개발' },
    )
    expect(created).toBe(true)
    expect(mockApi.get).toHaveBeenCalledWith(
      '/department/?limit=10&page=2&company=2&upper_depart=5&search=%EA%B0%9C%EB%B0%9C',
    )

    mockApi.put.mockRejectedValueOnce(new Error('400'))
    const updatedFail = await comStore.updateStaff(
      {
        pk: 7,
        sort: '2',
        name: '테스트',
        id_number: '******-*******',
        personal_phone: '010-0000-0000',
        direct_phone: '',
        direct_fax: '',
        email: '',
        department: '',
        grade: '',
        position: '',
        duty: '',
        date_join: '2026-01-01',
        date_leave: null,
        status: '1',
        user: null,
      },
      1,
      2,
    )
    expect(updatedFail).toBe(false)

    mockApi.put.mockResolvedValueOnce({ data: { pk: 7 } })
    const updatedOk = await comStore.updateStaff(
      {
        pk: 7,
        sort: '2',
        name: '테스트',
        id_number: '******-*******',
        personal_phone: '010-0000-0000',
        direct_phone: '',
        direct_fax: '',
        email: '',
        department: '',
        grade: '',
        position: '',
        duty: '',
        date_join: '2026-01-01',
        date_leave: null,
        status: '1',
        user: null,
      },
      2,
      2,
      { com: 2, sts: '' },
    )
    expect(updatedOk).toBe(true)
    expect(mockApi.get).toHaveBeenCalledWith('/staff/?limit=10&page=2&company=2')
  })

  it('refreshes all staff statuses after personnel order mutation', async () => {
    const comStore = useCompany()
    mockApi.post.mockResolvedValueOnce({ data: { pk: 99 } })

    const ok = await comStore.createPersonnelOrder(
      {
        staff: 3,
        order_type: '50',
        order_date: '2026-03-01',
        effective_end_date: null,
        order_no: '',
        prev_department: null,
        prev_grade: null,
        prev_position: null,
        prev_duty: null,
        new_department: null,
        new_grade: null,
        new_position: null,
        new_duty: null,
        description: '',
        is_processed: true,
      },
      1,
      4,
      { com: 4, order_type: '50' },
    )

    expect(ok).toBe(true)
    expect(mockApi.get).toHaveBeenCalledWith('/staff/?company=4&limit=500')
    expect(mockApi.get).toHaveBeenCalledWith('/personnel-order/?limit=10&page=1&company=4&order_type=50')
  })

  it('enforces requireHrRead strictly on ComHrAuthGuard while keeping default isStaff access', () => {
    const account = useAccount()
    const work = useWork()

    account.userInfo = makeUser({ is_hq_staff: true })
    work.myProjects = [makeIssueProject([])]

    const relaxedWrapper = shallowMount(ComHrAuthGuard, {
      slots: { default: '<div class="allowed">ok</div>' },
      global: { stubs: { NoAuth: { template: '<div class="no-auth" />' } } },
    })
    expect(relaxedWrapper.find('.allowed').exists()).toBe(true)

    const strictDenied = shallowMount(ComHrAuthGuard, {
      props: { requireHrRead: true },
      slots: { default: '<div class="allowed">ok</div>' },
      global: { stubs: { NoAuth: { template: '<div class="no-auth" />' } } },
    })
    expect(strictDenied.find('.no-auth').exists()).toBe(true)

    work.myProjects = [makeIssueProject(['hq.hr_work.read'])]
    const strictAllowed = shallowMount(ComHrAuthGuard, {
      props: { requireHrRead: true },
      slots: { default: '<div class="allowed">ok</div>' },
      global: { stubs: { NoAuth: { template: '<div class="no-auth" />' } } },
    })
    expect(strictAllowed.find('.allowed').exists()).toBe(true)
  })

  it('keeps attendance nav auth aligned between sidebar and headermixin3', () => {
    const hrGroup = nav.find(
      (item): item is { component: string; name: string; items: Array<{ name: string; auth?: string }> } =>
        typeof item === 'object' && item !== null && 'name' in item && item.name === '인사 조직 관리',
    )
    const attendanceGroup = hrGroup?.items.find(item => item.name === '근태 휴가 관리')
    expect(attendanceGroup?.auth).toBe('isHrManager')
    expect(attendanceNavMenu).toEqual(['연차 부여 관리', '휴가 사용 내역', '근태 현황 관리'])
  })
})
