<script lang="ts" setup>
import { computed, onBeforeMount, provide, reactive, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin6'
import { message } from '@/utils/helper'
import type { Project } from '@/store/types/project'
import type { OrderGroup } from '@/store/types/contract'
import type { Price, PriceFilter } from '@/store/types/payment'
import { usePayment } from '@/store/pinia/payment'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import PriceSelectForm from '@/views/projects/Price/components/PriceSelectForm.vue'
import PriceFormList from '@/views/projects/Price/components/PriceFormList.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const RefAlertModal = ref()
const selectForm = ref()
const sort = ref<'1' | '2' | '3' | '4' | '5' | '6'>('1')
const order_group = ref<number | null>(null)
const unit_type = ref<number | null>(null)
const priceSetting = ref<'1' | '2' | '3' | ''>('2')

const pFilters = reactive<PriceFilter>({
  project: null,
  order_group: null,
  unit_type: null,
})

const priceMessage = ref('')

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contStore = useContract()
const orderGroupList = computed(() => contStore.orderGroupList)
const default_order = computed(
  () => orderGroupList.value.find(o => o.is_default_for_uncontracted)?.pk,
)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)

const condTexts = computed(() => {
  const orderText =
    orderGroupList.value.find((o: OrderGroup) => o.pk === order_group.value)?.name || ''
  const typeText = unitTypeList.value.find(t => t.pk === unit_type.value)?.name || ''
  return { orderText, typeText }
})

provide('condTexts', condTexts)

const fetchOrderGroupList = (projId: number, ogSort: '' | '1' | '2' = '') =>
  contStore.fetchOrderGroupList(projId, ogSort)
const previewContractPriceUpdate = (projectId: number) =>
  contStore.previewContractPriceUpdate(projectId)
const bulkUpdateContractPrices = (projectId: number) =>
  contStore.bulkUpdateContractPrices(projectId)

const fetchTypeList = (projId: number, typeSort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchTypeList(projId, typeSort)
const fetchFloorTypeList = (projId: number, floorSort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchFloorTypeList(projId, floorSort)

const payStore = usePayment()
const fetchPriceList = (filters: PriceFilter) => payStore.fetchPriceList(filters)
const createPrice = (payload: Price) => payStore.createPrice(payload)
const updatePrice = (payload: Price) => payStore.updatePrice(payload)
const deletePrice = (payload: PriceFilter & { pk: number }) => payStore.deletePrice(payload)
const fetchPayOrderList = (proj: number, paySortIn?: string) =>
  payStore.fetchPayOrderList(proj, paySortIn)

// 구분 선택 시 실행 함수
const sortSelect = (projSort: '1' | '2' | '3' | '4' | '5' | '6') => {
  sort.value = projSort
  const ogSort = projSort !== '1' ? '2' : ''
  order_group.value = null
  unit_type.value = null
  pFilters.order_group = null
  pFilters.unit_type = null
  payStore.priceList = []

  if (project.value) {
    fetchOrderGroupList(project.value, ogSort)
    fetchFloorTypeList(project.value, sort.value).then(() => {
      pFilters.project = project.value
      pFilters.order_group = order_group.value
      pFilters.unit_type = unit_type.value
      fetchPriceList(pFilters)
    })
  }
}

// 차수 선택 시 실행 함수
const orderSelect = (order: number | null) => {
  order_group.value = order
  unit_type.value = null
  pFilters.order_group = order
  pFilters.unit_type = null
  if (project.value) fetchTypeList(project.value, sort.value)
  priceMessage.value = !order
    ? '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
    : '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.'
  payStore.priceList = []
}

// 타입 선택 시 실행 함수
const typeSelect = (type: number | null) => {
  unit_type.value = type
  pFilters.unit_type = type
  priceMessage.value = !type ? '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.' : ''
  if (type) {
    priceSetting.value = unitTypeList.value.find(t => t.pk === type)?.price_setting || '2'
  } else {
    priceSetting.value = '2'
  }

  if (project.value && sort.value) {
    fetchFloorTypeList(project.value, sort.value).then(() => {
      pFilters.project = project.value
      pFilters.order_group = order_group.value
      pFilters.unit_type = unit_type.value
      fetchPriceList(pFilters)
    })
  }
}

const onCreatePrice = (payload: Price) => createPrice(payload)
const onUpdatePrice = (payload: Price) => updatePrice(payload)
const onDeletePrice = (pk: number) => deletePrice({ pk, ...pFilters })

const contPriceView = async () => {
  if (!project.value) return

  try {
    const result = await previewContractPriceUpdate(project.value)
    if (result.success) {
      const { data } = result
      message(
        'info',
        '미리보기 완료',
        `${data.total_contracts}개 계약 업데이트 대상이 확인되었습니다.`,
        5000,
      )
    }
  } catch (error) {
    console.error('계약 가격 일괄 업데이트 미리보기 실패:', error)
  }
}

const contPriceSet = async () => {
  if (!project.value) return

  if (!default_order.value) {
    RefAlertModal.value.callModal(
      '알림 : 미계약세대 기본설정 차수 미설정',
      '이 작업을 진행하려면 [차수분류]의 데이터 중 "미계약세대 기본설정" 차수를 지정하세요.',
      '',
      'warning',
    )
  } else {
    try {
      loading.value = true
      await bulkUpdateContractPrices(project.value)
    } catch (error) {
      console.error('계약 가격 일괄 업데이트 실패:', error)
    } finally {
      loading.value = false
    }
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    fetchOrderGroupList(pk),
    fetchTypeList(pk, sort.value),
    fetchFloorTypeList(pk, sort.value),
    fetchPayOrderList(pk, '1,4,5,6,7'),
  ])
  priceMessage.value = '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
}

const dataReset = () => {
  order_group.value = null
  unit_type.value = null
  pFilters.order_group = null
  pFilters.unit_type = null
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  pDataStore.floorTypeList = []
  payStore.payOrderList = []
  selectForm.value?.dataReset()
}

watch(
  () => project.value,
  newProjId => {
    payStore.priceList = []
    dataReset()
    if (newProjId) dataSetup(newProjId)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await dataSetup(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <PriceSelectForm
          ref="selectForm"
          :project="project as number"
          :orders="orderGroupList"
          :types="unitTypeList"
          @on-sort-select="sortSelect"
          @on-order-select="orderSelect"
          @on-type-select="typeSelect"
          @cont-price-view="contPriceView"
          @cont-price-set="contPriceSet"
        />
        <PriceFormList
          :msg="priceMessage"
          :p-filters="pFilters"
          :price-setting="priceSetting"
          @on-create="onCreatePrice"
          @on-update="onUpdatePrice"
          @on-delete="onDeletePrice"
        />
      </CCardBody>
    </ContentBody>

    <AlertModal ref="RefAlertModal" />
  </ProjectAuthGuard>
</template>
