<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import { btnLight } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import { CModalBody } from '@coreui/vue'

// Props
const props = defineProps<{
  editItem?: { id: number; phone_number: string; label: string } | null
}>()

// Store
const notiStore = useNotice()

// Modal ref
const formModal = ref()

// Form state
const form = ref({
  phone_number: '',
  label: '',
})

const submitting = ref(false)

const resetForm = () => {
  form.value = {
    phone_number: '',
    label: '',
  }
}

// Watch props to populate form when editing
watch(
  () => props.editItem,
  newVal => {
    if (newVal) {
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
  formModal.value?.callModal()
}

const closeModal = () => {
  resetForm()
  formModal.value?.close()
}

const handleSubmit = async () => {
  if (!form.value.phone_number) return

  submitting.value = true

  try {
    if (props.editItem) {
      // 수정 모드
      await notiStore.updateSenderNumber(props.editItem.id, form.value)
    } else {
      // 생성 모드
      await notiStore.createSenderNumber(form.value)
    }
    closeModal()
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
      <v-icon icon="mdi-phone-plus" size="small" color="primary" class="mr-2" />
    </template>
    <template #header>
      {{ editItem ? '발신번호 수정' : '발신번호 등록' }}
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
      <input
        v-model="form.phone_number"
        label="발신번호"
        v-maska
        data-maska="['###-###-####', '###-####-####']"
        placeholder="예: 02-1234-5678 또는 01012345678"
        class="mb-3 form-control"
        required
      />

      <!-- 설명 입력 -->
      <CFormInput
        v-model="form.label"
        label="설명 (선택)"
        placeholder="예: 본사, 고객센터"
        class="mb-3"
      />
    </CModalBody>

    <CModalFooter>
      <v-btn :color="btnLight" size="small" @click="closeModal" :disabled="submitting">
        취소
      </v-btn>
      <v-btn color="primary" size="small" @click="handleSubmit" :loading="submitting">
        {{ editItem ? '수정' : '등록' }}
      </v-btn>
    </CModalFooter>
  </FormModal>
</template>
