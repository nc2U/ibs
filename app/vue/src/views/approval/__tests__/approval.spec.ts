import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { message } from '@/utils/helper'
import { markNotificationReadByTarget } from '@/utils/notification'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import PendingList from '../components/PendingList.vue'
import DocumentForm from '../components/DocumentForm.vue'
import DocumentDetail from '../components/DocumentDetail.vue'
import DelegationList from '../components/DelegationList.vue'
import ContractChangeForm from '../forms/ContractChangeForm.vue'
import LeaveApplicationForm from '../forms/LeaveApplicationForm.vue'
import BusinessTripForm from '../forms/BusinessTripForm.vue'
import OvertimeWorkForm from '../forms/OvertimeWorkForm.vue'
import OfficialLetterForm from '../forms/OfficialLetterForm.vue'
import ExpenseReportForm from '../forms/ExpenseReportForm.vue'
import { FORM_GUIDES } from '../data/formGuides'
import {
  calcInclusiveDays,
  extractApprovalAmount,
  filterStaffUserOptions,
  getExpenseTypeLabel,
  getInboundActionTypeInfo,
  getInboundUrgencyInfo,
  getReceiverTypeLabel,
  getSafeExternalUrl,
  getSettlementTypeLabel,
  parseNonNegativeNumberInput,
  parseSignedNumberInput,
  resolveRegistryEntry,
  toSafeUrl,
} from '../utils/approvalMeta'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
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

vi.mock('@/utils/notification', () => ({
  markNotificationReadByTarget: vi.fn(),
}))

const mockedApi = vi.mocked(api)
const mockedMessage = vi.mocked(message)
const mockedMarkNotification = vi.mocked(markNotificationReadByTarget)

const vuetify = createVuetify()

const ModalStub = defineComponent({
  name: 'CModal',
  props: { visible: Boolean },
  template: '<div v-if="visible" class="cmodal-stub"><slot /></div>',
})

const SimpleSlotStub = (name: string) =>
  defineComponent({
    name,
    template: '<div><slot /></div>',
  })

const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  template: '<input class="datepicker-stub" :value="modelValue" />',
})

const ConfirmModalStub = defineComponent({
  name: 'ConfirmModal',
  setup(_, { expose }) {
    expose({
      callModal: vi.fn(),
      close: vi.fn(),
    })
    return () => h('div', { class: 'confirm-modal-stub' })
  },
})

const createApprovalRouter = async (initialPath = '/pending') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/pending', name: '결재 대기함', component: { template: '<div />' } },
      { path: '/pending/:docId', name: '결재 대기함 - 보기', component: { template: '<div />' } },
      { path: '/drafted', name: '기안 문서함', component: { template: '<div />' } },
      { path: '/drafted/new', name: '기안 문서함 - 작성', component: { template: '<div />' } },
      { path: '/drafted/:docId', name: '기안 문서함 - 보기', component: { template: '<div />' } },
      { path: '/drafted/:docId/edit', name: '기안 문서함 - 수정', component: { template: '<div />' } },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('approvalMeta utilities', () => {
  it('calculates inclusive local day counts accurately', () => {
    expect(calcInclusiveDays('2026-05-01', '2026-05-01')).toBe(1)
    expect(calcInclusiveDays('2026-05-01', '2026-05-03')).toBe(3)
    expect(calcInclusiveDays('2026-05-05', '2026-05-01')).toBe(0)
    expect(calcInclusiveDays('invalid', '2026-05-01')).toBe(0)
  })

  it('resolves option labels, inbound metadata, and form guide aliases', () => {
    expect(getExpenseTypeLabel('CARD')).toBe('법인카드')
    expect(getSettlementTypeLabel('OTHER')).toBe('기타 경비 정산')
    expect(getReceiverTypeLabel('OTHER')).toBe('기타 계좌')
    expect(getInboundActionTypeInfo('BUDGET_ACTION')).toEqual({
      label: '예산 집행 및 시정·보수 조치 수반',
      color: 'warning',
    })
    expect(getInboundUrgencyInfo('VERY_URGENT')).toEqual({
      label: '당일/익일 긴급',
      color: 'error',
    })
    expect(FORM_GUIDES.TRIP.title).toContain('출장')
    expect(FORM_GUIDES.PROJECT_FEASIBILITY.title).toContain('신규 사업')
    expect(FORM_GUIDES.INBOUND.title).toContain('수신 공문')
  })

  it('sanitizes URLs and filters active staff user options', () => {
    expect(toSafeUrl('/media/doc.pdf')).toBe('/media/doc.pdf')
    expect(toSafeUrl('https://example.com/a.pdf')).toBe('https://example.com/a.pdf')
    expect(toSafeUrl('javascript:alert(1)')).toBe('#')
    expect(toSafeUrl('//evil.example.com/x')).toBe('#')

    const options = filterStaffUserOptions(
      [
        {
          pk: 1,
          username: 'me',
          is_active: true,
          has_staff: true,
          is_superuser: false,
          profile: { name: '본인' },
        },
        {
          pk: 2,
          username: 'staff1',
          is_active: true,
          has_staff: true,
          is_superuser: false,
          profile: { name: '홍길동' },
        },
        {
          pk: 3,
          username: 'inactive',
          is_active: false,
          has_staff: true,
          is_superuser: false,
        },
        {
          pk: 4,
          username: 'guest',
          is_active: true,
          has_staff: false,
          is_superuser: false,
        },
        {
          pk: 5,
          username: 'admin',
          is_active: true,
          has_staff: false,
          is_superuser: true,
        },
      ] as never[],
      1,
    )

    expect(options).toEqual([
      { value: 2, title: '홍길동 (staff1)' },
      { value: 5, title: 'admin' },
    ])
  })
})

describe('useApproval store contracts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('returns response data or null on actDocument/updateDocument and respects skipRefresh', async () => {
    const store = useApproval()

    mockedApi.post.mockResolvedValueOnce({ data: { detail: '승인 완료' } })
    const res = await store.actDocument(10, { action: 'approved' }, { skipRefresh: true })
    expect(res).toEqual({ detail: '승인 완료' })
    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(mockedMessage).not.toHaveBeenCalled()

    mockedApi.post.mockRejectedValueOnce(new Error('network fail'))
    const failRes = await store.actDocument(11, { action: 'approved' }, { skipRefresh: true })
    expect(failRes).toBeNull()

    mockedApi.patch.mockRejectedValueOnce(new Error('patch fail'))
    const updateFail = await store.updateDocument(12, new FormData())
    expect(updateFail).toBeNull()
  })

  it('passes seal query param and ignores stale route preview responses', async () => {
    const store = useApproval()

    let resolveFirst!: (val: { data: unknown }) => void
    let resolveSecond!: (val: { data: unknown }) => void
    mockedApi.get
      .mockReturnValueOnce(
        new Promise(r => {
          resolveFirst = r
        }),
      )
      .mockReturnValueOnce(
        new Promise(r => {
          resolveSecond = r
        }),
      )

    const p1 = store.fetchRoutePreview(1, 5, 100000, 9)
    const p2 = store.fetchRoutePreview(1, 5, 500000, 12)

    expect(mockedApi.get).toHaveBeenNthCalledWith(
      1,
      '/approval-document/preview_route/?doc_type=1&assignment=5&amount=100000&seal=9',
    )
    expect(mockedApi.get).toHaveBeenNthCalledWith(
      2,
      '/approval-document/preview_route/?doc_type=1&assignment=5&amount=500000&seal=12',
    )

    resolveSecond({ data: [{ step_order: 1, role_label: '대표이사', approvers: [], condition: 'OR' }] })
    await p2
    resolveFirst({ data: [{ step_order: 1, role_label: '구버전', approvers: [], condition: 'OR' }] })
    await p1

    expect(store.routePreview).toEqual([
      { step_order: 1, role_label: '대표이사', approvers: [], condition: 'OR' },
    ])
  })
})

describe('PendingList batch approval', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('reports mixed success/fail counts accurately and keeps only failed IDs selected', async () => {
    const store = useApproval()
    const pendingItems = [
      {
        id: 1,
        doc_number: 'DOC-1',
        title: '첫번째 품의',
        doc_type: 1,
        doc_type_name: '일반품의',
        drafter: { id: 10, username: 'kim', full_name: '김기안' },
        status: 'pending',
        current_step: 1,
        created_at: '2026-05-01T09:00:00Z',
        submitted_at: '2026-05-01T09:10:00Z',
        completed_at: null,
      },
      {
        id: 2,
        doc_number: 'DOC-2',
        title: '두번째 품의',
        doc_type: 1,
        doc_type_name: '일반품의',
        drafter: { id: 11, username: 'lee', full_name: '이기안' },
        status: 'pending',
        current_step: 1,
        created_at: '2026-05-01T09:00:00Z',
        submitted_at: '2026-05-01T09:10:00Z',
        completed_at: null,
      },
    ]

    mockedApi.get.mockResolvedValue({ data: pendingItems })
    mockedApi.post
      .mockResolvedValueOnce({ data: { detail: 'ok' } })
      .mockRejectedValueOnce(new Error('permission denied'))

    const router = await createApprovalRouter('/pending')
    const wrapper = mount(PendingList, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          CModal: ModalStub,
          CModalHeader: SimpleSlotStub('CModalHeader'),
          CModalTitle: SimpleSlotStub('CModalTitle'),
          CModalBody: SimpleSlotStub('CModalBody'),
          CModalFooter: SimpleSlotStub('CModalFooter'),
        },
      },
    })

    await flushPromises()
    expect(store.pendingList).toHaveLength(2)

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    // index 0 is select-all, 1 is row 1, 2 is row 2
    await checkboxes[1].setValue(true)
    await checkboxes[2].setValue(true)

    const openBatchBtn = wrapper.findAll('button').find(b => b.text().includes('선택 문서 일괄 승인'))
    expect(openBatchBtn).toBeDefined()
    await openBatchBtn!.trigger('click')
    await nextTick()

    const execBatchBtn = wrapper.findAll('button').find(b => b.text().includes('일괄 승인 실행'))
    expect(execBatchBtn).toBeDefined()
    await execBatchBtn!.trigger('click')
    await flushPromises()

    expect(mockedMessage).toHaveBeenCalledWith(
      'warning',
      '일괄 승인 결과',
      '총 1건 승인 완료 (실패 1건)',
      6000,
    )
    const updatedCheckboxes = wrapper.findAll('input[type="checkbox"]')
    expect((updatedCheckboxes[1].element as HTMLInputElement).checked).toBe(false)
    expect((updatedCheckboxes[2].element as HTMLInputElement).checked).toBe(true)
  })
})

describe('DocumentForm critical fixes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('loads secondary assignment doc types, falls back to doc_type_detail, and sends empty observer_ids []', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'drafter' } as never

    mockedApi.get.mockImplementation((url: string) => {
      if (url.startsWith('/approval-doc-category/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/my_assignments/')) {
        return Promise.resolve({
          data: [
            { pk: 10, is_primary: true, department_name: '개발팀', position_name: '팀장' },
            { pk: 77, is_primary: false, department_name: '감사TF', position_name: '팀원' },
          ],
        })
      }
      if (url.startsWith('/approval-document/42/')) {
        return Promise.resolve({
          data: {
            id: 42,
            doc_number: 'DRAFT-42',
            title: '기존 기안 제목',
            doc_type: 9,
            doc_type_detail: {
              id: 9,
              category_name: '특별양식',
              name: '비활성 서식',
              code: 'GENERAL',
              form_template_key: 'GENERAL',
              route_type: 'organization',
              is_active: false,
              route_templates: [],
            },
            drafter_assignment: 77,
            content: { purpose: '기존 목적', content: '기존 내용' },
            security_level: '1',
            observers: [{ id: 200, username: 'obs', full_name: '참조자' }],
            attachments: [],
          },
        })
      }
      if (url.startsWith('/approval-doc-type/for_draft/?assignment=77')) {
        return Promise.resolve({ data: [] })
      }
      if (url.startsWith('/approval-document/preview_route/')) {
        return Promise.resolve({ data: [] })
      }
      return Promise.resolve({ data: { results: [] } })
    })

    mockedApi.patch.mockResolvedValue({ data: { id: 42, title: '기존 기안 제목' } })

    const router = await createApprovalRouter('/drafted/42/edit')
    const wrapper = mount(DocumentForm, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    expect(mockedApi.get).toHaveBeenCalledWith('/approval-doc-type/for_draft/?assignment=77')
    const optionTexts = wrapper.findAll('option').map(o => o.text())
    expect(optionTexts.some(t => t.includes('비활성 서식'))).toBe(true)

    const clearObsBtn = wrapper.find('.v-autocomplete__clear, button[aria-label*="Clear"]')
    if (clearObsBtn.exists()) {
      await clearObsBtn.trigger('click')
    } else {
      // Simulate clearing selected observers via component vm binding fallback
      ;(wrapper.vm as unknown as { selectedObservers?: number[] }).selectedObservers = []
    }
    // Directly invoke save via draft button after ensuring empty observers
    const vmState = wrapper.vm as unknown as { selectedObservers: number[] }
    vmState.selectedObservers = []
    await nextTick()

    const draftBtn = wrapper.findAll('button').find(b => b.text().includes('임시저장'))
    expect(draftBtn).toBeDefined()
    await draftBtn!.trigger('click')
    await flushPromises()

    expect(mockedApi.patch).toHaveBeenCalled()
    const sentFormData = mockedApi.patch.mock.calls[0][1] as FormData
    expect(sentFormData.get('observer_ids')).toBe('[]')
  })

  it('prefetches inbound letter before mounting InboundReportForm in create mode', async () => {
    mockedApi.get.mockImplementation((url: string) => {
      if (url.startsWith('/approval-doc-category/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/my_assignments/')) {
        return Promise.resolve({
          data: [{ pk: 10, is_primary: true, department_name: '공무팀', position_name: '팀장' }],
        })
      }
      if (url.startsWith('/approval-doc-type/for_draft/')) {
        return Promise.resolve({
          data: [
            {
              id: 55,
              name: '수신공문 보고서',
              code: 'INBOUND_REPORT',
              form_template_key: 'INBOUND_REPORT',
              default_security_level: '2',
              route_type: 'organization',
              is_active: true,
              route_templates: [],
            },
          ],
        })
      }
      if (url === '/inbound-letter/99/') {
        return Promise.resolve({
          data: {
            pk: 99,
            sender_name: '연수구청 도시계획과',
            document_number: '도시-2026-1',
            receipt_number: 'IBS-001',
            received_date: '2026-05-02',
            reply_due_date: '2026-05-15',
            title: '사업계획 승인조건 확인',
            content: '승인조건 이행 여부를 회신바랍니다.',
          },
        })
      }
      if (url.startsWith('/approval-document/preview_route/')) {
        return Promise.resolve({ data: [] })
      }
      return Promise.resolve({ data: { results: [] } })
    })

    const router = await createApprovalRouter('/drafted/new?inbound_letter=99')
    const wrapper = mount(DocumentForm, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 30))
    await flushPromises()

    expect(mockedApi.get).toHaveBeenCalledWith('/inbound-letter/99/')
    const inputValues = wrapper.findAll('input').map(i => i.element.value)
    expect(inputValues).toContain('연수구청 도시계획과')
    expect(inputValues).toContain('사업계획 승인조건 확인')
  })
})

describe('DocumentDetail docId watch & notifications', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('marks approval_document notification read and re-fetches when docId route param changes', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'tester' } as never

    mockedApi.get.mockImplementation((url: string) => {
      if (url === '/approval-document/10/') {
        return Promise.resolve({
          data: {
            id: 10,
            doc_number: 'DOC-10',
            title: '문서 10',
            doc_type: 1,
            doc_type_detail: { form_template_key: 'GENERAL', code: 'GENERAL' },
            content: { purpose: '목적 10', content: '내용 10' },
            drafter: { id: 1, username: 'tester', full_name: '테스터' },
            status: 'pending',
            current_step: 1,
            content_hash: 'abc',
            pdf_url: null,
            created_at: '2026-05-01T00:00:00Z',
            submitted_at: '2026-05-01T01:00:00Z',
            completed_at: null,
            steps: [],
          },
        })
      }
      if (url === '/approval-document/20/') {
        return Promise.resolve({
          data: {
            id: 20,
            doc_number: 'DOC-20',
            title: '문서 20',
            doc_type: 1,
            doc_type_detail: { form_template_key: 'GENERAL', code: 'GENERAL' },
            content: { purpose: '목적 20', content: '내용 20' },
            drafter: { id: 1, username: 'tester', full_name: '테스터' },
            status: 'approved',
            current_step: 1,
            content_hash: 'def',
            pdf_url: null,
            created_at: '2026-05-02T00:00:00Z',
            submitted_at: '2026-05-02T01:00:00Z',
            completed_at: '2026-05-02T02:00:00Z',
            steps: [],
          },
        })
      }
      return Promise.resolve({ data: [] })
    })

    const router = await createApprovalRouter('/pending/10')
    const wrapper = mount(DocumentDetail, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          ConfirmModal: ConfirmModalStub,
          CModal: ModalStub,
          CModalHeader: SimpleSlotStub('CModalHeader'),
          CModalTitle: SimpleSlotStub('CModalTitle'),
          CModalBody: SimpleSlotStub('CModalBody'),
          CModalFooter: SimpleSlotStub('CModalFooter'),
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    expect(mockedMarkNotification).toHaveBeenCalledWith('approval_document', 10)
    expect(mockedApi.get).toHaveBeenCalledWith('/approval-document/10/')
    expect(wrapper.text()).toContain('문서 10')

    await router.push({ name: '결재 대기함 - 보기', params: { docId: '20' } })
    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    expect(mockedMarkNotification).toHaveBeenCalledWith('approval_document', 20)
    expect(mockedApi.get).toHaveBeenCalledWith('/approval-document/20/')
    expect(wrapper.text()).toContain('문서 20')
  })
})

describe('Pass 2 approval fixes & regressions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('extracts unified amount keys, normalizes registry lookup, sanitizes links, and parses signed input', () => {
    expect(parseSignedNumberInput('-50000')).toBe(-50000)
    expect(parseSignedNumberInput('-')).toBe('')
    expect(parseSignedNumberInput('')).toBe('')
    expect(parseSignedNumberInput('0')).toBe(0)

    expect(extractApprovalAmount({ total_cost: 500000 })).toBe(500000)
    expect(extractApprovalAmount({ financial_impact: -120000 })).toBe(-120000)
    expect(extractApprovalAmount({ estimated_amount: '300000' })).toBe(300000)
    expect(extractApprovalAmount({ amount: '' })).toBeNull()

    const reg = { LEAVE: 'leave-comp', GENERAL: 'general-comp' }
    expect(resolveRegistryEntry(reg, { form_template_key: ' leave ', code: 'OTHER' })).toBe(
      'leave-comp',
    )
    expect(resolveRegistryEntry(reg, { form_template_key: 'UNKNOWN', code: ' general ' })).toBe(
      'general-comp',
    )

    expect(getSafeExternalUrl('javascript:alert(1)')).toBe('')
    expect(getSafeExternalUrl('//evil.example/a')).toBe('')
    expect(getSafeExternalUrl('/media/a.pdf')).toBe('/media/a.pdf')
  })

  it('allows negative/arbitrary-step contract change amounts and guards date/time clearing', async () => {
    const changeWrapper = mount(ContractChangeForm, {
      props: {
        modelValue: { original_amount: 1000000, change_amount: 0, change_type: 'COMPREHENSIVE' },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })

    const changeInput = changeWrapper.find('input[placeholder*="감액"]')
    expect(changeInput.exists()).toBe(true)
    await changeInput.setValue('')
    await changeInput.setValue('-250400')

    const emittedChange = changeWrapper.emitted('update:modelValue') || []
    const lastPayload = emittedChange[emittedChange.length - 1][0] as Record<string, unknown>
    expect(lastPayload.change_amount).toBe(-250400)
    expect(lastPayload.final_amount).toBe(749600)
    expect(lastPayload.amount).toBe(250400)

    const leaveWrapper = mount(LeaveApplicationForm, {
      props: {
        modelValue: {
          leave_type: 'ANNUAL',
          start_date: '2026-05-01',
          end_date: '2026-05-03',
          days_count: 3,
        },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })
    const leaveDatePickers = leaveWrapper.findAllComponents(DatePickerStub)
    await leaveDatePickers[1].vm.$emit('update:modelValue', '')
    const leaveEmits = leaveWrapper.emitted('update:modelValue') || []
    expect((leaveEmits[leaveEmits.length - 1][0] as Record<string, unknown>).days_count).toBe(0)

    const tripWrapper = mount(BusinessTripForm, {
      props: {
        modelValue: {
          start_date: '2026-05-01',
          end_date: '2026-05-03',
          days_count: 3,
          nights_count: 2,
        },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })
    const tripPickers = tripWrapper.findAllComponents(DatePickerStub)
    await tripPickers[0].vm.$emit('update:modelValue', '')
    const tripEmits = tripWrapper.emitted('update:modelValue') || []
    const lastTrip = tripEmits[tripEmits.length - 1][0] as Record<string, unknown>
    expect(lastTrip.days_count).toBe(0)
    expect(lastTrip.nights_count).toBe(0)

    const overtimeWrapper = mount(OvertimeWorkForm, {
      props: {
        modelValue: {
          work_type: 'OVERTIME',
          start_time: '18:30',
          end_time: '21:30',
          break_hours: 0,
          total_hours: 3,
        },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })
    const timeInputs = overtimeWrapper.findAll('input[type="time"]')
    await timeInputs[1].setValue('')
    const otEmits = overtimeWrapper.emitted('update:modelValue') || []
    expect((otEmits[otEmits.length - 1][0] as Record<string, unknown>).total_hours).toBe(0)
  })

  it('allows incomplete child fields on draft save, warns on invalid submit, and preserves non-owner assignment option', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'admin', is_superuser: true } as never

    mockedApi.get.mockImplementation((url: string) => {
      if (url.startsWith('/approval-doc-category/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/my_assignments/')) {
        return Promise.resolve({
          data: [{ pk: 10, is_primary: true, department_name: '개발팀', position_name: '팀장' }],
        })
      }
      if (url.startsWith('/approval-doc-type/for_draft/')) {
        return Promise.resolve({
          data: [
            {
              id: 5,
              name: '일반 품의서',
              code: 'GENERAL',
              form_template_key: 'UNKNOWN_CUSTOM',
              route_type: 'organization',
              is_active: true,
              route_templates: [],
            },
          ],
        })
      }
      if (url.startsWith('/approval-document/77/')) {
        return Promise.resolve({
          data: {
            id: 77,
            doc_number: 'DRAFT-77',
            title: '타인 기안 수정',
            doc_type: 5,
            doc_type_detail: {
              id: 5,
              name: '일반 품의서',
              code: 'GENERAL',
              form_template_key: 'UNKNOWN_CUSTOM',
              route_type: 'organization',
              is_active: true,
              route_templates: [],
            },
            drafter_assignment: 999,
            drafter_assignment_desc: '법무팀 (과장)',
            content: {},
            security_level: '2',
            observers: [],
            attachments: [],
          },
        })
      }
      if (url.startsWith('/approval-document/preview_route/')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: { results: [] } })
    })
    mockedApi.patch.mockResolvedValue({ data: { id: 77, title: '타인 기안 수정' } })

    const router = await createApprovalRouter('/drafted/77/edit')
    const wrapper = mount(DocumentForm, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    const optionTexts = wrapper.findAll('option').map(o => o.text())
    expect(optionTexts.some(t => t.includes('법무팀 (과장)'))).toBe(true)

    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('저장 후 상신'))
    expect(submitBtn).toBeDefined()
    await submitBtn!.trigger('click')
    await flushPromises()
    expect(mockedMessage).toHaveBeenCalledWith(
      'warning',
      '입력 확인',
      '필수 항목 또는 입력 형식(기간/금액)을 확인해 주세요.',
    )
    expect(mockedApi.patch).not.toHaveBeenCalled()

    const draftBtn = wrapper.findAll('button').find(b => b.text().includes('임시저장'))
    expect(draftBtn).toBeDefined()
    await draftBtn!.trigger('click')
    await flushPromises()
    expect(mockedApi.patch).toHaveBeenCalledTimes(1)
  })

  it('hides duplicate delegation controls when user is also a direct approver in the same step and prevents double toggle', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'me' } as never
    const today = new Date()
    const fmt = (d: Date) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const todayStr = fmt(today)

    mockedApi.get.mockImplementation((url: string) => {
      if (url === '/approval-document/33/') {
        return Promise.resolve({
          data: {
            id: 33,
            doc_number: 'DOC-33',
            title: '합의 문서',
            doc_type: 1,
            doc_type_detail: { form_template_key: 'GENERAL', code: 'GENERAL' },
            content: { purpose: '목적', content: '내용' },
            drafter: { id: 9, username: 'drafter', full_name: '기안자' },
            status: 'pending',
            current_step: 1,
            content_hash: 'h',
            pdf_url: null,
            created_at: '2026-05-01T00:00:00Z',
            submitted_at: '2026-05-01T01:00:00Z',
            completed_at: null,
            steps: [
              {
                id: 1,
                step_order: 1,
                role_label: '팀장 합의',
                condition: 'AND',
                status: 'pending',
                approvers: [
                  { id: 1, username: 'me', full_name: '본인' },
                  { id: 2, username: 'other', full_name: '타결재자' },
                ],
                actions: [],
              },
            ],
          },
        })
      }
      if (url === '/approval-delegation/') {
        return Promise.resolve({
          data: [
            {
              id: 7,
              delegator: { id: 2, username: 'other', full_name: '타결재자' },
              delegatee: { id: 1, username: 'me', full_name: '본인' },
              start_date: todayStr,
              end_date: todayStr,
              is_active: true,
              is_valid_now: true,
            },
          ],
        })
      }
      return Promise.resolve({ data: { results: [] } })
    })

    const detailRouter = await createApprovalRouter('/pending/33')
    const detailWrapper = mount(DocumentDetail, {
      global: {
        plugins: [vuetify, CoreuiVue, detailRouter],
        stubs: {
          CIcon: true,
          ConfirmModal: ConfirmModalStub,
          CModal: ModalStub,
          CModalHeader: SimpleSlotStub('CModalHeader'),
          CModalTitle: SimpleSlotStub('CModalTitle'),
          CModalBody: SimpleSlotStub('CModalBody'),
          CModalFooter: SimpleSlotStub('CModalFooter'),
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    expect(detailWrapper.text()).not.toContain('대결 대상')
    const approveBtns = detailWrapper.findAll('button').filter(b => b.text().trim() === '승인')
    expect(approveBtns).toHaveLength(1)

    let resolvePatch!: (v: { data: unknown }) => void
    mockedApi.patch.mockReturnValue(
      new Promise(r => {
        resolvePatch = r
      }),
    )

    const delWrapper = mount(DelegationList, {
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
          CModal: ModalStub,
          CModalHeader: SimpleSlotStub('CModalHeader'),
          CModalTitle: SimpleSlotStub('CModalTitle'),
          CModalBody: SimpleSlotStub('CModalBody'),
          CModalFooter: SimpleSlotStub('CModalFooter'),
        },
      },
    })

    await flushPromises()
    const toggleBtn = delWrapper.findAll('button').find(b => b.text().trim() === '해제')
    expect(toggleBtn).toBeDefined()
    await toggleBtn!.trigger('click')
    await toggleBtn!.trigger('click')
    expect(mockedApi.patch).toHaveBeenCalledTimes(1)
    resolvePatch({ data: { id: 7, is_active: false } })
    await flushPromises()
  })
})

describe('Pass 3 edge-case fixes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('parses non-negative input without 0 snap-back on clear and supports 1-won ExpenseReportForm entry', async () => {
    expect(parseNonNegativeNumberInput('-5000')).toBe(0)
    expect(parseNonNegativeNumberInput('')).toBe('')
    expect(parseNonNegativeNumberInput('15400')).toBe(15400)

    const expWrapper = mount(ExpenseReportForm, {
      props: {
        modelValue: { items: [{ date: '2026-05-01', description: '식비', amount: 0 }] },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })

    const amountInput = expWrapper.find('input[type="number"]')
    expect(amountInput.exists()).toBe(true)
    await amountInput.setValue('')
    await amountInput.setValue('15400')

    const emitted = expWrapper.emitted('update:modelValue') || []
    const last = emitted[emitted.length - 1][0] as { items: Array<{ amount: unknown }>; amount: number }
    expect(last.items[0].amount).toBe(15400)
    expect(last.amount).toBe(15400)
  })

  it('re-mounts shared form components via key, cancels preview debounce timer on empty doc_type, and validates payment/settlement dates', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'drafter' } as never

    mockedApi.get.mockImplementation((url: string) => {
      if (url.startsWith('/approval-doc-category/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/my_assignments/')) {
        return Promise.resolve({
          data: [{ pk: 10, is_primary: true, department_name: '개발팀', position_name: '팀장' }],
        })
      }
      if (url.startsWith('/approval-doc-type/for_draft/')) {
        return Promise.resolve({
          data: [
            {
              id: 101,
              name: '지출결의서 A',
              code: 'EXPENSE',
              form_template_key: 'EXPENSE',
              route_type: 'organization',
              is_active: true,
              route_templates: [],
            },
            {
              id: 102,
              name: '지출결의서 B',
              code: 'EXPENSE_REPORT',
              form_template_key: 'EXPENSE_REPORT',
              route_type: 'organization',
              is_active: true,
              route_templates: [],
            },
          ],
        })
      }
      if (url.startsWith('/approval-document/preview_route/')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: { results: [] } })
    })

    const router = await createApprovalRouter('/drafted/new')
    const wrapper = mount(DocumentForm, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    const selects = wrapper.findAll('select')
    const docTypeSelect = selects[1]
    await docTypeSelect.setValue('101')
    await flushPromises()
    await new Promise(r => setTimeout(r, 30))
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)

    await docTypeSelect.setValue('102')
    await flushPromises()
    await new Promise(r => setTimeout(r, 30))
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)

    // Schedule debounced route preview, then clear doc_type before 200ms elapses
    const vm = wrapper.vm as unknown as {
      form: { doc_type: string; title: string }
      dynamicContent: Record<string, unknown>
    }
    vm.dynamicContent = { amount: 500000 }
    await nextTick()
    vm.form.doc_type = ''
    await nextTick()
    await new Promise(r => setTimeout(r, 230))
    await flushPromises()

    const calledUrls = mockedApi.get.mock.calls.map(c => String(c[0]))
    expect(calledUrls.some(u => u.includes('doc_type=0'))).toBe(false)

    // Advance payment date inversion check in validateBusinessRules
    vm.form.doc_type = '101'
    vm.form.title = '선급금 테스트'
    vm.dynamicContent = { payment_due_date: '2026-06-20', settlement_due_date: '2026-06-10' }
    await nextTick()

    const draftBtn = wrapper.findAll('button').find(b => b.text().includes('임시저장'))
    await draftBtn!.trigger('click')
    await flushPromises()
    expect(mockedMessage).toHaveBeenCalledWith(
      'warning',
      '정산 일정 확인',
      '정산 예정일은 지급 요청일과 같거나 이후여야 합니다.',
    )
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('redirects away from edit mode when document is non-editable for non-superuser', async () => {
    const accountStore = useAccount()
    accountStore.userInfo = { pk: 1, username: 'drafter', is_superuser: false } as never

    mockedApi.get.mockImplementation((url: string) => {
      if (url.startsWith('/approval-doc-category/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/my_assignments/')) return Promise.resolve({ data: [] })
      if (url.startsWith('/approval-document/88/')) {
        return Promise.resolve({
          data: {
            id: 88,
            doc_number: 'APPR-88',
            title: '이미 상신된 문서',
            doc_type: 1,
            drafter: { id: 1, username: 'drafter', full_name: '기안자' },
            status: 'pending',
            content: {},
          },
        })
      }
      return Promise.resolve({ data: { results: [] } })
    })

    const router = await createApprovalRouter('/drafted/88/edit')
    mount(DocumentForm, {
      global: {
        plugins: [vuetify, CoreuiVue, router],
        stubs: {
          CIcon: true,
          DatePicker: DatePickerStub,
          ConfirmModal: ConfirmModalStub,
        },
      },
    })

    await flushPromises()
    await new Promise(r => setTimeout(r, 20))
    await flushPromises()

    expect(mockedMessage).toHaveBeenCalledWith(
      'warning',
      '수정 불가',
      '임시저장 또는 반려 상태의 문서만 수정할 수 있습니다.',
    )
    expect(router.currentRoute.value.name).toBe('기안 문서함 - 보기')
  })

  it('renders fallback seal option in OfficialLetterForm and syncs search/selection in PendingList', async () => {
    const comStore = useCompany()
    comStore.sealList = [
      { pk: 1, company: 1, name: '법인인감(현)', seal_type: 'CORP_SEAL', seal_type_desc: '법인인감', seal_image: '' },
    ] as never
    vi.spyOn(comStore, 'fetchCompanySealList').mockResolvedValue(undefined as never)

    const letterWrapper = mount(OfficialLetterForm, {
      props: {
        modelValue: { seal_id: 99, seal_name: '구 사용인감', seal_type: 'USE_SEAL' },
      },
      global: {
        plugins: [vuetify, CoreuiVue],
        stubs: { CIcon: true, DatePicker: DatePickerStub },
      },
    })

    await flushPromises()
    const optionTexts = letterWrapper.findAll('option').map(o => o.text())
    expect(optionTexts.some(t => t.includes('구 사용인감'))).toBe(true)

    const store = useApproval()
    const docs = [
      {
        id: 1,
        doc_number: 'DOC-100',
        title: '품의 A',
        doc_type: 1,
        doc_type_name: '일반품의',
        drafter: { id: 10, username: 'kim', full_name: '김기안' },
        status: 'pending',
        current_step: 1,
        created_at: '2026-05-01T09:00:00Z',
        submitted_at: '2026-05-01T09:10:00Z',
        completed_at: null,
      },
      {
        id: 2,
        doc_number: 'DOC-200',
        title: '품의 B',
        doc_type: 1,
        doc_type_name: '일반품의',
        drafter: { id: 11, username: 'lee', full_name: '이기안' },
        status: 'pending',
        current_step: 1,
        created_at: '2026-05-01T09:00:00Z',
        submitted_at: '2026-05-01T09:10:00Z',
        completed_at: null,
      },
    ]
    mockedApi.get.mockResolvedValue({ data: docs })
    mockedApi.post.mockResolvedValue({ data: { detail: 'ok' } })

    const pendingRouter = await createApprovalRouter('/pending')
    const pendingWrapper = mount(PendingList, {
      global: {
        plugins: [vuetify, CoreuiVue, pendingRouter],
        stubs: {
          CIcon: true,
          CModal: ModalStub,
          CModalHeader: SimpleSlotStub('CModalHeader'),
          CModalTitle: SimpleSlotStub('CModalTitle'),
          CModalBody: SimpleSlotStub('CModalBody'),
          CModalFooter: SimpleSlotStub('CModalFooter'),
        },
      },
    })
    await flushPromises()

    const checkboxes = pendingWrapper.findAll('input[type="checkbox"]')
    await checkboxes[1].setValue(true)
    await checkboxes[2].setValue(true)

    // Drafter search
    const searchInput = pendingWrapper.find('input[placeholder*="기안자"]')
    await searchInput.setValue('이기안')
    expect(pendingWrapper.text()).toContain('품의 B')
    expect(pendingWrapper.text()).not.toContain('품의 A')

    // Prune stale selected ID when polling removes doc 1
    store.pendingList = [docs[1] as never]
    await nextTick()
    const batchBtn = pendingWrapper.findAll('button').find(b => b.text().includes('선택 문서 일괄 승인'))
    expect(batchBtn?.text()).toContain('(1건)')
  })
})
