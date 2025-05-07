<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useProjectData } from '@/store/pinia/project_data'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ unit: { type: Object, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = ref({
  unit_type: null,
  floor_type: null,
  building_unit: null,
  name: '',
  bldg_line: null,
  floor_no: null,
  is_hold: false,
  hold_reason: '',
})

const formCheck = computed(() => {
  const a = form.value.unit_type === props.unit.unit_type.pk
  const b = form.value.floor_type === props.unit.floor_type
  const c = form.value.building_unit === props.unit.building_unit
  const d = form.value.name === props.unit.name
  const e = form.value.bldg_line === props.unit.bldg_line
  const f = form.value.floor_no === props.unit.floor_no
  const g = form.value.is_hold === props.unit.is_hold
  const h = form.value.hold_reason === props.unit.hold_reason
  return a && b && c && d && e && f && g && h
})

const proDataStore = useProjectData()
const getTypes = computed(() => proDataStore.getTypes)
const getFloorTypes = computed(() => proDataStore.getFloorTypes)
const buildingList = computed(() => proDataStore.buildingList)

const onUpdateUnit = () => {
  if (write_project) {
    const pk = props.unit.pk
    emit('on-update', { ...{ pk }, ...form.value })
  } else refAlertModal.value.callModal()
}

const onDeleteUnit = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else refAlertModal.value.callModal()
}

const delConfirm = () => {
  emit('on-delete', { pk: props.unit.pk, type: props.unit.unit_type.pk })
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.value.unit_type = props.unit.unit_type.pk
  form.value.floor_type = props.unit.floor_type
  form.value.building_unit = props.unit.building_unit
  form.value.name = props.unit.name
  form.value.bldg_line = props.unit.bldg_line
  form.value.floor_no = props.unit.floor_no
  form.value.is_hold = props.unit.is_hold
  form.value.hold_reason = props.unit.hold_reason
}

onMounted(() => dataSetup())
</script>

<template>
  <CTableRow class="text-center">
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type" reqired>
        <option value="">타입</option>
        <option v-for="ut in getTypes" :key="ut.value" :value="ut.value">
          {{ ut.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.floor_type" reqired>
        <option value="">층범위타입</option>
        <option v-for="fl in getFloorTypes" :key="fl.value" :value="fl.value">
          {{ fl.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model.number="form.building_unit" reqired>
        <option value="">동</option>
        <option v-for="bd in buildingList" :key="bd.pk" :value="bd.pk">
          {{ bd.name }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.name"
        maxlength="5"
        placeholder="호수"
        reqired
        @keydown.enter="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.bldg_line"
        type="number"
        num="0"
        placeholder="라인"
        reqired
        @keydown.enter="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.floor_no"
        type="number"
        num="0"
        placeholder="층수"
        reqired
        @keydown.enter="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormCheck v-model="form.is_hold" />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.hold_reason"
        maxlength="100"
        placeholder="홀딩 사유"
        @keydown.enter="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell v-if="write_project">
      <v-btn color="success" size="small" :disabled="formCheck" @click="onUpdateUnit"> 수정 </v-btn>
      <v-btn color="warning" size="small" @click="onDeleteUnit">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 호수 유닛 삭제</template>
    <template #default>
      이 호수에 등록된 계약 건 데이터가 있는 경우 해당 계약 데이터의 동호수 유니트 정보가
      삭제됩니다. 해당 호수 유닛을 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" @click="delConfirm">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
