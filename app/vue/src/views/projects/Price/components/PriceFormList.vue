<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import { type Price as P } from '@/store/types/payment'
import { usePayment } from '@/store/pinia/payment'
import { useProjectData } from '@/store/pinia/project_data'
import Price from '@/views/projects/Price/components/Price.vue'

defineProps({
  msg: { type: String, default: '' },
  pFilters: { type: Object, default: null },
  priceSetting: { type: String, default: '2' },
})
const emit = defineEmits(['on-create', 'on-update', 'on-delete'])

const projectDataStore = useProjectData()
const floorTypeList = computed(() => projectDataStore.floorTypeList)

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)
const priceList = computed(() => paymentStore.priceList)

const getPrice = (floor: number) => priceList.value.filter((p: P) => p.unit_floor_type === floor)[0]

const onCreate = (payload: P) => emit('on-create', payload)
const onUpdate = (payload: P) => emit('on-update', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 7%" />
      <col style="width: 7%" />
      <col style="width: 7%" />
      <col style="width: 8%" />
      <col style="width: 7%" />
      <col style="width: 7%" />
      <col style="width: 8%" />
      <!--      <col style="width: 7%" />-->
      <!--      <col style="width: 7%" />-->
      <!--      <col style="width: 7%" />-->
      <!--      <col style="width: 7%" />-->
      <!--      <col style="width: 7%" />-->
      <col v-if="write_project" style="width: 7%" />
      <col v-if="write_project" style="width: 5%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>차수</CTableHeaderCell>
        <CTableHeaderCell>타입</CTableHeaderCell>
        <CTableHeaderCell>층별 조건</CTableHeaderCell>
        <CTableHeaderCell>건물가(단위:원)</CTableHeaderCell>
        <CTableHeaderCell>대지가(단위:원)</CTableHeaderCell>
        <CTableHeaderCell>부가세(단위:원)</CTableHeaderCell>
        <CTableHeaderCell>기준공급가(단위:원)</CTableHeaderCell>
        <!--        <CTableHeaderCell>계약금(단위:원)</CTableHeaderCell>-->
        <!--        <CTableHeaderCell>업무대행비(단위:원)</CTableHeaderCell>-->
        <!--        <CTableHeaderCell>업대비 포함 여부</CTableHeaderCell>-->
        <!--        <CTableHeaderCell>중도금(단위:원)</CTableHeaderCell>-->
        <!--        <CTableHeaderCell>잔금(단위:원)</CTableHeaderCell>-->
        <CTableHeaderCell v-if="write_project">비고</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">특별약정 추가</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="!msg">
      <Price
        v-for="floor in floorTypeList"
        :key="floor.pk"
        :p-filters="pFilters"
        :floor="floor"
        :price="getPrice(floor.pk)"
        :pay-orders="payOrderList"
        @on-create="onCreate"
        @on-update="onUpdate"
        @on-delete="onDelete"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 13 : 12" class="text-center p-5 text-info">
          {{ msg }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableBody v-if="!msg && floorTypeList.length === 0">
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 13 : 12" class="text-center p-5 text-danger">
          <p>
            <CIcon name="cilWarning" />
            등록된 [
            <router-link :to="{ name: '층별 조건 등록' }">층별조건</router-link>
            ] 데이터가 없습니다! 먼저 [
            <router-link :to="{ name: '층별 조건 등록' }">층별조건</router-link>
            ]을 등록한 후 진행하세요.
          </p>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
