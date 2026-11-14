<script lang="ts" setup>
import { ref, computed, type PropType, onMounted } from 'vue'
import { useAccount } from '@/store/pinia/account'
import type { OrderGroup } from '@/store/types/contract'
import type { UnitType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  project: { type: Number, default: null },
  orders: { type: Array as PropType<OrderGroup[]>, default: () => [] },
  types: { type: Array as PropType<UnitType[]>, default: () => [] },
})

const emit = defineEmits<{
  (e: 'on-sort-select', sort: '1' | '2' | '3' | '4' | '5' | '6'): void
  (e: 'on-order-select', order: number | null): void
  (e: 'on-type-select', type: number | null): void
  (e: 'cont-price-view'): void
  (e: 'cont-price-set'): void
}>()

const refConfirmModal = ref()

const form = ref<{
  sort: '1' | '2' | '3' | '4' | '5' | '6'
  order: number | null
  type: number | null
}>({
  sort: '1',
  order: null,
  type: null,
})

const dataReset = () => {
  form.value.sort = '1'
  form.value.order = null
  form.value.type = null
}

defineExpose({ dataReset })

const onSortSelect = (e: Event) => {
  form.value.order = null
  form.value.type = null
  emit('on-sort-select', (e.target as HTMLSelectElement).value as any)
}

const onOrderSelect = (e: Event) => {
  form.value.type = null
  const val = (e.target as HTMLSelectElement).value
  emit('on-order-select', val ? Number(val) : null)
}

const onTypeSelect = (e: Event) => {
  const val = (e.target as HTMLSelectElement).value
  emit('on-type-select', val ? Number(val) : null)
}

const accStore = useAccount()
const superAuth = computed(() => accStore.superAuth)

const contPriceSet = () => refConfirmModal.value.callModal()

const preViewModalAction = () => {
  emit('cont-price-view')
  refConfirmModal.value.close()
}

const bulkUpdateModalAction = () => {
  emit('cont-price-set')
  refConfirmModal.value.close()
}

onMounted(() => {
  dataReset()
})
</script>

<template>
  <CCallout color="warning" class="pb-2 mb-4">
    <CRow>
      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel for="sel_sort" class="col-sm-4 col-form-label"> 구분</CFormLabel>
          <CCol sm="8">
            <CFormSelect id="sel_sort" v-model="form.sort" :disabled="!project" @change="onSortSelect">
              <option value="">---------</option>
              <option value="1">공동주택</option>
              <option value="2">오피스텔</option>
              <option value="3">숙박시설</option>
              <option value="4">지식산업센터</option>
              <option value="5">근린생활시설</option>
              <option value="6">기타</option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel for="sel_order" class="col-sm-4 col-form-label"> 차수선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect
              id="sel_order"
              v-model.number="form.order"
              :disabled="!project"
              @change="onOrderSelect"
            >
              <option value="">---------</option>
              <option v-for="o in orders" :key="o.pk" :value="o.pk">
                {{ o.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow>
          <CFormLabel for="sel_type" class="col-sm-4 col-form-label"> 타입선택</CFormLabel>
          <CCol sm="8">
            <CFormSelect
              id="sel_type"
              v-model.number="form.type"
              :disabled="!form.order"
              @change="onTypeSelect"
            >
              <option value="">---------</option>
              <option v-for="t in types" :key="t.pk" :value="t.pk">
                {{ t.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="3" class="mb-2">
        <CRow class="justify-content-end">
          <CCol xl="8" class="d-grid gap-2">
            <v-btn
              v-if="superAuth"
              type="button"
              color="blue-grey-darken-2"
              :disabled="!project"
              @click="contPriceSet"
            >
              전체 계약건 공급가 재설정
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>

  <ConfirmModal ref="refConfirmModal">
    <template #icon>
      <v-icon icon="mdi-sync-alert" color="danger" class="me-2" />
    </template>
    <template #header> 전체 계약건 공급가 / 계약금 재설정</template>
    <template #default>
      <p>
        이 작업은 현재 등록된 전체 계약 건의 공급 가격 및 계약 금액 정보를 현재 등록된 공급 가격 및
        계약 금액 데이터로 일괄 반영하여 변경합니다. <br />
      </p>
      <p>
        이 작업은 수 분 정도 소요될 수 있습니다. 전체 계약 건 개별 공급가격 및 계약금액을 현재
        등록된 정보로 일괄 재설정하시겠습니까?
      </p>
    </template>
    <template #footer>
      <v-btn color="light-green-darken-3" size="small" @click="preViewModalAction">미리보기</v-btn>
      <v-btn color="blue-grey-darken-1" size="small" @click="bulkUpdateModalAction">
        전체 공급가 재설정
      </v-btn>
    </template>
  </ConfirmModal>
</template>
