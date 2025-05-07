<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ floor: { type: Object, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({
  sort: '',
  start_floor: null,
  end_floor: null,
  extra_cond: '',
  alias_name: '',
})

const formsCheck = computed(() => {
  const a = form.sort === props.floor.sort
  const b = form.start_floor === props.floor.start_floor
  const c = form.end_floor === props.floor.end_floor
  const d = form.extra_cond === props.floor.extra_cond
  const e = form.alias_name === props.floor.alias_name
  return a && b && c && d && e
})

const formCheck = (bool: boolean) => {
  if (bool) onUpdateFloor()
  return
}

const onUpdateFloor = () => {
  if (write_project.value) {
    const pk = props.floor.pk
    emit('on-update', { ...{ pk }, ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteFloor = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const modalAction = () => {
  emit('on-delete', props.floor.pk)
  refConfirmModal.value.close()
}
const dataSetup = () => {
  form.sort = props.floor.sort
  form.start_floor = props.floor.start_floor
  form.end_floor = props.floor.end_floor
  form.extra_cond = props.floor.extra_cond
  form.alias_name = props.floor.alias_name
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.sort" required>
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
        required
        @keypress.enter="formCheck(form.start_floor !== floor.start_floor)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.end_floor"
        placeholder="종료 층"
        type="number"
        min="-10"
        required
        @keypress.enter="formCheck(form.end_floor !== form.end_floor)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.extra_cond"
        maxlength="20"
        placeholder="방향/위치"
        @keypress.enter="formCheck(form.extra_cond !== floor.extra_cond)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.alias_name"
        maxlength="20"
        placeholder="층별 범위 명칭"
        required
        @keypress.enter="formCheck(form.alias_name !== floor.alias_name)"
      />
    </CTableDataCell>
    <CTableDataCell v-if="write_project" class="text-center">
      <v-btn color="success" size="small" :disabled="formsCheck" @click="onUpdateFloor">
        수정
      </v-btn>
      <v-btn color="warning" size="small" @click="onDeleteFloor">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 층별 타입 삭제</template>
    <template #default>
      이 타입에 종속된 분양가 데이터가 있는 경우 해당 데이터를 모두 제거한 후 삭제가능 합니다. 해당
      층별 타입을 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
