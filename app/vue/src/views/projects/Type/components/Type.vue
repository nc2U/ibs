<script lang="ts" setup>
import { computed, inject, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import type { SortType } from './TypeAddForm.vue'
import type { UnitType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  type: { type: Object as PropType<UnitType>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: UnitType): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const typeSort = inject<SortType[]>('typeSort')

interface TypeFormState {
  sort: '1' | '2' | '3' | '4' | '5' | '6' | ''
  main_or_sub: '1' | '2' | ''
  name: string
  color: string
  actual_area: number | '' | null
  supply_area: number | '' | null
  contract_area: number | '' | null
  average_price: number | '' | null
  price_setting: '1' | '2' | '3' | ''
  num_unit: number | '' | null
}

const form = ref<TypeFormState>({
  sort: '',
  main_or_sub: '',
  name: '',
  color: '',
  actual_area: null,
  supply_area: null,
  contract_area: null,
  average_price: null,
  price_setting: '',
  num_unit: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const isUnchanged = computed(() => {
  if (!props.type) return true
  const formNum = (v: number | '' | null) => (v === null || v === '' ? null : Number(v))
  const propNum = (v: number | string | null | undefined) =>
    v === null || v === undefined || v === '' ? null : Number(v)

  return (
    form.value.sort === props.type.sort &&
    form.value.main_or_sub === props.type.main_or_sub &&
    form.value.name.trim() === (props.type.name ?? '') &&
    form.value.color === props.type.color &&
    formNum(form.value.actual_area) === propNum(props.type.actual_area) &&
    formNum(form.value.supply_area) === propNum(props.type.supply_area) &&
    formNum(form.value.contract_area) === propNum(props.type.contract_area) &&
    formNum(form.value.average_price) === propNum(props.type.average_price) &&
    form.value.price_setting === props.type.price_setting &&
    formNum(form.value.num_unit) === propNum(props.type.num_unit)
  )
})

const isInvalid = computed(() => {
  return (
    !form.value.sort ||
    !form.value.main_or_sub ||
    !form.value.name.trim() ||
    !form.value.color ||
    !form.value.price_setting ||
    form.value.num_unit === null ||
    form.value.num_unit === '' ||
    Number(form.value.num_unit) < 0
  )
})

const formsCheck = computed(() => isUnchanged.value || isInvalid.value)

const onUpdateType = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.type.pk,
      project: props.type.project,
      sort: form.value.sort,
      main_or_sub: form.value.main_or_sub,
      name: form.value.name.trim(),
      color: form.value.color,
      actual_area:
        form.value.actual_area !== null && form.value.actual_area !== ''
          ? Number(form.value.actual_area)
          : null,
      supply_area:
        form.value.supply_area !== null && form.value.supply_area !== ''
          ? Number(form.value.supply_area)
          : null,
      contract_area:
        form.value.contract_area !== null && form.value.contract_area !== ''
          ? Number(form.value.contract_area)
          : null,
      average_price:
        form.value.average_price !== null && form.value.average_price !== ''
          ? Number(form.value.average_price)
          : null,
      price_setting: form.value.price_setting,
      num_unit: Number(form.value.num_unit),
    })
  } else {
    refAlertModal.value?.callModal()
    dataSetup()
  }
}

const onDeleteType = () => {
  if (isSuperAuth.value) refConfirmModal.value?.callModal()
  else {
    refAlertModal.value?.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.type?.pk) {
    emit('on-delete', props.type.pk)
  }
  refConfirmModal.value?.close()
}

const dataSetup = () => {
  if (props.type) {
    form.value.sort = props.type.sort ?? ''
    form.value.main_or_sub = props.type.main_or_sub ?? ''
    form.value.name = props.type.name ?? ''
    form.value.color = props.type.color ?? ''
    form.value.actual_area =
      props.type.actual_area !== null && props.type.actual_area !== undefined
        ? Number(props.type.actual_area)
        : null
    form.value.supply_area =
      props.type.supply_area !== null && props.type.supply_area !== undefined
        ? Number(props.type.supply_area)
        : null
    form.value.contract_area =
      props.type.contract_area !== null && props.type.contract_area !== undefined
        ? Number(props.type.contract_area)
        : null
    form.value.average_price =
      props.type.average_price !== null && props.type.average_price !== undefined
        ? Number(props.type.average_price)
        : null
    form.value.price_setting = props.type.price_setting ?? ''
    form.value.num_unit =
      props.type.num_unit !== null && props.type.num_unit !== undefined
        ? Number(props.type.num_unit)
        : null
  }
}

onBeforeMount(() => dataSetup())
watch(
  () => props.type,
  () => dataSetup(),
  { deep: true },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.sort" :disabled="!canProjectUpdate" required>
        <option v-for="tp in typeSort" :key="tp.value" :value="tp.value">
          {{ tp.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.main_or_sub" :disabled="!canProjectUpdate" required>
        <option value="1">메인유닛</option>
        <option value="2">보조시설</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.name"
        maxlength="10"
        placeholder="타입명칭"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.color"
        title="타입색상"
        type="color"
        :disabled="!canProjectUpdate"
        required
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.actual_area"
        placeholder="전용면적"
        type="number"
        min="0"
        step="0.0001"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.supply_area"
        placeholder="공급면적"
        type="number"
        min="0"
        step="0.0001"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.contract_area"
        placeholder="계약면적"
        type="number"
        min="0"
        step="0.0001"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.average_price"
        placeholder="평균가격"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.price_setting" :disabled="!canProjectUpdate" required>
        <option value="1">타입별 설정</option>
        <option value="2">층타입별 설정</option>
        <option value="3">호별 설정</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.num_unit"
        placeholder="세대수"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateType"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateType">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteType">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header>타입 정보 삭제</template>
    <template #default>
      이 타입에 종속 데이터가 있는 경우 해당 데이터를 모두 제거한 후 삭제가능 합니다. 해당 타입을
      삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
