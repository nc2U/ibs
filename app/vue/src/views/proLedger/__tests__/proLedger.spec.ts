import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { errorHandle, message } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { useProLedger } from '@/store/pinia/proLedger'
import type { AccountPicker } from '@/store/types/comLedger'
import type { ProBankTrans, ProjectBank } from '@/store/types/proLedger'
import { PERM, type PermissionCode } from '@/store/constants/permissions'
import StatusIndex from '../Status/Index.vue'
import Calculated from '../Status/components/Calculated.vue'
import StatusByAccount from '../Status/components/StatusByAccount.vue'
import SummaryForBudget from '../Status/components/SummaryForBudget.vue'
import ManageIndex from '../Manage/Index.vue'
import ImprestIndex from '../Imprest/Index.vue'
import BankAcc from '../Manage/components/BankAcc.vue'
import BankAccForm from '../Manage/components/BankAccForm.vue'
import ListController from '../Manage/components/ListController.vue'
import ProTransItem from '../Manage/components/ProTransItem.vue'
import ProAccountEntry from '../Manage/components/ProAccountEntry.vue'
import BankTransactionRow, {
  type BankTransactionData,
} from '../Manage/components/BankTransactionRow.vue'
import BulkTransUploadDialog from '../Manage/components/BulkTransUploadDialog.vue'
import ProTransForm from '../Manage/components/ProTransForm.vue'

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

const ContentHeaderStub = defineComponent({
  name: 'ContentHeader',
  emits: ['proj-select'],
  template: '<div class="content-header-stub" />',
})

const ContentBodyStub = defineComponent({
  name: 'ContentBody',
  template: '<div class="content-body-stub"><slot /></div>',
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

const MultiSelectStub = defineComponent({
  name: 'MultiSelect',
  props: { modelValue: { type: Number, default: null } },
  emits: ['update:modelValue', 'select', 'clear'],
  template:
    '<div class="multiselect-stub"><button type="button" class="ms-clear" @click="$emit(\'clear\')">clear</button></div>',
})

const ConfirmModalStub = defineComponent({
  name: 'ConfirmModal',
  emits: ['confirm-func', 'close'],
  data: () => ({ open: false }),
  methods: {
    callModal() {
      this.open = true
    },
    close() {
      this.open = false
      this.$emit('close')
    },
  },
  template:
    '<div class="confirm-modal-stub" :data-open="open"><slot /><slot name="footer" /><button type="button" class="confirm-ok" @click="$emit(\'confirm-func\')">ok</button></div>',
})

const AlertModalStub = defineComponent({
  name: 'AlertModal',
  methods: {
    callModal() {},
    close() {},
  },
  template: '<div class="alert-modal-stub"><slot /></div>',
})

const seedProjectPerms = (perms: PermissionCode[], isSuperuser = false, projectPk = 10) => {
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
      pk: projectPk,
      name: 'PR-10',
      slug: 'pr-10',
      type: '2',
      project: projectPk,
      my_perms: perms,
    } as unknown as (typeof workStore.myProjects)[number],
  ]

  const permStore = usePermission()
  permStore.setProjectPermissions(perms)

  const projectStore = useProject()
  projectStore.project = { pk: projectPk, name: '테스트 프로젝트' } as typeof projectStore.project
}

const makeProTrans = (overrides: Partial<ProBankTrans> = {}): ProBankTrans => ({
  pk: 101,
  transaction_id: 'ptx-101',
  project: 10,
  bank_account: 5,
  bank_account_name: '분양수입계좌',
  deal_date: '2026-08-15',
  amount: 100000,
  sort: 2,
  sort_name: '출금',
  content: '공사비 지급',
  note: '초기 메모',
  creator: 1,
  creator_name: 'tester',
  created_at: '2026-08-15T10:00:00Z',
  updated_at: '2026-08-15T10:00:00Z',
  is_balanced: true,
  accounting_entries: [
    {
      pk: 201,
      transaction_id: 'ptx-101',
      project: 10,
      sort: 2,
      sort_name: '출금',
      account: 30,
      account_name: '외주공사비',
      account_code: '5110',
      account_full_path: '비용 > 공사비 > 외주공사비',
      contract: null,
      contract_display: null,
      contractor: null,
      contractor_display: null,
      amount: 100000,
      trader: 'OO건설',
      evidence_type: '1',
      evidence_type_display: '세금계산서',
      contract_payment: null,
      created_at: '2026-08-15T10:00:00Z',
      updated_at: '2026-08-15T10:00:00Z',
    },
  ],
  ...overrides,
})

const createProLedgerRouter = async (initialPath = '/project-ledger/manage') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/project-ledger/status', name: '정산 현황 관리', component: { template: '<div />' } },
      { path: '/project-ledger/manage', name: '거래 내역 관리', component: { template: '<div />' } },
      {
        path: '/project-ledger/manage/create',
        name: '거래 내역 관리 - 생성',
        component: { template: '<div />' },
      },
      {
        path: '/project-ledger/manage/:transId(\\d+)/update',
        name: '거래 내역 관리 - 수정',
        component: { template: '<div />' },
      },
      {
        path: '/project-ledger/imprest',
        name: '운영비 내역 관리',
        component: { template: '<div />' },
      },
      {
        path: '/project-ledger/imprest/create',
        name: '운영비 내역 관리 - 생성',
        component: { template: '<div />' },
      },
      {
        path: '/project-ledger/imprest/:transId(\\d+)/update',
        name: '운영비 내역 관리 - 수정',
        component: { template: '<div />' },
      },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('proLedger module', () => {
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

  describe('useProLedger Pinia store', () => {
    it('fetches bank codes and project bank accounts with limit 200 and exposes getImprestProBanks', async () => {
      const store = useProLedger()
      mockedApi.get
        .mockResolvedValueOnce({ data: { results: [{ pk: 1, code: '004', name: '국민' }] } })
        .mockResolvedValueOnce({
          data: {
            results: [
              { pk: 11, project: 10, alias_name: '일반계좌', is_imprest: false },
              { pk: 12, project: 10, alias_name: '운영비계좌', is_imprest: true },
            ],
          },
        })

      await store.fetchBankCodeList()
      await store.fetchProBankAccList(10)

      expect(mockedApi.get).toHaveBeenNthCalledWith(1, '/ledger/bank-code/', {
        params: { limit: 200 },
      })
      expect(mockedApi.get).toHaveBeenNthCalledWith(2, '/ledger/project-bank-account/', {
        params: { project: 10, is_hide: false, inactive: false, limit: 200 },
      })
      expect(store.bankCodeList).toHaveLength(1)
      expect(store.getImprestProBanks).toEqual([{ value: 12, label: '운영비계좌' }])
    })

    it('findProBankTransPage forwards is_imprest, account_category, account_name, contract and limit', async () => {
      const store = useProLedger()
      mockedApi.get.mockResolvedValueOnce({ data: { page: 4 } })

      const page = await store.findProBankTransPage(99, {
        project: 10,
        is_imprest: 'true',
        account_category: 'expense',
        account_name: '공사',
        contract: 55,
        limit: 15,
      })

      expect(page).toBe(4)
      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/project-transaction/find_page/', {
        params: {
          highlight_id: 99,
          project: 10,
          is_imprest: 'true',
          account_category: 'expense',
          account_name: '공사',
          contract: 55,
          limit: 15,
        },
      })
    })

    it('fetchProLedgerBalanceByAccList forwards direct param and omits undefined date', async () => {
      const store = useProLedger()
      mockedApi.get.mockResolvedValueOnce({ data: [] })

      await store.fetchProLedgerBalanceByAccList({
        project: 10,
        direct: 'i',
        is_balance: '',
      })

      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/project-transaction/balance_by_account/', {
        params: {
          project: 10,
          direct: 'i',
        },
      })
    })

    it('createProBankTrans / updateProBankTrans / deleteProBankTrans return boolean and call errorHandle on failure', async () => {
      const store = useProLedger()
      mockedApi.post.mockRejectedValueOnce(new Error('bad payload'))
      mockedApi.put.mockRejectedValueOnce(new Error('update failed'))
      mockedApi.delete.mockRejectedValueOnce(new Error('delete failed'))

      const okCreate = await store.createProBankTrans({
        project: 10,
        deal_date: '2026-08-15',
        bank_account: 5,
        amount: 1000,
        sort: 2,
        content: '적요',
        accounting_entries: [],
      })
      const okUpdate = await store.updateProBankTrans({
        pk: 1,
        project: 10,
        deal_date: '2026-08-15',
        bank_account: 5,
        amount: 1000,
        sort: 2,
        content: '적요',
        accounting_entries: [],
      })
      const okDelete = await store.deleteProBankTrans(1)

      expect(okCreate).toBe(false)
      expect(okUpdate).toBe(false)
      expect(okDelete).toBe(false)
      expect(mockedErrorHandle).toHaveBeenCalledTimes(3)
    })
  })

  describe('Auth guards & Page index lifecycles', () => {
    it('blocks unauthorized users on Status, Manage, and Imprest without firing API calls', async () => {
      seedProjectPerms([], false, 10)
      const router = await createProLedgerRouter('/project-ledger/manage')

      for (const Comp of [StatusIndex, ManageIndex, ImprestIndex]) {
        const wrapper = mount(Comp, {
          global: {
            plugins: [router, vuetify, CoreuiVue],
            directives: { tooltip: tooltipDirective },
            stubs: {
              Loading: true,
              ContentHeader: ContentHeaderStub,
              ContentBody: ContentBodyStub,
              CIcon: CIconStub,
            },
          },
        })
        await flushPromises()
        expect(wrapper.text()).toContain('권한이 없습니다')
      }
      expect(mockedApi.get).not.toHaveBeenCalled()
    })

    it('Manage/Index loads base data once with highlight_id and forwards is_imprest to find_page', async () => {
      seedProjectPerms([PERM.LEDGER_READ], false, 10)
      const router = await createProLedgerRouter('/project-ledger/manage?project=10&highlight_id=88')

      mockedApi.get.mockImplementation((url: string) => {
        if (url === '/ledger/project-transaction/find_page/') return Promise.resolve({ data: { page: 2 } })
        if (url === '/project/10/') return Promise.resolve({ data: { pk: 10, name: '테스트 프로젝트' } })
        return Promise.resolve({ data: { count: 0, results: [] } })
      })

      mount(ManageIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            Loading: true,
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            CIcon: CIconStub,
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            MultiSelect: MultiSelectStub,
          },
        },
      })
      await flushPromises()

      const projectCalls = mockedApi.get.mock.calls.filter(c => c[0] === '/project/10/')
      expect(projectCalls).toHaveLength(1)
      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/project-transaction/find_page/', {
        params: expect.objectContaining({
          highlight_id: 88,
          project: 10,
          is_imprest: 'false',
          limit: 15,
        }),
      })
    })

    it('Imprest/Index filters transactions with is_imprest=true on mount', async () => {
      seedProjectPerms([PERM.LEDGER_READ], false, 10)
      const router = await createProLedgerRouter('/project-ledger/imprest')

      mockedApi.get.mockImplementation((url: string) => {
        if (url === '/project/10/') return Promise.resolve({ data: { pk: 10, name: '테스트 프로젝트' } })
        return Promise.resolve({ data: { count: 0, results: [] } })
      })

      mount(ImprestIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            Loading: true,
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            CIcon: CIconStub,
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            MultiSelect: MultiSelectStub,
          },
        },
      })
      await flushPromises()

      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/project-transaction/', {
        params: expect.objectContaining({ project: 10, is_imprest: 'true' }),
      })
    })

    it('Status/Index passes direct and is_balance flags cleanly and skips checkBalance without last deal date', async () => {
      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_MANAGE], false, 10)
      mockedApi.get.mockImplementation((url: string) => {
        if (url === '/project/10/') return Promise.resolve({ data: { pk: 10, name: '테스트 프로젝트' } })
        if (url === '/ledger/project-transaction/balance_by_account/') return Promise.resolve({ data: [] })
        return Promise.resolve({ data: { count: 0, results: [] } })
      })

      const wrapper = mount(StatusIndex, {
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            Loading: true,
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            CIcon: CIconStub,
            DatePicker: DatePickerStub,
          },
        },
      })
      await flushPromises()

      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/project-transaction/balance_by_account/', {
        params: expect.objectContaining({ project: 10, direct: '0', is_balance: 'true' }),
      })

      // Direct switch toggle updates balance_by_account direct='i'
      await wrapper.findComponent(StatusByAccount).vm.$emit('direct-balance', true)
      await flushPromises()

      expect(mockedApi.get).toHaveBeenLastCalledWith(
        '/ledger/project-transaction/balance_by_account/',
        {
          params: expect.objectContaining({ project: 10, direct: 'i' }),
        },
      )
      expect(mockedApi.post).not.toHaveBeenCalled()
    })
  })

  describe('Status components', () => {
    it('Calculated requires LEDGER_MANAGE and disables button without transactions', async () => {
      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_UPDATE], false, 10)
      const wReadOnly = mount(Calculated, {
        props: { project: 10, hasTransactions: true, isCalculated: false },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { ConfirmModal: ConfirmModalStub },
        },
      })
      expect(wReadOnly.findComponent({ name: 'CAlert' }).exists()).toBe(false)
      expect(wReadOnly.text()).not.toContain('당일잔고 정산확인')

      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_MANAGE], false, 10)
      const wManage = mount(Calculated, {
        props: { project: 10, hasTransactions: false, isCalculated: false },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { ConfirmModal: ConfirmModalStub },
        },
      })
      const btn = wManage.findComponent({ name: 'CAlert' }).find('button')
      expect(btn.attributes('disabled')).toBeDefined()
      expect(wManage.html()).not.toContain('10일')
    })

    it('SummaryForBudget avoids spurious PATCH on unmodified blur and parses comma-formatted numbers', async () => {
      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_UPDATE], false, 10)
      const projectStore = useProject()
      projectStore.statusOutBudgetList = [
        {
          pk: 5,
          account_opt: '토지비',
          budget: 1000000,
          revised_budget: null,
          account: { pk: 1, name: '토지구입비', parent: { pk: 2, name: '사업용지', children_pks: [1] } },
        } as never,
      ]

      const wrapper = mount(SummaryForBudget, {
        props: { project: 10, date: '2026-08-20' },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: { CIcon: CIconStub },
        },
      })

      const cell = wrapper.findAll('td.bg-amber-lighten-5')[0]
      await cell.trigger('dblclick')
      const input = wrapper.find('input[type="text"]')
      await input.trigger('blur')
      expect(wrapper.emitted('patch-budget')).toBeUndefined()

      await cell.trigger('dblclick')
      const input2 = wrapper.find('input[type="text"]')
      await input2.setValue('2,500,000')
      await input2.trigger('keydown.enter')
      expect(wrapper.emitted('patch-budget')?.[0]).toEqual([5, 2500000, true])
    })

    it('StatusByAccount computes balance totals accurately', () => {
      const store = useProLedger()
      store.proLedgerBalanceByAccList = [
        {
          bank_id: 1,
          bank_acc: '일반통장',
          bank_num: '111-222',
          is_imprest: false,
          inc_sum: 1000000,
          out_sum: 200000,
          date_inc: 300000,
          date_out: 50000,
          balance: 800000,
        },
      ]

      const wrapper = mount(StatusByAccount, {
        props: { date: '2026-08-20', isBalance: 'true', direct: '0' },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: CIconStub },
        },
      })

      expect(wrapper.text()).toContain('111-222')
      expect(wrapper.text()).toContain('800,000')
      expect(wrapper.text()).toContain('550,000')
    })
  })

  describe('BankAccForm & BankAcc', () => {
    it('fetches bankCodeList, preserves typed edits across updates, injects project, and sets is_imprest', async () => {
      seedProjectPerms([PERM.LEDGER_MANAGE], false, 10)
      mockedApi.get.mockResolvedValueOnce({
        data: { results: [{ pk: 3, code: '004', name: '국민은행' }] },
      })

      const wrapper = mount(BankAccForm, {
        props: {
          project: 10,
          isImprest: true,
          bankAcc: {
            pk: 7,
            project: 10,
            bankcode: 3,
            alias_name: '기존계좌',
            number: '111',
            holder: '예금주',
            open_date: null,
            note: '',
            is_hide: false,
            inactive: false,
            directpay: false,
            is_imprest: true,
          },
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            DatePicker: DatePickerStub,
            ConfirmModal: ConfirmModalStub,
            AlertModal: AlertModalStub,
          },
        },
      })
      await flushPromises()

      expect(mockedApi.get).toHaveBeenCalledWith('/ledger/bank-code/', { params: { limit: 200 } })

      const aliasInput = wrapper.find('input[placeholder="계좌별칭"]')
      await aliasInput.setValue('수정된별칭')
      // Trigger re-render by changing non-bankAcc prop or slot update
      await wrapper.setProps({ project: 10 })
      expect((aliasInput.element as HTMLInputElement).value).toBe('수정된별칭')
    })

    it('BankAcc filters to is_imprest accounts when isImprest prop is true', () => {
      const store = useProLedger()
      store.allProBankList = [
        { pk: 1, project: 10, alias_name: '일반계좌', number: '1', is_imprest: false } as ProjectBank,
        { pk: 2, project: 10, alias_name: '운영비계좌', number: '2', is_imprest: true } as ProjectBank,
      ]

      const wrapper = mount(BankAcc, {
        props: { project: 10, isImprest: true },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            AlertModal: AlertModalStub,
            BankAccForm: true,
          },
        },
      })

      expect(wrapper.text()).toContain('운영비계좌')
      expect(wrapper.text()).not.toContain('일반계좌')
    })
  })

  describe('ListController', () => {
    it('clears only contract on MultiSelect @clear and filters banks in imprestOnly mode', async () => {
      const store = useProLedger()
      store.proBankTransCount = 3
      const banks: ProjectBank[] = [
        { pk: 1, project: 10, alias_name: '일반계좌', number: '1', is_imprest: false } as ProjectBank,
        { pk: 2, project: 10, alias_name: '전도금계좌', number: '2', is_imprest: true } as ProjectBank,
      ]

      const wrapper = mount(ListController, {
        props: {
          project: 10,
          imprestOnly: true,
          dataFilter: { search: '공사비', contract: 99 },
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          provide: {
            proAccounts: computed(() => []),
            allProBankList: computed(() => banks),
            proBankTransCount: computed(() => store.proBankTransCount),
          },
          stubs: {
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            MultiSelect: MultiSelectStub,
          },
        },
      })

      const bankSelect = wrapper.findAll('select')[2]
      expect(bankSelect.html()).toContain('전도금계좌')
      expect(bankSelect.html()).not.toContain('일반계좌')

      await wrapper.find('.ms-clear').trigger('click')
      await flushPromises()

      const emitted = wrapper.emitted('list-filtering')
      expect(emitted).toBeTruthy()
      expect(emitted![0][0]).toEqual(
        expect.objectContaining({
          contract: null,
          search: '공사비',
          is_imprest: 'true',
        }),
      )

      // Project change resets form without spurious extra emit
      const beforeCount = wrapper.emitted('list-filtering')?.length ?? 0
      await wrapper.setProps({ project: 20 })
      await flushPromises()
      expect(wrapper.emitted('list-filtering')?.length ?? 0).toBe(beforeCount)
    })
  })

  describe('ProTransItem inline editing & settlement lock', () => {
    const accountsFixture: AccountPicker[] = [
      {
        value: 30,
        label: '외주공사비',
        parent: 20,
        is_cate_only: false,
        depth: 3,
        category: 'expense',
        direction: '출금',
        requires_contract: false,
        is_related_contractor: false,
      },
    ]

    it('does not lock body scroll when read-only user clicks account cell', async () => {
      seedProjectPerms([PERM.LEDGER_READ], false, 10)
      const router = await createProLedgerRouter()
      const wrapper = mount(ProTransItem, {
        props: { proTrans: makeProTrans(), project: 10, calculated: '2026-08-20' },
        global: {
          plugins: [router, vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          provide: {
            proAccounts: computed(() => accountsFixture),
            getContracts: computed(() => []),
            getAllContractors: computed(() => []),
          },
          stubs: { Teleport: true, BaseSelectModal: true },
        },
      })

      await wrapper.find('.account-cell > div').trigger('click')
      expect(document.body.style.position).toBe('')
      expect(useProLedger().sharedEditingState).toBeNull()
    })

    it('blocks text inline edit on settled transactions for LEDGER_UPDATE without LEDGER_MANAGE', async () => {
      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_UPDATE], false, 10)
      const router = await createProLedgerRouter()
      const wrapper = mount(ProTransItem, {
        props: {
          proTrans: makeProTrans({ deal_date: '2026-08-15' }),
          project: 10,
          calculated: '2026-08-20',
        },
        global: {
          plugins: [router, vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          provide: {
            proAccounts: computed(() => accountsFixture),
            getContracts: computed(() => []),
            getAllContractors: computed(() => []),
          },
          stubs: { Teleport: true, BaseSelectModal: true },
        },
      })

      // Settled date: dblclick on note does NOT enter edit mode
      await wrapper.findAll('td')[1].trigger('dblclick')
      expect(useProLedger().sharedEditingState).toBeNull()

      // Account click opens picker and unlocks body scroll cleanly on unmount
      await wrapper.find('.account-cell > div').trigger('click')
      expect(document.body.style.position).toBe('fixed')
      wrapper.unmount()
      expect(document.body.style.position).toBe('')
      expect(useProLedger().sharedEditingState).toBeNull()
    })
  })

  describe('ProAccountEntry, BankTransactionRow, BulkTransUploadDialog & ProTransForm', () => {
    it('ProAccountEntry checks transferFeePk.value safely and warns via message()', async () => {
      seedProjectPerms([PERM.LEDGER_CREATE], false, 10)
      const wrapper = mount(ProAccountEntry, {
        props: {
          sort: 2,
          project: 10,
          transAmount: 50000,
          displayRows: [{ account: 30, amount: 50000, trader: '거래처', evidence_type: '1' }],
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          provide: {
            proAccounts: computed(() => []),
            getContracts: computed(() => []),
            getAllContractors: computed(() => []),
            transferFeePk: computed(() => undefined),
          },
          stubs: { LedgerAccount: LedgerAccountStub, MultiSelect: MultiSelectStub },
        },
      })

      const icons = wrapper.findAll('.v-icon, i')
      const plusIcon = icons.find(i => i.classes().includes('mdi-playlist-plus'))
      expect(plusIcon).toBeDefined()
      await plusIcon!.trigger('click')
      expect(mockedMessage).toHaveBeenCalledWith(
        'warning',
        '알림!',
        expect.stringContaining('이체수수료'),
      )
    })

    it('BankTransactionRow preserves uid across row operations', async () => {
      seedProjectPerms([PERM.LEDGER_CREATE], false, 10)
      const tx: BankTransactionData = {
        uid: 42,
        bankForm: {
          deal_date: '2026-08-20',
          note: '',
          bank_account: 1,
          content: '자금지출',
          sort: 2,
          amount: 10000,
        },
        entries: [{ account: 30, trader: 'OO', amount: 10000, evidence_type: '0' }],
      }

      const wrapper = mount(BankTransactionRow, {
        props: {
          transaction: tx,
          index: 0,
          project: 10,
          bankAccounts: [{ value: 1, label: '계좌1' }],
          proAccounts: [],
          getContracts: [],
          getAllContractors: [],
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          provide: { transferFeePk: computed(() => 99) },
          stubs: {
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            MultiSelect: MultiSelectStub,
          },
        },
      })

      const buttons = wrapper.findAll('button')
      const addEntryBtn = buttons[buttons.length - 1]
      await addEntryBtn.trigger('click')
      const emitted = wrapper.emitted('update:transaction')
      expect(emitted).toBeTruthy()
      expect((emitted![0][0] as BankTransactionData).uid).toBe(42)
    })

    it('BulkTransUploadDialog emits update:result without mutating props.result', async () => {
      const originalResult = {
        fileFormat: 'ibs_template' as const,
        transactions: [
          {
            key: '1',
            firstRow: 2,
            bankForm: {
              deal_date: '2026-08-20',
              bank_account: null,
              bank_account_name: '',
              sort: 2 as const,
              amount: 10000,
              content: '테스트',
              note: '',
            },
            entries: [
              {
                rowNumber: 2,
                account: null,
                account_name: '',
                trader: '거래처',
                amount: 10000,
                evidence_type: '0' as const,
                contract: null,
                contract_name: '',
                errors: ['계정 미지정'],
                warnings: [],
              },
            ],
            entryTotal: 10000,
            isBalanced: true,
            isDuplicate: false,
            errors: ['거래계좌 미지정'],
            warnings: [],
            isValid: false,
          },
        ],
        summary: {
          transactionCount: 1,
          validTransactions: 0,
          invalidTransactions: 1,
          entryCount: 1,
          duplicateCount: 0,
        },
        isValid: false,
      }

      const wrapper = mount(BulkTransUploadDialog, {
        props: {
          modelValue: true,
          result: originalResult,
          hasExisting: false,
          bankAccounts: [{ value: 1, label: '운영계좌' }],
          accounts: [{ value: 30, label: '소모품비', is_cate_only: false }],
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: { VDialog: { template: '<div v-if="modelValue"><slot /></div>', props: ['modelValue'] } },
        },
      })

      expect(wrapper.text()).toContain('대량 거래 입력')
      expect(originalResult.transactions[0].bankForm.bank_account).toBeNull()
    })

    it('ProTransForm keeps unsaved rows on partial multi-submit failure and clears on full success', async () => {
      seedProjectPerms([PERM.LEDGER_READ, PERM.LEDGER_CREATE], false, 10)
      const router = await createProLedgerRouter('/project-ledger/manage/create')
      const proLedgerStore = useProLedger()
      proLedgerStore.proBankList = [
        {
          pk: 1,
          project: 10,
          bankcode: 3,
          alias_name: '일반통장',
          number: '111',
          holder: '',
          open_date: null,
          note: '',
          is_hide: false,
          inactive: false,
          directpay: false,
          is_imprest: false,
        },
      ]
      proLedgerStore.proAccountList = [
        {
          pk: 30,
          code: '5110',
          name: '공사비',
          description: '',
          parent: null,
          depth: 2,
          category: 'expense',
          category_display: '비용',
          direction: 'withdraw',
          direction_display: '출금',
          computed_direction: 'withdraw',
          computed_direction_display: '출금',
          is_category_only: false,
          is_transfer_fee: false,
          is_active: true,
          order: 1,
          is_payment: false,
          requires_contract: false,
          is_related_contractor: false,
          full_path: '비용 > 공사비',
          children_count: 0,
        },
      ]
      useContract().contractList = []
      usePayment().payOrderList = [{ pk: 1, alias_name: '1차 계약금' } as never]

      mockedApi.get.mockResolvedValue({ data: { count: 0, results: [] } })
      mockedApi.post.mockRejectedValueOnce(new Error('save failed'))

      const pushSpy = vi.spyOn(router, 'push')
      const wrapper = mount(ProTransForm, {
        props: { project: 10 },
        global: {
          plugins: [router, vuetify, CoreuiVue],
          directives: { tooltip: tooltipDirective },
          stubs: {
            CIcon: CIconStub,
            DatePicker: DatePickerStub,
            LedgerAccount: LedgerAccountStub,
            MultiSelect: MultiSelectStub,
            ConfirmModal: ConfirmModalStub,
            AlertModal: AlertModalStub,
            AccountManage: true,
            BankAcc: true,
            ExcelUploadDialog: true,
            BulkTransUploadDialog: true,
          },
        },
      })
      await flushPromises()

      // Fill required fields for 1 transaction
      await wrapper.find('select').setValue('1') // bank_account
      await wrapper.find('input[placeholder="적요"]').setValue('공사비 지급')
      await wrapper.find('input[placeholder="금액"]').setValue('50000')
      await wrapper.find('.ledger-account-stub').setValue('30')
      await wrapper.find('input[placeholder="분류 금액"]').setValue('50000')
      const selects = wrapper.findAll('select')
      await selects[selects.length - 1].setValue('0') // evidence_type

      // Attempt save when API fails -> must NOT navigate away
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(mockedApi.post).toHaveBeenCalledTimes(1)
      expect(pushSpy).not.toHaveBeenCalled()

      // Retry when API succeeds -> navigates cleanly
      mockedApi.post.mockResolvedValueOnce({ data: { bank_transaction: { pk: 1 } } })
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(pushSpy).toHaveBeenCalledWith({ name: '거래 내역 관리' })
    })
  })
})
