<script lang="ts" setup>
import { ref, watch } from 'vue'
import { btnLight } from '@/utils/cssMixins'
import { useNotice } from '@/store/pinia/notice'
import FormModal from '@/components/Modals/FormModal.vue'

// Props
const props = defineProps<{
  editItem?: { id: number; title: string; message_type: string; content: string } | null
}>()

// Store
const notiStore = useNotice()

// Modal ref
const formModal = ref()

// Form state
const form = ref({
  title: '',
  message_type: 'SMS',
  content: '',
})

const submitting = ref(false)

const resetForm = () => {
  form.value = {
    title: '',
    message_type: 'SMS',
    content: '',
  }
}

// Watch props to populate the form when editing
watch(
  () => props.editItem,
  newVal => {
    if (newVal) {
      form.value = {
        title: newVal.title,
        message_type: newVal.message_type,
        content: newVal.content,
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
  if (!form.value.title) {
    alert('템플릿 제목을 입력해주세요.')
    return
  }

  if (!form.value.content) {
    alert('메시지 내용을 입력해주세요.')
    return
  }

  submitting.value = true

  try {
    if (props.editItem) {
      // 수정 모드
      await notiStore.updateMessageTemplate(props.editItem.id, {
        title: form.value.title,
        message_type: form.value.message_type as 'SMS' | 'LMS' | 'MMS',
        content: form.value.content,
      })
    } else {
      // 생성 모드
      await notiStore.createMessageTemplate(form.value)
    }
    closeModal()
  } catch (error) {
    console.error('메시지 템플릿 등록/수정 실패:', error)
  } finally {
    submitting.value = false
  }
}

defineExpose({ openModal, closeModal })
</script>

<template>
  <FormModal ref="formModal">
    <template #icon>
      <v-icon icon="mdi-text-box" size="small" color="primary" class="mr-2" />
    </template>
    <template #header>
      {{ editItem ? '메시지 템플릿 수정' : '메시지 템플릿 등록' }}
    </template>

    <CModalBody>
      <!-- 템플릿 제목 -->
      <CFormInput
        v-model="form.title"
        label="템플릿 제목"
        placeholder="예: 납입 안내 템플릿"
        required
        class="mb-3"
      />

      <!-- 메시지 타입 -->
      <CFormSelect
        v-model="form.message_type"
        label="메시지 타입"
        :options="[
          { value: 'SMS', label: 'SMS (90자 이내)' },
          { value: 'LMS', label: 'LMS (장문메시지)' },
          { value: 'MMS', label: 'MMS (멀티미디어)' },
        ]"
        class="mb-3"
      />

      <!-- 메시지 내용 -->
      <div class="mb-3">
        <CFormLabel>메시지 내용</CFormLabel>
        <CFormTextarea v-model="form.content" rows="6" placeholder="메시지 내용을 입력하세요..." />
        <small class="text-muted"> 변수 사용 시: {이름}, {금액} 등의 형식으로 입력 가능 </small>
      </div>
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
