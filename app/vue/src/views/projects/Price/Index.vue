<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, provide } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePayment, type PriceFilter } from '@/store/pinia/payment'
import { useProjectData } from '@/store/pinia/project_data'
import { type OrderGroup, type SimpleCont, type UnitType } from '@/store/types/contract'
import { type Price } from '@/store/types/payment'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PriceSelectForm from '@/views/projects/Price/components/PriceSelectForm.vue'
import PriceFormList from '@/views/projects/Price/components/PriceFormList.vue'

const selectForm = ref()
const order_group = ref<number | null>(null)
const unit_type = ref<number | null>(null)

const pFilters = reactive<PriceFilter>({
  project: null,
  order_group: null,
  unit_type: null,
})

const priceMessage = ref('')

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const contStore = useContract()
const contList = computed(() => contStore.contList)
const orderGroupList = computed(() => contStore.orderGroupList)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)

const condTexts = computed(() => {
  // 차수명과 타입명 구하기
  const orderText = orderGroupList.value
    .filter((o: OrderGroup) => o.pk == order_group.value)
    .map((o: OrderGroup) => o.order_group_name)[0]
  const typeText = unitTypeList.value
    .filter((t: UnitType) => t.pk == unit_type.value)
    .map((t: UnitType) => t.name)[0]
  return { orderText, typeText }
})

provide('condTexts', condTexts)

const fetchContList = (projId: number) => contStore.fetchContList(projId)
const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)
const allContPriceSet = (payload: SimpleCont) => contStore.allContPriceSet(payload)

const fetchTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchTypeList(projId, sort)
const fetchFloorTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchFloorTypeList(projId, sort)

const payStore = usePayment()
const fetchPriceList = (pFilters: PriceFilter) => payStore.fetchPriceList(pFilters)
const createPrice = (payload: Price) => payStore.createPrice(payload)
const updatePrice = (payload: Price) => payStore.updatePrice(payload)
const deletePrice = (payload: PriceFilter & { pk: number }) => payStore.deletePrice(payload)

// 차수 선택 시 실행 함수
const orderSelect = (order: number) => {
  order_group.value = order // order_group pk 값 할당
  const sort = orderGroupList.value.filter(o => o.pk == order).map(o => o.sort)[0]
  if (project.value) fetchTypeList(project.value, sort !== '1' ? undefined : '1')
  priceMessage.value = !order
    ? '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
    : '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.'
  payStore.priceList = [] // 가격 상태 초기화
}
// 타입 선택 시 실행 함수
const typeSelect = (type: number) => {
  const sort = unitTypeList.value.filter(tp => tp.pk == type)[0].sort || ''
  unit_type.value = type // unit_type pk 값 할당
  priceMessage.value = !type ? '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.' : ''
  if (project.value && sort) {
    fetchFloorTypeList(project.value, sort).then(() => {
      pFilters.project = project.value
      pFilters.order_group = order_group.value
      pFilters.unit_type = unit_type.value
      fetchPriceList(pFilters) // 가격 상태 저장 실행
    })
  }
}

const onCreatePrice = (payload: Price) => createPrice(payload)
const onUpdatePrice = (payload: Price) => updatePrice(payload)
const onDeletePrice = (pk: number) => deletePrice({ ...{ pk }, ...pFilters })

const contPriceSet = () => {
  const cont = contList.value[0]
  allContPriceSet({ ...cont })
}

const dataSetup = (pk: number) => {
  fetchContList(pk)
  fetchOrderGroupList(pk)
  fetchTypeList(pk)
  fetchFloorTypeList(pk)
  priceMessage.value = '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
}

const dataReset = () => {
  contStore.contList = []
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  pDataStore.floorTypeList = []
  selectForm.value.dataReset()
}

const projSelect = (target: number | null) => {
  payStore.priceList = []
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <PriceSelectForm
        ref="selectForm"
        :project="project as number"
        :orders="orderGroupList"
        :types="unitTypeList"
        @on-order-select="orderSelect"
        @on-type-select="typeSelect"
        @cont-price-set="contPriceSet"
      />
      <PriceFormList
        :msg="priceMessage"
        :p-filters="pFilters"
        @on-create="onCreatePrice"
        @on-update="onUpdatePrice"
        @on-delete="onDeletePrice"
      />
    </CCardBody>
  </ContentBody>
</template>
