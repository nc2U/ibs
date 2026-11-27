import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, nextTick, ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { useAccount } from '@/store/pinia/account'
import { useContract } from '@/store/pinia/contract'
import { usePayment } from '@/store/pinia/payment'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { useSite } from '@/store/pinia/project_site'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { RequiredDocs } from '@/store/types/contract'
import type { OptionItem, Project, Site, SiteContract, SiteOwner } from '@/store/types/project'
import RequiredAddForm from '../Required/components/RequiredAddForm.vue'
import Required from '../Required/components/Required.vue'
import OptionAddForm from '../PaidOption/components/OptionAddForm.vue'
import PaidOption from '../PaidOption/components/PaidOption.vue'
import DownPayAddForm from '../DownPay/components/DownPayAddForm.vue'
import UnitController from '../Unit/components/UnitController.vue'
import PriceComponent from '../Price/components/Price.vue'
import SiteListIndex from '../SiteList/Index.vue'
import AddSite from '../SiteList/components/AddSite.vue'
import SiteOwnerIndex from '../SiteOwner/Index.vue'
import SiteOwnerRow from '../SiteOwner/components/SiteOwner.vue'
import SiteOwnerForm from '../SiteOwner/components/SiteOwnerForm.vue'
import SiteContractIndex from '../SiteContract/Index.vue'
import SiteContractForm from '../SiteContract/components/SiteContractForm.vue'

const { mockRouterPush, mockRouterReplace, mockRoute } = vi.hoisted(() => ({
  mockRouterPush: vi.fn(),
  mockRouterReplace: vi.fn().mockResolvedValue(undefined),
  mockRoute: {
    name: '사업 부지 목록',
    fullPath: '/projects/site',
    params: {} as Record<string, string>,
    query: {} as Record<string, string>,
  },
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

vi.mock('@/utils/helper', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/helper')>()
  return {
    ...actual,
    message: (...args: unknown[]) => mockMessage(...args),
    errorHandle: (...args: unknown[]) => mockErrorHandle(...args),
  }
})

const mockApi = api as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const makeVuetify = () => createVuetify({ components, directives })

const makeConfirmModalStub = () =>
  defineComponent({
    name: 'ConfirmModal',
    setup(_, { expose }) {
      const visible = ref(false)
      const callModal = vi.fn(() => {
        visible.value = true
      })
      const close = vi.fn(() => {
        visible.value = false
      })
      expose({ callModal, close, visible })
      return { visible }
    },
    template:
      '<div v-if="visible" class="confirm-modal-stub"><slot name="header" /><slot /><slot name="footer" /></div>',
  })

const makeAlertModalStub = () =>
  defineComponent({
    name: 'AlertModal',
    setup(_, { expose }) {
      const visible = ref(false)
      const lastArgs = ref<unknown[]>([])
      const callModal = vi.fn((...args: unknown[]) => {
        lastArgs.value = args
        visible.value = true
      })
      const close = vi.fn(() => {
        visible.value = false
      })
      expose({ callModal, close, visible, lastArgs })
      return { visible }
    },
    template: '<div v-if="visible" class="alert-modal-stub"><slot /></div>',
  })

const makeFormModalStub = () =>
  defineComponent({
    name: 'FormModal',
    setup(_, { expose }) {
      const visible = ref(false)
      const callModal = vi.fn(() => {
        visible.value = true
      })
      const close = vi.fn(() => {
        visible.value = false
      })
      expose({ callModal, close, visible })
      return { visible }
    },
    template: '<div v-if="visible" class="form-modal-stub"><slot name="header" /><slot /></div>',
  })

const DatePickerStub = defineComponent({
  name: 'DatePicker',
  props: {
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    required: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  template:
    '<input :value="modelValue" :placeholder="placeholder" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
})

const MultiselectStub = defineComponent({
  name: 'Multiselect',
  props: {
    modelValue: { type: [Number, String, Array], default: null },
    options: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    mode: { type: String, default: 'tags' },
  },
  emits: ['update:modelValue'],
  template: '<select :disabled="disabled" />',
})

const commonStubs = {
  Teleport: true,
  CIcon: { template: '<i />' },
  ProjectAuthGuard: { template: '<div><slot /></div>' },
  ContentHeader: { template: '<div><slot /></div>' },
  ContentBody: { template: '<div><slot /></div>' },
  Loading: { template: '<div />' },
  NoAuth: { template: '<div class="no-auth-stub">권한 없음</div>' },
  TableTitleRow: { props: ['url', 'filename', 'disabled'], template: '<div><slot /></div>' },
  Pagination: { template: '<div />' },
  DaumPostcode: {
    template: '<div />',
    methods: { initiate: vi.fn() },
  },
  DatePicker: DatePickerStub,
  Multiselect: MultiselectStub,
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
  ...overrides,
})

const makeProject = (overrides: Partial<Project> = {}): Project =>
  ({
    pk: 10,
    company: 1,
    name: '테스트 개발사업',
    order: 1,
    kind: '1',
    kind_desc: '공동주택',
    start_year: '2026',
    is_direct_manage: true,
    is_returned_area: false,
    is_unit_set: true,
    ...overrides,
  }) as unknown as Project

const makeSiteOwner = (overrides: Partial<SiteOwner> = {}): SiteOwner =>
  ({
    pk: 1,
    project: 10,
    own_sort: '1',
    own_sort_desc: '개인',
    owner: '김소유',
    date_of_birth: '1980-01-01',
    phone1: '010-1234-5678',
    phone2: '',
    zipcode: '12345',
    address1: '서울시 강남구',
    address2: '101호',
    address3: '역삼동',
    use_consent: true,
    note: '',
    sites: [
      {
        pk: 101,
        site: 11,
        __str__: '역삼동 100-1',
        ownership_ratio: '50.0000000',
        owned_area: '100.0000000',
        acquisition_date: '2026-01-10',
      },
      {
        pk: 102,
        site: 12,
        __str__: '역삼동 100-2',
        ownership_ratio: '50.0000000',
        owned_area: '200.0000000',
        acquisition_date: '2026-01-11',
      },
    ],
    ...overrides,
  }) as unknown as SiteOwner

describe('projects 모듈 정밀검사 회귀 테스트', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockRoute.name = '사업 부지 목록'
    mockRoute.fullPath = '/projects/site'
    mockRoute.params = {}
    mockRoute.query = {}
    mockRouterReplace.mockResolvedValue(undefined)
    window.HTMLElement.prototype.scrollIntoView = vi.fn()

    const accountStore = useAccount()
    accountStore.userInfo = makeUser()

    const permStore = usePermission()
    permStore.setProjectPermissions([
      PERM.PROJECT_CREATE,
      PERM.PROJECT_UPDATE,
      PERM.SITE_READ,
      PERM.SITE_CREATE,
      PERM.SITE_UPDATE,
      PERM.SITE_DELETE,
    ])

    const workStore = useWork()
    workStore.currentProject = {
      pk: 5,
      slug: 'test-proj',
      name: '테스트 개발사업',
      status: '1',
    } as never

    const projStore = useProject()
    projStore.project = makeProject()

    mockApi.get.mockResolvedValue({ data: { results: [], count: 0 } })
    mockApi.post.mockResolvedValue({ data: { pk: 1, project: 10 } })
    mockApi.put.mockResolvedValue({ data: { pk: 1, project: 10 } })
    mockApi.patch.mockResolvedValue({ data: { pk: 1, project: 10 } })
    mockApi.delete.mockResolvedValue({ status: 204, data: null })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Pinia 스토어 엔드포인트, 에러 핸들링 및 필터 보존', () => {
    it('useProject는 /inc-budget/ 소문자 URL과 limit=100을 사용하고 create/update boolean을 반환한다', async () => {
      const store = useProject()

      await store.fetchIncBudgetList(10)
      await store.fetchOutBudgetList(10)
      expect(mockApi.get).toHaveBeenCalledWith('/inc-budget/?project=10&limit=100')
      expect(mockApi.get).toHaveBeenCalledWith('/out-budget/?project=10&limit=100')

      await store.patchIncBudgetList(10, 11, 5000)
      expect(mockApi.patch).toHaveBeenCalledWith('/inc-budget/11/', { budget: 5000 })

      mockApi.patch.mockRejectedValueOnce(new Error('patch fail'))
      await store.patchOutBudget(10, 12, 6000)
      expect(mockErrorHandle).toHaveBeenCalled()

      mockApi.post.mockRejectedValueOnce(new Error('create fail'))
      const created = await store.createProject(makeProject({ name: '실패' }))
      expect(created).toBe(false)

      mockApi.put.mockResolvedValueOnce({ data: makeProject() })
      const updated = await store.updateProject(makeProject({ pk: 10, name: '성공' }))
      expect(updated).toBe(true)
    })

    it('useProjectData는 fetchHouseUnitList 실패 시 finally로 isLoading을 false로 복구하고 createUnit 에러를 전파한다', async () => {
      const store = useProjectData()
      mockApi.get.mockRejectedValueOnce(new Error('network error'))

      await store.fetchHouseUnitList(10, 1)
      expect(store.isLoading).toBe(false)
      expect(mockErrorHandle).toHaveBeenCalled()

      await store.fetchTypeList(10)
      await store.fetchFloorTypeList(10)
      await store.fetchBuildingList(10)
      await store.fetchOptionItemList(10)
      expect(mockApi.get).toHaveBeenCalledWith('/type/?project=10&sort=&limit=100')
      expect(mockApi.get).toHaveBeenCalledWith('/floor/?project=10&sort=&limit=100')
      expect(mockApi.get).toHaveBeenCalledWith('/bldg/?project=10&limit=100')
      expect(mockApi.get).toHaveBeenCalledWith('/option-item/?project=10&limit=100')

      mockApi.post.mockRejectedValueOnce(new Error('unit duplicate'))
      await expect(
        store.createUnit({
          project: 10,
          unit_type: 1,
          building_unit: 1,
          bldg_line: 1,
          floor_no: 1,
          name: '101',
          floor_type: 1,
          unit_code: '01',
        }),
      ).rejects.toThrow('unit duplicate')
      expect(mockErrorHandle).toHaveBeenCalled()
    })

    it('useSite는 URLSearchParams로 검색어를 인코딩하고 delete 시 필터와 limit을 유지하며 boolean을 반환한다', async () => {
      const store = useSite()
      await store.fetchSiteList({ project: 10, page: 2, limit: 25, search: '홍&길#동' })
      expect(mockApi.get).toHaveBeenCalledWith(
        '/site/?project=10&limit=25&page=2&search=%ED%99%8D%26%EA%B8%B8%23%EB%8F%99',
      )

      mockApi.get.mockRejectedValueOnce(new Error('sites fail'))
      await store.fetchAllSites(10)
      expect(mockErrorHandle).toHaveBeenCalled()

      mockApi.get.mockClear()
      mockApi.delete.mockResolvedValueOnce({ status: 204, data: null })
      const ok = await store.deleteSiteOwner(5, 10, {
        page: 3,
        limit: 20,
        sort: '1',
        is_use_consent: '1',
        search: '김&이',
      })
      expect(ok).toBe(true)
      expect(mockApi.get).toHaveBeenCalledWith(
        '/site-owner/?project=10&limit=20&page=3&own_sort=1&use_consent=1&search=%EA%B9%80%26%EC%9D%B4',
      )

      mockApi.delete.mockRejectedValueOnce(new Error('delete denied'))
      const failed = await store.deleteSiteCont(9, 10)
      expect(failed).toBe(false)
      expect(mockErrorHandle).toHaveBeenCalled()
    })

    it('useContract와 usePayment는 쿼리 문자열(&)과 limit=100, 에러 전파를 보장한다', async () => {
      const contStore = useContract()
      await contStore.fetchOrderGroupList(10, 'asc')
      await contStore.fetchRequiredDocsList(10)
      expect(mockApi.get).toHaveBeenCalledWith('/order-group/?project=10&sort=asc&limit=100')
      expect(mockApi.get).toHaveBeenCalledWith('/required-docs/?project=10&limit=100')

      const payStore = usePayment()
      await payStore.fetchDownPayList({ project: 10 })
      expect(mockApi.get).toHaveBeenCalledWith('/down-payment/?project=10&limit=100')

      mockApi.post.mockRejectedValueOnce(new Error('installment fail'))
      await expect(payStore.createPaymentPerInstallment({} as never)).rejects.toThrow(
        'installment fail',
      )
      expect(mockErrorHandle).toHaveBeenCalled()
    })
  })

  describe('Required / PaidOption / DownPay / Unit / Price 컴포넌트 수정 검증', () => {
    it('RequiredAddForm은 quantity 0과 display_order 0을 1로 덮어쓰지 않고 그대로 전송한다', async () => {
      const contStore = useContract()
      contStore.documentTypeList = [{ pk: 3, name: '인감증명서' }] as never
      const spyCreate = vi.spyOn(contStore, 'createRequiredDoc').mockResolvedValueOnce({} as never)

      const ConfirmStub = makeConfirmModalStub()
      const wrapper = mount(RequiredAddForm, {
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          stubs: {
            ...commonStubs,
            ConfirmModal: ConfirmStub,
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      await wrapper.findAll('select')[1].setValue('3')
      const numberInputs = wrapper.findAll('input[type="number"]')
      await numberInputs[0].setValue(0)
      await numberInputs[1].setValue(0)

      await wrapper.find('form').trigger('submit')
      await flushPromises()
      const confirmStub = wrapper.findComponent(ConfirmStub)
      expect(confirmStub.exists()).toBe(true)

      await wrapper.find('.confirm-modal-stub button').trigger('click')
      await flushPromises()

      expect(spyCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          project: 10,
          document_type: 3,
          quantity: 0,
          display_order: 0,
        }),
      )
    })

    it('Required 행은 PROJECT_UPDATE 권한이 없으면 입력을 비활성화하고 액션 셀을 숨긴다', () => {
      usePermission().setProjectPermissions([])
      const doc: RequiredDocs = {
        pk: 1,
        project: 10,
        document_type: 3,
        document_name: '신분증',
        sort: 'proof',
        quantity: 2,
        require_type: 'required',
        required: '필수',
        description: '',
        display_order: 1,
      }
      const wrapper = mount(Required, {
        props: { requiredDoc: doc, disabled: false },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      wrapper.findAll('select, input').forEach(node => {
        expect(node.attributes('disabled')).toBeDefined()
      })
      expect(wrapper.text()).not.toContain('수정')
      expect(wrapper.text()).not.toContain('삭제')
    })

    it('OptionAddForm은 계약금+잔금 불일치 시 즉시 오류 메시지를 표시하고 PaidOption은 비권한 시 입력을 막는다', async () => {
      const addWrapper = mount(OptionAddForm, {
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          provide: { getTypes: [{ value: 1, label: '84A' }] },
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      const numInputs = addWrapper.findAll('input[type="number"]')
      await numInputs[0].setValue(1000)
      await numInputs[1].setValue(400)
      await numInputs[2].setValue(500)
      await nextTick()

      expect(addWrapper.text()).toContain('계약금 + 잔금의 합계가 옵션 가격과 일치해야 합니다.')

      usePermission().setProjectPermissions([])
      const item: OptionItem = {
        pk: 7,
        project: 10,
        types: [1],
        opt_code: 'OPT1',
        opt_name: '시스템에어컨',
        opt_desc: '',
        opt_maker: 'LG',
        opt_price: 5000000,
        opt_deposit: 1000000,
        opt_balance: 4000000,
      }
      const rowWrapper = mount(PaidOption, {
        props: { optionItem: item },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          provide: { getTypes: [{ value: 1, label: '84A' }] },
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      rowWrapper.findAll('input').forEach(node => {
        expect(node.attributes('disabled')).toBeDefined()
      })
      expect(rowWrapper.findComponent(MultiselectStub).props('disabled')).toBe(true)
    })

    it('DownPayAddForm은 중복 조합 등록 시 native alert 대신 AlertModal을 호출한다', async () => {
      const payStore = usePayment()
      payStore.downPayList = [
        { pk: 1, project: 10, order_group: 2, unit_type: 3, payment_amount: 100 },
      ]
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

      const AlertStub = makeAlertModalStub()
      const wrapper = mount(DownPayAddForm, {
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          provide: {
            orders: [{ pk: 2, name: '1차' }],
            types: [{ pk: 3, name: '84A' }],
          },
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: AlertStub,
          },
        },
      })

      const selects = wrapper.findAll('select')
      await selects[0].setValue(2)
      await selects[1].setValue(3)
      await wrapper.find('input[type="number"]').setValue(1000)

      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(alertSpy).not.toHaveBeenCalled()
      expect(wrapper.find('.alert-modal-stub').exists()).toBe(true)
    })

    it('UnitController는 동 추가 시 공백을 trim하여 emit하고 Price는 금액 입력을 모두 지우면 price를 null로 초기화한다', async () => {
      const ctrlWrapper = mount(UnitController, {
        props: { project: 10 },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          stubs: {
            ...commonStubs,
            FormModal: makeFormModalStub(),
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      await ctrlWrapper.find('.mdi-plus-thick').trigger('click')
      await nextTick()
      const dongInput = ctrlWrapper.find('.form-modal-stub input')
      await dongInput.setValue('  101  ')
      await ctrlWrapper.find('.form-modal-stub form').trigger('submit')
      expect(ctrlWrapper.emitted('dong-register')).toEqual([['101']])

      const priceWrapper = mount(PriceComponent, {
        props: {
          floor: {
            pk: 1,
            project: 10,
            sort: '1',
            start_floor: 1,
            end_floor: 5,
            extra_cond: '',
            alias_name: '저층',
          },
          price: {
            pk: 9,
            project: 10,
            order_group: 1,
            unit_type: 1,
            unit_floor_type: 1,
            price_build: 1000,
            price_land: 2000,
            price_tax: null,
            price: 3000,
          },
        },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          provide: { condTexts: { orderText: '1차', typeText: '84A' } },
          stubs: {
            ...commonStubs,
            FormModal: makeFormModalStub(),
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      const priceInputs = priceWrapper.findAll('input[type="number"]')
      await priceInputs[0].setValue('')
      await priceInputs[1].setValue('')
      await nextTick()
      expect((priceInputs[3].element as HTMLInputElement).value).toBe('')
    })
  })

  describe('SiteList / SiteOwner / SiteContract 모듈 권한, 쿼리보존 및 테이블 회귀 검증', () => {
    it('SiteList / SiteOwner / SiteContract는 SITE_READ 권한이 없으면 NoAuth를 렌더링하고 API를 호출하지 않는다', async () => {
      usePermission().setProjectPermissions([])

      for (const Comp of [SiteListIndex, SiteOwnerIndex, SiteContractIndex]) {
        mockApi.get.mockClear()
        const wrapper = mount(Comp, {
          global: { plugins: [makeVuetify(), CoreuiVue], stubs: commonStubs },
        })
        await flushPromises()
        expect(wrapper.find('.no-auth-stub').exists()).toBe(true)
        expect(mockApi.get).not.toHaveBeenCalled()
        wrapper.unmount()
      }
    })

    it('SiteList는 프로젝트 전환 시 page와 highlight_id만 제거하고 project 쿼리를 유지하며 AddSite는 API 실패 시 모달을 닫지 않는다', async () => {
      mockRoute.query = { project: '10', page: '2', highlight_id: '99' }
      const siteWrapper = mount(SiteListIndex, {
        global: { plugins: [makeVuetify(), CoreuiVue], stubs: commonStubs },
      })
      await flushPromises()

      useProject().project = makeProject({ pk: 20 })
      await flushPromises()

      expect(mockRouterReplace).toHaveBeenCalledWith(
        expect.objectContaining({
          query: { project: '10' },
        }),
      )
      siteWrapper.unmount()

      const FormStub = makeFormModalStub()
      const addWrapper = mount(AddSite, {
        props: { project: 10 },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          stubs: {
            ...commonStubs,
            FormModal: FormStub,
            AlertModal: makeAlertModalStub(),
            SiteForm: {
              emits: ['multi-submit', 'close'],
              template:
                '<button class="emit-submit" @click="$emit(\'multi-submit\', { district: \'역삼동\' })" />',
            },
          },
        },
      })

      await addWrapper.find('button').trigger('click')
      await nextTick()
      await addWrapper.find('.emit-submit').trigger('click')

      const emitted = addWrapper.emitted('multi-submit') as [Site, (ok: boolean) => void][]
      expect(emitted).toHaveLength(1)
      emitted[0][1](false)
      await nextTick()
      expect(addWrapper.find('.form-modal-stub').exists()).toBe(true)

      emitted[0][1](true)
      await nextTick()
      expect(addWrapper.find('.form-modal-stub').exists()).toBe(false)
    })

    it('SiteOwner는 소유부지가 비어 있어도 행을 렌더링하고 다중 부지에서 사용동의를 첫 행에만 rowspan으로 표시한다', () => {
      const multiWrapper = mount(
        {
          components: { SiteOwnerRow },
          template: '<table><tbody><SiteOwnerRow :owner="owner" /></tbody></table>',
          setup() {
            return { owner: makeSiteOwner() }
          },
        },
        {
          global: {
            plugins: [makeVuetify(), CoreuiVue],
            stubs: {
              ...commonStubs,
              FormModal: makeFormModalStub(),
              SiteOwnerForm: true,
            },
          },
        },
      )

      const rows = multiWrapper.findAll('tbody tr')
      expect(rows).toHaveLength(2)
      const consentCells = multiWrapper.findAll('td.bg-success')
      expect(consentCells).toHaveLength(1)
      expect(consentCells[0].attributes('rowspan')).toBe('2')

      // Decimal string '50.0000000' vs numeric equality keeps 적용 button disabled
      const applyBtn = rows[0].findAll('button').find(b => b.text() === '적용')!
      expect(applyBtn.attributes('disabled')).toBeDefined()

      const emptyWrapper = mount(
        {
          components: { SiteOwnerRow },
          template: '<table><tbody><SiteOwnerRow :owner="owner" /></tbody></table>',
          setup() {
            return { owner: makeSiteOwner({ owner: '무지주소유자', sites: [] }) }
          },
        },
        {
          global: {
            plugins: [makeVuetify(), CoreuiVue],
            stubs: {
              ...commonStubs,
              FormModal: makeFormModalStub(),
              SiteOwnerForm: true,
            },
          },
        },
      )

      expect(emptyWrapper.findAll('tbody tr')).toHaveLength(1)
      expect(emptyWrapper.text()).toContain('무지주소유자')
    })

    it('SiteOwnerForm과 SiteContractForm은 권한에 따라 버튼을 숨기고 SiteContractForm은 빈 숫자 공백을 유효로 오인하지 않는다', async () => {
      usePermission().setProjectPermissions([PERM.SITE_READ])
      const ownerForm = mount(SiteOwnerForm, {
        props: { owner: makeSiteOwner(), project: 10 },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          directives: { maska: {} },
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })
      expect(ownerForm.text()).not.toContain('저장')
      expect(ownerForm.text()).not.toContain('삭제')

      usePermission().setProjectPermissions([PERM.SITE_READ, PERM.SITE_UPDATE])
      const contract: SiteContract = {
        pk: 30,
        project: 10,
        owner: 1,
        contract_date: '2026-01-01',
        total_price: 500000000,
        contract_area: 100,
        down_pay1: 50000000,
        down_pay1_date: null,
        down_pay1_is_paid: true,
        down_pay2: null,
        down_pay2_date: null,
        down_pay2_is_paid: false,
        inter_pay1: null,
        inter_pay1_date: null,
        inter_pay1_is_paid: false,
        inter_pay2: null,
        inter_pay2_date: null,
        inter_pay2_is_paid: false,
        remain_pay: 450000000,
        remain_pay_date: null,
        remain_pay_is_paid: false,
        ownership_completion: false,
        acc_bank: '국민은행',
        acc_number: '111-222',
        acc_owner: '김소유',
        note: '',
        site_cont_files: [],
      }
      const contWrapper = mount(SiteContractForm, {
        props: { project: 10, contract },
        global: {
          plugins: [makeVuetify(), CoreuiVue],
          stubs: {
            ...commonStubs,
            ConfirmModal: makeConfirmModalStub(),
            AlertModal: makeAlertModalStub(),
          },
        },
      })

      expect(contWrapper.text()).toContain('저장')
      expect(contWrapper.text()).not.toContain('삭제')

      const totalPriceInput = contWrapper.find('input[placeholder="총 매매가격"]')
      await totalPriceInput.setValue('')
      await nextTick()
      const saveBtn = contWrapper.findAll('button').find(b => b.text() === '저장')!
      expect(saveBtn.attributes('disabled')).toBeDefined()
    })
  })
})
