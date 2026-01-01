<script lang="ts" setup>
import { computed, onBeforeMount, provide, reactive, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin6'
import { message } from '@/utils/helper.ts'
import type { Project } from '@/store/types/project.ts'
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
  () => orderGroupList.value.filter(o => o.is_default_for_uncontracted)[0]?.pk,
)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)

const condTexts = computed(() => {
  // 차수명과 타입명 구하기
  const orderText = orderGroupList.value
    .filter((o: OrderGroup) => o.pk == order_group.value)
    .map((o: OrderGroup) => o.name)[0]
  const typeText = unitTypeList.value.filter(t => t.pk == unit_type.value).map(t => t.name)[0]
  return { orderText, typeText }
})

provide('condTexts', condTexts)

const fetchOrderGroupList = (projId: number, sort: '' | '1' | '2' = '') =>
  contStore.fetchOrderGroupList(projId, sort)
const previewContractPriceUpdate = (projectId: number) =>
  contStore.previewContractPriceUpdate(projectId)
const bulkUpdateContractPrices = (projectId: number) =>
  contStore.bulkUpdateContractPrices(projectId)

const fetchTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchTypeList(projId, sort)
const fetchFloorTypeList = (projId: number, sort?: '1' | '2' | '3' | '4' | '5' | '6') =>
  pDataStore.fetchFloorTypeList(projId, sort)

const payStore = usePayment()
const fetchPriceList = (pFilters: PriceFilter) => payStore.fetchPriceList(pFilters)
const createPrice = (payload: Price) => payStore.createPrice(payload)
const updatePrice = (payload: Price) => payStore.updatePrice(payload)
const deletePrice = (payload: PriceFilter & { pk: number }) => payStore.deletePrice(payload)
const fetchPayOrderList = (proj: number, pay_sort__in?: string) =>
  payStore.fetchPayOrderList(proj, pay_sort__in)

// 구분 선택 시 실행 함수
const sortSelect = (proj_sort: any) => {
  sort.value = proj_sort
  const og_sort = proj_sort !== '1' ? '2' : ''

  if (project.value) {
    fetchOrderGroupList(project.value, og_sort)
    fetchFloorTypeList(project.value, sort.value).then(() => {
      pFilters.project = project.value
      pFilters.order_group = order_group.value
      pFilters.unit_type = unit_type.value
      fetchPriceList(pFilters) // 가격 상태 저장 실행
    })
  }
}

// 차수 선택 시 실행 함수
const orderSelect = (order: number) => {
  order_group.value = order // order_group pk 값 할당
  if (project.value) fetchTypeList(project.value, sort.value)
  priceMessage.value = !order
    ? '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
    : '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.'
  payStore.priceList = [] // 가격 상태 초기화
}

// 타입 선택 시 실행 함수
const typeSelect = (type: number) => {
  unit_type.value = type // unit_type pk 값 할당
  priceMessage.value = !type ? '공급가격을 입력하기 위해 [타입 정보]를 선택하여 주십시요.' : ''
  // type.price_setting -> '1', '2', '3'
  if (type) priceSetting.value = unitTypeList.value.filter(t => t.pk == type)[0].price_setting
  else priceSetting.value = '2'
  // '1' 이면 타입별 가격 설정
  // '2' 이면 층타입별 가격 설정
  // '3' 이면 호별 가격 설정

  if (project.value && sort.value) {
    fetchFloorTypeList(project.value, sort.value).then(() => {
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

const contPriceView = async () => {
  if (!project.value) return

  try {
    const result = await previewContractPriceUpdate(project.value)
    console.log('📋 계약 가격 업데이트 미리보기 결과:', result)

    if (result.success) {
      const { data } = result
      console.log(`✅ 프로젝트: ${data.project_info.project_name}`)
      console.log(`📊 총 업데이트 대상: 계약 ${data.total_contracts} 건`)
      console.log('📝 업데이트 계약 목록:', data.sample_contracts)

      message(
        'info',
        '미리보기 완료',
        `${data.total_contracts}개 계약 업데이트! 세부사항은 콘솔을 확인하세요!`,
        10000,
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
      const result = await bulkUpdateContractPrices(project.value)
      loading.value = false
      console.log('🔍 계약 가격 일괄 업데이트 결과:', result)

      if (result.debug_info) {
        console.log('🐛 디버그 정보:', result.debug_info)
      }
    } catch (error) {
      console.error('계약 가격 일괄 업데이트 실패:', error)
    }
  }
}

const dataSetup = (pk: number) => {
  fetchOrderGroupList(pk)
  fetchTypeList(pk, sort.value)
  fetchFloorTypeList(pk, sort.value)
  fetchPayOrderList(pk, '1,4,5,6,7')
  priceMessage.value = '공급가격을 입력하기 위해 [차수 정보]를 선택하여 주십시요.'
}

const dataReset = () => {
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  pDataStore.floorTypeList = []
  payStore.payOrderList = []
  selectForm.value.dataReset()
}

const projSelect = (target: number | null) => {
  payStore.priceList = []
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
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
          :pay-orders="payStore.payOrderList"
          @on-create="onCreatePrice"
          @on-update="onUpdatePrice"
          @on-delete="onDeletePrice"
        />
      </CCardBody>
    </ContentBody>

    <AlertModal ref="RefAlertModal" />
  </ProjectAuthGuard>
</template>
