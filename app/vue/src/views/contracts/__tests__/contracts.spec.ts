import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createVuetify } from 'vuetify'
import CoreuiVue from '@coreui/vue'
import api from '@/api'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import type { Contractor, OrderGroup, Succession } from '@/store/types/contract'
import type { Project } from '@/store/types/project'
import ListController from '../List/components/ListController.vue'
import ContractSummary from '../List/components/ContractSummary.vue'
import ContSummary from '../Status/components/ContSummary.vue'
import Unit from '../Status/components/Unit.vue'
import AddRequiredDocs from '../Manage/components/manages/AddRequiredDocs.vue'
import SuccessionRow from '../Succession/components/Succession.vue'

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

vi.mock('@/composables/usePerms', () => ({
  usePerms: () => ({
    can: () => true,
    PERM: {
      CONTRACT_READ: 'contract.read',
      CONTRACT_CREATE: 'contract.create',
      CONTRACT_UPDATE: 'contract.update',
      CONTRACT_DELETE: 'contract.delete',
      CONTRACT_RELEASE: 'contract.release',
      CONTRACT_SUCCESSION: 'contract.succession',
    },
  }),
}))

vi.mock('@/composables/usePerms.ts', () => ({
  usePerms: () => ({
    can: () => true,
    PERM: {
      CONTRACT_READ: 'contract.read',
      CONTRACT_CREATE: 'contract.create',
      CONTRACT_UPDATE: 'contract.update',
      CONTRACT_DELETE: 'contract.delete',
      CONTRACT_RELEASE: 'contract.release',
      CONTRACT_SUCCESSION: 'contract.succession',
    },
  }),
}))

const mockedApi = vi.mocked(api)
const vuetify = createVuetify()

const createContractTestRouter = async (initialPath = '/contracts/succession?project=5') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/contracts/succession', name: '권리 의무 승계', component: { template: '<div />' } },
      {
        path: '/contracts/manage/:contractorId',
        name: '계약 상세 보기',
        component: { template: '<div />' },
      },
    ],
  })
  await router.push(initialPath)
  await router.isReady()
  return router
}

describe('contracts module regression suite', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('useContract store fixes', () => {
    it('queries available_for_contract when editing a contract key unit and omits conflicting available param', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: [] } })
      const store = useContract()

      await store.fetchKeyUnitList({ project: 1, unit_type: 2, contract: 42 })

      expect(mockedApi.get).toHaveBeenCalledWith('/key-unit/', {
        params: {
          project: 1,
          unit_type: 2,
          available_for_contract: 42,
        },
      })
    })

    it('resets isLoading even when fetchContractList fails and encodes contractor search params', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('network'))
      const store = useContract()

      await store.fetchContractList({ project: 1 })
      expect(store.isLoading).toBe(false)

      mockedApi.get.mockResolvedValueOnce({ data: { results: [{ pk: 10 }] } })
      await store.fetchContractorList(1, '홍&길동')
      expect(mockedApi.get).toHaveBeenLastCalledWith('/contractor/', {
        params: {
          contract__project: 1,
          search: '홍&길동',
          is_active: true,
        },
      })
    })

    it('preserves consultation page & status across updates and backs up one page when deleting last item', async () => {
      const store = useContract()
      mockedApi.get.mockResolvedValue({
        data: {
          count: 11,
          next: null,
          previous: 'prev',
          results: [{ pk: 99, contractor: 7, status: 'pending' }],
        },
      })
      await store.fetchConsultationLogs(7, { page: 2, status: 'pending' })

      expect(store.consultationLogPagination.page).toBe(2)
      expect(store.consultationLogPagination.status).toBe('pending')

      mockedApi.patch.mockResolvedValueOnce({ data: { pk: 99, contractor: 7 } })
      await store.updateConsultationLog(99, { title: '수정' })
      expect(mockedApi.get).toHaveBeenLastCalledWith(
        '/contractor-consultations/?contractor=7&page=2&status=pending',
      )

      mockedApi.delete.mockResolvedValueOnce({})
      await store.deleteConsultationLog(99, 7)
      expect(mockedApi.get).toHaveBeenLastCalledWith(
        '/contractor-consultations/?contractor=7&page=1&status=pending',
      )
    })

    it('rethrows release/succession errors and refreshes contractor on release update or succession status', async () => {
      const store = useContract()

      mockedApi.post.mockRejectedValueOnce(new Error('400'))
      await expect(
        store.createRelease({
          pk: 0,
          project: 1,
          contractor: 15,
          request_date: '2026-02-01',
          release_type: '1',
          status: '1',
          refund_amount: null,
          refund_account_bank: null,
          refund_account_number: null,
          refund_account_depositor: null,
          refund_completion_date: null,
          completion_date: null,
          note: '',
        }),
      ).rejects.toThrow('400')

      mockedApi.post.mockResolvedValueOnce({ data: { pk: 3, project: 1, contractor: 15 } })
      mockedApi.get.mockResolvedValue({ data: { results: [], count: 0, pk: 15 } })
      await store.createRelease({
        pk: 0,
        project: 1,
        contractor: 15,
        request_date: '2026-02-01',
        release_type: '1',
        status: '1',
        refund_amount: null,
        refund_account_bank: null,
        refund_account_number: null,
        refund_account_depositor: null,
        refund_completion_date: null,
        completion_date: null,
        note: '',
      })
      expect(mockedApi.get).toHaveBeenCalledWith('/contractor/15/?project=')

      mockedApi.post.mockResolvedValueOnce({
        data: { pk: 8, status: '1', seller: { pk: 20 }, buyer: { pk: 21 } },
      })
      await store.createSuccession({
        contract: 1,
        seller: 20,
        buyer: null,
        apply_date: '2026-02-01',
        trading_date: '2026-02-01',
        status: '1',
        project: 1,
        page: 1,
      })
      expect(mockedApi.get).toHaveBeenCalledWith('/contractor/20/?project=')
    })
  })

  describe('Status & ProjectData summaries', () => {
    it('counts status 3 contracts in unitSummary/allUnitSummary and renders changing class on Unit', () => {
      const pDataStore = useProjectData()
      const contStore = useContract()

      const makeUnit = (
        pk: number,
        sort: '1' | '5',
        status: '1' | '2' | '3',
      ): (typeof pDataStore.houseUnitList)[number] =>
        ({
          pk,
          unit_type: { pk: 1, sort },
          is_hold: false,
          key_unit: {
            pk,
            unit_code: `U-${pk}`,
            houseunit: null,
            contract: {
              pk,
              contractor: { pk: pk + 100, name: `계약자${pk}`, status },
            },
          },
        }) as unknown as (typeof pDataStore.houseUnitList)[number]

      pDataStore.houseUnitList = [
        makeUnit(1, '1', '2'),
        makeUnit(2, '1', '3'),
        makeUnit(3, '5', '2'),
      ]

      expect(pDataStore.unitSummary.contNum).toBe(2)
      expect(pDataStore.allUnitSummary.contNum).toBe(3)

      contStore.subsSummaryList = []
      contStore.contSummaryList = [{ order_group: 1, unit_type: 1, conts_num: 3, price_sum: 0 }]

      const wrapper = mount(ContSummary, {
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { 'v-icon': true },
        },
      })
      expect(wrapper.text()).toContain('3')

      const unitWrapper = mount(Unit, {
        props: {
          unit: {
            bldg: 1,
            line: 1,
            floor: 1,
            name: '102',
            color: '#fff',
            is_hold: false,
            hold_reason: '',
            key_unit: {
              pk: 2,
              contract: {
                pk: 2,
                contractor: { pk: 102, name: '변경중', status: '3' },
              },
            },
          },
          floor: 1,
          line: 1,
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { 'router-link': { template: '<a><slot /></a>' }, 'v-tooltip': true },
        },
      })
      expect(unitWrapper.find('.status').classes()).toContain('changing')
    })
  })

  describe('List, Manage & Succession component behaviors', () => {
    it('emits only a single filter call when ListController.resetForm runs', async () => {
      const wrapper = mount(ListController, {
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { DatePicker: true },
        },
      })

      const vm = wrapper.vm as unknown as {
        combinedStatus: string
        resetForm: () => Promise<void>
      }
      vm.combinedStatus = 'q1'
      await flushPromises()
      wrapper.emitted('cont-filtering')?.splice(0)

      await vm.resetForm()
      await flushPromises()
      expect(wrapper.emitted('cont-filtering')).toHaveLength(1)
    })

    it('renders matching fallback column count in ContractSummary when orderGroupList is empty', () => {
      const pDataStore = useProjectData()
      pDataStore.unitTypeList = [
        { pk: 1, name: '84A', sort: '1', color: '#111', num_unit: 10 },
      ] as unknown as typeof pDataStore.unitTypeList
      const contStore = useContract()
      contStore.orderGroupList = [] as OrderGroup[]

      const wrapper = mount(ContractSummary, {
        props: {
          project: { pk: 1, name: '테스트현장', num_unit: 10 } as unknown as Project,
        },
        global: {
          plugins: [vuetify, CoreuiVue],
          stubs: { CIcon: true },
        },
      })

      const bodyRows = wrapper.findAll('tbody tr')
      expect(bodyRows[0].findAll('td, th').length).toBe(bodyRows[1].findAll('td, th').length)
    })

    it('prevents double save in AddRequiredDocs endEdit when enter and blur fire consecutively', async () => {
      mockedApi.get.mockResolvedValue({ data: { results: [] } })
      mockedApi.post.mockResolvedValue({ data: { pk: 501, submitted_quantity: 2 } })

      const router = await createContractTestRouter('/contracts/manage/77')
      const contStore = useContract()
      contStore.requiredDocsList = [
        {
          pk: 10,
          sort: 'proof',
          document_name: '신분증',
          require_type: 'required',
          required: '필수',
          quantity: 1,
        } as unknown as (typeof contStore.requiredDocsList)[number] & { sort: string },
      ]

      const wrapper = mount(AddRequiredDocs, {
        props: { sortFilter: 'proof' },
        global: {
          plugins: [router, vuetify, CoreuiVue],
          stubs: {
            ConfirmModal: {
              template: '<div />',
              setup(_, { expose }) {
                expose({ callModal: vi.fn(), close: vi.fn() })
              },
            },
          },
        },
      })

      const qtyCell = wrapper.findAll('td')[3]
      await qtyCell.trigger('dblclick')
      const input = wrapper.find('input[type="number"]')
      await input.setValue('2')
      await input.trigger('keydown.enter')
      await input.trigger('blur')
      await flushPromises()

      expect(mockedApi.post).toHaveBeenCalledTimes(1)
    })

    it('Succession row invokes call-form without stripping route.query', async () => {
      const router = await createContractTestRouter('/contracts/succession?project=5')
      const wrapper = mount(SuccessionRow, {
        props: {
          succession: {
            pk: 11,
            status: '1',
            contract: { pk: 1, serial_number: 'S-001' },
            seller: { pk: 10, name: '양도인' } as Contractor,
            buyer: { pk: 11, name: '양수인' } as unknown as Succession['buyer'],
            apply_date: '2026-01-01',
            trading_date: '2026-01-01',
            approval_date: null,
            note: '',
          } as unknown as Succession,
        },
        global: {
          plugins: [router, vuetify, CoreuiVue],
        },
      })

      await wrapper.find('a').trigger('click')
      await flushPromises()
      expect(router.currentRoute.value.query.project).toBe('5')
      expect(wrapper.emitted('call-form')).toHaveLength(1)
    })
  })
})
