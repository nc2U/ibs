<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import type { SenderNumber } from '@/store/types/notice.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

// Props
const props = defineProps<{
  editItem?: { id: number; phone_number: string; label: string } | null
}>()

// Store
const notiStore = useNotice()

// Modal refs
const formModal = ref()
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)

// Form state
const form = ref({
  phone_number: '',
  label: '',
})

const submitting = ref(false)
const editingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)

const resetForm = () => {
  form.value = {
    phone_number: '',
    label: '',
  }
  editingId.value = null
}

// Watch props to populate form when editing
watch(
  () => props.editItem,
  newVal => {
    if (newVal) {
      editingId.value = newVal.id
      form.value = {
        phone_number: newVal.phone_number,
        label: newVal.label,
      }
    } else {
      resetForm()
    }
  },
)

const openModal = () => {
  if (!props.editItem) resetForm()
  formModal.value?.callModal()
}

const closeModal = () => {
  resetForm()
  formModal.value?.close()
}

const handleEdit = (item: SenderNumber) => {
  editingId.value = item.id
  form.value = {
    phone_number: item.phone_number,
    label: item.label || '',
  }
}

const confirmDelete = (id: number) => {
  deletingId.value = id
  refConfirmModal.value?.callModal(
    '발신번호 삭제',
    '정말 이 발신번호를 삭제하시겠습니까?',
    'mdi-alert-box',
    'red-lighten-3',
    '삭제',
    'error',
  )
}

const handleDelete = async () => {
  if (!deletingId.value) return
  try {
    await notiStore.deleteSenderNumber(deletingId.value)
    if (editingId.value === deletingId.value) {
      resetForm()
    }
    deletingId.value = null
    refConfirmModal.value?.close()
  } catch (error) {
    console.error('발신번호 삭제 실패:', error)
  }
}

const handleSubmit = async () => {
  const digitsOnly = form.value.phone_number.replace(/[^\d]/g, '')
  if (!digitsOnly || digitsOnly.length < 9 || digitsOnly.length > 11) {
    refAlertModal.value?.callModal(
      '발신번호 확인',
      '올바른 발신번호(9~11자리 숫자)를 입력해주세요.',
    )
    return
  }

  submitting.value = true

  try {
    if (editingId.value) {
      await notiStore.updateSenderNumber(editingId.value, form.value)
      resetForm()
    } else {
      await notiStore.createSenderNumber(form.value)
      resetForm()
    }
  } catch (error) {
    console.error('발신번호 등록/수정 실패:', error)
  } finally {
    submitting.value = false
  }
}

defineExpose({ openModal, closeModal })
</script>

<template>
  <FormModal ref="formModal">
    <template #icon>
      <v-icon icon="mdi-phone-plus" size="small" color="primary" class="me-2" />
    </template>
    <template #header>
      {{ editingId ? '발신번호 수정' : '발신번호 등록' }}
    </template>

    <CModalBody>
      <!-- 주의 메시지 -->
      <CAlert color="warning" class="mb-3">
        <strong>⚠️ 주의사항</strong><br />
        이 시스템에 등록하기 전에
        <strong>
          iwinv 관리자 페이지(https://console.iwinv.kr/msg/sender)에서 반드시 사전 등록
        </strong>
        을 완료해야 합니다. iwinv에 등록되지 않은 번호는 SMS 발송 시 오류가 발생합니다.
      </CAlert>

      <!-- 발신번호 입력 -->
      <div class="mb-3">
        <CFormLabel>발신번호</CFormLabel>
        <input
          v-model="form.phone_number"
          v-maska
          data-maska="['###-###-####', '###-####-####']"
          placeholder="예: 02-1234-5678 또는 01012345678"
          class="form-control"
          required
        />
      </div>

      <!-- 설명 입력 -->
      <CFormInput
        v-model="form.label"
        label="설명 (선택)"
        placeholder="예: 본사, 고객센터"
        class="mb-3"
      />
    </CModalBody>

    <CModalFooter>
      <v-btn
        :color="editingId ? 'success' : 'primary'"
        variant="flat"
        size="small"
        @click="handleSubmit"
        :loading="submitting"
      >
        {{ editingId ? '수정' : '등록' }}
      </v-btn>
      <v-btn v-if="editingId" color="primary" variant="flat" size="small" @click="resetForm">
        신규 입력
      </v-btn>
      <v-btn color="light" variant="flat" size="small" @click="closeModal" :disabled="submitting">
        닫기
      </v-btn>
    </CModalFooter>

    <!-- 등록된 발신번호 목록 -->
    <CModalBody>
      <v-divider class="my-3" />
      <h6 class="mb-2">
        <v-icon icon="mdi-phone-settings" class="me-2" size="small" />
        등록된 발신번호 ({{ notiStore.senderNumbers.length }}개)
      </h6>
      <div style="max-height: 220px; overflow-y: auto">
        <v-alert v-if="notiStore.senderNumbers.length === 0" type="info" variant="tonal">
          등록된 발신번호가 없습니다.
        </v-alert>
        <v-list v-else density="compact">
          <v-list-item v-for="item in notiStore.senderNumbers" :key="item.id" class="py-0">
            <v-list-item-title>
              <strong>{{ item.phone_number }}</strong>
              <span v-if="item.label" class="text-grey ms-2">({{ item.label }})</span>
            </v-list-item-title>
            <template #append>
              <v-btn
                icon="mdi-pencil"
                size="20"
                rounded
                variant="text"
                color="success"
                @click="handleEdit(item)"
              />
              <v-btn
                icon="mdi-delete"
                size="20"
                rounded
                variant="text"
                color="grey"
                @click="confirmDelete(item.id)"
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </CModalBody>
  </FormModal>

  <ConfirmModal ref="refConfirmModal" @confirm-func="handleDelete" />
  <AlertModal ref="refAlertModal" />
</template>
