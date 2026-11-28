import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
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
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { useSales } from '@/store/pinia/sales'
import type {
  CommissionPolicy,
  CommissionPayout,
  ContractSalesAgent,
  SalesPerson,
  SettlementPeriod,
} from '@/store/types/sales'
import { PERM, type PermissionCode } from '@/store/constants/permissions'
import SalesAuthGuard from '@/components/AuthGuard/SalesAuthGuard.vue'
import PerformanceIndex from '../Performance/Index.vue'
import ContractAgentModal from '../Performance/components/ContractAgentModal.vue'
import PolicyIndex from '../Policy/Index.vue'
import PolicyFormModal from '../Policy/components/PolicyFormModal.vue'
import SettlementIndex from '../Settlement/Index.vue'
import PeriodFormModal from '../Settlement/components/PeriodFormModal.vue'
import PayoutIndex from '../Payout/Index.vue'
import PersonPayoutHistoryModal from '../Payout/components/PersonPayoutHistoryModal.vue'
import OrganizationIndex from '../Organization/Index.vue'
import PersonList from '../Organization/components/PersonList.vue'
import PersonFormModal from '../Organization/components/PersonFormModal.vue'
import PersonDocumentModal from '../Organization/components/PersonDocumentModal.vue'

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

const CIconStub = defineComponent({ name: 'CIcon', template: '<span />' })
const ContentHeaderStub = defineComponent({ name: 'ContentHeader', template: '<div />' })
const ContentBodyStub = defineComponent({
  name: 'ContentBody',
  template: '<div><slot /></div>',
})
const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: { modelValue: { type: String, default: '' }, disabled: { type: Boolean, default: false } },
  emits: ['update:modelValue'],
  template:
    '<input class="datepicker-stub" :value="modelValue" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
})
const FormModalStub = defineComponent({
  name: 'FormModal',
  data: () => ({ isOpen: false }),
  methods: {
    callModal() {
      this.isOpen = true
    },
    close() {
      this.isOpen = false
    },
  },
  template:
    '<div v-if="isOpen" class="form-modal-stub"><slot name="header" /><slot /></div>',
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
  template:
    '<div v-if="isOpen" class="confirm-modal-stub"><slot /><slot name="footer" /></div>',
})

const seedSalesProjectPerms = (
  permsByProj: Record<number, PermissionCode[]>,
  activeProjectPk: number | null = 10,
  isSuperuser = false,
) => {
  const accountStore = useAccount()
  accountStore.userInfo = {
    pk: 1,
    username: 'sales-tester',
    email: 'sales@example.com',
    is_active: true,
    is_superuser: isSuperuser,
    work_manager: false,
    has_staff: true,
  } as unknown as typeof accountStore.userInfo

  const workStore = useWork()
  workStore.myProjects = Object.entries(permsByProj).map(
    ([projId, myPerms], idx) =>
      ({
        pk: Number(projId) + 100 + idx,
        name: `PR-${projId}`,
        slug: `pr-${projId}`,
        type: '2',
        status: '1',
        project: Number(projId),
        my_perms: myPerms,
      }) as unknown as (typeof workStore.myProjects)[number],
  )

  const permStore = usePermission()
  if (activeProjectPk && permsByProj[activeProjectPk]) {
    permStore.setProjectPermissions(permsByProj[activeProjectPk])
  } else {
    permStore.setProjectPermissions([])
  }

  const projectStore = useProject()
  projectStore.project = activeProjectPk
    ? ({ pk: activeProjectPk, name: `프로젝트 ${activeProjectPk}` } as typeof projectStore.project)
    : null
}

const makePeriod = (overrides: Partial<SettlementPeriod> = {}): SettlementPeriod => ({
  id: 1,
  project: 10,
  title: '2026년 9월 1차',
  start_date: '2026-09-01',
  end_date: '2026-09-30',
  payout_date: '2026-10-05',
  status: '1',
  status_display: '정산 작성 중',
  total_contracts: 2,
  total_gross_amount: 5000000,
  total_tax_amount: 165000,
  total_net_amount: 4835000,
  agency_fee_total: 1000000,
  billing_supply_price: 6000000,
  billing_vat: 600000,
  billing_total_amount: 6600000,
  payout_count: 1,
  agency_payout_count: 1,
  created_by: 1,
  created_at: '2026-09-30T10:00:00Z',
  updated_at: '2026-09-30T10:00:00Z',
  ...overrides,
})

const makePerson = (overrides: Partial<SalesPerson> = {}): SalesPerson => ({
  id: 7,
  team: 3,
  team_name: '분양1팀',
  agency_name: '직영대행',
  user: null,
  name: '김상담',
  duty: '1',
  duty_display: '분양상담사',
  status: '1',
  status_display: '재직 (활동 중)',
  phone: '010-1234-5678',
  id_number: '',
  tax_type: '1',
  tax_type_display: '3.3% 사업소득 (프리랜서)',
  bank_name: '',
  account_number: '',
  account_holder: '',
  join_date: '2026-01-01',
  quit_date: null,
  notes: '',
  documents_count: 0,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  ...overrides,
})

const createSalesRouter = async (initialPath = '/sales/performance') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/sales/performance', component: { template: '<div />' } },
      { path: '/sales/settlement', component: { template: '<div />' } },
      { path: '/sales/payout', component: { template: '<div />' } },
      { path: '/sales/policy', component: { template: '<div />' } },
      { path: '/sales/organization', component: { template: '<div />' } },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('sales module', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockedApi.get.mockResolvedValue({ data: { count: 0, results: [] } })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('useSales Pinia store', () => {
    it('fetches contract agents with contract__project and limit=3000 and resets lists on failure', async () => {
      const store = useSales()
      store.contractAgentList = [{ id: 99 } as ContractSalesAgent]
      mockedApi.get.mockResolvedValueOnce({ data: { results: [] } })

      await store.fetchContractAgentList(10, '홍길동')
      const url = mockedApi.get.mock.calls[0][0]
      expect(url).toContain('/sales-contract-agent/?')
      expect(url).toContain('contract__project=10')
      expect(url).toContain('limit=3000')
      expect(url).not.toContain('team__agency__project')

      mockedApi.get.mockRejectedValueOnce(new Error('network fail'))
      await store.fetchAgencyList(20)
      expect(store.agencyList).toEqual([])
    })

    it('mutations return boolean and preserve main payout list when fetching person history', async () => {
      const store = useSales()
      mockedApi.post.mockResolvedValueOnce({ data: { id: 1 } })
      expect(await store.createAgency({ project: 10, name: 'A대행' })).toBe(true)

      mockedApi.delete.mockRejectedValueOnce(new Error('conflict'))
      expect(await store.deletePeriod(5)).toBe(false)
      expect(mockedErrorHandle).toHaveBeenCalledTimes(1)

      const periodPayout = { id: 1, period: 1, sales_person: 7 } as CommissionPayout
      store.payoutList = [periodPayout]
      mockedApi.get.mockResolvedValueOnce({
        data: { results: [{ id: 2, period: 2, period_title: '8월 1차', sales_person: 7 }] },
      })
      const ok = await store.fetchPersonPayoutHistory(7)
      expect(ok).toBe(true)
      expect(store.payoutList).toHaveLength(1)
      expect(store.personPayoutHistoryList[0].period_title).toBe('8월 1차')
    })
  })

  describe('SalesAuthGuard & project-scoped authorization', () => {
    it('enforces project-specific requiredPerm without cross-project leakage', () => {
      seedSalesProjectPerms({ 10: [PERM.SALES_POLICY], 20: [PERM.SALES_READ] }, 10)

      const wAllowed = mount(SalesAuthGuard, {
        props: { project: 10, requiredPerm: PERM.SALES_POLICY },
        slots: { default: '<div class="allowed-content">ok</div>' },
        global: { plugins: [vuetify, CoreuiVue] },
      })
      expect(wAllowed.find('.allowed-content').exists()).toBe(true)

      const wWrongProj = mount(SalesAuthGuard, {
        props: { project: 20, requiredPerm: PERM.SALES_POLICY },
        slots: { default: '<div class="allowed-content">ok</div>' },
        global: { plugins: [vuetify, CoreuiVue] },
      })
      expect(wWrongProj.find('.allowed-content').exists()).toBe(false)

      const wAny = mount(SalesAuthGuard, {
        props: { project: 20, requiredPerm: [PERM.SALES_READ, PERM.SALES_MANAGE] },
        slots: { default: '<div class="allowed-content">ok</div>' },
        global: { plugins: [vuetify, CoreuiVue] },
      })
      expect(wAny.find('.allowed-content').exists()).toBe(true)
    })

    it('blocks unauthorized project views without firing API calls', async () => {
      const router = await createSalesRouter('/sales/settlement')
      seedSalesProjectPerms({ 10: [PERM.SALES_READ] }, 10)

      mount(SettlementIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            PeriodFormModal: FormModalStub,
            PayoutDetailModal: FormModalStub,
            ConfirmModal: ConfirmModalStub,
          },
        },
      })
      await flushPromises()
      expect(mockedApi.get).not.toHaveBeenCalled()

      mount(PolicyIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            PolicyFormModal: FormModalStub,
            ConfirmModal: ConfirmModalStub,
          },
        },
      })
      await flushPromises()
      expect(mockedApi.get).not.toHaveBeenCalled()

      mount(OrganizationIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            AgencyFormModal: FormModalStub,
            TeamFormModal: FormModalStub,
            PersonFormModal: FormModalStub,
            PersonDocumentModal: FormModalStub,
          },
        },
      })
      await flushPromises()
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })

  describe('Performance & ContractAgentModal', () => {
    it('locks settled contract mappings and keeps ContractAgentModal open on API error', async () => {
      seedSalesProjectPerms({ 10: [PERM.SALES_READ, PERM.SALES_MANAGE] }, 10)
      const router = await createSalesRouter('/sales/performance')
      const contStore = useContract()
      contStore.getContracts = [{ value: 100, label: 'CONT-100 (홍길동)' }] as never

      const settledMapping: ContractSalesAgent = {
        id: 1,
        contract: 100,
        contract_serial: 'CONT-100',
        contractor_name: '홍길동',
        agency: 2,
        agency_name: '직영대행',
        sales_person: 7,
        sales_person_name: '김상담',
        team: 3,
        team_name: '분양1팀',
        policy: null,
        contract_date: '2026-09-10',
        mgm_name: '',
        mgm_phone: '',
        mgm_fee: 0,
        note: '',
        is_settlement_approved: true,
        is_settled: true,
        settled_period_title: '2026년 9월 1차',
        created_at: '2026-09-10T00:00:00Z',
        updated_at: '2026-09-10T00:00:00Z',
      }
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/simple-contract/')) {
          return Promise.resolve({ data: { results: [{ value: 100, label: 'CONT-100 (홍길동)' }] } })
        }
        if (url.includes('/sales-contract-agent/')) {
          return Promise.resolve({ data: { results: [settledMapping] } })
        }
        return Promise.resolve({ data: { results: [] } })
      })

      const wPerf = mount(PerformanceIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            ContractAgentModal: FormModalStub,
            SettlementApprovalModal: FormModalStub,
          },
        },
      })
      await flushPromises()

      const approveBtn = wPerf.find('button[title*="이미 정산 회차에 반영"]')
      expect(approveBtn.attributes('disabled')).toBeDefined()
      expect(wPerf.text()).toContain('조회')

      // ContractAgentModal keeps open when createContractAgent fails
      const salesStore = useSales()
      salesStore.personList = [makePerson({ id: 7, status: '1' }), makePerson({ id: 8, name: '퇴사자', status: '3' })]
      mockedApi.post.mockRejectedValueOnce(new Error('bad request'))

      const wModal = mount(ContractAgentModal, {
        props: { project: 10, contractOptions: [{ value: 101, label: 'CONT-101' }] },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: {
            FormModal: FormModalStub,
            ConfirmModal: ConfirmModalStub,
            DatePicker: DatePickerStub,
          },
        },
      })
      ;(wModal.vm as unknown as { open: () => void }).open()
      await flushPromises()

      // Quit person (status '3') excluded in new assignment dropdown
      const optionTexts = wModal.findAll('option').map(o => o.text())
      expect(optionTexts.some(t => t.includes('퇴사자'))).toBe(false)

      const selects = wModal.findAll('select')
      await selects[0].setValue('101')
      await selects[1].setValue('7')
      await wModal.find('form').trigger('submit.prevent')
      await flushPromises()

      expect(mockedApi.post).toHaveBeenCalledTimes(1)
      expect(wModal.find('.form-modal-stub').exists()).toBe(true)
      expect(wModal.emitted('saved')).toBeUndefined()
    })
  })

  describe('Policy & Settlement & Payout flows', () => {
    it('PolicyFormModal validates date order and keeps open on failure', async () => {
      mockedApi.post.mockRejectedValueOnce(new Error('server error'))
      const wrapper = mount(PolicyFormModal, {
        props: { project: 10, orderGroupList: [], unitTypeList: [] },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { FormModal: FormModalStub, DatePicker: DatePickerStub },
        },
      })
      ;(wrapper.vm as unknown as { open: (p?: CommissionPolicy) => void }).open()
      await flushPromises()

      await wrapper.find('input[placeholder*="정규 분양"]').setValue('84A 기준')
      const dateInputs = wrapper.findAll('.datepicker-stub')
      await dateInputs[0].setValue('2026-10-10')
      await dateInputs[1].setValue('2026-10-01')
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(mockedMessage).toHaveBeenCalled()
      expect(mockedApi.post).not.toHaveBeenCalled()

      await dateInputs[1].setValue('2026-10-31')
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(mockedApi.post).toHaveBeenCalledTimes(1)
      expect(wrapper.find('.form-modal-stub').exists()).toBe(true)
    })

    it('Settlement hides run/edit/delete for confirmed periods, reloads clawbacks on settle, and skips navigation when confirm fails', async () => {
      seedSalesProjectPerms({ 10: [PERM.SALES_SETTLE, PERM.SALES_PAYOUT] }, 10)
      const router = await createSalesRouter('/sales/settlement')
      const pushSpy = vi.spyOn(router, 'push')

      const draftPeriod = makePeriod({ id: 1, status: '1', status_display: '정산 작성 중' })
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/sales-settlement-period/?')) {
          return Promise.resolve({ data: { results: [draftPeriod] } })
        }
        return Promise.resolve({ data: { results: [] } })
      })

      const wrapper = mount(SettlementIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            CIcon: CIconStub,
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            PeriodFormModal: FormModalStub,
            PayoutDetailModal: FormModalStub,
            ConfirmModal: ConfirmModalStub,
          },
        },
      })
      await flushPromises()

      expect(wrapper.text()).toContain('수수료 자동 정산 실행')
      expect(wrapper.text()).toContain('회차 수정')
      expect(wrapper.text()).toContain('회차 삭제')

      // Confirm failure must NOT navigate to /sales/payout
      mockedApi.post.mockRejectedValueOnce(new Error('confirm failed'))
      const btns = wrapper.findAll('button')
      const confirmBtn = btns.find(b => b.text().includes('정산 확정'))
      await confirmBtn!.trigger('click')
      await flushPromises()
      const execConfirmBtn = wrapper
        .findAll('.confirm-modal-stub button')
        .find(b => b.text().includes('정산 확정'))
      await execConfirmBtn!.trigger('click')
      await flushPromises()
      expect(pushSpy).not.toHaveBeenCalled()

      // Confirmed period hides settle/edit/delete buttons
      useSales().periodList = [makePeriod({ id: 1, status: '2', status_display: '정산 확정 (승인 대기)' })]
      await flushPromises()
      expect(wrapper.text()).not.toContain('수수료 자동 정산 실행')
      expect(wrapper.text()).not.toContain('회차 수정')
      expect(wrapper.text()).toContain('수수료 지급 관리로 이동')

      // PeriodFormModal never sends read-only status in payload
      mockedApi.post.mockResolvedValueOnce({ data: { id: 9 } })
      const wPeriodModal = mount(PeriodFormModal, {
        props: { project: 10 },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { FormModal: FormModalStub, DatePicker: DatePickerStub },
        },
      })
      ;(wPeriodModal.vm as unknown as { open: () => void }).open()
      await flushPromises()
      await wPeriodModal.find('input[placeholder*="수수료 정산"]').setValue('10월 1차')
      await wPeriodModal.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(mockedApi.post).toHaveBeenLastCalledWith(
        '/sales-settlement-period/',
        expect.not.objectContaining({ status: expect.anything() }),
      )
    })

    it('Payout refreshes periods after status update and neutralizes CSV formula prefixes', async () => {
      seedSalesProjectPerms({ 10: [PERM.SALES_PAYOUT] }, 10)
      const router = await createSalesRouter('/sales/payout')

      const payout: CommissionPayout = {
        id: 11,
        period: 1,
        period_title: '2026년 9월 1차',
        sales_person: 7,
        sales_person_name: '=CMD|calc',
        duty_display: '분양상담사',
        team_name: '분양1팀',
        base_pay: 0,
        contract_count: 1,
        commission_amount: 1000000,
        bonus_amount: 0,
        deduction_amount: 0,
        gross_amount: 1000000,
        income_tax: 30000,
        local_income_tax: 3000,
        total_tax: 33000,
        net_amount: 967000,
        pay_status: '1',
        pay_status_display: '대기',
        paid_date: null,
        bank_name: '국민은행',
        account_number: '123456',
        account_holder: '김상담',
        note: '+HYPERLINK()',
        created_at: '2026-09-30T00:00:00Z',
        updated_at: '2026-09-30T00:00:00Z',
      }
      mockedApi.get.mockImplementation((url: string) => {
        if (url.includes('/sales-settlement-period/')) {
          return Promise.resolve({ data: { results: [makePeriod({ id: 1, status: '2' })] } })
        }
        if (url.includes('/sales-payout/')) {
          return Promise.resolve({ data: { results: [payout] } })
        }
        return Promise.resolve({ data: { results: [] } })
      })
      mockedApi.post.mockResolvedValueOnce({ data: { pay_status: '3' } })

      let capturedBlobText = ''
      const OrigBlob = globalThis.Blob
      vi.spyOn(globalThis, 'Blob').mockImplementation(function (
        this: Blob,
        parts?: BlobPart[],
        opts?: BlobPropertyBag,
      ) {
        capturedBlobText = String(parts?.[0] ?? '')
        return new OrigBlob(parts, opts)
      } as unknown as typeof Blob)
      vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
      vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
      vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)

      const wrapper = mount(PayoutIndex, {
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            CIcon: CIconStub,
            ContentHeader: ContentHeaderStub,
            ContentBody: ContentBodyStub,
            PayoutDetailModal: FormModalStub,
            PersonPayoutHistoryModal: FormModalStub,
            ConfirmModal: ConfirmModalStub,
          },
        },
      })
      await flushPromises()

      // Change pay status -> re-fetches /sales-settlement-period/ to sync period status
      const periodCallsBefore = mockedApi.get.mock.calls.filter(([u]) =>
        u.includes('/sales-settlement-period/'),
      ).length
      const statusSelect = wrapper.find('select.form-select-sm')
      await statusSelect.setValue('3')
      await flushPromises()
      const periodCallsAfter = mockedApi.get.mock.calls.filter(([u]) =>
        u.includes('/sales-settlement-period/'),
      ).length
      expect(periodCallsAfter).toBeGreaterThan(periodCallsBefore)

      // CSV download escapes leading = and +
      const csvBtn = wrapper.findAll('button').find(b => b.text().includes('은행 이체용 CSV'))
      await csvBtn!.trigger('click')
      expect(capturedBlobText).toContain('"\'=CMD|calc"')
      expect(capturedBlobText).toContain('"\'+HYPERLINK()"')

      // PersonPayoutHistoryModal renders period_title cleanly
      mockedApi.get.mockResolvedValueOnce({ data: { results: [payout] } })
      mockedApi.get.mockResolvedValueOnce({ data: { results: [] } })
      const wHist = mount(PersonPayoutHistoryModal, {
        global: { plugins: [vuetify, CoreuiVue] },
      })
      await (wHist.vm as unknown as { open: (p: CommissionPayout) => Promise<void> }).open(payout)
      await flushPromises()
      expect(wHist.text()).toContain('2026년 9월 1차')
    })
  })

  describe('Organization components', () => {
    it('PersonFormModal preserves blank bank_name on edit and PersonDocumentModal warns cleanly and resets file input', async () => {
      seedSalesProjectPerms({ 10: [PERM.SALES_MANAGE] }, 10)
      const salesStore = useSales()
      salesStore.teamList = [
        { id: 3, agency: 1, agency_name: '직영', parent: null, name: '분양1팀', order: 1, is_active: true, created_at: '' },
      ]

      const wPersonForm = mount(PersonFormModal, {
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { FormModal: FormModalStub, DatePicker: DatePickerStub },
        },
      })
      ;(wPersonForm.vm as unknown as { open: (p?: SalesPerson) => void }).open(makePerson({ bank_name: '' }))
      await flushPromises()
      mockedApi.patch.mockResolvedValueOnce({ data: { id: 7 } })
      await wPersonForm.find('form').trigger('submit.prevent')
      await flushPromises()
      expect(mockedApi.patch).toHaveBeenCalledWith(
        '/sales-person/7/',
        expect.objectContaining({ bank_name: '' }),
      )

      // PersonList only renders editable name link for project managers
      seedSalesProjectPerms({ 10: [PERM.SALES_READ] }, 10)
      salesStore.personList = [makePerson()]
      const wList = mount(PersonList, {
        props: { project: 10 },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { ConfirmModal: ConfirmModalStub },
        },
      })
      expect(wList.find('td a').exists()).toBe(false)

      // PersonDocumentModal uses message() instead of alert() and resets native input
      seedSalesProjectPerms({ 10: [PERM.SALES_MANAGE] }, 10)
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => undefined)
      const wDocs = mount(PersonDocumentModal, {
        props: { project: 10 },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { FormModal: FormModalStub, ConfirmModal: ConfirmModalStub },
        },
      })
      await (wDocs.vm as unknown as { open: (p: SalesPerson) => Promise<void> }).open(makePerson())
      await flushPromises()

      expect(wDocs.find('input[type="file"]').exists()).toBe(true)
      expect(alertSpy).not.toHaveBeenCalled()
    })
  })
})
