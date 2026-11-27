<script lang="ts" setup>
import { ref, reactive, computed, watch, type PropType } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account'
import type { OrderGroup } from '@/store/types/contract.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  order: { type: Object as PropType<OrderGroup>, required: true },
  hasDefault: { type: Boolean, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: OrderGroup): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const form = reactive<{
  order_number: number | ''
  sort: '1' | '2' | ''
  name: string
  is_default_for_uncontracted: boolean
}>({
  order_number: '',
  sort: '',
  name: '',
  is_default_for_uncontracted: false,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const isUnchanged = computed(() => {
  return (
    Number(form.order_number) === props.order?.order_number &&
    form.sort === props.order?.sort &&
    form.name.trim() === props.order?.name &&
    form.is_default_for_uncontracted === props.order?.is_default_for_uncontracted
  )
})

const formsCheck = computed(() => {
  return (
    form.order_number === '' ||
    Number(form.order_number) <= 0 ||
    !form.sort ||
    !form.name.trim() ||
    isUnchanged.value
  )
})

// 체크박스 disabled 로직: 다른 항목이 이미 기본으로 설정되어 있는 경우 비활성화
const isCheckboxDisabled = computed(() => {
  return props.hasDefault && !props.order?.is_default_for_uncontracted
})

const onUpdateOrder = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.order.pk,
      project: props.order.project,
      order_number: Number(form.order_number),
      sort: form.sort as '1' | '2',
      sort_desc: props.order.sort_desc,
      name: form.name.trim(),
      is_default_for_uncontracted: form.is_default_for_uncontracted,
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteOrder = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.order?.pk) {
    emit('on-delete', props.order.pk)
  }
  refConfirmModal.value.close()
}

const dataSetup = () => {
  if (props.order) {
    form.order_number = props.order.order_number
    form.sort = props.order.sort
    form.name = props.order.name
    form.is_default_for_uncontracted = props.order.is_default_for_uncontracted
  }
}

watch(
  () => props.order,
  () => dataSetup(),
  { deep: true, immediate: true },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.order_number"
        type="number"
        min="1"
        required
        placeholder="등록차수"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOrder"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormSelect v-model="form.sort" :disabled="!canProjectUpdate" required>
        <option value="">구분선택</option>
        <option value="1">조합모집</option>
        <option value="2">일반분양</option>
      </CFormSelect>
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.name"
        maxlength="20"
        placeholder="차수그룹명"
        required
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOrder"
      />
    </CTableDataCell>

    <CTableDataCell class="ps-lg-5 pt-sm-3 pt-lg-1">
      <CFormCheck
        v-model="form.is_default_for_uncontracted"
        :disabled="!canProjectUpdate || isCheckboxDisabled"
        label="미계약세대 기본설정"
        :id="`uncontracted-base-order-${order.pk}`"
      />
      <div class="form-text d-none d-lg-block">
        미계약 세대 분양(공급)가격 생성 시 적용할 기본 차수 여부
      </div>
    </CTableDataCell>

    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateOrder">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteOrder">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 차수그룹 삭제</template>
    <template #default>
      이 그룹에 종속 데이터가 있는 경우 해당 데이터를 모두 제거한 후 삭제가능 합니다. 해당
      차수그룹을 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
