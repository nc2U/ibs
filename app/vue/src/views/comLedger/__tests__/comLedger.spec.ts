import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, defineComponent, h } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { errorHandle, message } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { useWork } from '@/store/pinia/work_project'
import { useComLedger } from '@/store/pinia/comLedger'
import type {
  AccountPicker,
  BankTransaction,
  ComMonthlySummary,
  CompanyAccount,
  CompanyBank,
} from '@/store/types/comLedger'
import { PERM, type PermissionCode } from '@/store/constants/permissions'
import AccountManage from '../Manage/components/AccountManage.vue'
import BankAccForm from '../Manage/components/BankAccForm.vue'
import TransactionItem from '../Manage/components/TransactionItem.vue'
import TransForm from '../Manage/components/TransForm.vue'
import Calculated from '../Status/components/Calculated.vue'
import StatusByAccount from '../Status/components/StatusByAccount.vue'
import MonthlySummary from '../Status/components/MonthlySummary.vue'
import MonthlySummaryTable from '../Status/components/MonthlySummaryTable.vue'
import DateChoicer from '../Status/components/DateChoicer.vue'
import TabSelect from '../Status/components/TabSelect.vue'
import CashListByDate from '../Status/components/CashListByDate.vue'

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
const mockedMessage = vi.mocked(message)
const mockedErrorHandle = vi.mocked(errorHandle)

const vuetify = createVuetify()

const tooltipDirective = {
  mounted: () => undefined,
  updated: () => undefined,
}

const CIconStub = defineComponent({
  name: 'CIcon',
  template: '<span class="cicon-stub" />',
})

const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  template:
    '<input class="datepicker-stub" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
})

const LedgerAccountStub = defineComponent({
  name: 'LedgerAccount',
  props: { modelValue: { type: Number, default: null } },
  emits: ['update:modelValue'],
  template:
    '<input class="ledger-account-stub" :value="modelValue" @input="$emit(\'update:modelValue\', Number($event.target.value) || null)" />',
})

const seedPermissions = (perms: PermissionCode[], isSuperuser = false) => {
  const accountStore = useAccount()
  accountStore.userInfo = {
    pk: 1,
    username: 'tester',
    email: 'tester@example.com',
    is_active: true,
    is_superuser: isSuperuser,
    work_manager: false,
    has_staff: true,
  } as unknown as typeof accountStore.userInfo

  const workStore = useWork()
  workStore.myProjects = [
    {
      pk: 10,
      name: 'HQ',
      slug: 'hq',
      type: '1',
      my_perms: perms,
    } as unknown as (typeof workStore.myProjects)[number],
  ]
}

const makeTransaction = (overrides: Partial<BankTransaction> = {}): BankTransaction => ({
  pk: 101,
  transaction_id: 'tx-101',
  company: 1,
  bank_account: 5,
  bank_account_name: '국민은행 주계좌',
  deal_date: '2026-08-15',
  amount: 100000,
  sort: 2,
  sort_name: '출금',
  content: '사무용품 구입',
  note: '초기 메모',
  creator: 1,
  creator_name: 'tester',
  created_at: '2026-08-15T10:00:00Z',
  updated_at: '2026-08-15T10:00:00Z',
  is_balanced: true,
  accounting_entries: [
    {
      pk: 201,
      transaction_id: 'tx-101',
      company: 1,
      sort: 2,
      sort_name: '출금',
      account: 30,
      account_name: '소모품비',
      account_code: '5210',
      account_full_path: '비용 > 판관비 > 소모품비',
      affiliate: null,
      affiliate_display: null,
      amount: 100000,
      trader: '알파문구',
      evidence_type: '3',
      evidence_type_display: '신용/체크카드 매출전표',
      created_at: '2026-08-15T10:00:00Z',
      updated_at: '2026-08-15T10:00:00Z',
    },
  ],
  ...overrides,
})

const createComLedgerRouter = async (initialPath = '/com-ledger/manage') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/com-ledger/manage', name: '본사 거래 내역', component: { template: '<div>List</div>' } },
      {
        path: '/com-ledger/manage/create',
        name: '본사 거래 내역 - 생성',
        component: { template: '<div>Create</div>' },
      },
      {
        path: '/com-ledger/manage/edit/:transId',
        name: '본사 거래 내역 - 수정',
        component: { template: '<div>Edit</div>' },
      },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('comLedger module', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
    document.body.style.cssText = ''
    document.documentElement.style.cssText = ''
  })

  afterEach(() => {
    document.body.style.cssText = ''
    document.documentElement.style.cssText = ''
  })

  describe('useComLedger Pinia store', () => {
    it('findBankTransactionPage passes account_category and limit params', async () => {
      const store = useComLedger()
      mockedApi.get.mockResolvedValueOnce({ data: { page: 3 } })

      const page = await store.findBankTransactionPage(77, {
        company: 2,
        account_category: 'revenue',
        search: '용역',
        limit: 15,
      })

      expect(page).toBe(3)
      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/company-transaction/find_page/', {
        params: {
          highlight_id: 77,
          company: 2,
          account_category: 'revenue',
          search: '용역',
          limit: 15,
        },
      })
    })

    it('rethrows API errors in createComBankAcc and deleteBankTransaction after errorHandle', async () => {
      const store = useComLedger()
      const apiErr = new Error('validation failed')
      mockedApi.post.mockRejectedValueOnce(apiErr)
      mockedApi.delete.mockRejectedValueOnce(apiErr)

      await expect(
        store.createComBankAcc({
          company: 1,
          depart: null,
          bankcode: 1,
          alias_name: '신규계좌',
          number: '123',
          holder: '회사',
          open_date: null,
          note: '',
          is_hide: false,
          inactive: false,
        }),
      ).rejects.toThrow('validation failed')
      expect(mockedErrorHandle).toHaveBeenCalledTimes(1)

      await expect(store.deleteBankTransaction(999)).rejects.toThrow('validation failed')
      expect(mockedErrorHandle).toHaveBeenCalledTimes(2)
    })

    it('supports skipRefresh and silent options on createBankTransaction', async () => {
      const store = useComLedger()
      mockedApi.post.mockResolvedValueOnce({ data: { pk: 500 } })

      const result = await store.createBankTransaction(
        {
          company: 1,
          bank_account: 5,
          deal_date: '2026-08-20',
          amount: 50000,
          sort: 1,
          content: '입금 테스트',
          note: '',
          accounting_entries: [],
        },
        { skipRefresh: true, silent: true },
      )

      expect(result).toEqual({ pk: 500 })
      expect(mockedApi.get).not.toHaveBeenCalled()
      expect(mockedMessage).not.toHaveBeenCalled()
    })
  })

  describe('AccountManage', () => {
    it('filters by computed_direction, renders depth 4 accounts, and omits empty description parens', async () => {
      const store = useComLedger()
      store.comAccountList = [
        {
          pk: 1,
          code: '1000',
          name: '자산',
          description: '',
          parent: null,
          depth: 1,
          category: 'asset',
          direction: 'withdraw',
          direction_display: '출금',
          computed_direction: 'both',
          computed_direction_display: '입금/출금',
          is_category_only: true,
          is_transfer_fee: false,
          is_active: true,
          requires_affiliate: false,
          order: 1,
          full_path: '자산',
          children_count: 1,
        },
        {
          pk: 2,
          code: '1111',
          name: '세부항목',
          description: '',
          parent: 1,
          depth: 4,
          category: 'asset',
          direction: 'deposit',
          direction_display: '입금',
          computed_direction: 'deposit',
          computed_direction_display: '입금',
          is_category_only: false,
          is_transfer_fee: false,
          is_active: true,
          requires_affiliate: false,
          order: 2,
          full_path: '자산 > 현금성자산 > 보통예금 > 세부항목',
          children_count: 0,
        },
      ] as CompanyAccount[]

      const AlertModalStub = defineComponent({
        name: 'AlertModal',
        setup(_, { expose }) {
          expose({ callModal: vi.fn(), close: vi.fn() })
          return () => h('div', { class: 'alert-modal-inline' }, _)
        },
      })

      const wrapper = mount(AccountManage, {
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: {
            AlertModal: {
              template: '<div><slot /></div>',
              methods: { callModal: vi.fn(), close: vi.fn() },
            },
          },
        },
      })
      void AlertModalStub

      // 입금 탭 클릭 시 computed_direction === 'both' | 'deposit' 모두 유지되고 depth=4도 렌더링되어야 함
      const buttons = wrapper.findAll('.v-btn')
      await buttons[1].trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('자산')
      expect(wrapper.text()).toContain('세부항목')
      expect(wrapper.text()).not.toContain('()')
    })
  })

  describe('BankAccForm', () => {
    it('uses getPkDeparts PK values, injects company, and preserves form state when submit fails', async () => {
      seedPermissions([PERM.HQ_LEDGER_MANAGE])
      const comStore = useCompany()
      comStore.company = { pk: 7, name: '(주)테스트' } as typeof comStore.company
      comStore.allDepartList = [
        { pk: 12, company: 7, name: '재무팀' },
      ] as unknown as typeof comStore.allDepartList

      const ledgerStore = useComLedger()
      ledgerStore.bankCodeList = [{ pk: 3, code: '004', name: '국민은행' }]
      mockedApi.post.mockRejectedValueOnce(new Error('server error'))

      const wrapper = mount(BankAccForm, {
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: {
            DatePicker: DatePickerStub,
            ConfirmModal: {
              template: '<div class="confirm-stub"><slot /><slot name="footer" /></div>',
              methods: { callModal: vi.fn(), close: vi.fn() },
            },
            AlertModal: {
              template: '<div class="alert-stub" />',
              methods: { callModal: vi.fn(), close: vi.fn() },
            },
          },
        },
      })

      await flushPromises()
      const selects = wrapper.findAll('select')
      expect(selects[1].html()).toContain('value="12"')
      expect(selects[1].html()).not.toContain('value="재무팀"')

      await selects[0].setValue('3')
      await wrapper.find('input[placeholder="계좌별칭"]').setValue('운영계좌')

      const saveBtn = wrapper.findAll('button').find(b => b.text().trim() === '저장')
      expect(saveBtn).toBeDefined()
      await saveBtn!.trigger('click')
      await flushPromises()

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/ledger/company-bank-account/',
        expect.objectContaining({
          company: 7,
          bankcode: 3,
          depart: null,
          alias_name: '운영계좌',
        }),
      )
      // 실패 시 입력값이 초기화되지 않아야 함
      expect((wrapper.find('input[placeholder="계좌별칭"]').element as HTMLInputElement).value).toBe(
        '운영계좌',
      )
    })
  })

  describe('TransactionItem', () => {
    const accountsFixture: AccountPicker[] = [
      {
        value: 30,
        label: '소모품비',
        parent: 20,
        is_cate_only: false,
        depth: 3,
        category: 'expense',
        direction: '출금',
        req_affiliate: false,
      },
    ]

    const mountTransactionItem = (tx: BankTransaction, calculated = '2026-08-20') => {
      mockedApi.patch.mockResolvedValue({ data: tx })
      mockedApi.get.mockResolvedValue({ data: { count: 1, results: [tx] } })

      return mount(TransactionItem, {
        props: { transaction: tx, calculated },
        global: {
          plugins: [vuetify, CoreuiVue],
          provide: {
            comAccounts: computed(() => accountsFixture),
            affiliates: computed(() => [{ value: 1, label: '[PR]프로젝트A' }]),
          },
          stubs: {
            CIcon: CIconStub,
            LedgerAccountPicker: { template: '<div class="picker-stub" />' },
            AffiliateSelectModal: { template: '<div class="aff-modal-stub" />' },
          },
        },
      })
    }

    it('blocks account picker and note inline edit for read-only users', async () => {
      seedPermissions([PERM.HQ_LEDGER_READ])
      const wrapper = mountTransactionItem(makeTransaction({ deal_date: '2026-08-25' }), '2026-08-20')
      const ledgerStore = useComLedger()

      await wrapper.find('.account-cell > div').trigger('click')
      expect(ledgerStore.sharedEditingState).toBeNull()
      expect(document.body.style.overflow).toBe('')

      const cells = wrapper.findAll('td')
      await cells[1].trigger('dblclick')
      expect(ledgerStore.sharedEditingState).toBeNull()
    })

    it('blocks note inline edit on settled transactions while allowing account-only click, and cleans scroll lock on unmount', async () => {
      seedPermissions([PERM.HQ_LEDGER_UPDATE])
      // 2026-08-19 <= calculated(2026-08-20) -> 정산 마감 이전 거래
      const wrapper = mountTransactionItem(makeTransaction({ deal_date: '2026-08-19' }), '2026-08-20')
      const ledgerStore = useComLedger()

      // 메모 더블클릭은 마감일 lock으로 차단되어야 함 (10일 유예 없음)
      const cells = wrapper.findAll('td')
      await cells[1].trigger('dblclick')
      expect(ledgerStore.sharedEditingState).toBeNull()

      // 계정 클릭은 마감일 이후라도 update 권한으로 허용되어야 함 (백엔드 account-only 허용)
      await wrapper.find('.account-cell > div').trigger('click')
      expect(ledgerStore.sharedEditingState).toEqual({
        type: 'entry',
        pk: 201,
        field: 'account_affiliate',
      })
      expect(document.body.style.overflow).toBe('hidden')

      // 언마운트 시 스크롤 잠금 및 공유 상태 정리
      wrapper.unmount()
      expect(document.body.style.overflow).toBe('')
      expect(document.body.style.position).toBe('')
      expect(ledgerStore.sharedEditingState).toBeNull()
    })
  })

  describe('TransForm', () => {
    it('does not redirect out of edit mode on initial company hydration, and redirects on real company switch', async () => {
      seedPermissions([PERM.HQ_LEDGER_UPDATE, PERM.HQ_LEDGER_CREATE])
      const tx = makeTransaction()
      mockedApi.get.mockResolvedValue({ data: tx })

      const ledgerStore = useComLedger()
      ledgerStore.comAccountList = [
        {
          pk: 30,
          code: '5210',
          name: '소모품비',
          description: '',
          parent: null,
          depth: 3,
          category: 'expense',
          category_display: '비용',
          direction: 'withdraw',
          direction_display: '출금',
          computed_direction: 'withdraw',
          computed_direction_display: '출금',
          is_category_only: false,
          is_transfer_fee: false,
          is_active: true,
          requires_affiliate: false,
          order: 1,
          full_path: '소모품비',
          children_count: 0,
        },
      ]
      ledgerStore.comBankList = [
        {
          pk: 5,
          company: 1,
          depart: null,
          bankcode: 1,
          alias_name: '국민은행 주계좌',
          number: '111',
          holder: '회사',
          open_date: null,
          note: '',
          is_hide: false,
          inactive: false,
        } as CompanyBank,
      ]

      const router = await createComLedgerRouter('/com-ledger/manage/edit/101')
      const pushSpy = vi.spyOn(router, 'push')

      const wrapper = mount(TransForm, {
        props: { company: undefined as unknown as number },
        global: {
          plugins: [vuetify, CoreuiVue, router],
          directives: { tooltip: tooltipDirective },
          stubs: {
            CIcon: CIconStub,
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            BulkTransUploadDialog: { template: '<div />' },
            ExcelUploadDialog: { template: '<div />' },
            AccountManage: { template: '<div />', methods: { callModal: vi.fn() } },
            BankAcc: { template: '<div />', methods: { callModal: vi.fn() } },
          },
        },
      })

      await flushPromises()
      // 초기 company prop 주입: undefined -> 1
      await wrapper.setProps({ company: 1 })
      await flushPromises()
      expect(pushSpy).not.toHaveBeenCalled()

      // 실제 회사 전환: 1 -> 2
      await wrapper.setProps({ company: 2 })
      await flushPromises()
      expect(pushSpy).toHaveBeenCalledWith({ name: '본사 거래 내역' })
    })
  })

  describe('Status components', () => {
    it('Calculated renders only for HQ_LEDGER_MANAGE and disables when no transactions exist', async () => {
      seedPermissions([PERM.HQ_LEDGER_UPDATE])
      const updateOnly = mount(Calculated, {
        props: { calcDate: null, isCalculated: false, hasTransactions: false },
        global: { plugins: [vuetify, CoreuiVue] },
      })
      expect(updateOnly.find('button').exists()).toBe(false)

      seedPermissions([PERM.HQ_LEDGER_MANAGE])
      const managerView = mount(Calculated, {
        props: { calcDate: '2026-08-01', isCalculated: false, hasTransactions: false },
        global: { plugins: [vuetify, CoreuiVue] },
      })
      const btn = managerView.find('button')
      expect(btn.exists()).toBe(true)
      expect(btn.attributes('disabled')).toBeDefined()
    })

    it('StatusByAccount emits is-exist-balance on switch toggle and calculates totals accurately', async () => {
      const store = useComLedger()
      store.comLedgerBalanceByAccList = [
        {
          bank_acc: '보통예금1',
          bank_num: '111-222',
          date_inc: 3000,
          date_out: 1000,
          inc_sum: 10000,
          out_sum: 4000,
        },
      ]

      const wrapper = mount(StatusByAccount, {
        props: { date: '2026-08-15', isBalance: 'true' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: CIconStub },
        },
      })

      expect(wrapper.text()).toContain('4,000') // 전일잔고 = (10000-4000)-(3000-1000)
      expect(wrapper.text()).toContain('6,000') // 금일잔고 = 10000-4000

      const switchComp = wrapper.findComponent({ name: 'CFormSwitch' })
      switchComp.vm.$emit('update:modelValue', false)
      await flushPromises()
      expect(wrapper.emitted('is-exist-balance')).toEqual([[false]])
    })

    it('MonthlySummaryTable displays dash for total share when grandTotal.cur is 0', () => {
      const zeroSummary: ComMonthlySummary = {
        company: 1,
        from_date: '2026-08-01',
        to_date: '2026-08-15',
        periods: {
          prev: { from: '2026-07-01', to: '2026-07-15' },
          cur: { from: '2026-08-01', to: '2026-08-15' },
          ytd: { from: '2026-01-01', to: '2026-08-15' },
        },
        opening_balance: 0,
        closing_balance: 0,
        income: {
          revenue: { groups: [], total: { prev: 0, cur: 0, ytd: 0 } },
          other: { groups: [], total: { prev: 0, cur: 0, ytd: 0 } },
          total: { prev: 0, cur: 0, ytd: 0 },
        },
        expense: {
          cost: { groups: [], total: { prev: 0, cur: 0, ytd: 0 } },
          other: { groups: [], total: { prev: 0, cur: 0, ytd: 0 } },
          total: { prev: 0, cur: 0, ytd: 0 },
        },
        operating_net: { prev: 0, cur: 0, ytd: 0 },
        net: { prev: 0, cur: 0, ytd: 0 },
        transfer: { in: { prev: 0, cur: 0, ytd: 0 }, out: { prev: 0, cur: 0, ytd: 0 } },
        cancel: { in: { prev: 0, cur: 0, ytd: 0 }, out: { prev: 0, cur: 0, ytd: 0 } },
        unclassified: { in: { prev: 0, cur: 0, ytd: 0 }, out: { prev: 0, cur: 0, ytd: 0 } },
        bank_flow: { in: { prev: 0, cur: 0, ytd: 0 }, out: { prev: 0, cur: 0, ytd: 0 } },
        affiliates: [],
      }

      const wrapper = mount(MonthlySummaryTable, {
        props: { summary: zeroSummary, direction: 'income' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: CIconStub },
        },
      })

      const totalCells = wrapper.find('.total-row').findAll('th')
      expect(totalCells[totalCells.length - 1].text().trim()).toBe('-')
    })

    it('MonthlySummary disables next month button for current month and DateChoicer avoids double emit', async () => {
      const todayMonth = new Date(Date.now() + 32400000).toISOString().slice(0, 7)
      const msWrapper = mount(MonthlySummary, {
        props: { date: `${todayMonth}-15`, company: 1, periodMode: 'mtd' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: CIconStub },
        },
      })
      const nextBtn = msWrapper.findAll('button').find(b => b.text().includes('익월'))
      expect(nextBtn?.attributes('disabled')).toBeDefined()

      const dcWrapper = mount(DateChoicer, {
        props: { value: '2026-08-10' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { DatePicker: DatePickerStub },
        },
      })
      await dcWrapper.find('input').setValue('')
      await flushPromises()
      expect(dcWrapper.emitted('set-date')?.length).toBe(1)
    })

    it('TabSelect clamps invalid localStorage values and CashListByDate labels unclassified entries', () => {
      localStorage.setItem('comLedgerStatus', '999')
      const tabWrapper = mount(TabSelect, {
        global: { plugins: [vuetify, CoreuiVue] },
      })
      const activeBtns = tabWrapper.findAll('.nav-link.active')
      expect(activeBtns[0].text()).toContain('계좌별 자금현황')

      const store = useComLedger()
      store.dateLedgerTransactions = [
        makeTransaction({
          pk: 88,
          sort: 1,
          sort_name: '입금',
          accounting_entries: [],
        }),
      ]
      const cashWrapper = mount(CashListByDate, {
        props: { date: '2026-08-15' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: CIconStub },
        },
      })
      expect(cashWrapper.text()).toContain('(미분류)')
    })
  })
})
