import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount, shallowMount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { useDocs } from '@/store/pinia/docs'
import { PERM } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { Company } from '@/store/types/settings'
import type { IssueProject } from '@/store/types/work_project'
import type { InboundLetter, OfficialLetter, OfficialLetterSealDetail } from '@/store/types/docs'
import {
  composeAddress,
  getDDayBadgeColor,
  getDDayText,
  getFileExt,
  getFileNameFromUrl,
  getScanFileIcon,
  parseRepresentatives,
  resolveApproverDutyTitle,
  resolveFinalApproverName,
  resolveSenderContact,
  splitStoredAddress,
  stripDrafterTitles,
  useLetterPerms,
} from '../utils/letterMeta'
import OutboundLetterForm from '../Outbound/components/LetterForm.vue'
import OutboundLetterView from '../Outbound/components/LetterView.vue'
import InboundLetterForm from '../Inbound/components/LetterForm.vue'
import InboundLetterView from '../Inbound/components/LetterView.vue'

const mockRouterPush = vi.fn()
const mockRouteQuery: Record<string, string> = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockRouterPush, replace: vi.fn() }),
  useRoute: () => ({ query: mockRouteQuery, params: {}, name: '발송 공문 관리 - 작성' }),
  RouterLink: { template: '<a><slot /></a>' },
}))

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockDownloadFile = vi.fn()
vi.mock('@/utils/helper', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/helper')>()
  return {
    ...actual,
    errorHandle: vi.fn(),
    message: vi.fn(),
    downloadFile: (...args: unknown[]) => mockDownloadFile(...args),
  }
})

vi.mock('@/utils/baseMixins', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/baseMixins')>()
  return {
    ...actual,
    getToday: () => '2026-11-27',
  }
})

const mockApi = api as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
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
  staff_name: '홍길동',
  staff_phone: '010-1234-5678',
  staff_fax: '02-1111-2222',
  ...overrides,
})

const makeCompany = (overrides: Partial<Company> = {}): Company => ({
  pk: 1,
  name: '주식회사 테스트건설',
  ceo: '김대표',
  tax_number: '123-45-67890',
  org_number: '110111-1234567',
  business_cond: '건설업',
  business_even: '주택건설',
  es_date: '2020-01-01',
  op_date: '2020-01-01',
  zipcode: '06000',
  address1: '서울 강남구 테헤란로 100',
  address2: '5층',
  address3: '(역삼동)',
  phone: '02-0000-1111',
  fax: '02-0000-2222',
  email: 'corp@example.com',
  com_issue_project: 10,
  ...overrides,
})

const makeIssueProject = (
  pk: number,
  company: number,
  perms: string[],
  status: '1' | '2' = '1',
): IssueProject => ({
  pk,
  company,
  project: null,
  type: company ? '1' : '2',
  name: `워크스페이스-${pk}`,
  slug: `ws-${pk}`,
  description: '',
  is_public: false,
  parent: null,
  parent_name: null,
  allowed_roles: [],
  status,
  status_display: status === '1' ? '사용중' : '닫힘',
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

const commonStubs = {
  MdEditor: { template: '<textarea />', props: ['modelValue'] },
  DatePicker: { template: '<input />', props: ['modelValue'] },
  DaumPostcode: { template: '<div />', methods: { initiate: vi.fn() } },
  ConfirmModal: { template: '<div />', methods: { callModal: vi.fn(), close: vi.fn() } },
  AlertModal: { template: '<div />', methods: { callModal: vi.fn(), close: vi.fn() } },
  LetterA4Preview: { template: '<div />' },
  CRow: { template: '<div><slot /></div>' },
  CCol: { template: '<div><slot /></div>' },
  CCard: { template: '<div><slot /></div>' },
  CCardHeader: { template: '<div><slot /></div>' },
  CCardBody: { template: '<div><slot /></div>' },
  CAlert: { template: '<div><slot /></div>' },
  CForm: {
    template: '<form @submit="$emit(\'submit\', $event)"><slot /></form>',
    emits: ['submit'],
  },
  CFormLabel: { template: '<label><slot /></label>' },
  CFormInput: { template: '<input />', props: ['modelValue', 'size'] },
  CFormTextarea: { template: '<textarea />', props: ['modelValue', 'rows'] },
  CFormSelect: { template: '<select><slot /></select>', props: ['modelValue', 'size'] },
  CFormCheck: { template: '<input type="checkbox" />', props: ['modelValue'] },
  CFormText: { template: '<div><slot /></div>' },
  CInputGroup: { template: '<div><slot /></div>', props: ['size'] },
  CButton: {
    template: '<button type="button" @click="$emit(\'click\', $event)"><slot /></button>',
    props: ['color', 'variant', 'size', 'disabled'],
    emits: ['click'],
  },
  CModal: { template: '<div v-if="visible"><slot /></div>', props: ['visible'] },
  CModalHeader: { template: '<div><slot /></div>' },
  CModalTitle: { template: '<div><slot /></div>' },
  CModalBody: { template: '<div><slot /></div>' },
  CModalFooter: { template: '<div><slot /></div>' },
  CSpinner: { template: '<span />' },
  CIcon: { template: '<span />' },
  'v-btn': {
    template:
      '<button :type="type || \'button\'" :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
    props: ['type', 'disabled', 'color', 'variant', 'size'],
    emits: ['click'],
  },
  'v-btn-toggle': { template: '<div><slot /></div>', props: ['modelValue', 'disabled'] },
  'v-chip': { template: '<span><slot /></span>' },
  'v-icon': { template: '<span />' },
  'router-link': { template: '<a><slot /></a>' },
}

describe('letters meta & regression suite', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    for (const k of Object.keys(mockRouteQuery)) delete mockRouteQuery[k]
    mockApi.get.mockResolvedValue({ data: { results: [], count: 0 } })
  })

  it('strips title tokens cleanly in order and parses representatives & addresses', () => {
    expect(stripDrafterTitles('홍길동 현장소장')).toBe('홍길동')
    expect(stripDrafterTitles('김철수 대표이사')).toBe('김철수')

    const reps = parseRepresentatives('홍길동; 김영희')
    expect(reps).toEqual([
      { title: '공동대표이사', name: '홍길동' },
      { title: '공동대표이사', name: '김영희' },
    ])

    const fullAddr = composeAddress('서울 강남구 테헤란로 123', '4층', '역삼동')
    expect(fullAddr).toBe('서울 강남구 테헤란로 123 4층 (역삼동)')
    expect(splitStoredAddress(fullAddr)).toEqual({
      base: '서울 강남구 테헤란로 123 4층',
      detail: '',
      ref: '(역삼동)',
    })

    expect(
      resolveApproverDutyTitle('', { internal_manager_duty: '본부장' } as OfficialLetterSealDetail),
    ).toBe('본부장')
    expect(
      resolveFinalApproverName({
        senderName: '',
        seal: null,
        dutyTitle: '현장소장',
        cleanDrafter: '홍길동',
        representativeName: '김대표',
      }),
    ).toBe('홍길동')

    const contact = resolveSenderContact({
      company: makeCompany(),
      letter: {
        sender_contact: { phone: '02-999-8888', fax: '', email: 'u@example.com' },
      } as OfficialLetter,
    })
    expect(contact).toEqual({
      phone: '02-999-8888',
      fax: '02-0000-2222',
      email: 'u@example.com',
    })

    expect(getFileExt('https://s3.example.com/a/b.PDF?X-Amz=1')).toBe('pdf')
    expect(getFileNameFromUrl('https://s3.example.com/%EA%B3%B5%EB%AC%B8.hwp?x=1')).toBe('공문.hwp')
    expect(getScanFileIcon('test.hwp')).toBe('mdi-file-document-outline')
    expect(getDDayBadgeColor(-1)).toBe('danger')
    expect(getDDayText(0, true)).toBe('오늘 마감 (D-Day)')
  })

  it('checks permissions against active company HQ project even if stale currentProject is closed', () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()
    const permStore = usePermission()

    accStore.userInfo = makeUser()
    comStore.company = makeCompany({ com_issue_project: 10 })
    const hqProj = makeIssueProject(
      10,
      1,
      [PERM.DOCS_READ, PERM.DOCS_CREATE, PERM.DOCS_UPDATE],
      '1',
    )
    const staleClosedProj = makeIssueProject(99, 2, [PERM.DOCS_READ], '2')
    workStore.myProjects = [hqProj, staleClosedProj]
    workStore.currentProject = staleClosedProj
    permStore.setProjectPermissions([PERM.DOCS_READ])

    let permsResult!: ReturnType<typeof useLetterPerms>
    const Harness = defineComponent({
      setup() {
        permsResult = useLetterPerms()
        return () => null
      },
    })
    shallowMount(Harness)

    expect(permsResult.hasPerm(PERM.DOCS_CREATE)).toBe(true)
    expect(permsResult.hasPerm(PERM.DOCS_UPDATE)).toBe(true)
    expect(permsResult.hasPerm(PERM.DOCS_DELETE)).toBe(false)
  })

  it('useDocs store encodes letter search, passes filters, awaits generatePdf, and returns null/false on failures', async () => {
    const docStore = useDocs()

    await docStore.fetchLetterList({
      company: 1,
      page: 2,
      search: '인허가&회신',
      approval_status: 'pending',
      dispatch_method: 'registered_mail',
    })
    expect(mockApi.get).toHaveBeenCalledWith(
      '/official-letter/?limit=10&page=2&company=1&approval_status=pending&dispatch_method=registered_mail&search=%EC%9D%B8%ED%97%88%EA%B0%80%26%ED%9A%8C%EC%8B%A0',
    )

    mockApi.post.mockRejectedValueOnce(new Error('400 Bad Request'))
    const failedCreate = await docStore.createLetter({} as OfficialLetter)
    expect(failedCreate).toBeNull()

    mockApi.delete.mockRejectedValueOnce(new Error('400 Bad Request'))
    const failedDel = await docStore.deleteLetter(5, { company: 1, page: 1 })
    expect(failedDel).toBe(false)

    mockApi.post.mockResolvedValueOnce({ data: { status: 'success' } })
    mockApi.get.mockResolvedValueOnce({ data: { pk: 5, pdf_file: 'https://cdn/doc.pdf' } })
    const pdfRes = await docStore.generatePdf(5)
    expect(pdfRes).toEqual({ status: 'success' })
    expect(docStore.letter?.pdf_file).toBe('https://cdn/doc.pdf')
  })

  it('prevents manual Outbound form submit from accidentally passing SubmitEvent as isDirectSubmit', async () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()
    accStore.userInfo = makeUser()
    comStore.company = makeCompany({ com_issue_project: 10 })
    workStore.myProjects = [
      makeIssueProject(10, 1, [PERM.DOCS_READ, PERM.DOCS_CREATE, PERM.DOCS_UPDATE]),
    ]

    mockApi.get.mockResolvedValue({ data: { next_document_number: 'TST-2026-001', results: [] } })
    mockRouteQuery.reply_to_inbound = '77'
    mockRouteQuery.recipient_name = '서울시청'
    mockRouteQuery.title = '[회신] 회신건'

    const wrapper = mount(OutboundLetterForm, {
      props: { company: 1, viewRoute: '발송 공문 관리' },
      global: { stubs: commonStubs },
    })

    // Fill required fields and switch to manual mode
    const vm = wrapper.vm as unknown as {
      approvalMode: 'approval' | 'manual'
      form: OfficialLetter
      onSubmit: (flag?: boolean) => void
    }
    vm.approvalMode = 'manual'
    vm.form.content = '본문 테스트'

    // Trigger native form submit event (simulating Enter key or submit)
    await wrapper.find('form').trigger('submit')

    const emitted = wrapper.emitted('onSubmit')
    expect(emitted).toBeTruthy()
    expect(emitted![0][2]).toBe(false)
    expect((emitted![0][0] as OfficialLetter).parent_inbound_letter).toBe(77)

    // Explicit approval submit button passes true
    vm.approvalMode = 'approval'
    vm.onSubmit(true)
    expect(wrapper.emitted('onSubmit')![1][2]).toBe(true)
  })

  it('hides delete button for pending OfficialLetter and uses download_pdf endpoint', async () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()
    accStore.userInfo = makeUser()
    comStore.company = makeCompany({ com_issue_project: 10 })
    workStore.myProjects = [
      makeIssueProject(10, 1, [
        PERM.DOCS_READ,
        PERM.DOCS_CREATE,
        PERM.DOCS_UPDATE,
        PERM.DOCS_DELETE,
      ]),
    ]

    const pendingLetter: OfficialLetter = {
      pk: 42,
      company: 1,
      document_number: 'TST-2026-042',
      title: '결재 진행 공문',
      recipient_name: '구로구청',
      drafter_name: '홍길동',
      content: '내용',
      issue_date: '2026-11-27',
      approval_mode: 'approval',
      approval_status: 'pending',
      pdf_file: '/media/letter.pdf',
      creator: { pk: 1, username: 'staff' },
    }

    const wrapper = mount(OutboundLetterView, {
      props: {
        letter: pendingLetter,
        viewRoute: '발송 공문 관리',
        letterFilter: { company: 1, page: 1 },
      },
      global: { stubs: commonStubs },
    })

    expect(wrapper.findAll('button').some(b => b.text().trim() === '삭제')).toBe(false)
    expect(wrapper.findAll('button').some(b => b.text().trim() === '수정')).toBe(false)

    const downloadBtn = wrapper.findAll('button').find(b => b.text().includes('PDF 다운로드'))
    expect(downloadBtn).toBeTruthy()
    await downloadBtn!.trigger('click')
    expect(mockDownloadFile).toHaveBeenCalledWith(
      '/api/v1/official-letter/42/download_pdf/',
      'TST-2026-042_결재_진행_공문.pdf',
    )
  })

  it('InboundLetterForm fetches receipt number once, blocks inverted dates, and includes clear flags in FormData', async () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()
    accStore.userInfo = makeUser()
    comStore.company = makeCompany({ com_issue_project: 10 })
    workStore.myProjects = [
      makeIssueProject(10, 1, [
        PERM.DOCS_READ,
        PERM.DOCS_CREATE,
        PERM.DOCS_UPDATE,
        PERM.DOCS_DELETE,
      ]),
    ]

    mockApi.get.mockResolvedValue({ data: { next_receipt_number: 'TST-접수-2026-001' } })

    const createWrapper = mount(InboundLetterForm, {
      props: {
        company: 1,
        viewRoute: '수신 공문 관리',
        departments: [{ value: 3, label: '기획팀' }],
        staffs: [{ value: 8, label: '김담당' }],
      },
      global: { stubs: commonStubs },
    })
    await Promise.resolve()
    const receiptCalls = mockApi.get.mock.calls.filter(c =>
      String(c[0]).includes('next_receipt_number'),
    )
    expect(receiptCalls.length).toBe(1)
    createWrapper.unmount()

    const existingInbound: InboundLetter = {
      pk: 9,
      company: 1,
      receipt_number: 'TST-접수-2026-009',
      document_number: 'GOV-100',
      sender_name: '서울시청',
      received_date: '2026-11-20',
      reply_due_date: '2026-11-30',
      title: '수정 테스트',
      scan_file: 'https://cdn/origin.pdf',
      recipient_dept: 3,
      recipient_manager: 8,
      status: 'received',
    }

    const editWrapper = mount(InboundLetterForm, {
      props: {
        company: 1,
        letter: existingInbound,
        viewRoute: '수신 공문 관리',
        departments: [{ value: 3, label: '기획팀' }],
        staffs: [{ value: 8, label: '김담당' }],
      },
      global: { stubs: commonStubs },
    })

    const vm = editWrapper.vm as unknown as {
      form: {
        reply_due_date: string
        recipient_dept: number | null
        recipient_manager: number | null
      }
      markClearExistingScan: () => void
      handleSubmit: () => void
    }

    // Inverted reply_due_date should prevent emit
    vm.form.reply_due_date = '2026-11-10'
    vm.handleSubmit()
    expect(editWrapper.emitted('onSubmit')).toBeUndefined()

    // Clearing optional fields & scan_file should append empty strings and clear_scan_file=true
    vm.form.reply_due_date = ''
    vm.form.recipient_dept = null
    vm.form.recipient_manager = null
    vm.markClearExistingScan()
    vm.handleSubmit()

    const emitted = editWrapper.emitted('onSubmit')
    expect(emitted).toBeTruthy()
    const fd = emitted![0][0] as FormData
    expect(fd.get('reply_due_date')).toBe('')
    expect(fd.get('recipient_dept')).toBe('')
    expect(fd.get('recipient_manager')).toBe('')
    expect(fd.get('clear_scan_file')).toBe('true')
  })

  it('InboundLetterView hides status quick-change controls when user only has docs.read', () => {
    const accStore = useAccount()
    const comStore = useCompany()
    const workStore = useWork()
    accStore.userInfo = makeUser()
    comStore.company = makeCompany({ com_issue_project: 10 })
    workStore.myProjects = [makeIssueProject(10, 1, [PERM.DOCS_READ])]

    const wrapper = mount(InboundLetterView, {
      props: {
        letter: {
          pk: 1,
          company: 1,
          receipt_number: 'TST-접수-2026-001',
          document_number: 'EXT-1',
          sender_name: '서울시청',
          received_date: '2026-11-27',
          title: '열람 테스트',
          status: 'received',
        },
        viewRoute: '수신 공문 관리',
        letterFilter: { company: 1, page: 1 },
      },
      global: { stubs: commonStubs },
    })

    expect(wrapper.text()).not.toContain('상태 간편 변경')
    expect(wrapper.findAll('button').some(b => b.text().trim() === '삭제')).toBe(false)
    expect(wrapper.findAll('button').some(b => b.text().trim() === '수정')).toBe(false)
  })
})
