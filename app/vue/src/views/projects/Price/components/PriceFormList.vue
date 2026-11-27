<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import { usePayment } from '@/store/pinia/payment'
import { useProjectData } from '@/store/pinia/project_data'
import type { Price as P, PriceFilter } from '@/store/types/payment'
import Price from '@/views/projects/Price/components/Price.vue'

defineProps<{
  msg?: string
  pFilters: PriceFilter
  priceSetting?: string
}>()

const emit = defineEmits<{
  (e: 'on-create', payload: P): void
  (e: 'on-update', payload: P): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projectDataStore = useProjectData()
const floorTypeList = computed(() => projectDataStore.floorTypeList)

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)
const priceList = computed(() => paymentStore.priceList)

const getPrice = (floor: number) => priceList.value.find((p: P) => p.unit_floor_type === floor)

const onCreate = (payload: P) => emit('on-create', payload)
const onUpdate = (payload: P) => emit('on-update', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup v-if="canProjectUpdate">
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 12%" />
      <col style="width: 14%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
    </colgroup>
    <colgroup v-else>
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 16%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 14%" />
      <col style="width: 16%" />
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
        <CTableHeaderCell v-if="canProjectUpdate">비고</CTableHeaderCell>
        <CTableHeaderCell v-if="canProjectUpdate">특별약정 추가</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="!msg && floorTypeList.length > 0">
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

    <CTableBody v-else-if="msg">
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 9 : 7" class="text-center p-5 text-info">
          {{ msg }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="canProjectUpdate ? 9 : 7" class="text-center p-5 text-danger">
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
