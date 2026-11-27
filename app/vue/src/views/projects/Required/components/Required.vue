<script lang="ts" setup>
import { computed, reactive, ref, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms'
import type { RequiredDocs } from '@/store/types/contract'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  requiredDoc: { type: Object as PropType<RequiredDocs>, required: true },
  disabled: Boolean,
})

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const accountStore = useAccount()
const isSuperAuth = computed(() => accountStore.superAuth)

const contStore = useContract()
const documentTypeList = computed(() => contStore.documentTypeList)
const existingOtherTypeIds = computed(() =>
  contStore.requiredDocsList
    .filter(doc => doc.pk !== props.requiredDoc?.pk)
    .map(doc => doc.document_type),
)

const parseNum = (val: number | '' | null | undefined): number | null =>
  val !== undefined && val !== null && val !== '' ? Number(val) : null

const form = reactive({
  sort: 'proof' as 'proof' | 'pledge',
  document_type: undefined as number | undefined,
  quantity: undefined as number | '' | undefined,
  require_type: 'required' as 'required' | 'optional' | 'conditional',
  description: '',
  display_order: undefined as number | '' | undefined,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const isFormUnchanged = computed(() => {
  const qty = parseNum(form.quantity)
  const order = parseNum(form.display_order)
  return (
    form.sort === props.requiredDoc?.sort &&
    form.document_type === props.requiredDoc?.document_type &&
    (qty !== null ? qty : 1) === props.requiredDoc?.quantity &&
    form.require_type === props.requiredDoc?.require_type &&
    form.description === (props.requiredDoc?.description ?? '') &&
    (order !== null ? order : 0) === (props.requiredDoc?.display_order ?? 0)
  )
})

const isFormValid = computed(() => {
  const qty = parseNum(form.quantity)
  const order = parseNum(form.display_order)
  return Boolean(form.document_type) && (qty === null || qty >= 0) && (order === null || order >= 0)
})

const onUpdateRequiredDoc = async () => {
  if (isFormUnchanged.value || !isFormValid.value) return

  if (canProjectUpdate.value) {
    const qty = parseNum(form.quantity)
    const order = parseNum(form.display_order)
    try {
      await contStore.updateRequiredDoc(props.requiredDoc.pk, {
        sort: form.sort,
        document_type: form.document_type,
        require_type: form.require_type,
        description: form.description,
        quantity: qty !== null ? qty : 1,
        display_order: order !== null ? order : 0,
      })
    } catch (error) {
      console.error('Failed to update required document:', error)
    }
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteRequiredDoc = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
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
  if (!props.requiredDoc) return
  form.sort = props.requiredDoc.sort
  form.document_type = props.requiredDoc.document_type
  form.quantity = props.requiredDoc.quantity
  form.require_type = props.requiredDoc.require_type
  form.description = props.requiredDoc.description ?? ''
  form.display_order = props.requiredDoc.display_order ?? 0
}

watch(() => props.requiredDoc, dataSetup, { immediate: true, deep: true })
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.sort" :disabled="disabled || !canProjectUpdate" required>
        <option value="proof">증빙서류</option>
        <option value="pledge">동의서류</option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.document_type" :disabled="disabled || !canProjectUpdate" required>
        <option value="">서류 유형</option>
        <option
          v-for="tp in documentTypeList"
          :key="tp.pk"
          :value="tp.pk"
          :disabled="existingOtherTypeIds.includes(tp.pk)"
        >
          {{ tp.name }}{{ existingOtherTypeIds.includes(tp.pk) ? ' (이미 등록됨)' : '' }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.quantity"
        placeholder="필요 수량"
        type="number"
        min="0"
        :disabled="disabled || !canProjectUpdate"
        @keydown.enter.prevent="onUpdateRequiredDoc"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormSelect v-model="form.require_type" :disabled="disabled || !canProjectUpdate" required>
        <option value="required">필수</option>
        <option value="optional">선택</option>
        <option value="conditional">조건부 필수</option>
      </CFormSelect>
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.description"
        maxlength="255"
        placeholder="설명"
        :disabled="disabled || !canProjectUpdate"
        @keydown.enter.prevent="onUpdateRequiredDoc"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.display_order"
        placeholder="표시 순서"
        type="number"
        min="0"
        :disabled="disabled || !canProjectUpdate"
        @keydown.enter.prevent="onUpdateRequiredDoc"
      />
    </CTableDataCell>

    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn
        color="success"
        size="x-small"
        :disabled="isFormUnchanged || !isFormValid"
        @click="onUpdateRequiredDoc"
      >
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteRequiredDoc">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header>구비 서류 삭제</template>
    <template #default>
      해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 구비 서류 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
