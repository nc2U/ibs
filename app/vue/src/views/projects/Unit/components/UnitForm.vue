<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import type { AllHouseUnit, HouseUnitUpdatePayload } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ unit: { type: Object as PropType<AllHouseUnit>, required: true } })
const emit = defineEmits<{
  (e: 'on-update', payload: HouseUnitUpdatePayload): void
  (e: 'on-delete', payload: { pk: number; type: number }): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const refAlertModal = ref()
const refConfirmModal = ref()

interface UnitFormData {
  unit_type: number | null
  floor_type: number | null
  building_unit: number | null
  name: string
  bldg_line: number | '' | null
  floor_no: number | '' | null
  is_hold: boolean
  hold_reason: string
}

const form = ref<UnitFormData>({
  unit_type: null,
  floor_type: null,
  building_unit: null,
  name: '',
  bldg_line: null,
  floor_no: null,
  is_hold: false,
  hold_reason: '',
})

const isEmptyNum = (val: number | '' | null | undefined): val is '' | null | undefined =>
  val === null || val === undefined || val === ''

const isUnchanged = computed(() => {
  return (
    form.value.unit_type === (props.unit?.unit_type?.pk ?? null) &&
    form.value.floor_type === (props.unit?.floor_type ?? null) &&
    form.value.building_unit === (props.unit?.building_unit ?? null) &&
    form.value.name.trim() === (props.unit?.name ?? '') &&
    (isEmptyNum(form.value.bldg_line) ? null : Number(form.value.bldg_line)) ===
      (props.unit?.bldg_line ?? null) &&
    (isEmptyNum(form.value.floor_no) ? null : Number(form.value.floor_no)) ===
      (props.unit?.floor_no ?? null) &&
    form.value.is_hold === (props.unit?.is_hold ?? false) &&
    form.value.hold_reason.trim() === (props.unit?.hold_reason ?? '')
  )
})

const isInvalid = computed(() => {
  return (
    !form.value.unit_type ||
    !form.value.floor_type ||
    !form.value.building_unit ||
    !form.value.name.trim() ||
    isEmptyNum(form.value.bldg_line) ||
    isEmptyNum(form.value.floor_no)
  )
})

const formCheck = computed(() => isUnchanged.value || isInvalid.value)

const proDataStore = useProjectData()
const getTypes = computed(() => proDataStore.getTypes)
const getFloorTypes = computed(() => proDataStore.getFloorTypes)
const buildingList = computed(() => proDataStore.buildingList)

const onUpdateUnit = () => {
  if (formCheck.value) return

  if (canProjectUpdate.value && props.unit?.pk) {
    emit('on-update', {
      pk: props.unit.pk,
      unit_type: Number(form.value.unit_type),
      floor_type: Number(form.value.floor_type),
      building_unit: Number(form.value.building_unit),
      name: form.value.name.trim(),
      bldg_line: Number(form.value.bldg_line),
      floor_no: Number(form.value.floor_no),
      is_hold: form.value.is_hold,
      hold_reason: form.value.hold_reason.trim(),
    })
  } else {
    refAlertModal.value?.callModal()
    dataSetup()
  }
}

const onDeleteUnit = () => {
  if (isSuperAuth.value) refConfirmModal.value?.callModal()
  else {
    refAlertModal.value?.callModal()
    dataSetup()
  }
}

const delConfirm = () => {
  if (props.unit?.pk && props.unit?.unit_type?.pk) {
    emit('on-delete', { pk: props.unit.pk, type: props.unit.unit_type.pk })
  }
  refConfirmModal.value?.close()
}

const dataSetup = () => {
  form.value.unit_type = props.unit?.unit_type?.pk ?? null
  form.value.floor_type = props.unit?.floor_type ?? null
  form.value.building_unit = props.unit?.building_unit ?? null
  form.value.name = props.unit?.name ?? ''
  form.value.bldg_line = props.unit?.bldg_line ?? null
  form.value.floor_no = props.unit?.floor_no ?? null
  form.value.is_hold = props.unit?.is_hold ?? false
  form.value.hold_reason = props.unit?.hold_reason ?? ''
}

onMounted(() => dataSetup())
watch(
  () => props.unit,
  () => dataSetup(),
  { deep: true },
)
</script>

<template>
  <CTableRow class="text-center">
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type" :disabled="!canProjectUpdate" required>
        <option value="">타입</option>
        <option v-for="ut in getTypes" :key="ut.value" :value="ut.value">
          {{ ut.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.floor_type" :disabled="!canProjectUpdate" required>
        <option value="">층범위타입</option>
        <option v-for="fl in getFloorTypes" :key="fl.value" :value="fl.value">
          {{ fl.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model.number="form.building_unit" :disabled="!canProjectUpdate" required>
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
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.bldg_line"
        type="number"
        min="1"
        placeholder="라인"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.floor_no"
        type="number"
        min="-10"
        placeholder="층수"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormCheck v-model="form.is_hold" :disabled="!canProjectUpdate" />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.hold_reason"
        maxlength="100"
        placeholder="홀딩 사유"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateUnit"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate">
      <v-btn color="success" size="x-small" :disabled="formCheck" @click="onUpdateUnit">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteUnit">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header>호수 유닛 삭제</template>
    <template #default>
      이 호수에 등록된 계약 건 데이터가 있는 경우 해당 계약 데이터의 동호수 유니트 정보가
      삭제됩니다. 해당 호수 유닛을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="delConfirm">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
