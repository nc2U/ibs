<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { type OrderGroup } from '@/store/types/contract'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  project: { type: Number, default: null },
  orders: { type: Object as PropType<OrderGroup[]>, default: null },
  types: { type: Object, default: null },
})

const emit = defineEmits(['on-order-select', 'on-type-select', 'cont-price-set'])

const refConfirmModal = ref()

const order = ref<number | null>(null)
const type = ref<number | null>(null)

const dataReset = () => {
  order.value = null
  type.value = null
}
defineExpose({ dataReset })

const onOrderSelect = (e: Event) => {
  type.value = null
  emit('on-order-select', (e.target as HTMLSelectElement).value)
}
const onTypeSelect = (e: Event) => emit('on-type-select', (e.target as HTMLSelectElement).value)

const accStore = useAccount()
const superAuth = computed(() => accStore.superAuth)

const contPriceSet = () => refConfirmModal.value.callModal()

const modalAction = () => {
  emit('cont-price-set')
  refConfirmModal.value.close()
}
</script>

<template>
  <CCallout color="warning" class="pb-2 mb-4">
    <CRow>
      <CCol md="4" class="mb-2">
        <CRow>
          <CFormLabel for="sel1" class="col-sm-3 col-form-label"> 차수선택</CFormLabel>
          <CCol sm="9">
            <CFormSelect
              id="sel1"
              v-model.number="order"
              :disabled="!project"
              @change="onOrderSelect"
            >
              <option value="">---------</option>
              <option v-for="o in orders" :key="o.pk" :value="o.pk">
                {{ o.order_group_name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="4" class="mb-2">
        <CRow>
          <CFormLabel for="sel2" class="col-sm-3 col-form-label"> 타입선택</CFormLabel>
          <CCol sm="9">
            <CFormSelect id="sel2" v-model="type" :disabled="!order" @change="onTypeSelect">
              <option value="">---------</option>
              <option v-for="t in types" :key="t.pk" :value="t.pk">
                {{ t.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="4" class="mb-2">
        <CRow class="justify-content-end">
          <CCol xl="6" class="d-grid gap-2">
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
      <v-icon icon="mdi mdi-sync-alert" color="danger" class="mr-2" />
    </template>
    <template #header> 전체 계약건 공급가 / 계약금 재설정</template>
    <template #default>
      <p>
        이 작업은 현재 등록된 전체 계약 건의 공급 가격 및 계약 금액 정보를 현재 등록된 공급 가격 및
        계약 금액 데이터로 일괄 변경합니다. <br />
      </p>
      <p>
        이 작업은 수 분 정도 소요될 수 있습니다. 전체 계약 건 개별 공급가격 및 계약금액을 현재
        등록된 정보로 재설정하시겠습니까?
      </p>
    </template>
    <template #footer>
      <v-btn color="blue-grey-darken-2" @click="modalAction">재설정</v-btn>
    </template>
  </ConfirmModal>
</template>
