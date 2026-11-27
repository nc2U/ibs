import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { useProLedger } from '@/store/pinia/proLedger'
import { useProject } from '@/store/pinia/project'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { Contract } from '@/store/types/contract'
import type { Project } from '@/store/types/project'
import type { OriginPayment, PaymentList } from '@/store/types/payment'
import ListContChoicer from '../List/components/ContChoicer.vue'
import ListController from '../List/components/ListController.vue'
import ListIndex from '../List/Index.vue'
import StatusIndex from '../Status/Index.vue'
import OverallSummary from '../Status/components/OverallSummary.vue'
import PaymentForm from '../Register/components/PaymentForm.vue'
import OrdersBoard from '../Register/components/OrdersBoard.vue'
import PaymentListAll from '../Register/components/PaymentListAll.vue'
import RegisterContChoicer from '../Register/components/ContChoicer.vue'

const { mockRouterPush, mockRouterReplace, mockRoute } = vi.hoisted(() => ({
  mockRouterPush: vi.fn(),
  mockRouterReplace: vi.fn(),
  mockRoute: { params: {} as Record<string, string>, query: {} as Record<string, string> },
}))

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ push: mockRouterPush, replace: mockRouterReplace }),
  onBeforeRouteLeave: vi.fn(),
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

const mockMessage = vi.fn()
const mockErrorHandle = vi.fn()
const mockDownloadFile = vi.fn()

vi.mock('@/utils/helper', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/helper')>()
  return {
    ...actual,
    message: (...args: unknown[]) => mockMessage(...args),
    errorHandle: (...args: unknown[]) => mockErrorHandle(...args),
    downloadFile: (...args: unknown[]) => mockDownloadFile(...args),
  }
})

vi.mock('@/utils/baseMixins', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/baseMixins')>()
  return {
    ...actual,
    getToday: () => '2026-11-28',
  }
})

const mockApi = api as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: {
    to: { type: [String, Object], required: false, default: '' },
  },
  template: '<a><slot /></a>',
})

const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: {
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  template:
    '<input :value="modelValue" :placeholder="placeholder" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
})

const makeVuetify = () => createVuetify({ components, directives })

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

const makeProject = (overrides: Partial<Project> = {}): Project =>
  ({
    pk: 10,
    company: 1,
    name: '테스트 프로젝트',
    issue_project: 5,
    issue_project_slug: 'test-proj',
    ...overrides,
  }) as unknown as Project

const makeContract = (overrides: Partial<Contract> = {}): Contract =>
  ({
    pk: 101,
    project: 10,
    order_group_sort: '2',
    order_group: 1,
    unit_type: 1,
    unit_type_desc: {
      pk: 1,
      sort: '1',
      name: '84A',
      color: '#123456',
      average_price: 300000000,
    },
    serial_number: 'CONT-001',
    is_active: true,
    is_completed: false,
    is_sup_cont: true,
    sup_cont_date: '2026-01-01',
    key_unit: null,
    contractprice: {
      pk: 1,
      price: 300000000,
      price_build: null,
      price_land: null,
      price_tax: null,
    },
    contractor: { pk: 50, name: '홍길동', contract_date: '2026-01-01' },
    payments: [],
    last_paid_order: null,
    total_paid: 0,
    order_group_desc: { pk: 1, sort: '2', name: '1차 일반' },
    contract_files: [],
    ...overrides,
  }) as unknown as Contract

const commonStubs = {
  Teleport: true,
  RouterLink: RouterLinkStub,
  CIcon: { template: '<i />' },
  DatePicker: DatePickerStub,
  Loading: { template: '<div />' },
  ContentHeader: { template: '<div><slot /></div>' },
  ContentBody: { template: '<div><slot /></div>' },
  TableTitleRow: { props: ['url', 'filename', 'disabled'], template: '<div><slot /></div>' },
  Multiselect: {
    props: ['modelValue', 'options', 'placeholder', 'disabled'],
    emits: ['update:modelValue', 'change'],
    template: '<select />',
  },
}

describe('payment module regression suite', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockRoute.params = {}
    mockRoute.query = {}

    const accountStore = useAccount()
    accountStore.userInfo = makeUser()
    const permStore = usePermission()
    permStore.setProjectPermissions([
      PERM.PAYMENT_READ,
      PERM.PAYMENT_CREATE,
      PERM.PAYMENT_UPDATE,
      PERM.PAYMENT_DELETE,
    ])
    const workStore = useWork()
    workStore.currentProject = {
      pk: 5,
      slug: 'test-proj',
      name: '테스트 프로젝트',
      status: '1',
    } as never
    const projectStore = useProject()
    projectStore.project = makeProject()

    mockApi.get.mockResolvedValue({ data: { count: 0, results: [] } })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('keeps separate filters for List/Register, supports ordering, and is null-safe in ledgerGetPayments', async () => {
    const paymentStore = usePayment()
    expect('overallSummary' in paymentStore).toBe(false)
    expect('paymentStatusByUnitType' in paymentStore).toBe(false)

    mockApi.get.mockResolvedValueOnce({
      data: {
        count: 1,
        results: [
          {
            pk: 77,
            project: 10,
            deal_date: '2026-11-20',
            contract: null,
            installment_order: null,
            bank_account: null,
            trader: '무통장입금',
            note: null,
            amount: 5000000,
            bank_transaction_id: 88,
            accounting_entry: {
              pk: 99,
              transaction_id: 'uuid',
              amount: 5000000,
              account: 1,
              related_transaction: null,
            },
            is_payment_mismatch: false,
            created_at: '',
            updated_at: '',
            creator: null,
          } satisfies OriginPayment,
        ],
      },
    })

    await paymentStore.fetchLedgerPaymentList({ project: 10, page: 1 })
    expect(paymentStore.ledgerGetPayments).toHaveLength(1)
    expect(paymentStore.ledgerGetPayments[0].bank_account).toBe('-')
    expect(paymentStore.ledgerGetPayments[0].order_group).toBe('-')

    mockApi.get.mockResolvedValueOnce({ data: { count: 0, results: [] } })
    await paymentStore.fetchLedgerAllPaymentList({
      project: 10,
      contract: 101,
      ordering: 'deal_date',
    })
    expect(mockApi.get).toHaveBeenLastCalledWith(
      '/ledger/all-payment/?is_payment_mismatch=false&project=10&contract=101&ordering=deal_date',
    )
    expect(paymentStore.ledgerPaymentFilter).toEqual({ project: 10, page: 1 })
    expect(paymentStore.ledgerAllPaymentFilter).toEqual({
      project: 10,
      contract: 101,
      ordering: 'deal_date',
    })

    mockApi.post.mockResolvedValueOnce({ data: { bank_transaction: { pk: 5 } } })
    mockApi.get.mockResolvedValueOnce({ data: { count: 0, results: [] } })
    await paymentStore.createContractPayment({
      project: 10,
      bank_account: 1,
      deal_date: '2026-11-20',
      amount: 1000000,
      sort: 1,
      content: '대금',
      accounting_entries: [],
    })
    expect(mockApi.get).toHaveBeenLastCalledWith(
      '/ledger/all-payment/?is_payment_mismatch=false&project=10&contract=101&ordering=deal_date',
    )
  })

  it('encodes search param and uses to_date param in List Excel export URLs without calling API when unauthorized', async () => {
    const permStore = usePermission()
    permStore.setProjectPermissions([])

    const vuetify = makeVuetify()
    const wrapperDenied = mount(ListIndex, {
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()
    expect(mockApi.get).not.toHaveBeenCalled()
    wrapperDenied.unmount()

    permStore.setProjectPermissions([PERM.PAYMENT_READ, PERM.PAYMENT_UPDATE])
    mockApi.get.mockImplementation(async (url: string) => {
      if (url.startsWith('/ledger/payment-summary/')) {
        return { data: [] }
      }
      return { data: { count: 0, results: [] } }
    })
    const wrapper = mount(ListIndex, {
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()

    const ctrl = wrapper.findComponent(ListController)
    const datePickers = ctrl.findAllComponents(DatePickerStub)
    await datePickers[1].setValue('2026-11-28')
    const searchInput = ctrl.find('input[placeholder="계약자, 입금자, 적요, 비고"]')
    await searchInput.setValue('홍&길#동')
    await searchInput.trigger('keydown.enter')
    await flushPromises()

    const titleRow = wrapper.findComponent(commonStubs.TableTitleRow)
    const excelUrl1 = titleRow.props('url') as string
    expect(excelUrl1).toContain('/excel/ledger/payment/?')
    expect(excelUrl1).toContain('q=%ED%99%8D%26%EA%B8%B8%23%EB%8F%99')

    const radios = wrapper.findAll('input[type="radio"]')
    await radios[1].setValue()
    await flushPromises()
    const excelUrl2 = titleRow.props('url') as string
    expect(excelUrl2).toContain('/excel/ledger/paid-by-cont/?project=10&to_date=2026-11-28')
  })

  it('emits filter once on ListController resetForm', async () => {
    const vuetify = makeVuetify()
    const wrapper = mount(ListController, {
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()

    const inputs = wrapper.findAllComponents(DatePickerStub)
    await inputs[0].setValue('2026-01-01')
    await inputs[1].setValue('2026-01-31')
    await nextTick()
    await nextTick()

    const prevCount = wrapper.emitted('payment-filtering')?.length ?? 0
    const resetBtn = wrapper.findAll('button').find(b => b.text().includes('검색조건 초기화'))
    expect(resetBtn).toBeTruthy()
    await resetBtn!.trigger('click')
    await nextTick()
    await nextTick()

    const afterCount = wrapper.emitted('payment-filtering')?.length ?? 0
    expect(afterCount - prevCount).toBe(1)
  })

  it('awaits contract search in List ContChoicer before empty-state message and omits content overwrite on match', async () => {
    const vuetify = makeVuetify()
    const contractStore = useContract()
    const fetchSpy = vi.spyOn(contractStore, 'fetchContractList').mockImplementation(async () => {
      contractStore.contractList = [makeContract()]
    })

    const payment: PaymentList = {
      pk: 1,
      trans_id: 55,
      entry_id: 66,
      deal_date: '2026-11-01',
      contract: null,
      order_group: '-',
      type_color: '-',
      type_name: '-',
      serial_number: '-',
      contractor: '-',
      amount: 1000000,
      installment_order: '-',
      bank_account: '국민은행',
      trader: '홍길동',
      note: '',
    }

    const wrapper = mount(ListContChoicer, {
      props: { project: 10, payment },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })

    const searchInput = wrapper.find('input')
    await searchInput.setValue('홍길동')
    await searchInput.trigger('keydown.enter')
    await flushPromises()

    expect(fetchSpy).toHaveBeenCalledWith({ project: 10, search: '홍길동' })
    expect(wrapper.text()).not.toContain('해당 검색어로 등록된 데이터가 없습니다.')
    expect(wrapper.text()).toContain('홍길동(CONT-001)')

    // Select contract and confirm match -> payload must NOT overwrite parent content
    const contBtn = wrapper.findAll('button').find(b => b.text().includes('홍길동(CONT-001)'))
    await contBtn!.trigger('click')
    await flushPromises()

    const saveBtn = wrapper.findAll('button').find(b => b.text() === '저장')
    await saveBtn!.trigger('click')
    await flushPromises()

    const emitted = wrapper.emitted('pay-match')
    expect(emitted).toBeTruthy()
    expect(emitted![0][0]).toEqual({
      trans_id: 55,
      accounting_entries: [{ pk: 66, contract: 101 }],
    })
  })

  it('loads Status data once without child duplication, resets ledger store fields on project switch, and deduplicates pay_time totals in OverallSummary', async () => {
    const vuetify = makeVuetify()
    const paymentStore = usePayment()
    const projectStore = useProject()

    mockApi.get.mockResolvedValue({ data: [] })
    const statusSpy = vi
      .spyOn(paymentStore, 'fetchLedgerPaymentStatusByUnitType')
      .mockResolvedValue([])
    vi.spyOn(paymentStore, 'fetchLedgerOverallSummary').mockResolvedValue({
      pay_orders: [],
      aggregate: { conts_num: 0, non_conts_num: 0, total_units: 0, contract_rate: 0 },
    })

    const wrapper = mount(StatusIndex, {
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()

    // No duplicate call between Status/Index and PaymentStatus.vue
    expect(statusSpy).toHaveBeenCalledTimes(1)

    paymentStore.ledgerPaymentStatusByUnitType = [
      {
        order_group_id: 1,
        order_group_name: '1차',
        unit_type_id: 1,
        unit_type_name: '84A',
        unit_type_color: '#000',
        total_sales_amount: 100,
        planned_units: 1,
        contract_units: 1,
        non_contract_units: 0,
        contract_amount: 100,
        paid_amount: 50,
        unpaid_amount: 50,
        non_contract_amount: 0,
        total_budget: 100,
      },
    ]
    projectStore.project = makeProject({ pk: 20, name: '프로젝트 B' })
    await flushPromises()
    expect(paymentStore.ledgerPaymentStatusByUnitType).toEqual([])
    wrapper.unmount()

    paymentStore.ledgerOverallSummary = {
      aggregate: { conts_num: 1, non_conts_num: 0, total_units: 1, contract_rate: 100 },
      pay_orders: [
        {
          pk: 1,
          pay_name: '1차 계약금(아파트)',
          pay_due_date: '2026-01-01',
          pay_sort: '1',
          pay_code: 1,
          pay_time: 1,
          contract_amount: 30000000,
          non_contract_amount: 10000000,
          contract_rate: 75,
          collection: {
            collected_amount: 30000000,
            discount_amount: 0,
            overdue_fee: 0,
            actual_collected: 30000000,
            collection_rate: 100,
          },
          due_period: {
            contract_amount: 30000000,
            unpaid_amount: 0,
            unpaid_rate: 0,
            overdue_fee: 0,
            subtotal: 0,
          },
          not_due_unpaid: 0,
          total_unpaid: 0,
          total_unpaid_rate: 0,
        },
        {
          pk: 2,
          pay_name: '1차 계약금(상가)',
          pay_due_date: '2026-01-01',
          pay_sort: '1',
          pay_code: 1,
          pay_time: 1,
          contract_amount: 30000000,
          non_contract_amount: 10000000,
          contract_rate: 75,
          collection: {
            collected_amount: 0,
            discount_amount: 0,
            overdue_fee: 0,
            actual_collected: 0,
            collection_rate: 0,
          },
          due_period: {
            contract_amount: 0,
            unpaid_amount: 0,
            unpaid_rate: 0,
            overdue_fee: 0,
            subtotal: 0,
          },
          not_due_unpaid: 0,
          total_unpaid: 0,
          total_unpaid_rate: 0,
        },
      ],
    }

    const overallWrapper = mount(OverallSummary, {
      props: { date: '2026-11-28' },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()
    // Should display 30,000,000 once in 계약(1) total column instead of 60,000,000
    const rowTexts = overallWrapper.findAll('tr').map(tr => tr.text())
    const contractRow = rowTexts.find(t => t.includes('계약(1)'))
    expect(contractRow).toBeTruthy()
    expect(contractRow).not.toContain('60,000,000')
  })

  it('handles PaymentForm mixed sibling_entries, bank_account=null, distinct sibling traders, removeCont, and saving reset', async () => {
    const vuetify = makeVuetify()
    const paymentStore = usePayment()
    const proLedgerStore = useProLedger()

    paymentStore.payOrderList = [
      {
        pk: 11,
        pay_sort: '1',
        pay_code: 1,
        pay_time: 1,
        pay_name: '계약금',
        str_display: '계약금',
      },
      {
        pk: 12,
        pay_sort: '2',
        pay_code: 2,
        pay_time: 2,
        pay_name: '중도금',
        str_display: '중도금',
      },
    ]
    proLedgerStore.allProBankList = [{ pk: 1, project: 10, alias_name: '국민은행' } as never]
    proLedgerStore.proAccountList = [
      {
        pk: 200,
        code: '4100',
        name: '분양대금',
        category: 'revenue',
        is_payment: true,
        is_active: true,
      } as never,
    ]

    const contract = makeContract()
    const mixedPayment: OriginPayment = {
      pk: 300,
      project: 10,
      deal_date: '2026-11-20',
      contract: null,
      installment_order: {
        pk: 11,
        pay_sort: '1',
        pay_name: '계약금',
        pay_time: 1,
        str_display: '계약금',
      },
      bank_account: null,
      trader: '홍길동',
      note: '',
      amount: 5000000,
      bank_transaction_id: 900,
      bank_transaction_amount: 15000000,
      accounting_entry: {
        pk: 701,
        transaction_id: 'uuid-900',
        amount: 5000000,
        account: 200,
        related_transaction: {
          pk: 900,
          deal_date: '2026-11-20',
          amount: 15000000,
          content: '원본 복합 적요',
          note: '',
        },
      },
      is_payment_mismatch: false,
      created_at: '',
      updated_at: '',
      creator: 1,
      sibling_entries: [
        {
          pk: 701,
          amount: 5000000,
          trader: '입금자A',
          contract: 101,
          account: { pk: 200, name: '분양대금', is_payment: true },
          is_contract_payment: true,
          contract_payment_pk: 300,
          installment_order: 11,
          installment_order_display: '계약금',
        },
        {
          pk: 702,
          amount: 5000000,
          trader: '입금자B',
          contract: 101,
          account: { pk: 200, name: '분양대금', is_payment: true },
          is_contract_payment: true,
          contract_payment_pk: 301,
          installment_order: 12,
          installment_order_display: '중도금',
        },
        {
          pk: 703,
          amount: 5000000,
          trader: '기타거래처',
          contract: null,
          account: { pk: 299, name: '선수수익', is_payment: false },
          is_contract_payment: false,
          contract_payment_pk: null,
          installment_order: null,
          installment_order_display: null,
        },
      ],
    }

    const wrapper = mount(PaymentForm, {
      props: { contract, payment: mixedPayment },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()

    // Adaptive dark-mode background class, no container div.bg-light
    expect(wrapper.findAll('div.bg-light')).toHaveLength(0)
    expect(wrapper.findAll('div.bg-body-tertiary')).toHaveLength(2)

    // Distinct trader on 2nd editable row preserved on mount
    const traderInputs = wrapper
      .findAll('input[placeholder="실제 입금자명"]')
      .map(i => (i.element as HTMLInputElement).value)
    expect(traderInputs).toEqual(['입금자A', '입금자B'])

    // Unchanged mixed form disables save button cleanly without throwing bank_account.pk error
    const saveBtn = wrapper.find('button[type="submit"]')
    expect(saveBtn.attributes('disabled')).toBeDefined()

    // Delete button hidden when readonlyEntries exist and user lacks LEDGER_DELETE
    expect(wrapper.findAll('button').some(b => b.text() === '삭제')).toBe(false)

    // Select bank account & check removeCont -> submits with contract=null, installment_order=null, preserved content, and unlocks after failed done(false)
    const selects = wrapper.findAll('select')
    await selects[0].setValue('1')
    const contChangeCheckbox = wrapper.find('#cont-change')
    await contChangeCheckbox.setValue(true)
    await nextTick()

    expect(saveBtn.attributes('disabled')).toBeUndefined()
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const confirmBtn = wrapper.findAll('button').find(b => b.text() === '변경')
    expect(confirmBtn).toBeTruthy()
    await confirmBtn!.trigger('click')
    await flushPromises()

    const submitted = wrapper.emitted('on-submit')
    expect(submitted).toBeTruthy()
    const [txId, payload, done] = submitted![0] as [
      number,
      { content: string; accounting_entries: Array<Record<string, unknown>> },
      (ok: boolean) => void,
    ]
    expect(txId).toBe(900)
    expect(payload.content).toBe('원본 복합 적요')
    expect(payload.accounting_entries[0].contract).toBeNull()
    expect(payload.accounting_entries[0].installment_order).toBeNull()
    expect(payload.accounting_entries[2]).toEqual({
      pk: 703,
      account: 299,
      amount: 5000000,
      trader: '기타거래처',
    })

    // Calling done(false) resets isSaving so save button can be clicked again
    done(false)
    await nextTick()
    expect(saveBtn.attributes('disabled')).toBeUndefined()
  })

  it('filters OrdersBoard by type_sort & excluded_order_groups, looks up plan by pk, matches PaymentListAll columns, and uses downloadFile in Register ContChoicer', async () => {
    const vuetify = makeVuetify()
    const paymentStore = usePayment()
    const contractStore = useContract()
    const permStore = usePermission()

    paymentStore.payOrderList = [
      {
        pk: 1,
        type_sort: '1',
        pay_code: 1,
        pay_time: 1,
        pay_name: '계약금(아파트)',
        excluded_order_groups: [],
      },
      {
        pk: 2,
        type_sort: '2',
        pay_code: 1,
        pay_time: 1,
        pay_name: '계약금(상가)',
        excluded_order_groups: [],
      },
      {
        pk: 3,
        type_sort: '1',
        pay_code: 2,
        pay_time: 2,
        pay_name: '제외회차',
        excluded_order_groups: [1],
      },
    ]
    vi.spyOn(contractStore, 'fetchContractPricePaymentPlan').mockResolvedValue({
      pk: 1,
      price: 300000000,
      price_build: null,
      price_land: null,
      price_tax: null,
      payment_amounts: { '1': 99999999 },
      is_cache_valid: true,
      calculated: null,
      payment_plan: [
        {
          installment_order: {
            pk: 2,
            pay_sort: '1',
            pay_code: 1,
            pay_time: 1,
            pay_name: '계약금(상가)',
            alias_name: '',
          },
          amount: 50000000,
          due_date: '2026-01-15',
          source: 'calculated',
        },
        {
          installment_order: {
            pk: 1,
            pay_sort: '1',
            pay_code: 1,
            pay_time: 1,
            pay_name: '계약금(아파트)',
            alias_name: '',
          },
          amount: 30000000,
          due_date: '2026-01-15',
          source: 'calculated',
        },
      ],
    } as never)

    const ordersWrapper = mount(OrdersBoard, {
      props: { contract: makeContract(), paymentList: [] },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    await flushPromises()
    expect(ordersWrapper.text()).toContain('계약금(아파트)')
    expect(ordersWrapper.text()).not.toContain('계약금(상가)')
    expect(ordersWrapper.text()).not.toContain('제외회차')
    expect(ordersWrapper.text()).toContain('30,000,000')
    expect(ordersWrapper.text()).not.toContain('50,000,000')

    permStore.setProjectPermissions([PERM.PAYMENT_READ])
    const listAllWrapper = mount(PaymentListAll, {
      props: { contract: makeContract(), paymentList: [] },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    const headerRows = listAllWrapper.findAll('thead tr')
    expect(headerRows[0].findAll('th')).toHaveLength(5)
    expect(headerRows[1].findAll('th')).toHaveLength(5)

    const choicerWrapper = mount(RegisterContChoicer, {
      props: {
        project: 10,
        contract: makeContract(),
        paymentUrl: '/pdf/ledger/payment/?project=10&contract=101',
      },
      global: { plugins: [vuetify, CoreuiVue], stubs: commonStubs },
    })
    const pdfLink = choicerWrapper.findAll('a').find(a => a.text().includes('납부내역서 출력'))
    await pdfLink!.trigger('click')
    expect(mockDownloadFile).toHaveBeenCalledWith(
      '/pdf/ledger/payment/?project=10&contract=101',
      '납부_확인서.pdf',
    )
    const closeLink = choicerWrapper.find('a[aria-label="계약 선택 해제"]')
    mockRoute.params = { contractId: '101' }
    await closeLink.trigger('click')
    expect(mockRouterReplace).toHaveBeenCalledWith({ name: '건별 납부 관리' })
  })
})
