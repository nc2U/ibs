<script lang="ts" setup>
import { ref, reactive, computed, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import type { UnitFloorType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  floor: { type: Object as PropType<UnitFloorType>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: UnitFloorType): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive<{
  sort: '' | '1' | '2' | '3' | '4' | '5' | '6'
  start_floor: number | ''
  end_floor: number | ''
  extra_cond: string
  alias_name: string
}>({
  sort: '',
  start_floor: '',
  end_floor: '',
  extra_cond: '',
  alias_name: '',
})

// 시작 층이 종료 층보다 큰지 여부 검증
const isRangeInvalid = computed(() => {
  if (form.start_floor === '' || form.end_floor === '') return false
  return Number(form.start_floor) > Number(form.end_floor)
})

// 기존 데이터와 동일한지 여부
const isUnchanged = computed(() => {
  return (
    form.sort === props.floor.sort &&
    Number(form.start_floor) === props.floor.start_floor &&
    Number(form.end_floor) === props.floor.end_floor &&
    form.extra_cond.trim() === (props.floor.extra_cond || '') &&
    form.alias_name.trim() === props.floor.alias_name
  )
})

// 수정 버튼 비활성화 여부
const formsCheck = computed(() => {
  return (
    !form.sort ||
    form.start_floor === '' ||
    form.end_floor === '' ||
    !form.alias_name.trim() ||
    isRangeInvalid.value ||
    isUnchanged.value
  )
})

const onUpdateFloor = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.floor.pk,
      project: props.floor.project,
      sort: form.sort,
      start_floor: Number(form.start_floor),
      end_floor: Number(form.end_floor),
      extra_cond: form.extra_cond.trim(),
      alias_name: form.alias_name.trim(),
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteFloor = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.floor.pk) {
    emit('on-delete', props.floor.pk)
  }
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.sort = props.floor.sort
  form.start_floor = props.floor.start_floor
  form.end_floor = props.floor.end_floor
  form.extra_cond = props.floor.extra_cond ?? ''
  form.alias_name = props.floor.alias_name ?? ''
}

watch(
  () => props.floor,
  () => dataSetup(),
  { deep: true, immediate: true },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.sort" :disabled="!canProjectUpdate" required>
        <option value="">---------</option>
        <option value="1">공동주택</option>
        <option value="2">오피스텔</option>
        <option value="3">숙박시설</option>
        <option value="4">지식산업센터</option>
        <option value="5">근린생활시설</option>
        <option value="6">기타</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.start_floor"
        placeholder="시작 층"
        type="number"
        min="-10"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateFloor"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.end_floor"
        placeholder="종료 층"
        type="number"
        min="-10"
        :disabled="!canProjectUpdate"
        required
        :invalid="isRangeInvalid"
        @keydown.enter.prevent="onUpdateFloor"
      />
      <div v-if="isRangeInvalid" class="text-danger small mt-1">
        ※ 종료 층은 시작 층 이상이어야 합니다.
      </div>
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.extra_cond"
        maxlength="20"
        placeholder="방향/위치"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateFloor"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.alias_name"
        maxlength="20"
        placeholder="층별 범위 명칭"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateFloor"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateFloor">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteFloor">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 층별 타입 삭제</template>
    <template #default>
      이 타입에 종속된 분양가 데이터가 있는 경우 해당 데이터를 모두 제거한 후 삭제가능 합니다. 해당
      층별 타입을 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
