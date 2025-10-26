<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useContract } from '@/store/pinia/contract.ts'
import { write_project } from '@/utils/pageAuth'
import type { RequiredDocs } from '@/store/types/contract.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  requiredDoc: { type: Object as () => RequiredDocs, required: true },
  disabled: Boolean
})

const emit = defineEmits(['on-update', 'on-delete'])

const contStore = useContract()

const form = reactive({
  sort: 'proof' as 'proof' | 'pledge',
  document_type: null as null | number,
  quantity: null as null | number,
  require_type: 'required' as 'required' | 'optional' | 'conditional',
  description: '',
  display_order: null as null | number,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.sort === props.requiredDoc.sort
  const b = form.document_type === props.requiredDoc.document_type
  const c = form.quantity === props.requiredDoc.quantity
  const d = form.require_type === props.requiredDoc.require_type
  const e = form.description === props.requiredDoc.description
  const f = form.display_order === props.requiredDoc.display_order
  return a && b && c && d && e && f
})

const onUpdateRequiredDoc = async () => {
  if (write_project.value) {
    try {
      await contStore.updateRequiredDoc(props.requiredDoc.pk, form)
    } catch (error) {
      console.error('Failed to update required document:', error)
    }
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteRequiredDoc = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = async () => {
  try {
    await contStore.deleteRequiredDoc(props.requiredDoc.pk, props.requiredDoc.project)
    refConfirmModal.value.close()
  } catch (error) {
    console.error('Failed to delete required document:', error)
  }
}

const dataSetup = () => {
  form.sort = props.requiredDoc.sort
  form.document_type = props.requiredDoc.document_type
  form.quantity = props.requiredDoc.quantity
  form.require_type = props.requiredDoc.require_type
  form.description = props.requiredDoc.description
  form.display_order = props.requiredDoc.display_order
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.sort" :disabled="disabled" required>
        <option value="proof">증빙서류</option>
        <option value="pledge">동의서류</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.document_type" :disabled="disabled" required>
        <option value="">서류 유형</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.quantity"
        placeholder="필요 수량"
        type="number"
        min="0"
        :disabled="disabled"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormSelect v-model="form.require_type" :disabled="disabled" required>
        <option value="required">필수</option>
        <option value="optional">선택</option>
        <option value="conditional">조건부 필수</option>
      </CFormSelect>
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.description"
        maxlength="255"
        placeholder="비고"
        :disabled="disabled"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.display_order"
        placeholder="표시 순서"
        type="number"
        min="0"
        :disabled="disabled"
      />
    </CTableDataCell>

    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateRequiredDoc">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeleteRequiredDoc">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 구비 서류 삭제</template>
    <template #default>
      해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 계약 조건 정보를 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
