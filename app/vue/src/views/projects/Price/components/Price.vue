<script lang="ts" setup>
import { ref, reactive, computed, watch, onMounted, onUpdated, inject, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import type { PayOrder, Price } from '@/store/types/payment'
import { type UnitFloorType } from '@/store/types/project'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import { numFormat } from '@/utils/baseMixins.ts'

const condTexts = inject<{ orderText: string; typeText: string }>('condTexts')

const props = defineProps({
  floor: { type: Object as PropType<UnitFloorType>, required: true },
  pFilters: { type: Object, default: null },
  price: { type: Object as PropType<Price>, default: null },
})

const emit = defineEmits(['on-create', 'on-update', 'on-delete'])

const refFormModal = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const form = reactive({
  price_build: null as number | null,
  price_land: null as number | null,
  price_tax: null as number | null,
  price: null as number | null,
  down_pay: null as number | null,
  biz_agency_fee: null as number | null,
  is_included_baf: false,
  middle_pay: null as number | null,
  remain_pay: null as number | null,
})

watch(form, val => {
  if (!val.price_build) form.price_build = null
  if (!val.price_land) form.price_land = null
  if (!val.price_tax) form.price_tax = null
  if (!val.price) form.price = null
  if (!val.down_pay) form.down_pay = null
  if (!val.biz_agency_fee) form.biz_agency_fee = null
  if (!val.is_included_baf) form.is_included_baf = false
  if (!val.middle_pay) form.middle_pay = null
  if (!val.remain_pay) form.remain_pay = null
})

watch(props, val => {
  if (val.price) dataSetup()
})

const btnColor = computed(() => (props.price ? 'success' : 'primary'))
const btnTitle = computed(() => (props.price ? '수정' : '등록'))

const formsCheck = computed(() => {
  if (props.price) {
    const a = form.price_build === props.price.price_build
    const b = form.price_land === props.price.price_land
    const c = form.price_tax === props.price.price_tax
    const d = form.price === props.price.price || !props.price
    const e = form.down_pay === props.price.down_pay || !props.price
    const f = form.biz_agency_fee === props.price.biz_agency_fee || !props.price
    const g = form.is_included_baf === props.price.is_included_baf || !props.price
    const h = form.middle_pay === props.price.middle_pay || !props.price
    const i = form.remain_pay === props.price.remain_pay || !props.price
    return a && b && c && d && e && f && g && h && i
  } else {
    return (
      !form.price_build &&
      !form.price_land &&
      !form.price_tax &&
      !form.price &&
      !form.down_pay &&
      !form.biz_agency_fee &&
      !form.is_included_baf &&
      !form.middle_pay &&
      !form.remain_pay
    )
  }
})

const onStorePrice = () => {
  if (write_project.value) {
    const payload = {
      ...props.pFilters,
      ...{ unit_floor_type: props.floor?.pk },
      ...form,
    }
    if (!props.price) emit('on-create', payload)
    else {
      const updatePayload = { ...{ pk: props.price.pk }, ...payload }
      emit('on-update', updatePayload)
    }
  } else refAlertModal.value.callModal()
}

const deletePrice = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else refAlertModal.value.callModal()
}
const modalAction = () => {
  emit('on-delete', props.price?.pk)
  refConfirmModal.value.close()
  dataReset()
}

const dataSetup = () => {
  if (props.price) {
    form.price_build = props.price.price_build
    form.price_land = props.price.price_land
    form.price_tax = props.price.price_tax
    form.price = props.price.price
    form.down_pay = props.price.down_pay
    form.biz_agency_fee = props.price.biz_agency_fee
    form.is_included_baf = props.price.is_included_baf
    form.middle_pay = props.price.middle_pay
    form.remain_pay = props.price.remain_pay
  }
}

const dataReset = () => {
  form.price_build = null
  form.price_land = null
  form.price_tax = null
  form.price = null
  form.down_pay = null
  form.biz_agency_fee = null
  form.is_included_baf = false
  form.middle_pay = null
  form.remain_pay = null
}

onMounted(() => dataSetup())
onUpdated(() => {
  dataReset()
  dataSetup()
})
</script>

<template>
  <CTableRow>
    <CTableDataCell class="text-center">
      {{ condTexts?.orderText }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      {{ condTexts?.typeText }}
    </CTableDataCell>
    <CTableDataCell>
      {{ floor.alias_name }}
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_build"
        type="number"
        min="0"
        placeholder="타입별 건물가"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_land"
        type="number"
        min="0"
        placeholder="타입별 대지가"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_tax"
        type="number"
        min="0"
        placeholder="타입별 부가세"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price"
        type="number"
        min="0"
        placeholder="타입별 공급가격"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <!--    <CTableDataCell>-->
    <!--      <CFormInput-->
    <!--        v-model.number="form.down_pay"-->
    <!--        type="number"-->
    <!--        min="0"-->
    <!--        placeholder="계약금"-->
    <!--        @keydown.enter="onStorePrice"-->
    <!--      />-->
    <!--    </CTableDataCell>-->
    <!--    <CTableDataCell>-->
    <!--      <CFormInput-->
    <!--        v-model.number="form.biz_agency_fee"-->
    <!--        type="number"-->
    <!--        min="0"-->
    <!--        placeholder="업무대행비"-->
    <!--        @keydown.enter="onStorePrice"-->
    <!--      />-->
    <!--    </CTableDataCell>-->
    <!--    <CTableDataCell>-->
    <!--      <CFormSwitch v-model="form.is_included_baf" :id="`iib-${price?.pk}`" label="업대비 포함" />-->
    <!--    </CTableDataCell>-->
    <!--    <CTableDataCell>-->
    <!--      <CFormInput-->
    <!--        v-model.number="form.middle_pay"-->
    <!--        type="number"-->
    <!--        min="0"-->
    <!--        placeholder="중도금"-->
    <!--        @keydown.enter="onStorePrice"-->
    <!--      />-->
    <!--    </CTableDataCell>-->
    <!--    <CTableDataCell>-->
    <!--      <CFormInput-->
    <!--        v-model.number="form.remain_pay"-->
    <!--        type="number"-->
    <!--        min="0"-->
    <!--        placeholder="잔금"-->
    <!--        @keydown.enter="onStorePrice"-->
    <!--      />-->
    <!--    </CTableDataCell>-->
    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn :color="btnColor" size="x-small" :disabled="formsCheck" @click="onStorePrice">
        {{ btnTitle }}
      </v-btn>
      <v-btn color="warning" size="x-small" :disabled="!price" @click="deletePrice"> 삭제</v-btn>
    </CTableDataCell>
    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="primary" size="x-small" @click="refFormModal.callModal()"> 추가</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="refFormModal">
    <template #header>특별약정 추가</template>
    <template #default>
      <CForm>
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel for="inputEmail3" class="col-sm-4 col-form-label">기준 공급가</CFormLabel>
            <CCol sm="8" class="pt-2">
              <span class="text-primary bold">{{ numFormat(price.price) }} </span>
              ({{ condTexts?.orderText }} / {{ condTexts?.typeText }} / {{ floor.alias_name }})
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="inputEmail3" class="col-sm-4 col-form-label">지정 납부회차</CFormLabel>
            <CCol sm="8">
              <CFormSelect>
                <option value="">---------</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="inputPassword3" class="col-sm-4 col-form-label">
              납부 약정금액
            </CFormLabel>
            <CCol sm="8">
              <CFormInput
                type="number"
                placeholder="특별 지정 납부 약정금액"
                text="일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나, 이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" size="small" @click="refFormModal.close()"> 닫기</v-btn>
          <v-btn color="primary" size="small" disabled>확인</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 공급가격 삭제</template>
    <template #default>
      해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 공급가격 정보를 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
